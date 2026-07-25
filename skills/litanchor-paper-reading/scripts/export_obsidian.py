#!/usr/bin/env python3
"""Export a validated LitAnchor note into one explicitly authorized Obsidian test root."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from litanchor_local import PipelineError, atomic_write_text, load_json


SIDECAR_FILES = (
    "evidence.json",
    "claims.json",
    "figures.json",
    "coverage_receipt.json",
    "validation.json",
    "run.json",
)
WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _existing_directory(path: Path, label: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise PipelineError(f"{label} does not exist: {path}") from exc
    if not resolved.is_dir():
        raise PipelineError(f"{label} is not a directory: {resolved}")
    return resolved


def safe_note_stem(title: str, fallback: str) -> str:
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title).strip().rstrip(". ")
    stem = re.sub(r"\s+", " ", stem)[:120].rstrip(". ") or fallback
    if stem.upper() in WINDOWS_RESERVED:
        stem = f"_{stem}"
    return stem


def export_run(
    run_dir: Path,
    allowed_root: Path,
    inbox: Path,
    *,
    allow_warnings: bool = False,
    confirmed: bool = False,
) -> dict[str, object]:
    if not confirmed:
        raise PipelineError("Export requires explicit confirmation")
    run_dir = _existing_directory(run_dir, "Run directory")
    allowed_root = _existing_directory(allowed_root, "Authorized root")
    inbox = _existing_directory(inbox, "Inbox")
    if inbox == allowed_root or not _inside(inbox, allowed_root):
        raise PipelineError("Inbox must be a child directory of the authorized root")

    source = load_json(run_dir / "source-bundle.json")
    validation = load_json(run_dir / "validation.json")
    status = validation.get("status")
    if status not in {"completed", "completed_with_warnings"}:
        raise PipelineError(f"Only a completed validation can be exported; status is {status!r}")
    if status == "completed_with_warnings" and not allow_warnings:
        raise PipelineError("Validation has warnings; repeat with explicit warning acceptance")
    quality = validation.get("quality", {})
    if quality.get("format_valid") is not True:
        raise PipelineError("Markdown format validation did not pass")

    preview_value = validation.get("files", {}).get("markdown_note")
    if not isinstance(preview_value, str) or not preview_value:
        raise PipelineError("Validation does not identify a Markdown preview")
    preview = Path(preview_value).resolve(strict=True)
    if preview.suffix.casefold() != ".md" or not _inside(preview, run_dir):
        raise PipelineError("Validated Markdown preview must be inside the run directory")
    markdown = preview.read_text(encoding="utf-8")
    digest = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
    if quality.get("markdown_sha256") != digest:
        raise PipelineError("Markdown preview changed after validation")
    if not markdown.startswith("---\n") or "<!-- litanchor:user:start -->" not in markdown or "<!-- litanchor:user:end -->" not in markdown:
        raise PipelineError("Markdown preview is missing required Obsidian note markers")

    paper_id = str(source.get("paper_id", "")).strip()
    if not re.fullmatch(r"[A-Za-z0-9._-]+", paper_id):
        raise PipelineError("SourceBundle contains an unsafe paper_id")
    title = str(source.get("metadata", {}).get("title", "")).strip()
    note_path = inbox / f"{safe_note_stem(title, paper_id)}.md"
    sidecar_parent = allowed_root / ".litanchor"
    if sidecar_parent.exists() and not _inside(sidecar_parent.resolve(strict=True), allowed_root):
        raise PipelineError("Existing .litanchor directory escapes the authorized root")
    sidecar_dir = sidecar_parent / paper_id
    if sidecar_dir.exists() and not _inside(sidecar_dir.resolve(strict=True), allowed_root):
        raise PipelineError("Existing paper sidecar directory escapes the authorized root")
    sidecar_paths = [sidecar_dir / name for name in SIDECAR_FILES]

    collisions = [path for path in [note_path, *sidecar_paths] if path.exists()]
    if collisions:
        raise PipelineError(f"Refusing to overwrite existing export: {collisions[0]}")
    payloads: dict[Path, str] = {}
    for name, destination in zip(SIDECAR_FILES, sidecar_paths):
        source_path = run_dir / name
        if not source_path.is_file():
            raise PipelineError(f"Required export sidecar is missing: {source_path}")
        payloads[destination] = source_path.read_text(encoding="utf-8")

    sidecar_dir.mkdir(parents=True, exist_ok=True)
    if not _inside(sidecar_dir.resolve(strict=True), allowed_root):
        raise PipelineError("Resolved sidecar directory escapes the authorized root")
    for destination, payload in payloads.items():
        atomic_write_text(destination, payload, overwrite=False)
    atomic_write_text(note_path, markdown, overwrite=False)
    return {
        "status": "exported_with_warnings" if status == "completed_with_warnings" else "exported",
        "note": str(note_path),
        "sidecars": [str(path) for path in sidecar_paths],
        "overwritten": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safely export a validated LitAnchor run to Obsidian")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--allowed-root", type=Path, required=True)
    parser.add_argument("--inbox", type=Path, required=True)
    parser.add_argument("--allow-warnings", action="store_true")
    parser.add_argument("--confirm-export", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = export_run(
            args.run_dir,
            args.allowed_root,
            args.inbox,
            allow_warnings=args.allow_warnings,
            confirmed=args.confirm_export,
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except PipelineError as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
