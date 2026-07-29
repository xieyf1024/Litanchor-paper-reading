#!/usr/bin/env python3
"""Repository-local Skill validation for clean CI environments."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml


def validate(skill: Path) -> dict[str, object]:
    issues: list[str] = []
    skill = skill.resolve()
    entry = skill / "SKILL.md"
    if not entry.is_file():
        return {"status": "failed", "issues": [f"Missing {entry}"]}
    text = entry.read_text(encoding="utf-8")
    frontmatter = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not frontmatter:
        issues.append("SKILL.md must start with YAML frontmatter")
    else:
        payload = yaml.safe_load(frontmatter.group(1))
        if not isinstance(payload, dict):
            issues.append("Skill frontmatter must be a mapping")
        elif set(payload) != {"name", "description"}:
            issues.append("Skill frontmatter may contain only name and description")
        else:
            if payload["name"] != "litanchor-paper-reading":
                issues.append("Unexpected Skill name")
            if "Use when" not in str(payload["description"]):
                issues.append("Description must include an explicit trigger")
    if len(text.splitlines()) > 100:
        issues.append("SKILL.md exceeds the 100-line lightweight limit")
    if re.search(r"\bv\d+\.\d+\b", text):
        issues.append("Operational SKILL.md must not pin a release version")
    for relative in sorted(set(re.findall(r"`((?:references|assets)/[^`]+)`", text))):
        if not (skill / relative).is_file():
            issues.append(f"Missing referenced resource: {relative}")
    for schema in sorted((skill / "schemas").glob("*.schema.json")):
        try:
            payload = json.loads(schema.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(f"Invalid schema {schema.name}: {exc}")
            continue
        if payload.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            issues.append(f"Unexpected JSON Schema draft: {schema.name}")
    return {
        "status": "passed" if not issues else "failed",
        "skill": str(skill),
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the LitAnchor Skill package")
    parser.add_argument(
        "skill",
        nargs="?",
        type=Path,
        default=Path("skills/litanchor-paper-reading"),
    )
    args = parser.parse_args()
    result = validate(args.skill)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
