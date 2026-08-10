#!/usr/bin/env python3
"""Export a validated LitAnchor note into one explicitly authorized Obsidian test root."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
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
OPTIONAL_AUTONOMOUS_SIDECARS = (
    "autonomous-run.json",
    "page-classification.json",
    "section_map.json",
    "section_synthesis.json",
    "visual_analysis.json",
    "fidelity_review.json",
    "recall_review.json",
    "semantic-generation.json",
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
    original = str(title or "").strip()
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", original).strip().rstrip(". ")
    stem = re.sub(r"\s+", " ", stem) or fallback
    if len(stem) > 120:
        suffix = hashlib.sha256(original.encode("utf-8")).hexdigest()[:8]
        prefix = stem[:111].rstrip(" ._-—–")
        if " " in prefix:
            word_prefix = prefix.rsplit(" ", 1)[0].rstrip(" ._-—–")
            if len(word_prefix) >= 72:
                prefix = word_prefix
        stem = f"{prefix}-{suffix}"
    if stem.upper() in WINDOWS_RESERVED:
        stem = f"_{stem}"
    return stem


def safe_asset_slug(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug[:80].rstrip("-") or fallback


def candidate_export_required(run_record: dict[str, object]) -> bool:
    """Keep autonomous output provisional until its required review is accepted."""
    review_status = run_record.get("review_status")
    return review_status == "user_visual_review_pending" or (
        bool(run_record.get("autonomous_generation"))
        and review_status
        not in {"user_visual_review_passed", "independently_reviewed"}
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export_run(
    run_dir: Path,
    allowed_root: Path,
    inbox: Path,
    *,
    allow_warnings: bool = False,
    confirmed: bool = False,
    asset_slug: str | None = None,
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
    run_record = load_json(run_dir / "run.json")
    digest = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
    if quality.get("markdown_sha256") != digest:
        raise PipelineError("Markdown preview changed after validation")
    if not markdown.startswith("---\n"):
        raise PipelineError("Markdown preview is missing required Obsidian frontmatter")
    if "<!--" in markdown:
        raise PipelineError("Markdown preview contains internal HTML comments")

    paper_id = str(source.get("paper_id", "")).strip()
    if not re.fullmatch(r"[A-Za-z0-9._-]+", paper_id):
        raise PipelineError("SourceBundle contains an unsafe paper_id")
    title = str(source.get("metadata", {}).get("title", "")).strip()
    run_id = str(run_record.get("run_id") or run_dir.name).strip()
    if not re.fullmatch(r"[A-Za-z0-9._-]+", run_id):
        raise PipelineError("Run record contains an unsafe run_id")
    is_candidate = candidate_export_required(run_record)
    note_suffix = ".candidate.md" if is_candidate else ".md"
    note_path = inbox / f"{safe_note_stem(title, paper_id)}{note_suffix}"
    sidecar_parent = allowed_root / ".litanchor"
    if sidecar_parent.exists() and not _inside(sidecar_parent.resolve(strict=True), allowed_root):
        raise PipelineError("Existing .litanchor directory escapes the authorized root")
    sidecar_dir = sidecar_parent / run_id
    promoted_from: Path | None = None
    previous_receipt: dict[str, object] | None = None
    if sidecar_dir.exists() and not _inside(sidecar_dir.resolve(strict=True), allowed_root):
        raise PipelineError("Existing paper sidecar directory escapes the authorized root")
    previous_receipt_path = sidecar_dir / "export-receipt.json"
    if sidecar_dir.exists() and not is_candidate and previous_receipt_path.is_file():
        candidate_receipt = load_json(previous_receipt_path)
        previous_note_value = candidate_receipt.get("note")
        previous_note = (
            Path(previous_note_value)
            if isinstance(previous_note_value, str) and previous_note_value
            else None
        )
        if (
            candidate_receipt.get("run_id") == run_id
            and candidate_receipt.get("paper_id") == paper_id
            and candidate_receipt.get("review_status") == "user_visual_review_pending"
            and previous_note is not None
            and previous_note.name.endswith(".candidate.md")
            and previous_note.is_file()
            and run_record.get("review_status")
            in {"user_visual_review_passed", "independently_reviewed"}
        ):
            promoted_from = previous_receipt_path
            previous_receipt = candidate_receipt
            sidecar_dir = sidecar_parent / f"{run_id}-final"
    sidecar_names = [
        *SIDECAR_FILES,
        *(
            name
            for name in OPTIONAL_AUTONOMOUS_SIDECARS
            if (run_dir / name).is_file()
        ),
    ]
    sidecar_paths = [sidecar_dir / name for name in sidecar_names]

    figures = load_json(run_dir / "figures.json")
    selected = figures.get("selected", []) if isinstance(figures, dict) else []
    # Skim notes intentionally render Section 1 only.  Keep the complete visual
    # inventory in the private sidecar, but do not require or publish crops that
    # the reader-facing note does not embed.
    selected_for_export = [] if run_record.get("reading_mode") == "skim" else selected
    slug = safe_asset_slug(asset_slug or title, paper_id.casefold())
    asset_dir = allowed_root / "_assets" / slug
    visual_sources: list[tuple[Path, Path]] = []
    replacements: dict[str, str] = {}
    manifest_sources: list[Path] = []
    for visual in selected_for_export:
        if not isinstance(visual, dict):
            raise PipelineError("Selected visual must be an object")
        try:
            image_source = Path(str(visual["image_path"])).resolve(strict=True)
            manifest_source = Path(str(visual["manifest_path"])).resolve(strict=True)
        except (KeyError, FileNotFoundError) as exc:
            raise PipelineError("Selected visual is missing its image or manifest") from exc
        if not _inside(image_source, run_dir) or not _inside(manifest_source, run_dir):
            raise PipelineError("Selected visual artifacts must stay inside the run directory")
        old_embed = str(visual.get("embed_path") or "")
        if not old_embed:
            raise PipelineError("Selected visual is missing its source embed path")
        new_embed = f"_assets/{slug}/{image_source.name}"
        replacements[f"![[{old_embed}]]"] = f"![[{new_embed}]]"
        visual_sources.append((image_source, asset_dir / image_source.name))
        manifest_sources.append(manifest_source)
    for old_embed, new_embed in replacements.items():
        if old_embed not in markdown:
            raise PipelineError(f"Validated note does not contain selected visual {old_embed}")
        markdown = markdown.replace(old_embed, new_embed)
    unresolved_embeds = re.findall(r"!\[\[(visuals/[^]]+)\]\]", markdown)
    if unresolved_embeds:
        raise PipelineError(
            "Validated note still contains runtime visual embeds: "
            + ", ".join(unresolved_embeds)
        )

    reuse_visual_assets = False
    if promoted_from is not None and visual_sources:
        previous_asset_value = previous_receipt.get("asset_directory") if previous_receipt else None
        if not isinstance(previous_asset_value, str) or not previous_asset_value:
            raise PipelineError("Candidate export receipt has no visual asset directory")
        previous_asset_dir = Path(previous_asset_value).resolve(strict=True)
        if not _inside(previous_asset_dir, allowed_root):
            raise PipelineError("Candidate visual asset directory escapes the authorized root")
        if previous_asset_dir != asset_dir.resolve(strict=True):
            raise PipelineError("Promotion must reuse the candidate export asset directory")
        for source_image, destination in visual_sources:
            if not destination.is_file() or _sha256(destination) != _sha256(source_image):
                raise PipelineError(
                    f"Candidate visual asset differs from the accepted source: {destination}"
                )
        reuse_visual_assets = True

    collision_candidates = [
        note_path,
        sidecar_dir,
    ]
    if visual_sources and not reuse_visual_assets:
        collision_candidates.extend(destination for _, destination in visual_sources)
        collision_candidates.append(asset_dir)
    collisions = [path for path in collision_candidates if path.exists()]
    if collisions:
        raise PipelineError(f"Refusing to overwrite existing export: {collisions[0]}")
    payloads: dict[str, str] = {}
    for name in sidecar_names:
        source_path = run_dir / name
        if name in SIDECAR_FILES and not source_path.is_file():
            raise PipelineError(f"Required export sidecar is missing: {source_path}")
        if source_path.is_file():
            payloads[name] = source_path.read_text(encoding="utf-8")

    staging_parent = sidecar_parent / "_export_staging"
    staging_parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(tempfile.mkdtemp(prefix=f"{run_id}-", dir=staging_parent))
    moved: list[Path] = []
    try:
        staged_note = staging_dir / note_path.name
        atomic_write_text(staged_note, markdown, overwrite=False)
        staged_sidecars = staging_dir / "sidecars"
        staged_sidecars.mkdir()
        for name, payload in payloads.items():
            atomic_write_text(staged_sidecars / name, payload, overwrite=False)
        staged_assets = staging_dir / "assets"
        if visual_sources and not reuse_visual_assets:
            staged_assets.mkdir()
        exported_visuals: list[dict[str, str]] = []
        for (source_image, destination), manifest_source in zip(
            visual_sources,
            manifest_sources,
        ):
            if not reuse_visual_assets:
                staged_image = staged_assets / destination.name
                shutil.copy2(source_image, staged_image)
                if _sha256(staged_image) != _sha256(source_image):
                    raise PipelineError(f"Copied visual failed hash verification: {source_image}")
            staged_manifest = staged_sidecars / "visuals" / manifest_source.name
            staged_manifest.parent.mkdir(exist_ok=True)
            shutil.copy2(manifest_source, staged_manifest)
            exported_visuals.append(
                {
                    "source_image": str(source_image),
                    "exported_embed": f"_assets/{slug}/{destination.name}",
                    "sha256": _sha256(source_image),
                    "crop_manifest": f".litanchor/{run_id}/visuals/{manifest_source.name}",
                }
            )
        receipt = {
            "schema_version": "0.1",
            "status": (
                "exported_with_warnings"
                if status == "completed_with_warnings"
                else "exported"
            ),
            "run_id": run_id,
            "paper_id": paper_id,
            "validation_status": status,
            "review_status": run_record.get("review_status"),
            "note": str(note_path),
            "note_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
            "sidecar_directory": str(sidecar_dir),
            "asset_directory": str(asset_dir) if visual_sources else None,
            "visuals": exported_visuals,
            "overwritten": False,
            "promoted_from": str(promoted_from) if promoted_from else None,
            "reused_visual_assets": reuse_visual_assets,
        }
        atomic_write_text(
            staged_sidecars / "export-receipt.json",
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
            overwrite=False,
        )

        sidecar_parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(staged_sidecars), str(sidecar_dir))
        moved.append(sidecar_dir)
        if visual_sources and not reuse_visual_assets:
            asset_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(staged_assets), str(asset_dir))
            moved.append(asset_dir)
        shutil.move(str(staged_note), str(note_path))
        moved.append(note_path)
    except Exception:
        for path in reversed(moved):
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()
        raise
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)
    return {
        "status": "exported_with_warnings" if status == "completed_with_warnings" else "exported",
        "note": str(note_path),
        "sidecars": [str(path) for path in sidecar_paths],
        "receipt": str(sidecar_dir / "export-receipt.json"),
        "assets": [str(destination) for _, destination in visual_sources],
        "overwritten": False,
        "promoted_from": str(promoted_from) if promoted_from else None,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safely export a validated LitAnchor run to Obsidian")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--allowed-root", type=Path, required=True)
    parser.add_argument("--inbox", type=Path, required=True)
    parser.add_argument("--allow-warnings", action="store_true")
    parser.add_argument("--confirm-export", action="store_true")
    parser.add_argument("--asset-slug")
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
            asset_slug=args.asset_slug,
        )
        # Keep the CLI JSON stream portable on legacy Windows consoles whose
        # active encoding (for example GBK) cannot represent every paper title.
        print(json.dumps(result, ensure_ascii=True))
        return 0
    except PipelineError as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
