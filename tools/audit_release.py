#!/usr/bin/env python3
"""Fail CI on evaluation-answer leakage or private artifacts in public payloads."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "litanchor-paper-reading"
PRIVATE_PATH_PARTS = {
    "runtime",
    "Test-PDF",
    ".litanchor",
    "evolution/feedback",
    "evolution/trajectories",
}
SECRET_PATTERN = re.compile(
    r"""(?ix)
    (?:api[_-]?key|access[_-]?token|secret|password)
    \s*[:=]\s*
    ["'][A-Za-z0-9_./+=-]{20,}["']
    """
)


def _git_tracked_files() -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def _evaluation_tokens() -> list[str]:
    tokens: set[str] = set()
    for corpus in sorted((ROOT / "evals" / "cases").glob("*.json")):
        payload = json.loads(corpus.read_text(encoding="utf-8"))
        stack = [payload]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                for key, value in current.items():
                    if (
                        key.casefold() in {"title", "doi"}
                        and isinstance(value, str)
                        and len(value.strip()) >= 12
                    ):
                        tokens.add(value.strip())
                    elif isinstance(value, (dict, list)):
                        stack.append(value)
            elif isinstance(current, list):
                stack.extend(current)
    for example in (ROOT / "examples").glob("**/*.md"):
        text = example.read_text(encoding="utf-8")
        match = re.search(r"(?m)^title:\s*[\"']?(.+?)[\"']?\s*$", text)
        if match and len(match.group(1).strip()) >= 12:
            tokens.add(match.group(1).strip())
    return sorted(tokens, key=str.casefold)


def audit() -> dict[str, object]:
    issues: list[str] = []
    tracked = _git_tracked_files()
    for relative in tracked:
        folded = relative.casefold()
        if folded.endswith(".pdf"):
            issues.append(f"Tracked PDF: {relative}")
        if Path(relative).name.casefold() == ".env" or Path(relative).name.casefold().startswith(".env."):
            issues.append(f"Tracked environment file: {relative}")
        if any(part.casefold() in folded for part in PRIVATE_PATH_PARTS):
            issues.append(f"Tracked private runtime path: {relative}")

    distributable_text: list[tuple[Path, str]] = []
    for path in SKILL.rglob("*"):
        if path.is_file() and path.suffix.casefold() in {".md", ".py", ".json", ".yaml", ".yml"}:
            distributable_text.append((path, path.read_text(encoding="utf-8")))
    for token in _evaluation_tokens():
        folded = token.casefold()
        for path, text in distributable_text:
            if folded in text.casefold():
                issues.append(
                    f"Evaluation token leaked into distributable Skill: {token!r} in "
                    f"{path.relative_to(ROOT).as_posix()}"
                )
    for path, text in distributable_text:
        if SECRET_PATTERN.search(text):
            issues.append(f"Secret-shaped assignment in {path.relative_to(ROOT).as_posix()}")
    return {
        "status": "passed" if not issues else "failed",
        "tracked_file_count": len(tracked),
        "evaluation_token_count": len(_evaluation_tokens()),
        "issues": sorted(set(issues)),
    }


def main() -> int:
    result = audit()
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
