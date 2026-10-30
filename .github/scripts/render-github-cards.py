#!/usr/bin/env python3
"""Render GitHub stats and top-language cards as SVGs.

Public profile data comes from the GraphQL API. The default Actions
GITHUB_TOKEN can read it; a personal access token is not required.
Writes github-stats.svg and github-top-langs.svg into OUTPUT_DIR.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

API_URL = "https://api.github.com/graphql"
PROFILE = os.environ.get("GITHUB_REPOSITORY", "rimkahan888/rimkahan888")
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "dist"))
LANG_LIMIT = 6
CARD_W = 452
CARD_H = 200
BG = "#0d1117"
SURFACE = "#161b22"
BORDER = "#30363d"
TITLE = "#F7B32B"
TEXT = "#f0f6fc"
MUTED = "#8b949e"
TRACK = "#21262d"
FONT = "Segoe UI, Ubuntu, Helvetica, Arial, sans-serif"

REPOSITORIES = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    login
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions
    }
    repositories(
      first: 100
      after: $cursor
      ownerAffiliations: OWNER
      isFork: false
      privacy: PUBLIC
    ) {
      pageInfo { hasNextPage endCursor }
      nodes {
        stargazerCount
        languages(first: 100, orderBy: {field: SIZE, direction: DESC}) {
          pageInfo { hasNextPage }
          edges { size node { name color } }
        }
      }
    }
  }
}
"""


def owner_login(profile: str) -> str:
    owner, _, name = profile.partition("/")
    if not owner or not name:
        raise SystemExit(f"GITHUB_REPOSITORY must look like owner/name, got {profile!r}")
    return owner


def graphql(token: str, query: str, variables: dict) -> dict:
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "profile-readme-stats-cards",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:500]
        raise SystemExit(f"GitHub API {error.code}: {detail}") from error
    if payload.get("errors"):
        raise SystemExit(f"GitHub GraphQL error: {json.dumps(payload['errors'])[:800]}")
    return payload["data"]


def fetch_profile(token: str, login: str) -> dict:
    stars = 0
    repos = 0
    languages: dict[str, dict] = {}
    followers = 0
    commits = 0
    cursor = None
    seen_user = False

    while True:
        data = graphql(token, REPOSITORIES, {"login": login, "cursor": cursor})
        user = data.get("user")
        if user is None:
            raise SystemExit(f"GitHub user {login!r} was not found")
        if not seen_user:
            followers = int(user["followers"]["totalCount"])
            commits = int(user["contributionsCollection"]["totalCommitContributions"])
            seen_user = True
        page = user["repositories"]
        for repo in page["nodes"]:
            repos += 1
            stars += int(repo.get("stargazerCount") or 0)
            language_page = repo.get("languages") or {}
            if language_page.get("pageInfo", {}).get("hasNextPage"):
                name = repo.get("name")
                raise SystemExit(f"Repository {name!r} has more than 100 languages; refusing to undercount")
            for edge in language_page.get("edges") or []:
                node = edge.get("node") or {}
                lang_name = str(node.get("name") or "").strip()
                if not lang_name:
                    continue
                size = int(edge.get("size") or 0)
                bucket = languages.setdefault(
                    lang_name,
                    {"name": lang_name, "size": 0, "color": node.get("color") or MUTED},
                )
                bucket["size"] += size
                if node.get("color"):
                    bucket["color"] = node["color"]
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]

    ranked = sorted(languages.values(), key=lambda item: (-item["size"], item["name"].lower()))
    return {
        "login": login,
        "stars": stars,
        "commits": commits,
        "followers": followers,
        "repos": repos,
        "languages": ranked,
    }


def xml_text(value: object) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def comma(value: int) -> str:
    return f"{value:,}"


def safe_color(value: object) -> str:
    text = str(value or "")
    if re.fullmatch(r"#[0-9A-Fa-f]{3}|#[0-9A-Fa-f]{6}", text):
        return text
    return MUTED


def icon(kind: str, x: float, y: float) -> str:
    """16px gold icons. Origin is the top-left of the icon box."""
    stroke = TITLE
    common = f'stroke="{stroke}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"'
    body = {
        "star": (
            f'<polygon points="8,1.4 10.0,5.9 14.8,6.4 11.2,9.6 12.2,14.4 8,12.0 3.8,14.4 4.8,9.6 1.2,6.4 6.0,5.9" '
            f'fill="{stroke}"/>'
        ),
        "commit": (
            f'<line x1="1" y1="8" x2="4.5" y2="8" {common}/>'
            f'<line x1="11.5" y1="8" x2="15" y2="8" {common}/>'
            f'<circle cx="8" cy="8" r="3.1" fill="none" {common}/>'
            f'<circle cx="8" cy="8" r="1.15" fill="{stroke}" stroke="none"/>'
        ),
        "pr": (
            f'<circle cx="4" cy="3.4" r="1.9" fill="none" {common}/>'
            f'<circle cx="4" cy="12.6" r="1.9" fill="none" {common}/>'
            f'<circle cx="12" cy="12.6" r="1.9" fill="none" {common}/>'
            f'<path d="M4 5.3 V10.7 M12 7.2 V10.7 M12 7.2 H7.2" fill="none" {common}/>'
            f'<path d="M9.2 5.4 L7.2 7.2 L9.2 9.0" fill="none" {common}/>'
        ),
        "issue": (
            f'<circle cx="8" cy="8" r="6" fill="none" {common}/>'
            f'<line x1="8" y1="4.6" x2="8" y2="8.6" {common}/>'
            f'<circle cx="8" cy="11.2" r="0.8" fill="{stroke}" stroke="none"/>'
        ),
        "people": (
            f'<circle cx="6" cy="5.2" r="2.1" fill="none" {common}/>'
            f'<path d="M1.6 13.4 c.5-2.5 2.1-3.8 4.4-3.8 s3.9 1.3 4.4 3.8" fill="none" {common}/>'
            f'<circle cx="11.4" cy="5.8" r="1.6" fill="none" {common}/>'
            f'<path d="M11.2 9.8 c1.6.2 2.8 1.1 3.3 2.6" fill="none" {common}/>'
        ),
        "repo": (
            f'<path d="M3 5.2 V12.4 c0 .7.5 1.2 1.2 1.2 H13 c.7 0 1.2-.5 1.2-1.2 V6.4 c0-.7-.5-1.2-1.2-1.2 H8.2 L7.2 4 H4.2 C3.5 4 3 4.5 3 5.2 Z" '
            f'fill="none" {common}/>'
        ),
    }[kind]
    return f'<g transform="translate({x:.1f} {y:.1f})">{body}</g>'


def card_shell(title: str, description: str, body: str, clip_id: str) -> str:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{CARD_H}" viewBox="0 0 {CARD_W} {CARD_H}" role="img">
  <title>{xml_text(title)}</title>
  <desc>{xml_text(description)}</desc>
  <defs>
    <clipPath id="{clip_id}">
      <rect width="{CARD_W}" height="{CARD_H}" rx="8"/>
    </clipPath>
  </defs>
  <g clip-path="url(#{clip_id})">
    <rect width="{CARD_W}" height="{CARD_H}" fill="{SURFACE}"/>
    <rect width="4" height="{CARD_H}" fill="{TITLE}"/>
    <text x="22" y="34" fill="{TITLE}" font-family="{FONT}" font-size="16" font-weight="700">{xml_text(title)}</text>
    {body}
  </g>
  <rect x="0.5" y="0.5" width="{CARD_W - 1}" height="{CARD_H - 1}" rx="8" fill="none" stroke="{BORDER}"/>
</svg>
"""
    ET.fromstring(svg)
    return svg


def render_stats(stats: dict) -> str:
    rows = [
        ("star", "Stars", stats["stars"]),
        ("commit", "Commits", stats["commits"]),
        ("pr", "Pull requests", stats["pull_requests"]),
        ("issue", "Issues", stats["issues"]),
        ("people", "Followers", stats["followers"]),
        ("repo", "Repositories", stats["repos"]),
    ]
    parts = [
        f'<text x="22" y="54" fill="{MUTED}" font-family="{FONT}" font-size="12">Public activity, forks excluded. Commits are the past year.</text>'
    ]
    for index, (kind, label, value) in enumerate(rows):
        column = index // 3
        row = index % 3
        x = 22 + column * 216
        y = 76 + row * 38
        parts.append(icon(kind, x, y))
        parts.append(
            f'<text x="{x + 24}" y="{y + 13}" fill="{MUTED}" font-family="{FONT}" font-size="13">{xml_text(label)}</text>'
        )
        parts.append(
            f'<text x="{x + 200}" y="{y + 13}" fill="{TEXT}" font-family="{FONT}" font-size="15" font-weight="700" text-anchor="end">{comma(value)}</text>'
        )
    description = (
        f"{stats['login']}: {comma(stats['stars'])} stars, "
        f"{comma(stats['commits'])} commits in the past year, "
        f"{comma(stats['pull_requests'])} pull requests, {comma(stats['issues'])} issues, "
        f"{comma(stats['followers'])} followers, {comma(stats['repos'])} public repositories"
    )
    return card_shell(f"{stats['login']}'s GitHub stats", description, "\n  ".join(parts), "stats-card")


def render_languages(stats: dict) -> str:
    languages = stats["languages"][:LANG_LIMIT]
    total = sum(item["size"] for item in stats["languages"])
    parts = [
        f'<text x="22" y="54" fill="{MUTED}" font-family="{FONT}" font-size="12">Share of code by file size, top {LANG_LIMIT}.</text>'
    ]
    if not languages or total <= 0:
        parts.append(
            f'<text x="22" y="110" fill="{TEXT}" font-family="{FONT}" font-size="14">No language data yet.</text>'
        )
    else:
        bar_x = 176
        bar_w = 196
        for index, language in enumerate(languages):
            y = 76 + index * 20
            share = language["size"] / total
            width = max(2.0, share * bar_w) if language["size"] else 0.0
            radius = min(4.0, width / 2)
            name = language["name"]
            if len(name) > 18:
                name = name[:17].rstrip() + "…"
            color = safe_color(language["color"])
            parts.append(
                f'<circle cx="28" cy="{y - 3}" r="4" fill="{xml_text(color)}"/>'
            )
            parts.append(
                f'<text x="40" y="{y}" fill="{TEXT}" font-family="{FONT}" font-size="13">{xml_text(name)}</text>'
            )
            parts.append(
                f'<rect x="{bar_x}" y="{y - 9}" width="{bar_w}" height="8" rx="4" fill="{TRACK}"/>'
            )
            parts.append(
                f'<rect x="{bar_x}" y="{y - 9}" width="{width:.2f}" height="8" rx="{radius:.2f}" fill="{xml_text(color)}"/>'
            )
            parts.append(
                f'<text x="{CARD_W - 18}" y="{y}" fill="{MUTED}" font-family="{FONT}" font-size="12" text-anchor="end">{share * 100:.1f}%</text>'
            )
    description = ", ".join(
        f"{item['name']} {item['size']}" for item in languages
    ) or "No languages"
    return card_shell("Most used languages", description, "\n  ".join(parts), "languages-card")


def pull_requests_and_issues(token: str, login: str) -> tuple[int, int]:
    """All-time authored pull requests and issues, matching the old stats card."""
    query = """
    query($login: String!) {
      user(login: $login) {
        pullRequests(states: [OPEN, CLOSED, MERGED]) { totalCount }
        issues(states: [OPEN, CLOSED]) { totalCount }
      }
    }
    """
    user = graphql(token, query, {"login": login})["user"]
    if user is None:
        raise SystemExit(f"GitHub user {login!r} was not found")
    return int(user["pullRequests"]["totalCount"]), int(user["issues"]["totalCount"])


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is not set")
    login = owner_login(PROFILE)
    stats = fetch_profile(token, login)
    stats["pull_requests"], stats["issues"] = pull_requests_and_issues(token, login)
    if stats["repos"] <= 0 or not stats["languages"]:
        raise SystemExit("Refusing to publish cards with no repositories or languages")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stats_path = OUTPUT_DIR / "github-stats.svg"
    langs_path = OUTPUT_DIR / "github-top-langs.svg"
    stats_path.write_text(render_stats(stats), encoding="utf-8")
    langs_path.write_text(render_languages(stats), encoding="utf-8")
    print(
        f"Wrote {stats_path} and {langs_path} "
        f"({stats['repos']} repos, {stats['stars']} stars, {len(stats['languages'])} languages)"
    )


if __name__ == "__main__":
    main()
