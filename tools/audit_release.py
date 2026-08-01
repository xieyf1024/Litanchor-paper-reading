#!/usr/bin/env python3
"""Fail CI on evaluation-answer leakage or private artifacts in public payloads."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path, PurePosixPath


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


def _skill_compaction_audit() -> dict[str, object]:
    entry = SKILL / "SKILL.md"
    text = entry.read_text(encoding="utf-8")
    lines = text.splitlines()
    normalized_rules: dict[str, list[int]] = {}
    in_frontmatter = False
    fence = False
    for number, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if stripped == "---" and number <= 5:
            in_frontmatter = not in_frontmatter
            continue
        if stripped.startswith("```"):
            fence = not fence
            continue
        if in_frontmatter or fence or len(stripped) < 50:
            continue
        if stripped.startswith(("#", "|")):
            continue
        normalized = re.sub(r"\s+", " ", stripped).casefold()
        normalized_rules.setdefault(normalized, []).append(number)
    duplicates = [numbers for numbers in normalized_rules.values() if len(numbers) > 1]
    referenced = sorted(
        set(re.findall(r"`((?:references|assets)/[^`]+)`", text))
    )
    missing = [relative for relative in referenced if not (SKILL / relative).is_file()]
    issues: list[str] = []
    if len(lines) > 100:
        issues.append(f"SKILL.md has {len(lines)} lines; public entry limit is 100")
    if duplicates:
        issues.append(f"SKILL.md has duplicate long-form rules at lines {duplicates}")
    if missing:
        issues.append(f"SKILL.md references missing resources: {missing}")
    return {
        "status": "passed" if not issues else "failed",
        "skill_line_count": len(lines),
        "referenced_resource_count": len(referenced),
        "duplicate_long_rule_count": len(duplicates),
        "missing_resources": missing,
        "issues": issues,
    }


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


def _is_private_runtime_path(relative: str) -> bool:
    directories = tuple(
        part.casefold() for part in PurePosixPath(relative).parts[:-1]
    )
    for private_path in PRIVATE_PATH_PARTS:
        pattern = tuple(
            part.casefold() for part in PurePosixPath(private_path).parts
        )
        width = len(pattern)
        if any(
            directories[index : index + width] == pattern
            for index in range(len(directories) - width + 1)
        ):
            return True
    return False


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
        if _is_private_runtime_path(relative):
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
    compaction = _skill_compaction_audit()
    issues.extend(f"Skill compaction: {item}" for item in compaction["issues"])
    return {
        "status": "passed" if not issues else "failed",
        "tracked_file_count": len(tracked),
        "evaluation_token_count": len(_evaluation_tokens()),
        "skill_compaction": compaction,
        "issues": sorted(set(issues)),
    }


def main() -> int:
    result = audit()
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
