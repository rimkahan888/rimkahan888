#!/usr/bin/env python3
"""Rewrite the Projects table in README.md (between the RECENT_REPOS markers).

Lists the projects in .github/featured-projects.json, in that order, with each
repo's current main language folded into each line (icon, tagline, detail from the JSON).
Leaves README.md untouched when nothing changed.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

START = "<!-- RECENT_REPOS:START -->"
END = "<!-- RECENT_REPOS:END -->"
DESCRIPTION_LIMIT = 140
README_PATH = Path(os.environ.get("README_PATH", "README.md"))
FEATURED_PATH = Path(os.environ.get("FEATURED_PATH", ".github/featured-projects.json"))
PROFILE = os.environ.get("GITHUB_REPOSITORY", "rimkahan888/rimkahan888")
BLOCK = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)


def owner_and_name(profile: str) -> tuple[str, str]:
    owner, _, name = profile.partition("/")
    if not owner or not name:
        raise SystemExit(f"GITHUB_REPOSITORY must look like owner/name, got {profile!r}")
    return owner, name


def github_json(url: str) -> list[dict]:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-readme-projects",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:500]
        raise SystemExit(f"GitHub API {error.code} for {url}: {detail}") from error
    if not isinstance(payload, list):
        raise SystemExit(f"Expected a list from {url}")
    return payload


def fetch_repos(owner: str) -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        url = (
            "https://api.github.com/users/"
            f"{owner}/repos?per_page=100&type=owner&sort=pushed&page={page}"
        )
        batch = github_json(url)
        repos.extend(batch)
        if len(batch) < 100:
            return repos
        page += 1


def one_line(value: str | None, fallback: str) -> str:
    text = re.sub(r"\s+", " ", (value or "")).strip()
    if not text:
        return fallback
    text = text.replace("|", "\\|")
    if len(text) > DESCRIPTION_LIMIT:
        text = text[: DESCRIPTION_LIMIT - 1].rstrip() + "…"
    return text


def eligible(repo: dict, profile: str, profile_name: str) -> bool:
    if repo.get("fork") or repo.get("private"):
        return False
    full_name = str(repo.get("full_name") or "")
    name = str(repo.get("name") or "")
    if full_name.lower() == profile.lower() or name.lower() == profile_name.lower():
        return False
    return int(repo.get("size") or 0) > 0


def load_featured() -> list[dict]:
    if not FEATURED_PATH.exists():
        return []
    items = json.loads(FEATURED_PATH.read_text(encoding="utf-8"))
    return [item for item in items if item.get("repo")]


BADGES = {  # language -> (shields colour, simple-icons logo)
    "TypeScript": ("3178C6", "typescript"), "C#": ("512BD4", "dotnet"),
    "HTML": ("E34F26", "html5"), "JavaScript": ("F7DF1E", "javascript"), "Python": ("3776AB", "python"),
}


def md_to_html(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def tex(text: str) -> str:
    return text.replace("#", r"\#").replace(" ", r"\ ")


def row(repo: dict, item: dict) -> str:
    name = str(repo["name"])
    url = str(repo.get("html_url") or f"https://github.com/{repo.get('full_name')}")
    language = str(repo.get("language") or "")
    icon = item.get("icon", "▫️")
    tagline = item.get("tagline") or one_line(repo.get("description"), "No description")
    detail = item.get("detail", "")
    tag = f" · $`\\small\\color{{#E8C36A}}\\textsf{{{tex(language)}}}`$" if language else ""
    tail = f" · {detail}" if detail else ""
    return f"- {icon} **[{name}]({url})** — *{tagline}*{tag}{tail}"


def render_table(repos: list[dict], profile: str, profile_name: str) -> str:
    by_name = {str(r.get("name") or "").lower(): r for r in repos}
    lines = []
    for item in load_featured():
        repo = by_name.get(str(item["repo"]).lower())
        if repo is None or repo.get("private"):
            continue
        lines.append(row(repo, item))

    return "\n".join(lines)


def replace_block(readme: str, table: str) -> str:
    if not BLOCK.search(readme):
        raise SystemExit("README is missing RECENT_REPOS:START / RECENT_REPOS:END markers")
    updated, count = BLOCK.subn(f"{START}\n{table}\n{END}", readme, count=1)
    if count != 1:
        raise SystemExit(f"Expected to replace one projects block, replaced {count}")
    return updated


def main() -> None:
    owner, profile_name = owner_and_name(PROFILE)
    table = render_table(fetch_repos(owner), PROFILE, profile_name)
    original = README_PATH.read_text(encoding="utf-8")
    updated = replace_block(original, table)
    if updated == original:
        print("Projects table is unchanged.")
        return
    README_PATH.write_text(updated, encoding="utf-8")
    print(f"Updated {README_PATH}")


if __name__ == "__main__":
    main()
