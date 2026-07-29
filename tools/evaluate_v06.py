#!/usr/bin/env python3
"""Validate the frozen v0.6 corpus and summarize private run artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "evals" / "cases" / "v0.6-frozen-holdout.json"
DEFAULT_STATUS = ROOT / "evals" / "cases" / "v0.6-holdout-status.json"
FORBIDDEN_PRIVATE_FIELDS = {
    "zotero_item_key",
    "zotero_attachment_key",
    "pdf_path",
    "local_path",
}
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class EvaluationError(RuntimeError):
    """Raised when a frozen evaluation contract is not reproducible."""


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise EvaluationError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def validate_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest = load_json(path)
    serialized = json.dumps(manifest, ensure_ascii=False).casefold()
    leaked = sorted(field for field in FORBIDDEN_PRIVATE_FIELDS if field in serialized)
    if leaked:
        raise EvaluationError(
            f"Frozen manifest contains private runtime fields: {', '.join(leaked)}"
        )

    frozen_commit = str(manifest.get("frozen_skill_commit", ""))
    if not re.fullmatch(r"[0-9a-f]{40}", frozen_commit):
        raise EvaluationError("frozen_skill_commit must be a full Git commit SHA")
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", frozen_commit, "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise EvaluationError("Frozen Skill commit is not an ancestor of HEAD")

    rubric = manifest.get("rubric", {})
    rubric_path = ROOT / str(rubric.get("path", ""))
    if not rubric_path.is_file():
        raise EvaluationError(f"Frozen rubric is missing: {rubric_path}")
    expected_rubric_hash = str(rubric.get("sha256", "")).casefold()
    if sha256_file(rubric_path) != expected_rubric_hash:
        raise EvaluationError("Evaluation rubric changed after the holdout was frozen")

    cases = manifest.get("cases")
    if not isinstance(cases, list) or len(cases) < 3:
        raise EvaluationError("At least three frozen holdout cases are required")
    case_ids: set[str] = set()
    pdf_hashes: set[str] = set()
    for case in cases:
        case_id = str(case.get("case_id", ""))
        pdf_hash = str(case.get("pdf_sha256", "")).casefold()
        if not case_id or case_id in case_ids:
            raise EvaluationError(f"Duplicate or empty case_id: {case_id!r}")
        if not SHA256_PATTERN.fullmatch(pdf_hash) or pdf_hash in pdf_hashes:
            raise EvaluationError(f"Invalid or duplicate PDF SHA-256 for {case_id}")
        if case.get("split") != "frozen_holdout":
            raise EvaluationError(f"{case_id} is not marked frozen_holdout")
        if int(case.get("page_count", 0)) < 1:
            raise EvaluationError(f"{case_id} has no valid physical page count")
        case_ids.add(case_id)
        pdf_hashes.add(pdf_hash)

    return {
        "status": "pass",
        "manifest": str(path.resolve()),
        "frozen_skill_commit": frozen_commit,
        "evaluated_commit": _git("rev-parse", "HEAD"),
        "rubric_sha256": expected_rubric_hash,
        "case_count": len(cases),
    }


def _load_optional(path: Path) -> Any:
    return load_json(path) if path.is_file() else None


def _mineru_metrics(run_dir: Path) -> dict[str, Any]:
    plan = _load_optional(run_dir / "mineru-plan.json") or {}
    sections = _load_optional(run_dir / "sections.json") or []
    figures = _load_optional(run_dir / "figure-candidates.json") or []
    alignment = _load_optional(run_dir / "mineru" / "alignment.json") or {}
    stats = alignment.get("statistics", {}) if isinstance(alignment, dict) else {}
    return {
        "route": plan.get("route"),
        "status": plan.get("status"),
        "selected_original_pages": plan.get("selected_original_pages", []),
        "alignment": stats,
        "baseline_section_count": sum(
            item.get("source") != "mineru_aligned_heading"
            for item in sections
            if isinstance(item, dict)
        ),
        "mineru_added_section_count": sum(
            item.get("source") == "mineru_aligned_heading"
            for item in sections
            if isinstance(item, dict)
        ),
        "mineru_added_figure_candidate_count": sum(
            item.get("mineru_used_as") == "structure_hint"
            for item in figures
            if isinstance(item, dict)
        ),
        "authoritative_evidence_created": bool(
            plan.get("authoritative_evidence_created", False)
        ),
    }


def summarize_run(run_dir: Path) -> dict[str, Any]:
    source = load_json(run_dir / "source-bundle.json")
    evidence = _load_optional(run_dir / "evidence.json") or []
    claims = _load_optional(run_dir / "claims.json") or []
    autonomous = _load_optional(run_dir / "autonomous-run.json") or {}
    validation = _load_optional(run_dir / "validation.json") or {}
    fidelity = _load_optional(run_dir / "fidelity-review.json") or {}
    recall = _load_optional(run_dir / "recall-review.json") or {}
    final_notes = sorted(
        {
            *run_dir.glob("final-note*.md"),
            *run_dir.glob("final_note*.md"),
            *run_dir.glob("candidate-note.md"),
        }
    )
    return {
        "run_dir": str(run_dir.resolve()),
        "paper_title": source.get("metadata", {}).get("title"),
        "pdf_sha256": source.get("pdf", {}).get("sha256"),
        "page_count": source.get("pdf", {}).get("page_count"),
        "status": autonomous.get("status")
        or validation.get("status")
        or _load_optional(run_dir / "run.json").get("status"),
        "evidence_count": len(evidence),
        "claim_count": len(claims),
        "fidelity_status": fidelity.get("final_status"),
        "recall_status": recall.get("final_status"),
        "quality": validation.get("quality", {}),
        "final_note_present": bool(final_notes),
        "mineru": _mineru_metrics(run_dir),
    }


def release_gate_status(
    summary: dict[str, Any],
    expected_mineru_route: str,
) -> dict[str, Any]:
    """Apply deterministic release gates without replacing human content review."""
    quality = summary.get("quality", {})
    checks = {
        "terminal_status": summary.get("status")
        in {"completed", "completed_with_warnings"},
        "evidence_present": int(summary.get("evidence_count", 0)) > 0,
        "claims_present": int(summary.get("claim_count", 0)) > 0,
        "fidelity_pass": summary.get("fidelity_status") == "pass",
        "recall_pass": summary.get("recall_status") == "pass",
        "final_note_present": summary.get("final_note_present") is True,
        "mineru_route": summary.get("mineru", {}).get("route")
        == expected_mineru_route,
        "mineru_not_authoritative": summary.get("mineru", {}).get(
            "authoritative_evidence_created"
        )
        is False,
        "evidence_coverage": float(quality.get("evidence_coverage", 0)) == 1.0,
        "page_reference_accuracy": float(
            quality.get("page_reference_accuracy", 0)
        )
        >= 0.99,
        "numeric_fidelity": float(quality.get("numeric_fidelity", 0)) >= 0.995,
        "template_completeness": float(
            quality.get("template_completeness", 0)
        )
        == 1.0,
        "content_recall_pass": quality.get("content_recall_pass") is True,
        "format_valid": quality.get("format_valid") is True,
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
    }


def load_holdout_status(
    manifest: dict[str, Any],
    status_path: Path = DEFAULT_STATUS,
) -> dict[str, dict[str, Any]]:
    if not status_path.is_file():
        return {}
    payload = load_json(status_path)
    known_case_ids = {str(case["case_id"]) for case in manifest["cases"]}
    statuses: dict[str, dict[str, Any]] = {}
    for item in payload.get("cases", []):
        case_id = str(item.get("case_id", ""))
        if case_id not in known_case_ids:
            raise EvaluationError(f"Holdout status references unknown case: {case_id}")
        status = str(item.get("status", ""))
        if status not in {"frozen_holdout", "promoted_to_development"}:
            raise EvaluationError(f"Invalid holdout status for {case_id}: {status}")
        statuses[case_id] = item
    return statuses


def _latest_runs_by_hash(runs_root: Path) -> dict[str, Path]:
    matches: dict[str, Path] = {}
    for source_path in runs_root.rglob("source-bundle.json"):
        try:
            pdf_hash = str(load_json(source_path).get("pdf", {}).get("sha256", ""))
        except (OSError, json.JSONDecodeError):
            continue
        if not SHA256_PATTERN.fullmatch(pdf_hash):
            continue
        run_dir = source_path.parent
        previous = matches.get(pdf_hash)
        if previous is None or run_dir.stat().st_mtime > previous.stat().st_mtime:
            matches[pdf_hash] = run_dir
    return matches


def summarize_manifest_runs(
    manifest_path: Path,
    runs_root: Path,
) -> dict[str, Any]:
    contract = validate_manifest(manifest_path)
    manifest = load_json(manifest_path)
    holdout_status = load_holdout_status(manifest)
    runs = _latest_runs_by_hash(runs_root)
    case_results = []
    for case in manifest["cases"]:
        pdf_hash = case["pdf_sha256"]
        run_dir = runs.get(pdf_hash)
        summary = summarize_run(run_dir) if run_dir else None
        status_record = holdout_status.get(
            case["case_id"],
            {"status": "frozen_holdout"},
        )
        release_eligible = status_record["status"] == "frozen_holdout"
        case_results.append(
            {
                "case_id": case["case_id"],
                "expected_mineru_route": case["expected_mineru_route"],
                "holdout_status": status_record["status"],
                "release_decision_eligible": release_eligible,
                "run_found": run_dir is not None,
                "run": summary,
                "release_gate": (
                    release_gate_status(summary, case["expected_mineru_route"])
                    if summary
                    else {"status": "not_run", "checks": {}}
                ),
            }
        )
    eligible = [item for item in case_results if item["release_decision_eligible"]]
    return {
        "schema_version": "0.1",
        "contract": contract,
        "runs_root": str(runs_root.resolve()),
        "cases": case_results,
        "all_runs_found": all(item["run_found"] for item in case_results),
        "all_release_eligible_runs_pass": bool(eligible)
        and all(
            item["run_found"] and item["release_gate"]["status"] == "pass"
            for item in eligible
        ),
        "replacement_required": any(
            item["holdout_status"] == "promoted_to_development"
            for item in case_results
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate-manifest")
    validate.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    summarize = subparsers.add_parser("summarize")
    summarize.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    summarize.add_argument("--runs-root", type=Path, required=True)
    summarize.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate-manifest":
            payload = validate_manifest(args.manifest.resolve())
        else:
            payload = summarize_manifest_runs(
                args.manifest.resolve(),
                args.runs_root.resolve(),
            )
        rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        if getattr(args, "output", None):
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8", newline="\n")
        print(rendered, end="")
        return 0
    except (EvaluationError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
