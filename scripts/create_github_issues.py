"""Parse docs/ISSUES_SEED.md and create real GitHub Issues from it via
`gh issue create`.

docs/ISSUES_SEED.md stays the single source of truth for issue content —
this script parses it directly rather than duplicating its content into a
separate data file that could drift out of sync.

Safe by default: running with no flags only PARSES and PRINTS what would
be created (a dry run). Nothing is created on GitHub unless you pass
--repo and --execute explicitly. Requires the GitHub CLI (`gh`),
authenticated, and a repository that already exists -- this script
creates issues in an existing repo, it does not create the repo itself
(see docs/GITHUB_LAUNCH_SETUP.md for that step).

Usage:
    python scripts/create_github_issues.py                       # dry run, prints all parsed issues
    python scripts/create_github_issues.py --track "Platform"    # dry run, filtered to one track
    python scripts/create_github_issues.py --repo OWNER/NAME --execute   # actually create them
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SEED_PATH = Path(__file__).resolve().parent.parent / "docs" / "ISSUES_SEED.md"

_GOOD_FIRST_HEADER = re.compile(
    r"^### (?P<num>\d+[a-z]?)\. \[(?P<track>[^\]]+)\] (?P<title>.+)$", re.MULTILINE
)
_GOOD_FIRST_LABELS = re.compile(r"^\*\*Labels:\*\* (?P<labels>.+)$", re.MULTILINE)

_COMPACT_ITEM = re.compile(
    r"^(?P<num>\d+[a-z]?)\. \*\*\[(?P<track>[^\]]+)\] (?P<title>[^*]+)\*\*"
    r"(?: — (?P<rest>.+))?$",
    re.MULTILINE,
)


@dataclass
class Issue:
    number: str
    track: str
    title: str
    labels: list[str]
    body: str

    @property
    def full_title(self) -> str:
        return f"[{self.track}] {self.title}"


def _extract_backtick_labels(text: str) -> list[str]:
    return re.findall(r"`([^`]+)`", text)


def parse_good_first_issues(text: str) -> list[Issue]:
    issues = []
    headers = list(_GOOD_FIRST_HEADER.finditer(text))
    for i, m in enumerate(headers):
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        block = text[start:end]
        labels_m = _GOOD_FIRST_LABELS.search(block)
        labels = _extract_backtick_labels(labels_m.group("labels")) if labels_m else []
        # Drop the **Labels:** line from the body -- gh issue create sets
        # labels structurally via --label, restating them in the body text
        # too is just noise.
        body = _GOOD_FIRST_LABELS.sub("", block).strip()
        issues.append(Issue(m.group("num"), m.group("track"), m.group("title").strip(), labels, body))
    return issues


_LEADING_LABEL_RUN = re.compile(r"^((?:`[^`]+`,?\s*)+)\.\s*(.*)$", re.DOTALL)


def parse_compact_issues(text: str) -> list[Issue]:
    issues = []
    for m in _COMPACT_ITEM.finditer(text):
        rest = (m.group("rest") or "").strip()
        # Only the leading run of backtick items (before the first period
        # that ends it) is the label list -- backtick-quoted code
        # references later in the body (file paths, function names) must
        # NOT be picked up as labels.
        run_m = _LEADING_LABEL_RUN.match(rest)
        if run_m:
            labels = _extract_backtick_labels(run_m.group(1))
            body = run_m.group(2).strip()
        else:
            labels = []
            body = rest
        issues.append(Issue(m.group("num"), m.group("track"), m.group("title").strip(), labels, body or rest))
    return issues


def _ensure_label(issues: list[Issue], label: str) -> None:
    """Section headers (## Help Wanted, ## Research) imply this label for
    every item in that section, even when an individual item doesn't
    redundantly restate it inline -- add it if missing rather than
    silently shipping an issue without its section's own label."""
    for issue in issues:
        if label not in issue.labels:
            issue.labels.append(label)


def parse_all(seed_text: str) -> list[Issue]:
    good_first_section = seed_text.split("## Good First Issues", 1)[1].split("## Help Wanted", 1)[0]
    help_and_research = seed_text.split("## Help Wanted", 1)[1]
    help_section, research_section = help_and_research.split("## Research", 1)

    good_first = parse_good_first_issues(good_first_section)
    help_wanted = parse_compact_issues(help_section)
    research = parse_compact_issues(research_section)

    _ensure_label(help_wanted, "help wanted")
    _ensure_label(research, "research")

    return good_first + help_wanted + research


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", help="owner/name of an EXISTING GitHub repo to create issues in")
    parser.add_argument("--execute", action="store_true", help="actually call `gh issue create` (default: dry run)")
    parser.add_argument("--track", help="only issues whose track name contains this (case-insensitive)")
    args = parser.parse_args()

    if not SEED_PATH.exists():
        print(f"ERROR: {SEED_PATH} not found", file=sys.stderr)
        return 1

    issues = parse_all(SEED_PATH.read_text(encoding="utf-8"))
    if args.track:
        issues = [i for i in issues if args.track.lower() in i.track.lower()]

    if not issues:
        print("No issues parsed/matched — check docs/ISSUES_SEED.md's format hasn't changed.", file=sys.stderr)
        return 1

    print(f"Parsed {len(issues)} issue(s) from {SEED_PATH}\n")

    if args.execute and not args.repo:
        print("ERROR: --execute requires --repo owner/name", file=sys.stderr)
        return 1

    for issue in issues:
        print(f"#{issue.number:<4} {issue.full_title}")
        print(f"      labels: {', '.join(issue.labels) or '(none parsed)'}")
        if not args.execute:
            continue
        cmd = [
            "gh", "issue", "create",
            "--repo", args.repo,
            "--title", issue.full_title,
            "--body", issue.body,
        ]
        for label in issue.labels:
            cmd += ["--label", label]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"      FAILED: {result.stderr.strip()}")
        else:
            print(f"      created: {result.stdout.strip()}")

    if not args.execute:
        print(
            "\nDry run only -- nothing was created. Re-run with "
            "--repo OWNER/NAME --execute against a real, already-created "
            "repository to actually file these."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
