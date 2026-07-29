#!/usr/bin/env python3
"""Check repository-local Markdown links without following network URLs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", ".venv", "runtime", "dist", ".tmp", "__pycache__"}
LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\(([^)\n]+)\)")
SCHEME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def check_links() -> dict[str, object]:
    issues: list[str] = []
    checked = 0
    for markdown in ROOT.rglob("*.md"):
        if any(part in EXCLUDED_PARTS for part in markdown.parts):
            continue
        text = markdown.read_text(encoding="utf-8")
        for raw in LINK_PATTERN.findall(text):
            target = raw.strip()
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            if not target or target.startswith("#") or "{{" in target or SCHEME_PATTERN.match(target):
                continue
            target = target.split("#", 1)[0].strip()
            if not target:
                continue
            # Markdown titles after a URL are outside this repository's style;
            # retain spaces because local filenames may legitimately contain them.
            resolved = (markdown.parent / unquote(target)).resolve()
            checked += 1
            if not resolved.exists():
                issues.append(
                    f"{markdown.relative_to(ROOT).as_posix()} -> {target}"
                )
    return {
        "status": "passed" if not issues else "failed",
        "checked_local_links": checked,
        "issues": issues,
    }


def main() -> int:
    result = check_links()
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
