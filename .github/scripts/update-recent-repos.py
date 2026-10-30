#!/usr/bin/env python3
"""Rewrite the Projects table in README.md (between the RECENT_REPOS markers).

One table: featured projects from .github/featured-projects.json first (marked
with a star, in that order), then the most recently pushed public repos that
aren't featured. Excludes forks, private and empty repos, and this profile repo.
Leaves README.md untouched when nothing changed.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

START = "<!-- RECENT_REPOS:START -->"
END = "<!-- RECENT_REPOS:END -->"
RECENT_LIMIT = 6
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


def row(repo: dict, summary: str, star: bool) -> str:
    name = str(repo["name"])
    url = str(repo.get("html_url") or f"https://github.com/{repo.get('full_name')}")
    label = f"⭐ [{name}]({url})" if star else f"[{name}]({url})"
    language = one_line(repo.get("language"), "—")
    updated = str(repo.get("pushed_at") or "")[:10] or "—"
    return f"| {label} | {summary} | {language} | {updated} |"


def render_table(repos: list[dict], profile: str, profile_name: str) -> str:
    by_name = {str(r.get("name") or "").lower(): r for r in repos}
    lines = [
        "| Project | Summary | Language | Updated |",
        "| --- | --- | --- | --- |",
    ]
    featured_names: set[str] = set()
    for item in load_featured():
        key = str(item["repo"]).lower()
        repo = by_name.get(key)
        if repo is None or repo.get("private"):
            continue
        featured_names.add(key)
        summary = one_line(item.get("summary") or repo.get("description"), "No description")
        lines.append(row(repo, summary, star=True))

    recent = [
        r for r in repos
        if eligible(r, profile, profile_name) and str(r.get("name") or "").lower() not in featured_names
    ]
    recent.sort(key=lambda r: (str(r.get("pushed_at") or ""), str(r.get("name") or "")), reverse=True)
    for repo in recent[:RECENT_LIMIT]:
        lines.append(row(repo, one_line(repo.get("description"), "No description"), star=False))
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
