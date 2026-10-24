#!/usr/bin/env python3
"""Rewrite the RECENT_REPOS block in README.md from the public repos API.

Excludes forks, this profile repository, and empty repositories (size 0).
Prints nothing and leaves the file untouched when the generated list matches
what is already between the markers.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

START = "<!-- RECENT_REPOS:START -->"
END = "<!-- RECENT_REPOS:END -->"
LIMIT = 8
DESCRIPTION_LIMIT = 140
README_PATH = Path(os.environ.get("README_PATH", "README.md"))
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
        "User-Agent": "profile-readme-recent-repos",
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
    if repo.get("fork"):
        return False
    if repo.get("private"):
        return False
    full_name = str(repo.get("full_name") or "")
    name = str(repo.get("name") or "")
    if full_name.lower() == profile.lower() or name.lower() == profile_name.lower():
        return False
    if int(repo.get("size") or 0) <= 0:
        return False
    return True


def render_table(repos: list[dict]) -> str:
    lines = [
        "| Repository | Description | Language |",
        "| --- | --- | --- |",
    ]
    for repo in repos:
        name = str(repo["name"])
        url = str(repo.get("html_url") or f"https://github.com/{repo.get('full_name')}")
        description = one_line(repo.get("description"), "No description")
        language = one_line(repo.get("language"), "—")
        lines.append(f"| [{name}]({url}) | {description} | {language} |")
    return "\n".join(lines)


def select_recent(repos: list[dict], profile: str, profile_name: str) -> list[dict]:
    chosen = [repo for repo in repos if eligible(repo, profile, profile_name)]
    chosen.sort(key=lambda repo: (str(repo.get("pushed_at") or ""), str(repo.get("name") or "")), reverse=True)
    return chosen[:LIMIT]


def replace_block(readme: str, table: str) -> str:
    if not BLOCK.search(readme):
        raise SystemExit("README is missing RECENT_REPOS:START / RECENT_REPOS:END markers")
    block = f"{START}\n{table}\n{END}"
    updated, count = BLOCK.subn(block, readme, count=1)
    if count != 1:
        raise SystemExit(f"Expected to replace one recent-repos block, replaced {count}")
    return updated


def main() -> None:
    owner, profile_name = owner_and_name(PROFILE)
    table = render_table(select_recent(fetch_repos(owner), PROFILE, profile_name))
    original = README_PATH.read_text(encoding="utf-8")
    updated = replace_block(original, table)
    if updated == original:
        print("Recent repositories list is unchanged.")
        return
    README_PATH.write_text(updated, encoding="utf-8")
    print(f"Updated {README_PATH}")


if __name__ == "__main__":
    main()
