#!/usr/bin/env python3
"""Deterministic local PDF preparation, validation, and note rendering for LitAnchor."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from paper_quality_gate import (  # noqa: E402
    FINAL_TEMPLATE_ID,
    FINAL_TEMPLATE_NAME,
    FINAL_TEMPLATE_VERSION,
    PAPER_TYPE_LABELS_ZH,
    canonical_paper_type,
    evidence_quote_completeness,
    evaluate_deep_claims,
    evaluate_summary_completeness,
    evaluate_visual_result_coverage,
    validate_cross_section_consistency,
    validate_duplicated_section_content,
    validate_final_markdown,
    validate_generic_claim_headings,
    validate_metadata_consistency,
    validate_numeric_rendering_integrity,
    validate_page_semantic_coverage,
    validate_range_symbol_integrity,
    validate_table_sentence_rendering_integrity,
)
from pdf_reading_order import extract_page_text as extract_pymupdf_page_text  # noqa: E402

SCHEMA_VERSION = "0.1"
SKILL_VERSION = "0.6.0-beta.2"
ID_PATTERN = re.compile(r"^[EC]-[A-Za-z0-9_-]+$")
NUMBER_PATTERN = re.compile(r"(?<![A-Za-z0-9_])[+-]?\d+(?:[.,]\d+)?%?")
BLOCKING_SEVERITIES = {"blocker", "error"}
EVIDENCE_REQUIRED = {
    "evidence_id",
    "evidence_type",
    "page_index",
    "section",
    "quote_original",
    "epistemic_status",
    "contains_number",
    "contains_unit",
    "confidence",
    "needs_review",
    "page_verified",
    "source_match_kind",
}
CLAIM_REQUIRED = {
    "claim_id",
    "claim_text_zh",
    "claim_type",
    "epistemic_status",
    "evidence_ids",
    "page_refs",
    "numeric_items",
    "validation",
}
EVIDENCE_TYPES = {
    "summary", "paper_type", "research_question", "background", "prior_work",
    "research_gap", "hypothesis", "contribution", "data", "material", "preprocessing",
    "model", "method_step", "parameter", "metric", "experiment", "result", "figure",
    "table", "equation", "discussion", "limitation", "uncertainty", "conclusion",
    "future_work", "term", "writing_expression", "reference",
}
CLAIM_TYPES = {
    "summary",
    "paper_type",
    "question",
    "background",
    "prior_work",
    "gap",
    "hypothesis",
    "contribution",
    "data",
    "material",
    "preprocessing",
    "method",
    "model",
    "equation",
    "metric",
    "parameter",
    "experiment",
    "result",
    "figure_interpretation",
    "interpretation",
    "discussion",
    "limitation",
    "conclusion",
    "future_work",
    "learning_value",
    "term",
    "writing_expression",
    "reference",
}
EPISTEMIC_STATUSES = {"observed", "supported", "interpreted", "hypothesized", "speculative", "unknown"}
AUTONOMOUS_ORIGINS = {"auto_extracted", "auto_synthesized"}
SECONDARY_PAPER_TYPE_LABELS_ZH = {
    "benchmark": "基准评测",
    "method": "方法",
}


class PipelineError(RuntimeError):
    """Raised when a safe local run cannot continue."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_text(path: Path, text: str, *, overwrite: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise PipelineError(f"Refusing to overwrite existing file: {path}")
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        temporary.write_text(text, encoding="utf-8", newline="\n")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_write_json(path: Path, payload: Any, *, overwrite: bool = True) -> None:
    atomic_write_text(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        overwrite=overwrite,
    )


def unique_run_dir(output_root: Path, digest: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = output_root / f"{stamp}-{digest[:12]}"
    candidate = base
    counter = 2
    while candidate.exists():
        candidate = output_root / f"{base.name}-{counter}"
        counter += 1
    candidate.mkdir(parents=True)
    return candidate


def _extract_page_text(page: Any) -> tuple[str, list[str]]:
    warnings: list[str] = []
    try:
        text, multicolumn = extract_pymupdf_page_text(page)
        if multicolumn:
            warnings.append("multicolumn_layout_detected_coordinate_order_used")
    except Exception as exc:
        warnings.append(f"page_extraction_failed:{type(exc).__name__}")
        text = ""
    control_count = sum(ord(character) < 32 and character not in "\n\r\t" for character in text)
    if control_count:
        text = "".join(character for character in text if ord(character) >= 32 or character in "\n\r\t")
        warnings.append(f"control_characters_removed:{control_count}")
    visible_count = len(re.sub(r"\s+", "", text))
    if visible_count == 0:
        warnings.append("empty_page_text")
    elif visible_count < 80:
        warnings.append("sparse_page_text")
    if text and text.count("\ufffd") / max(len(text), 1) > 0.005:
        warnings.append("replacement_character_rate_high")
    suspicious_ligatures = len(re.findall(r"(?:[A-Za-z][®¯]|[®¯][A-Za-z])", text))
    if suspicious_ligatures:
        warnings.append(f"suspicious_ligature_glyphs:{suspicious_ligatures}")
    return text, warnings


def _page_confidence(text: str, warnings: list[str]) -> float:
    visible_count = len(re.sub(r"\s+", "", text))
    if visible_count == 0:
        return 0.0
    confidence = 1.0 if visible_count >= 200 else 0.75 if visible_count >= 80 else 0.4
    confidence -= 0.15 * len([item for item in warnings if "failed" in item or "high" in item])
    return max(0.0, round(confidence, 2))


def prepare_pdf(
    pdf_path: Path,
    output_root: Path,
    *,
    reading_mode: str = "deep",
    title: str | None = None,
    authors: list[str] | None = None,
    year: int | None = None,
    journal: str | None = None,
    doi: str | None = None,
    citekey: str | None = None,
    acquisition_method: str = "manual_pdf",
    source_query: str | None = None,
    zotero_item_key: str | None = None,
    zotero_attachment_key: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Extract physical PDF pages into a private run directory."""
    if reading_mode not in {"skim", "deep", "internalize"}:
        raise PipelineError(f"Unsupported reading mode: {reading_mode}")
    if acquisition_method not in {"manual_pdf", "zotero_local_api"}:
        raise PipelineError(f"Unsupported acquisition method: {acquisition_method}")
    pdf_path = pdf_path.resolve()
    if not pdf_path.is_file() or pdf_path.suffix.lower() != ".pdf":
        raise PipelineError(f"Input is not a readable PDF file: {pdf_path}")

    try:
        import pymupdf
    except ImportError as exc:
        raise PipelineError(
            "PyMuPDF is required. Install the repository requirements before preparing a PDF."
        ) from exc

    digest = sha256_file(pdf_path)
    try:
        document = pymupdf.open(pdf_path)
        page_count = document.page_count
    except Exception as exc:
        raise PipelineError(f"PDF cannot be parsed: {type(exc).__name__}: {exc}") from exc
    if page_count < 1:
        document.close()
        raise PipelineError("PDF contains no pages")

    run_dir = unique_run_dir(output_root.resolve(), digest)
    paper_id = f"pdf-{digest[:16]}"
    resolved_authors = list(authors or [])

    pages: list[dict[str, Any]] = []
    pdf_warnings: list[str] = []
    try:
        if document.needs_pass or document.is_encrypted:
            preflight_status = "BLOCKED"
            pdf_warnings.append("encrypted_pdf")
        else:
            for page_index, page in enumerate(document, start=1):
                text, page_warnings = _extract_page_text(page)
                pages.append(
                    {
                        "page_index": page_index,
                        "printed_page": None,
                        "raw_text": text,
                        "extraction_method": "pymupdf_native",
                        "confidence": _page_confidence(text, page_warnings),
                        "warnings": page_warnings,
                    }
                )
            readable_pages = sum(
                len(re.sub(r"\s+", "", page["raw_text"])) >= 80 for page in pages
            )
            coverage = readable_pages / page_count
            total_visible = sum(
                len(re.sub(r"\s+", "", page["raw_text"])) for page in pages
            )
            if coverage < 0.5 or total_visible < 500:
                preflight_status = "FALLBACK_REQUIRED"
                pdf_warnings.append("native_text_coverage_insufficient")
            elif coverage < 0.9 or any(page["warnings"] for page in pages):
                preflight_status = "PASS_WITH_WARNINGS"
                pdf_warnings.append("review_page_extraction_warnings")
            else:
                preflight_status = "PASS"
            if page_count > 60:
                pdf_warnings.append("page_count_above_mvp_limit")
                if preflight_status == "PASS":
                    preflight_status = "PASS_WITH_WARNINGS"
            if pdf_warnings and preflight_status == "PASS":
                preflight_status = "PASS_WITH_WARNINGS"
    finally:
        document.close()

    bundle: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "paper_id": paper_id,
        "source": {
            "acquisition_method": acquisition_method,
            "query": source_query or str(pdf_path),
            "zotero_item_key": zotero_item_key,
            "zotero_attachment_key": zotero_attachment_key,
            "external_knowledge_allowed": False,
        },
        "metadata": {
            "title": title or pdf_path.stem,
            "authors": resolved_authors,
            "year": year,
            "journal": journal,
            "doi": doi,
            "citekey": citekey,
        },
        "annotations": [],
        "pdf": {
            "path": str(pdf_path),
            "sha256": digest,
            "page_count": page_count,
            "preflight_status": preflight_status,
            "warnings": pdf_warnings,
        },
        "pages": pages,
    }
    run_record = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_dir.name,
        "paper_id": paper_id,
        "skill_version": SKILL_VERSION,
        "reading_mode": reading_mode,
        "created": utc_now(),
        "status": "blocked" if preflight_status == "BLOCKED" else "prepared",
        "artifacts": {
            "source_bundle": "source-bundle.json",
            "evidence": "evidence.json",
            "claims": "claims.json",
            "figures": "figures.json",
        },
    }
    figures = {
        "schema_version": SCHEMA_VERSION,
        "selection_status": (
            "pending" if reading_mode in {"deep", "internalize"} else "completed"
        ),
        "selected": [],
        "rejected": [],
        "no_selection_reason": (
            None
            if reading_mode in {"deep", "internalize"}
            else "Visual selection is not required for skim mode."
        ),
    }
    atomic_write_json(run_dir / "source-bundle.json", bundle, overwrite=False)
    atomic_write_json(run_dir / "evidence.json", [], overwrite=False)
    atomic_write_json(run_dir / "claims.json", [], overwrite=False)
    atomic_write_json(run_dir / "figures.json", figures, overwrite=False)
    atomic_write_json(run_dir / "run.json", run_record, overwrite=False)
    return run_dir, bundle


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PipelineError(f"Required artifact is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PipelineError(f"Invalid JSON in {path}: {exc}") from exc


def trace_forms(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKC", text)
    normalized = re.sub(r"(?<=\w)\u00ad\s*(?=\w)", "", normalized)
    normalized = normalized.replace("\u00ad", "")
    normalized = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2212]", "-", normalized)
    normalized = re.sub(r"\s*-\s*", "-", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    normalized = re.sub(r"\s+([,.;:?!%)\]])", r"\1", normalized)
    normalized = re.sub(r"([(\[])\s+", r"\1", normalized)
    normalized = re.sub(r"\s*/\s*", "/", normalized)
    joined_hyphen = re.sub(r"(?<=\w)-\s+(?=\w)", "-", normalized)
    dehyphenated = re.sub(r"(?<=\w)-\s+(?=\w)", "", normalized)
    return {normalized, joined_hyphen, dehyphenated, dehyphenated.replace("-", "")}


def quote_is_traceable(quote: str, page_text: str) -> bool:
    return quote_match_kind(quote, page_text) != "unmatched"


def trace_token_present(token: str, text: str) -> bool:
    return any(
        token_form and token_form in text_form
        for token_form in trace_forms(token)
        for text_form in trace_forms(text)
    )


def resolve_paper_type(run_dir: Path, source: dict[str, Any]) -> Any:
    """Prefer the autonomous paper profile over optional source metadata."""
    profile_path = run_dir / "paper-profile.json"
    if profile_path.is_file():
        profile = load_json(profile_path)
        if isinstance(profile, dict) and profile.get("paper_type"):
            return profile["paper_type"]
    return source.get("metadata", {}).get("paper_type")


def quote_match_kind(quote: str, page_text: str) -> str:
    if quote.strip() and quote.strip() in page_text:
        return "exact"
    quote_forms = trace_forms(quote)
    page_forms = trace_forms(page_text)
    if any(
        quote_form and quote_form in page_form
        for quote_form in quote_forms
        for page_form in page_forms
    ):
        return "normalized"
    return "unmatched"


def _numeric_bbox(block: dict[str, Any]) -> tuple[float, float, float, float] | None:
    bbox = block.get("bbox")
    if (
        isinstance(bbox, list)
        and len(bbox) == 4
        and all(isinstance(value, (int, float)) for value in bbox)
    ):
        return tuple(float(value) for value in bbox)
    return None


def _layout_block_groups(page: dict[str, Any]) -> list[list[dict[str, Any]]]:
    """Keep line blocks from the same PDF column in reading order."""
    blocks = [
        block
        for block in page.get("text_blocks", [])
        if isinstance(block, dict)
        and block.get("block_type") == "text"
        and str(block.get("text") or "").strip()
        and _numeric_bbox(block) is not None
    ]
    if not blocks:
        return []
    page_width = float(page.get("page_width") or 0)
    if page_width <= 0:
        return [blocks]
    midpoint = page_width / 2
    narrow = [
        block
        for block in blocks
        if (_numeric_bbox(block)[2] - _numeric_bbox(block)[0]) < page_width * 0.7
    ]
    left = [
        block
        for block in narrow
        if (_numeric_bbox(block)[0] + _numeric_bbox(block)[2]) / 2 < midpoint
    ]
    right = [block for block in narrow if block not in left]
    ordered_columns = [
        sorted(
            group,
            key=lambda block: (_numeric_bbox(block)[1], _numeric_bbox(block)[0]),
        )
        for group in (left, right)
        if group
    ]
    groups = [blocks, *ordered_columns]
    if len(ordered_columns) > 1:
        groups.append([block for column in ordered_columns for block in column])
    return [
        sorted(
            group,
            key=lambda block: (_numeric_bbox(block)[1], _numeric_bbox(block)[0]),
        )
        if group is blocks
        else group
        for group in groups
    ]


def page_quote_match_location(
    quote: str,
    page: dict[str, Any],
) -> tuple[str, list[dict[str, Any]]]:
    """Match a quote and return the smallest layout-preserving block span."""
    blocks = [
        block
        for block in page.get("text_blocks", [])
        if isinstance(block, dict)
        and block.get("block_type") == "text"
        and str(block.get("text") or "").strip()
    ]
    for desired in ("exact", "normalized"):
        for block in blocks:
            if quote_match_kind(quote, str(block.get("text") or "")) == desired:
                return desired, [block]
        for group in _layout_block_groups(page):
            text = "\n".join(str(block.get("text") or "") for block in group)
            if quote_match_kind(quote, text) == desired:
                return desired, group
        if quote_match_kind(quote, str(page.get("raw_text", ""))) == desired:
            return desired, []
    return "unmatched", []


def page_quote_match_kind(quote: str, page: dict[str, Any]) -> str:
    """Match a quote to a PyMuPDF page, including layout-preserving text blocks."""
    return page_quote_match_location(quote, page)[0]


def build_coverage_receipt(
    source: dict[str, Any],
    evidence: list[Any],
    run_record: dict[str, Any],
    page_classification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    page_count = int(source.get("pdf", {}).get("page_count", 0) or 0)
    expected_pages = list(range(1, page_count + 1))
    extracted_pages = sorted(
        {
            page.get("page_index")
            for page in source.get("pages", [])
            if isinstance(page, dict) and isinstance(page.get("page_index"), int)
        }
    )
    readable_pages = sorted(
        page["page_index"]
        for page in source.get("pages", [])
        if isinstance(page, dict)
        and isinstance(page.get("page_index"), int)
        and len(re.sub(r"\s+", "", str(page.get("raw_text", "")))) >= 80
    )
    verified_evidence = [
        item
        for item in evidence
        if isinstance(item, dict)
        and item.get("page_verified") is True
        and item.get("source_match_kind") in {"exact", "normalized"}
        and isinstance(item.get("page_index"), int)
    ]
    evidence_pages = sorted({item["page_index"] for item in verified_evidence})
    sections = sorted(
        {
            str(item.get("section", "")).strip()
            for item in verified_evidence
            if str(item.get("section", "")).strip()
        },
        key=str.casefold,
    )
    preflight_status = source.get("pdf", {}).get("preflight_status")
    extraction_complete = (
        page_count > 0
        and extracted_pages == expected_pages
        and preflight_status in {"PASS", "PASS_WITH_WARNINGS"}
    )
    classification_pages = (
        page_classification.get("pages", [])
        if isinstance(page_classification, dict)
        else []
    )
    relevant_main_pages = sorted(
        int(item["page_index"])
        for item in classification_pages
        if isinstance(item, dict)
        and item.get("classification") == "main_content"
        and isinstance(item.get("page_index"), int)
    )
    analysis_extent_pages = relevant_main_pages or expected_pages
    reading_mode = run_record.get("reading_mode")
    if reading_mode == "deep":
        minimum_evidence_pages = min(3, page_count)
        minimum_sections = 1 if page_count == 1 else min(3, page_count)
        later_half_boundary = (
            analysis_extent_pages[(len(analysis_extent_pages) - 1) // 2]
            if analysis_extent_pages
            else 1
        )
        reaches_later_half = bool(
            evidence_pages
            and max(evidence_pages) >= later_half_boundary
        )
        analysis_complete = (
            len(evidence_pages) >= minimum_evidence_pages
            and len(sections) >= minimum_sections
            and reaches_later_half
        )
    else:
        minimum_evidence_pages = 1
        minimum_sections = 1
        reaches_later_half = bool(evidence_pages)
        analysis_complete = bool(evidence_pages and sections)

    excluded_reference_pages = sorted(
        int(item["page_index"])
        for item in classification_pages
        if isinstance(item, dict)
        and item.get("classification") == "references_only"
        and isinstance(item.get("page_index"), int)
    )
    appendix_pages = sorted(
        int(item["page_index"])
        for item in classification_pages
        if isinstance(item, dict)
        and item.get("classification") in {"appendix", "supplementary_content"}
        and isinstance(item.get("page_index"), int)
    )
    semantically_reviewed_pages = sorted(
        int(item["page_index"])
        for item in classification_pages
        if isinstance(item, dict)
        and item.get("semantic_reviewed") is True
        and isinstance(item.get("page_index"), int)
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "paper_id": source.get("paper_id", "unknown"),
        "run_id": run_record.get("run_id"),
        "reading_mode": reading_mode,
        "document_page_count": page_count,
        "pages_extracted": extracted_pages,
        "pages_with_readable_text": readable_pages,
        "pages_used_as_evidence": evidence_pages,
        "sections_evidenced": sections,
        "excluded_reference_pages": excluded_reference_pages,
        "appendix_or_supplementary_pages": appendix_pages,
        "semantically_reviewed_pages": semantically_reviewed_pages,
        "minimum_evidence_pages": minimum_evidence_pages,
        "minimum_sections": minimum_sections,
        "reaches_later_half": reaches_later_half,
        "extraction_status": "complete" if extraction_complete else "incomplete",
        "analysis_status": "complete" if analysis_complete else "insufficient",
        "coverage_status": (
            "complete" if extraction_complete and analysis_complete else "incomplete"
        ),
    }


def _issue(
    issue_id: str,
    severity: str,
    issue_type: str,
    message: str,
    *,
    page_index: int | None = None,
    claim_id: str | None = None,
    evidence_id: str | None = None,
) -> dict[str, Any]:
    return {
        "issue_id": issue_id,
        "severity": severity,
        "issue_type": issue_type,
        "message": message,
        "page_index": page_index,
        "claim_id": claim_id,
        "evidence_id": evidence_id,
        "suggested_action": "Correct the structured ledger and rebuild.",
        "resolved": False,
    }


def validate_run(
    run_dir: Path,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    list[Any],
    list[Any],
    dict[str, Any],
    dict[str, Any],
]:
    """Validate traceability invariants without making semantic claims."""
    run_dir = run_dir.resolve()
    source = load_json(run_dir / "source-bundle.json")
    evidence = load_json(run_dir / "evidence.json")
    claims = load_json(run_dir / "claims.json")
    figures = load_json(run_dir / "figures.json")
    run_record = load_json(run_dir / "run.json")
    if not isinstance(evidence, list) or not isinstance(claims, list):
        raise PipelineError("evidence.json and claims.json must each contain a JSON array")
    if not isinstance(figures, dict):
        raise PipelineError("figures.json must contain a JSON object")
    autonomous_generation = bool(run_record.get("autonomous_generation", False))
    page_classification_path = run_dir / "page-classification.json"
    page_classification = (
        load_json(page_classification_path)
        if page_classification_path.is_file()
        else None
    )

    issues: list[dict[str, Any]] = []
    issue_counter = 1

    def add_issue(*args: Any, **kwargs: Any) -> None:
        nonlocal issue_counter
        issues.append(_issue(f"V-{issue_counter:03d}", *args, **kwargs))
        issue_counter += 1

    pages = {page.get("page_index"): page for page in source.get("pages", [])}
    page_count = source.get("pdf", {}).get("page_count", 0)
    preflight_status = source.get("pdf", {}).get("preflight_status")
    if source.get("source", {}).get("external_knowledge_allowed") is not False:
        add_issue("blocker", "external_knowledge_enabled", "Formal runs must set external_knowledge_allowed to false.")
    if len(pages) != page_count:
        add_issue("blocker", "page_count_mismatch", "SourceBundle page_count does not match its unique physical pages.")
    if preflight_status in {"BLOCKED", "FALLBACK_REQUIRED"}:
        add_issue(
            "blocker",
            "pdf_preflight",
            f"PDF preflight status is {preflight_status}; native-text note generation is blocked.",
        )
    elif preflight_status == "PASS_WITH_WARNINGS":
        add_issue(
            "warning",
            "pdf_preflight_warning",
            "PDF passed preflight with extraction warnings; inspect the listed physical pages.",
        )
    for finding in validate_metadata_consistency(
        source,
        resolve_paper_type(run_dir, source),
        require_paper_type=run_record.get("reading_mode")
        in {"deep", "internalize"},
    ):
        add_issue(
            finding.get("severity", "blocker"),
            finding["issue_type"],
            finding["message"],
        )
    if (
        autonomous_generation
        and run_record.get("review_status") == "user_visual_review_pending"
    ):
        add_issue(
            "warning",
            "user_visual_review_pending",
            "Automated checks passed, but the exported Obsidian note and selected "
            "figures still require user visual review.",
        )
    for page_index, page in pages.items():
        page_warnings = page.get("warnings", [])
        if page_warnings:
            add_issue(
                "warning",
                "pdf_page_warning",
                f"Physical PDF page {page_index} warnings: {', '.join(map(str, page_warnings))}.",
                page_index=page_index,
            )
    if not evidence:
        add_issue("blocker", "empty_evidence_ledger", "No EvidenceUnits were provided.")
    if not claims:
        add_issue("blocker", "empty_claim_ledger", "No ClaimRecords were provided.")

    selected_figures = figures.get("selected")
    rejected_figures = figures.get("rejected")
    selection_status = figures.get("selection_status")
    if (
        selection_status != "completed"
        or not isinstance(selected_figures, list)
        or not isinstance(rejected_figures, list)
    ):
        add_issue(
            "blocker",
            "visual_selection_incomplete",
            "Every run must complete the visual selection pass before note generation.",
        )
        selected_figures = []
    elif len(selected_figures) > 3:
        add_issue(
            "blocker",
            "too_many_selected_figures",
            "A deep note may embed at most three key visual objects.",
        )
    elif (
        run_record.get("reading_mode") in {"deep", "internalize"}
        and not selected_figures
        and not str(figures.get("no_selection_reason") or "").strip()
    ):
        add_issue(
            "blocker",
            "missing_visual_selection_reason",
            "A deep note with no embedded figure must record why no suitable visual was selected.",
        )

    valid_selected_figures = 0
    for index, figure in enumerate(selected_figures, start=1):
        if not isinstance(figure, dict):
            add_issue(
                "blocker",
                "invalid_selected_figure",
                f"Selected visual {index} must be an object.",
            )
            continue
        required = {
            "figure_label",
            "physical_pdf_page",
            "caption_original",
            "selection_reason",
            "discussion_location",
            "image_path",
            "manifest_path",
            "embed_path",
        }
        missing = sorted(required - set(figure))
        if missing:
            add_issue(
                "blocker",
                "invalid_selected_figure",
                f"Selected visual {index} is missing: {', '.join(missing)}.",
            )
            continue
        page_index = figure.get("physical_pdf_page")
        embed_path = str(figure.get("embed_path", ""))
        if (
            not isinstance(page_index, int)
            or page_index < 1
            or page_index > page_count
        ):
            add_issue(
                "blocker",
                "invalid_figure_page",
                f"Selected visual {index} has invalid physical page {page_index!r}.",
            )
            continue
        if (
            not embed_path
            or Path(embed_path).is_absolute()
            or ".." in Path(embed_path).parts
            or Path(embed_path).suffix.casefold() not in {".png", ".jpg", ".jpeg", ".webp"}
        ):
            add_issue(
                "blocker",
                "unsafe_figure_embed_path",
                f"Selected visual {index} has an unsafe Obsidian embed path.",
            )
            continue
        try:
            image_path = Path(str(figure["image_path"])).resolve(strict=True)
            manifest_path = Path(str(figure["manifest_path"])).resolve(strict=True)
        except FileNotFoundError:
            add_issue(
                "blocker",
                "missing_figure_artifact",
                f"Selected visual {index} image or crop manifest does not exist.",
            )
            continue
        manifest = load_json(manifest_path)
        if (
            not isinstance(manifest, dict)
            or manifest.get("crop_validation_status") != "pass"
            or manifest.get("needs_human_review") is not False
            or manifest.get("source_pdf_sha256") != source.get("pdf", {}).get("sha256")
            or manifest.get("physical_pdf_page") != page_index
            or manifest.get("output_image_sha256") != sha256_file(image_path)
        ):
            add_issue(
                "blocker",
                "figure_quality_gate_failed",
                f"Selected visual {index} did not pass the crop quality and provenance gate.",
                page_index=page_index,
            )
            continue
        valid_selected_figures += 1

    evidence_by_id: dict[str, dict[str, Any]] = {}
    valid_evidence = 0
    for item in evidence:
        if not isinstance(item, dict):
            add_issue("blocker", "invalid_evidence", "EvidenceUnit must be an object.")
            continue
        missing_fields = sorted(EVIDENCE_REQUIRED - set(item))
        if missing_fields:
            add_issue("blocker", "invalid_evidence_schema", f"EvidenceUnit is missing required fields: {', '.join(missing_fields)}.")
            continue
        evidence_id = item.get("evidence_id")
        page_index = item.get("page_index")
        quote = item.get("quote_original")
        if not isinstance(evidence_id, str) or not ID_PATTERN.fullmatch(evidence_id) or not evidence_id.startswith("E-"):
            add_issue("blocker", "invalid_evidence_id", f"Invalid Evidence ID: {evidence_id!r}")
            continue
        if evidence_id in evidence_by_id:
            add_issue("blocker", "duplicate_evidence_id", f"Duplicate Evidence ID: {evidence_id}", evidence_id=evidence_id)
            continue
        evidence_by_id[evidence_id] = item
        if (
            autonomous_generation
            and item.get("origin") not in AUTONOMOUS_ORIGINS
        ):
            add_issue(
                "blocker",
                "invalid_autonomous_origin",
                f"Evidence {evidence_id} has a disallowed or missing autonomous origin.",
                evidence_id=evidence_id,
            )
        if item.get("evidence_type") not in EVIDENCE_TYPES or item.get("epistemic_status") not in EPISTEMIC_STATUSES:
            add_issue(
                "blocker",
                "invalid_evidence_schema",
                f"Evidence {evidence_id} has an invalid type or epistemic status.",
                evidence_id=evidence_id,
            )
            continue
        if (
            item.get("page_verified") is not True
            or item.get("source_match_kind") not in {"exact", "normalized"}
        ):
            add_issue(
                "blocker",
                "unverified_evidence_page",
                f"Evidence {evidence_id} is not verified against one physical PDF page.",
                page_index=page_index if isinstance(page_index, int) else None,
                evidence_id=evidence_id,
            )
            continue
        if not isinstance(page_index, int) or page_index < 1 or page_index > page_count or page_index not in pages:
            add_issue(
                "blocker",
                "invalid_evidence_page",
                f"Evidence {evidence_id} points to invalid physical PDF page {page_index!r}.",
                page_index=page_index if isinstance(page_index, int) else None,
                evidence_id=evidence_id,
            )
            continue
        if not isinstance(quote, str) or max((len(form) for form in trace_forms(quote)), default=0) < 20:
            add_issue(
                "error",
                "evidence_quote_too_short",
                f"Evidence {evidence_id} lacks a sufficiently specific original quote.",
                page_index=page_index,
                evidence_id=evidence_id,
            )
            continue
        quote_complete, completeness_message = evidence_quote_completeness(
            str(item.get("evidence_type") or ""),
            quote,
        )
        if not quote_complete:
            add_issue(
                "blocker",
                "evidence_quote_completeness",
                f"Evidence {evidence_id} is not a complete source sentence: "
                f"{completeness_message}",
                page_index=page_index,
                evidence_id=evidence_id,
            )
            continue
        actual_match_kind = page_quote_match_kind(quote, pages[page_index])
        if actual_match_kind == "unmatched":
            add_issue(
                "blocker",
                "untraceable_quote",
                f"Evidence {evidence_id} quote was not found on physical PDF page {page_index}.",
                page_index=page_index,
                evidence_id=evidence_id,
            )
            continue
        if item.get("source_match_kind") != actual_match_kind:
            add_issue(
                "warning",
                "source_match_kind_mismatch",
                f"Evidence {evidence_id} declared {item.get('source_match_kind')!r} "
                f"but deterministic matching found {actual_match_kind!r}.",
                page_index=page_index,
                evidence_id=evidence_id,
            )
        valid_evidence += 1
        if item.get("needs_review") is True:
            add_issue(
                "warning",
                "evidence_needs_review",
                f"Evidence {evidence_id} is marked for human review.",
                page_index=page_index,
                evidence_id=evidence_id,
            )

    for finding in validate_range_symbol_integrity(evidence):
        add_issue(
            "blocker",
            finding["issue_type"],
            finding["message"],
        )

    valid_claims = 0
    valid_page_claims = 0
    numeric_checks = 0
    numeric_passes = 0
    seen_claim_ids: set[str] = set()
    for claim in claims:
        if not isinstance(claim, dict):
            add_issue("blocker", "invalid_claim", "ClaimRecord must be an object.")
            continue
        missing_fields = sorted(CLAIM_REQUIRED - set(claim))
        if missing_fields:
            add_issue("blocker", "invalid_claim_schema", f"ClaimRecord is missing required fields: {', '.join(missing_fields)}.")
            continue
        claim_id = claim.get("claim_id")
        if not isinstance(claim_id, str) or not ID_PATTERN.fullmatch(claim_id) or not claim_id.startswith("C-"):
            add_issue("blocker", "invalid_claim_id", f"Invalid Claim ID: {claim_id!r}")
            continue
        if claim_id in seen_claim_ids:
            add_issue("blocker", "duplicate_claim_id", f"Duplicate Claim ID: {claim_id}", claim_id=claim_id)
            continue
        seen_claim_ids.add(claim_id)
        if (
            autonomous_generation
            and claim.get("origin") not in AUTONOMOUS_ORIGINS
        ):
            add_issue(
                "blocker",
                "invalid_autonomous_origin",
                f"Claim {claim_id} has a disallowed or missing autonomous origin.",
                claim_id=claim_id,
            )
        if (
            not isinstance(claim.get("claim_text_zh"), str)
            or not claim["claim_text_zh"].strip()
            or claim.get("claim_type") not in CLAIM_TYPES
            or claim.get("epistemic_status") not in EPISTEMIC_STATUSES
        ):
            add_issue("blocker", "invalid_claim_schema", f"Claim {claim_id} has invalid text, type, or epistemic status.", claim_id=claim_id)
            continue
        detail_points = claim.get("detail_points_zh", [])
        if (
            not isinstance(detail_points, list)
            or any(not isinstance(point, str) or not point.strip() for point in detail_points)
            or (
                "importance" in claim
                and claim.get("importance") not in {"core", "supporting", "context"}
            )
            or (
                "conditions_zh" in claim
                and claim.get("conditions_zh") is not None
                and not isinstance(claim.get("conditions_zh"), str)
            )
        ):
            add_issue(
                "blocker",
                "invalid_claim_schema",
                f"Claim {claim_id} has invalid deep-reading detail fields.",
                claim_id=claim_id,
            )
            continue
        evidence_ids = claim.get("evidence_ids")
        page_refs = claim.get("page_refs")
        if not isinstance(evidence_ids, list) or not evidence_ids:
            add_issue("blocker", "claim_without_evidence", f"Claim {claim_id} has no Evidence ID.", claim_id=claim_id)
            continue
        missing_ids = [item for item in evidence_ids if item not in evidence_by_id]
        if missing_ids:
            add_issue(
                "blocker",
                "missing_claim_evidence",
                f"Claim {claim_id} references missing evidence: {', '.join(map(str, missing_ids))}.",
                claim_id=claim_id,
            )
            continue
        supporting = [evidence_by_id[item] for item in evidence_ids]
        supporting_pages = sorted({item.get("page_index") for item in supporting})
        if not isinstance(page_refs, list) or sorted(set(page_refs)) != supporting_pages:
            add_issue(
                "blocker",
                "claim_page_mismatch",
                f"Claim {claim_id} page_refs do not match its EvidenceUnits.",
                claim_id=claim_id,
            )
            continue
        valid_page_claims += 1
        supporting_text = " ".join(
            evidence_quote_for_display(item) for item in supporting
        )
        numeric_ok = True
        numeric_items = claim.get("numeric_items", [])
        if not isinstance(numeric_items, list):
            add_issue("blocker", "invalid_numeric_items", f"Claim {claim_id} numeric_items must be an array.", claim_id=claim_id)
            continue
        for numeric_item in numeric_items:
            numeric_checks += 1
            value = str(numeric_item.get("value_original", "")) if isinstance(numeric_item, dict) else ""
            unit = numeric_item.get("unit_original") if isinstance(numeric_item, dict) else None
            value_found = bool(value) and trace_token_present(value, supporting_text)
            unit_found = unit in {None, ""} or trace_token_present(
                str(unit), supporting_text
            )
            if value_found and unit_found:
                numeric_passes += 1
            else:
                numeric_ok = False
                add_issue(
                    "blocker",
                    "numeric_fidelity",
                    f"Claim {claim_id} numeric item {value!r} / {unit!r} is absent from its evidence.",
                    claim_id=claim_id,
                )
        for token in NUMBER_PATTERN.findall(claim.get("claim_text_zh", "")):
            if not trace_token_present(token, supporting_text):
                numeric_ok = False
                add_issue(
                    "blocker",
                    "claim_number_untraceable",
                    f"Claim {claim_id} contains number {token!r}, which is absent from its evidence.",
                    claim_id=claim_id,
                )
        validation = claim.get("validation", {})
        required_validation = {"traceable", "semantic_support", "numeric_fidelity", "modality_fidelity", "final_status"}
        if not isinstance(validation, dict) or not required_validation.issubset(validation) or validation.get("final_status") == "fail":
            add_issue("error", "claim_validation_failed", f"Claim {claim_id} did not pass semantic validation.", claim_id=claim_id)
            continue
        if any(validation.get(key) == "warning" for key in ("semantic_support", "numeric_fidelity", "modality_fidelity", "final_status")):
            add_issue("warning", "claim_validation_warning", f"Claim {claim_id} has a semantic validation warning.", claim_id=claim_id)
        if numeric_ok:
            valid_claims += 1

    if run_record.get("reading_mode") in {"deep", "internalize"}:
        for finding in validate_generic_claim_headings(claims):
            add_issue(
                "blocker",
                finding["issue_type"],
                finding["message"],
            )

    deep_quality_findings: list[dict[str, str]] = []
    if run_record.get("reading_mode") in {"deep", "internalize"}:
        deep_quality_findings = evaluate_deep_claims(
            claims,
            page_count,
            resolve_paper_type(run_dir, source),
            str(run_record.get("reading_mode") or "deep"),
        )
        deep_quality_findings.extend(
            evaluate_visual_result_coverage(figures, claims)
        )
        deep_quality_findings.extend(
            evaluate_summary_completeness(claims, evidence)
        )
        if autonomous_generation:
            if not isinstance(page_classification, dict):
                deep_quality_findings.append(
                    {
                        "issue_type": "page_semantic_coverage",
                        "message": (
                            "Autonomous deep reading requires page-classification.json."
                        ),
                    }
                )
            else:
                deep_quality_findings.extend(
                    validate_page_semantic_coverage(
                        page_classification,
                        int(page_count),
                    )
                )
        for finding in deep_quality_findings:
            add_issue(
                "blocker",
                finding["issue_type"],
                finding["message"],
            )

    coverage_receipt = build_coverage_receipt(
        source,
        evidence,
        run_record,
        page_classification,
    )
    if deep_quality_findings:
        coverage_receipt["analysis_status"] = "insufficient"
        coverage_receipt["coverage_status"] = "incomplete"
    if coverage_receipt["coverage_status"] != "complete":
        add_issue(
            "blocker",
            "incomplete_reading_coverage",
            "The run does not prove complete extraction and sufficient analysis coverage "
            "for its declared reading mode.",
        )

    blocking = [issue for issue in issues if issue["severity"] in BLOCKING_SEVERITIES]
    warning_count = sum(issue["severity"] == "warning" for issue in issues)
    claim_count = len(claims)
    range_symbol_integrity = not any(
        issue["issue_type"] == "range_symbol_integrity"
        and issue["severity"] in BLOCKING_SEVERITIES
        for issue in issues
    )
    generic_heading_integrity = not any(
        issue["issue_type"] == "generic_heading_detection"
        and issue["severity"] in BLOCKING_SEVERITIES
        for issue in issues
    )
    metadata_consistency = not any(
        issue["issue_type"] == "metadata_consistency"
        and issue["severity"] in BLOCKING_SEVERITIES
        for issue in issues
    )
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "paper_id": source.get("paper_id", "unknown"),
        "status": "blocked" if blocking else "completed_with_warnings" if warning_count else "completed",
        "files": {
            "markdown_note": None,
            "evidence": str(run_dir / "evidence.json"),
            "claims": str(run_dir / "claims.json"),
            "validation": str(run_dir / "validation.json"),
            "run_record": str(run_dir / "run.json"),
            "coverage_receipt": str(run_dir / "coverage_receipt.json"),
            "failure_report": None,
        },
        "issues": issues,
        "statistics": {
            "page_count": page_count,
            "evidence_count": len(evidence),
            "claim_count": claim_count,
            "figure_count": valid_selected_figures,
            "table_count": sum(item.get("evidence_type") == "table" for item in evidence if isinstance(item, dict)),
            "equation_count": sum(item.get("evidence_type") == "equation" for item in evidence if isinstance(item, dict)),
            "warning_count": warning_count,
            "blocker_count": sum(issue["severity"] == "blocker" for issue in issues),
        },
        "quality": {
            "evidence_coverage": valid_claims / claim_count if claim_count else 0.0,
            "page_reference_accuracy": valid_page_claims / claim_count if claim_count else 0.0,
            "numeric_fidelity": (
                numeric_passes / numeric_checks
                if numeric_checks and range_symbol_integrity
                else 1.0 if range_symbol_integrity else 0.0
            ),
            "modality_fidelity": (
                sum(
                    isinstance(claim, dict)
                    and isinstance(claim.get("validation"), dict)
                    and claim["validation"].get("modality_fidelity") == "pass"
                    for claim in claims
                )
                / claim_count
                if claim_count
                else 0.0
            ),
            "template_completeness": 0.0 if any(
                item["issue_type"] == "deep_required_section_missing"
                for item in issues
            ) else 1.0,
            "content_recall_pass": not any(
                item["issue_type"] == "deep_content_recall_insufficient"
                for item in issues
            ),
            "section_depth_pass": not any(
                item["issue_type"] in {
                    "deep_section_depth_insufficient",
                    "deep_substantive_content_too_short",
                }
                for item in issues
            ),
            "range_symbol_integrity": range_symbol_integrity,
            "generic_heading_integrity": generic_heading_integrity,
            "metadata_consistency": metadata_consistency,
            "duplicated_section_content": False,
            "format_valid": False,
        },
    }
    return result, source, evidence, claims, figures, coverage_receipt


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    return json.dumps(value, ensure_ascii=False)


def metadata_presentation(
    source: dict[str, Any],
) -> tuple[str | None, str | None, list[str]]:
    """Return stable type fields and explicit missing-metadata warnings."""
    metadata = source.get("metadata", {})
    machine_type = canonical_paper_type(metadata.get("paper_type"))
    label_zh = str(metadata.get("paper_type_label_zh") or "").strip() or (
        PAPER_TYPE_LABELS_ZH.get(machine_type) if machine_type else None
    )
    warnings = [
        str(item).strip()
        for item in metadata.get("metadata_warnings", [])
        if str(item).strip()
    ] if isinstance(metadata.get("metadata_warnings"), list) else []
    provider = (
        "Zotero"
        if source.get("source", {}).get("acquisition_method") == "zotero_local_api"
        else "来源元数据"
    )
    for field in ("year", "journal", "doi"):
        value = metadata.get(field)
        if value is None or value == "":
            warnings.append(f"{field} 未由 {provider} 提供")
    return machine_type, label_zh, list(dict.fromkeys(warnings))


def evidence_quote_for_display(item: dict[str, Any]) -> str:
    """Apply only original-page-verified glyph corrections for display."""
    quote = str(item.get("quote_original") or "")
    receipt = item.get("symbol_verification")
    if not isinstance(receipt, dict):
        return quote
    if (
        receipt.get("status") != "corrected_from_original_page"
        or receipt.get("method") != "pymupdf_page_render"
    ):
        return quote
    corrections = receipt.get("corrections")
    if not isinstance(corrections, list):
        return quote
    for correction in corrections:
        if not isinstance(correction, dict):
            continue
        extracted = str(correction.get("extracted") or "")
        verified = str(correction.get("verified") or "")
        if extracted and verified:
            quote = quote.replace(extracted, verified)
    return quote


def first_author_only(authors: Any) -> list[str]:
    """Return the first verified author for concise note frontmatter."""
    if not isinstance(authors, list):
        return []
    return [authors[0]] if authors and isinstance(authors[0], str) and authors[0].strip() else []


def _escape_table(text: Any) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def zotero_page_link(
    source: dict[str, Any],
    page_index: int,
    *,
    page_verified: bool,
) -> str | None:
    if page_verified is not True:
        return None
    source_record = source.get("source", {})
    attachment_key = source_record.get("zotero_attachment_key")
    if (
        source_record.get("acquisition_method") != "zotero_local_api"
        or not isinstance(attachment_key, str)
        or re.fullmatch(r"[A-Z0-9]{8}", attachment_key) is None
    ):
        return None
    return f"zotero://open-pdf/library/items/{attachment_key}?page={page_index}"


def render_skim_markdown(
    source: dict[str, Any],
    evidence: list[Any],
    claims: list[Any],
    figures: dict[str, Any],
    run_record: dict[str, Any],
    status: str,
) -> str:
    metadata = source["metadata"]
    pdf = source["pdf"]
    paper_type, paper_type_label_zh, metadata_warnings = metadata_presentation(
        source
    )
    primary_paper_type = metadata.get("primary_paper_type") or paper_type
    secondary_paper_types = [
        value
        for value in metadata.get("secondary_paper_types", [])
        if value in SECONDARY_PAPER_TYPE_LABELS_ZH
    ]
    evidence_by_id = {item["evidence_id"]: item for item in evidence}
    verified_pages = {
        item["page_index"]
        for item in evidence
        if item.get("page_verified") is True
        and item.get("source_match_kind") in {"exact", "normalized"}
    }
    sections = [
        ("## 1. 核心科学问题", {"question"}),
        ("## 2. 研究背景与研究空白", {"background", "gap"}),
        ("## 3. 方法流程", {"method"}),
        ("## 4. 核心结果", {"result"}),
        ("## 5. 作者的解释、假设与讨论", {"interpretation", "hypothesis"}),
        ("## 6. 局限性、不确定性与适用边界", {"limitation"}),
        ("## 7. 结论", {"conclusion"}),
    ]
    review_pages = [str(page["page_index"]) for page in source["pages"] if page.get("warnings")]
    lines = [
        "---",
        f"title: {yaml_scalar(metadata.get('title'))}",
        f"authors: {yaml_scalar(first_author_only(metadata.get('authors', [])))}",
        f"year: {yaml_scalar(metadata.get('year'))}",
        f"journal: {yaml_scalar(metadata.get('journal'))}",
        f"doi: {yaml_scalar(metadata.get('doi'))}",
        f"paper_type: {yaml_scalar(paper_type)}",
        f"primary_paper_type: {yaml_scalar(primary_paper_type)}",
        f"secondary_paper_types: {yaml_scalar(secondary_paper_types)}",
        f"paper_type_label_zh: {yaml_scalar(paper_type_label_zh)}",
        f"metadata_warning: {yaml_scalar(metadata_warnings)}",
        f"citekey: {yaml_scalar(metadata.get('citekey'))}",
        f"zotero_item_key: {yaml_scalar(source['source'].get('zotero_item_key'))}",
        f"zotero_attachment_key: {yaml_scalar(source['source'].get('zotero_attachment_key'))}",
        f"source_file: {yaml_scalar(source['source']['query'])}",
        f"document_hash: {yaml_scalar(pdf['sha256'])}",
        f"reading_mode: {yaml_scalar(run_record.get('reading_mode'))}",
        f"skill_version: {yaml_scalar(SKILL_VERSION)}",
        f"validation_status: {yaml_scalar(status)}",
        f"created: {yaml_scalar(utc_now())}",
        "tags: [literature-note, litanchor]",
        "---",
        "",
        f"# {metadata.get('title')}",
        "",
        "## 0. 阅读状态",
        "",
        f"- 阅读模式：`{run_record.get('reading_mode')}`",
        f"- PDF 解析状态：`{pdf.get('preflight_status')}`",
        f"- 校验状态：`{status}`",
        f"- PDF 物理页数：{pdf.get('page_count')}",
        f"- 建议人工复核页：{', '.join(review_pages) if review_pages else '无'}",
        "",
    ]

    for heading, claim_types in sections:
        lines.extend([heading, ""])
        selected = [claim for claim in claims if claim.get("claim_type") in claim_types]
        if not selected:
            lines.extend(["- 尚无已校验主张。", ""])
            continue
        for claim in selected:
            evidence_ids = claim["evidence_ids"]
            pages = sorted(set(claim["page_refs"]))
            marker_parts = [", ".join(evidence_ids), f"PDF {', '.join(f'p.{page}' for page in pages)}"]
            links = [
                f"[打开 p.{page}]({link})"
                for page in pages
                if (
                    link := zotero_page_link(
                        source,
                        page,
                        page_verified=page in verified_pages,
                    )
                )
                is not None
            ]
            marker_parts.extend(links)
            marker = f"〔{'｜'.join(marker_parts)}〕"
            lines.append(f"- {claim['claim_text_zh']} {marker}")
            if claim.get("display_level") == "collapsed":
                for evidence_id in evidence_ids:
                    item = evidence_by_id[evidence_id]
                    lines.append("")
                    lines.append(f"> [!evidence]- {evidence_id}｜PDF p.{item['page_index']}")
                    quote_lines = evidence_quote_for_display(item).splitlines() or [""]
                    lines.extend(f"> {quote_line}" for quote_line in quote_lines)
                    lines.append("")
        lines.append("")

    lines.extend(["## 8. 关键视觉证据", ""])
    selected_figures = figures.get("selected", [])
    if selected_figures:
        for figure in selected_figures:
            page_index = figure["physical_pdf_page"]
            source_link = zotero_page_link(
                source,
                page_index,
                page_verified=True,
            )
            lines.extend(
                [
                    f"### {figure['figure_label']}",
                    "",
                    f"![[{figure['embed_path']}]]",
                    "",
                    f"- 选择理由：{figure['selection_reason']}",
                    f"- 正文讨论位置：{figure['discussion_location']}",
                    f"- PDF 物理页码：p.{page_index}",
                ]
            )
            if source_link:
                lines.append(f"- [在 Zotero 打开原页]({source_link})")
            lines.append("")
    else:
        lines.extend(
            [
                f"- 未嵌入图片：{figures.get('no_selection_reason')}",
                "",
            ]
        )

    lines.extend([
        "## 9. 我的思考",
        "",
        "<!-- litanchor:user:start -->",
        "此区域由用户编辑；自动更新不得覆盖。",
        "<!-- litanchor:user:end -->",
        "",
        "## 10. 证据索引",
        "",
        "| Evidence ID | PDF 页 | 类型 | 原文证据 |",
        "|---|---:|---|---|",
    ])
    for item in evidence:
        lines.append(
            f"| {_escape_table(item['evidence_id'])} | {item['page_index']} | "
            f"{_escape_table(item['evidence_type'])} | "
            f"{_escape_table(evidence_quote_for_display(item))} |"
        )
    lines.extend([
        "",
        "## 11. 校验信息",
        "",
        f"- EvidenceUnits：{len(evidence)}",
        f"- ClaimRecords：{len(claims)}",
        f"- 运行 ID：`{run_record.get('run_id')}`",
        "- 事实来源：仅限本地 PDF 原文。",
        "",
    ])
    return "\n".join(lines)


def _claim_marker(
    claim: dict[str, Any],
    source: dict[str, Any],
    verified_pages: set[int],
) -> str:
    evidence_ids = [str(item) for item in claim.get("evidence_ids", [])]
    pages = sorted(
        {
            page
            for page in claim.get("page_refs", [])
            if isinstance(page, int)
        }
    )
    marker_parts = [", ".join(evidence_ids), f"PDF {', '.join(f'p.{page}' for page in pages)}"]
    marker_parts.extend(
        f"[打开 p.{page}]({link})"
        for page in pages
        if (
            link := zotero_page_link(
                source,
                page,
                page_verified=page in verified_pages,
            )
        )
        is not None
    )
    return f"〔{'｜'.join(part for part in marker_parts if part)}〕"


def _claims_by_type(
    claims: list[Any],
    claim_types: set[str],
) -> list[dict[str, Any]]:
    return [
        claim
        for claim in claims
        if isinstance(claim, dict) and claim.get("claim_type") in claim_types
    ]


def _render_section_synthesis(
    section_synthesis: dict[str, Any] | None,
    section_target: str,
    claims: list[Any],
    source: dict[str, Any],
    verified_pages: set[int],
) -> str | None:
    """Render the prose bridge between Claim Ledger and the Final template."""
    if not isinstance(section_synthesis, dict):
        return None
    section = next(
        (
            item
            for item in section_synthesis.get("sections", [])
            if isinstance(item, dict) and item.get("section_target") == section_target
        ),
        None,
    )
    if section is None:
        return None
    if section.get("status") == "source_silent":
        return "**原文未说明**"
    if section.get("status") == "not_applicable":
        return "**不适用**"
    paragraphs = [
        str(item).strip()
        for item in section.get("paragraphs_zh", [])
        if str(item).strip()
    ]
    if not paragraphs:
        return None
    claim_by_id = {
        str(claim.get("claim_id")): claim
        for claim in claims
        if isinstance(claim, dict) and claim.get("claim_id")
    }
    selected_claims = [
        claim_by_id[claim_id]
        for claim_id in section.get("claim_ids", [])
        if claim_id in claim_by_id
    ]
    evidence_ids = sorted(
        {
            str(evidence_id)
            for claim in selected_claims
            for evidence_id in claim.get("evidence_ids", [])
        }
    )
    pages = sorted(
        {
            int(page)
            for claim in selected_claims
            for page in claim.get("page_refs", [])
            if isinstance(page, int)
        }
    )
    marker_parts = [", ".join(evidence_ids), f"PDF {', '.join(f'p.{page}' for page in pages)}"]
    marker_parts.extend(
        f"[打开 p.{page}]({link})"
        for page in pages
        if (
            link := zotero_page_link(
                source,
                page,
                page_verified=page in verified_pages,
            )
        )
        is not None
    )
    marker = f"〔{'｜'.join(part for part in marker_parts if part)}〕"
    return "\n\n".join([*paragraphs, f"*本节证据：{marker}*"])


def _prepend_synthesis(synthesis: str | None, details: str) -> str:
    if not synthesis:
        return details
    if details in {"**原文未说明**", "**不适用**"}:
        return synthesis
    return f"{synthesis}\n\n{details}"


def _render_claim_group(
    claims: list[Any],
    claim_types: set[str],
    source: dict[str, Any],
    verified_pages: set[int],
    *,
    empty: str = "**原文未说明**",
) -> str:
    selected = _claims_by_type(claims, claim_types)
    if not selected:
        return empty
    lines: list[str] = []
    for claim in selected:
        title = str(claim.get("title_zh") or "").strip()
        text = str(claim.get("claim_text_zh") or "").strip()
        marker = _claim_marker(claim, source, verified_pages)
        if title and title != text:
            lines.append(f"- **{title}**：{text} {marker}")
        else:
            lines.append(f"- {text} {marker}")
        for point in claim.get("detail_points_zh", []):
            lines.append(f"  - {point}")
        conditions = str(claim.get("conditions_zh") or "").strip()
        if conditions:
            lines.append(f"  - **成立条件与边界**：{conditions}")
    return "\n".join(lines)


def _overview_value(
    claims: list[Any],
    claim_types: set[str],
    source: dict[str, Any],
    verified_pages: set[int],
    *,
    limit: int = 3,
) -> str:
    selected = _claims_by_type(claims, claim_types)[:limit]
    if not selected:
        return "**原文未说明**"
    return "<br>".join(
        _escape_table(
            f"{claim['claim_text_zh']} {_claim_marker(claim, source, verified_pages)}"
        )
        for claim in selected
    )


def _format_numeric_value(value: Any, unit: Any) -> str:
    rendered_value = str(value or "").strip()
    rendered_unit = str(unit or "").strip()
    if not rendered_unit:
        return rendered_value

    def comparable(text: str) -> str:
        return (
            re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))
            .replace("◦", "°")
            .casefold()
        )

    if comparable(rendered_value).endswith(comparable(rendered_unit)):
        return rendered_value
    separator = "" if rendered_unit.startswith(("%", "‰", "°", "◦")) else " "
    return f"{rendered_value}{separator}{rendered_unit}".strip()


def _render_deep_results(
    claims: list[Any],
    source: dict[str, Any],
    verified_pages: set[int],
) -> str:
    results = _claims_by_type(claims, {"result"})
    if not results:
        return "**原文未说明**"
    lines: list[str] = []
    for index, claim in enumerate(results, start=1):
        title = str(claim.get("title_zh") or f"核心结果 {index}")
        numeric_parts = []
        for item in claim.get("numeric_items", []):
            if not isinstance(item, dict):
                continue
            value = str(item.get("value_original") or "")
            unit = str(item.get("unit_original") or "")
            variable = str(item.get("variable") or "")
            condition = str(item.get("condition") or "")
            rendered = " ".join(
                part for part in (variable, _format_numeric_value(value, unit)) if part
            ).strip()
            if condition:
                rendered = f"{rendered}（{condition}）"
            if rendered:
                numeric_parts.append(rendered)
        epistemic = {
            "observed": "作者报告",
            "supported": "作者认为证据支持",
            "interpreted": "作者解释",
            "hypothesized": "作者假设",
            "speculative": "作者推测",
            "unknown": "状态待核验",
        }.get(str(claim.get("epistemic_status")), "状态待核验")
        lines.extend(
            [
                f"### R{index}. {title}",
                "",
                f"- **主要发现**：{claim['claim_text_zh']} {_claim_marker(claim, source, verified_pages)}",
            ]
        )
        details = [str(point) for point in claim.get("detail_points_zh", [])]
        if details:
            lines.append("- **论证与细节**：")
            lines.extend(f"  - {point}" for point in details)
        lines.extend(
            [
                f"- **关键数值、比较或不确定性**：{'；'.join(numeric_parts) if numeric_parts else '原文未说明'}",
                f"- **证据状态**：{epistemic}",
                f"- **成立条件与适用范围**：{claim.get('conditions_zh') or '原文未说明'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _render_models(
    claims: list[Any],
    source: dict[str, Any],
    verified_pages: set[int],
) -> str:
    models = _claims_by_type(claims, {"model"})
    if not models:
        return "**不适用**"
    lines: list[str] = []
    for index, claim in enumerate(models, start=1):
        lines.extend(
            [
                f"#### M{index}. {claim.get('title_zh') or f'关键模型 {index}'}",
                "",
                f"- **作用与核心机制**：{claim['claim_text_zh']} {_claim_marker(claim, source, verified_pages)}",
            ]
        )
        for point in claim.get("detail_points_zh", []):
            lines.append(f"- {point}")
        lines.extend(
            [
                f"- **关键假设 / 条件**：{claim.get('conditions_zh') or '原文未说明'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _render_equations_metrics(
    claims: list[Any],
    source: dict[str, Any],
    verified_pages: set[int],
) -> str:
    records = _claims_by_type(claims, {"equation", "metric", "parameter"})
    if not records:
        return "**不适用**"
    lines: list[str] = []
    for index, claim in enumerate(records, start=1):
        prefix = {
            "equation": "Eq.",
            "metric": "Metric",
            "parameter": "Parameter",
        }[str(claim.get("claim_type"))]
        lines.extend(
            [
                f"#### {prefix} {index}：{claim.get('title_zh') or '名称原文未说明'}",
                "",
                f"- **用途与定义**：{claim['claim_text_zh']} {_claim_marker(claim, source, verified_pages)}",
            ]
        )
        for point in claim.get("detail_points_zh", []):
            lines.append(f"- {point}")
        lines.extend(
            [
                f"- **成立条件、单位或适用限制**：{claim.get('conditions_zh') or '原文未说明'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _render_experiments(
    claims: list[Any],
    source: dict[str, Any],
    verified_pages: set[int],
) -> str:
    experiments = _claims_by_type(claims, {"experiment"})
    if not experiments:
        return "**原文未说明**"
    lines = [
        "| 实验 / 比较 | 设置、目的与关键结果 | 证据位置 |",
        "| --- | --- | --- |",
    ]
    for claim in experiments:
        fragments = [
            str(claim["claim_text_zh"]),
            *(str(item) for item in claim.get("detail_points_zh", [])),
        ]
        text = "；".join(
            fragment.strip().rstrip("。；！？!?")
            for fragment in fragments
            if fragment.strip().rstrip("。；！？!?")
        )
        lines.append(
            f"| {_escape_table(claim.get('title_zh') or '实验')} | "
            f"{_escape_table(text)} | "
            f"{_escape_table(_claim_marker(claim, source, verified_pages))} |"
        )
    return "\n".join(lines)


def _render_visuals(
    figures: dict[str, Any],
    source: dict[str, Any],
    visual_analysis: dict[str, Any] | None = None,
) -> tuple[str, str]:
    selected = figures.get("selected", [])
    if not selected:
        reason = figures.get("no_selection_reason") or "原文未说明"
        return f"| 不适用 | { _escape_table(reason) } | 不适用 | 不适用 | 不适用 | 未嵌入 |", f"- **未嵌入图片**：{reason}"
    rows: list[str] = []
    details: list[str] = []
    analysis_by_label = {
        str(item.get("figure_label")): item
        for item in (
            visual_analysis.get("analyses", [])
            if isinstance(visual_analysis, dict)
            else []
        )
        if isinstance(item, dict) and item.get("figure_label")
    }
    for figure in selected:
        analysis = analysis_by_label.get(str(figure.get("figure_label")), {})
        page = figure["physical_pdf_page"]
        link = zotero_page_link(source, page, page_verified=True)
        page_cell = f"[PDF p.{page}]({link})" if link else f"PDF p.{page}"
        visual_role = {
            "method": "核心方法图",
            "result": "核心结果图",
            "both": "方法与结果图",
            "context": "背景图",
        }.get(str(figure.get("visual_role") or ""), "关键图")
        rows.append(
            f"| {_escape_table(figure['figure_label'])} | "
            f"{_escape_table(figure['selection_reason'])} | "
            f"{_escape_table(analysis.get('interpretation_zh') or figure['caption_original'])} | "
            f"{_escape_table(visual_role)} | "
            f"{_escape_table(page_cell)} | 已查看原 PDF 裁图 |"
        )
        details.extend(
            [
                f"### {figure['figure_label']}",
                "",
                f"![[{figure['embed_path']}]]",
                "",
                f"- **选择理由**：{figure['selection_reason']}",
                f"- **正文讨论位置**：{figure['discussion_location']}",
                f"- **视觉解读**：{analysis.get('interpretation_zh') or '解析失败'}",
                f"- **读图注意事项**：{analysis.get('reading_cautions') or figure.get('reading_cautions') or '解析失败'}",
            ]
        )
        if link:
            details.append(f"- [在 Zotero 打开原页]({link})")
        details.append("")
    return "\n".join(rows), "\n".join(details).rstrip()


def _render_evidence_quotes(
    evidence: list[Any],
    claims: list[Any],
) -> str:
    core_types = {
        "question",
        "gap",
        "contribution",
        "method",
        "model",
        "experiment",
        "result",
        "limitation",
        "conclusion",
    }
    support_map: dict[str, list[str]] = {}
    for claim in _claims_by_type(claims, core_types):
        for evidence_id in claim.get("evidence_ids", []):
            support_map.setdefault(str(evidence_id), []).append(str(claim["claim_id"]))
    selected = [
        item
        for item in evidence
        if isinstance(item, dict) and item.get("evidence_id") in support_map
    ][:16]
    if not selected:
        return "**原文未说明**"
    lines = [
        "| ID | 原文 | 页码 / 章节 | 支撑内容 |",
        "| --- | --- | --- | --- |",
    ]
    for item in selected:
        evidence_id = str(item["evidence_id"])
        location = f"PDF p.{item['page_index']} / {item.get('section') or 'Section 未说明'}"
        lines.append(
            f"| {_escape_table(evidence_id)} | "
            f"{_escape_table(evidence_quote_for_display(item))} | "
            f"{_escape_table(location)} | "
            f"{_escape_table(', '.join(support_map[evidence_id]))} |"
        )
    return "\n".join(lines)


def render_deep_markdown(
    source: dict[str, Any],
    evidence: list[Any],
    claims: list[Any],
    figures: dict[str, Any],
    run_record: dict[str, Any],
    status: str,
    section_synthesis: dict[str, Any] | None = None,
    visual_analysis: dict[str, Any] | None = None,
) -> str:
    template_path = Path(__file__).resolve().parents[1] / "assets" / FINAL_TEMPLATE_NAME
    try:
        template = template_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise PipelineError(f"Canonical deep-note template is missing: {template_path}") from exc

    metadata = source["metadata"]
    pdf = source["pdf"]
    machine_paper_type, paper_type_label_zh, metadata_warnings = (
        metadata_presentation(source)
    )
    primary_paper_type = (
        metadata.get("primary_paper_type") or machine_paper_type
    )
    secondary_paper_types = [
        value
        for value in metadata.get("secondary_paper_types", [])
        if value in SECONDARY_PAPER_TYPE_LABELS_ZH
    ]
    reading_mode = str(run_record.get("reading_mode") or "deep")
    autonomous_generation = bool(run_record.get("autonomous_generation", False))
    review_status = run_record.get("review_status") or (
        "evidence-checked" if status == "completed" else "draft"
    )
    generation_mode = run_record.get("generation_mode") or (
        "autonomous" if autonomous_generation else "structured_ledger"
    )
    optional_learning_placeholder = (
        "**原文未说明**"
        if reading_mode == "internalize"
        else "**本模式未生成（仅 internalize 模式要求）**"
    )
    verified_pages = {
        item["page_index"]
        for item in evidence
        if isinstance(item, dict)
        and item.get("page_verified") is True
        and item.get("source_match_kind") in {"exact", "normalized"}
    }
    paper_type_claims = _claims_by_type(claims, {"paper_type"})
    paper_type_labels = [str(item["claim_text_zh"]) for item in paper_type_claims]
    if not paper_type_labels and paper_type_label_zh:
        paper_type_labels = [paper_type_label_zh]
    if secondary_paper_types:
        paper_type_labels.append(
            "次级类型："
            + "、".join(
                SECONDARY_PAPER_TYPE_LABELS_ZH[value]
                for value in secondary_paper_types
            )
        )
    keywords = metadata.get("keywords") if isinstance(metadata.get("keywords"), list) else []
    frontmatter = "\n".join(
        [
            "---",
            f"title: {yaml_scalar(metadata.get('title'))}",
            f"authors: {yaml_scalar(first_author_only(metadata.get('authors', [])))}",
            f"year: {yaml_scalar(metadata.get('year'))}",
            f"journal: {yaml_scalar(metadata.get('journal'))}",
            f"doi: {yaml_scalar(metadata.get('doi'))}",
            f"paper_type: {yaml_scalar(machine_paper_type)}",
            f"primary_paper_type: {yaml_scalar(primary_paper_type)}",
            f"secondary_paper_types: {yaml_scalar(secondary_paper_types)}",
            f"paper_type_label_zh: {yaml_scalar(paper_type_label_zh)}",
            f"metadata_warning: {yaml_scalar(metadata_warnings)}",
            f"keywords: {yaml_scalar(keywords)}",
            f"zotero_key: {yaml_scalar(metadata.get('citekey') or source['source'].get('zotero_item_key'))}",
            f"source_pdf: {yaml_scalar(source['source'].get('query'))}",
            'extraction_engine: "PyMuPDF page baseline + consent-aware MinerU structure hints"',
            f"validation_status: {yaml_scalar(status)}",
            f"review_status: {yaml_scalar(review_status)}",
            f"generation_mode: {yaml_scalar(generation_mode)}",
            f"autonomous_generation: {yaml_scalar(autonomous_generation)}",
            "tags: [literature-note, deep-reading, litanchor]",
            f"created: {yaml_scalar(utc_now())}",
            "---",
        ]
    )
    summary_claims = _claims_by_type(claims, {"summary"})
    abstract = (
        f"{summary_claims[0]['claim_text_zh']} "
        f"{_claim_marker(summary_claims[0], source, verified_pages)}"
        if summary_claims
        else "**原文未说明**"
    )
    overview_rows = "\n".join(
        [
            f"| 论文类型 | {_escape_table('；'.join(paper_type_labels) if paper_type_labels else '原文未说明')} |",
            f"| 研究对象 / 数据 / 模型 | {_overview_value(claims, {'data', 'material', 'model'}, source, verified_pages)} |",
            f"| 核心问题 | {_overview_value(claims, {'question'}, source, verified_pages)} |",
            f"| 方法路线 | {_overview_value(claims, {'method', 'model'}, source, verified_pages)} |",
            f"| 主要发现 | {_overview_value(claims, {'result'}, source, verified_pages)} |",
            f"| 核心贡献 | {_overview_value(claims, {'contribution'}, source, verified_pages)} |",
            f"| 关键限制 | {_overview_value(claims, {'limitation'}, source, verified_pages)} |",
            "| 论证主线 | 背景与缺口 → 研究问题 → 方法与证据 → 结果与解释 → 结论与边界 |",
        ]
    )
    visual_rows, visual_details = _render_visuals(figures, source, visual_analysis)
    learning_claims = _claims_by_type(claims, {"learning_value"})
    expressions = _render_claim_group(
        claims,
        {"writing_expression"},
        source,
        verified_pages,
        empty=optional_learning_placeholder,
    )
    synthesis = {
        target: _render_section_synthesis(
            section_synthesis,
            target,
            claims,
            source,
            verified_pages,
        )
        for target in ("2.1", "2.2", "2.3", "3.1", "3.2", "3.3", "3.4", "3.5", "4", "6.1", "6.2", "6.3")
    }
    context = {
        "frontmatter": frontmatter,
        "title": str(metadata.get("title") or "Untitled paper"),
        "abstract": abstract,
        "overview_rows": overview_rows,
        "background_prior": _prepend_synthesis(
            synthesis["2.1"],
            _render_claim_group(claims, {"background", "prior_work"}, source, verified_pages),
        ),
        "gap_question": _prepend_synthesis(
            synthesis["2.2"],
            _render_claim_group(claims, {"gap", "question", "hypothesis"}, source, verified_pages),
        ),
        "contributions": _prepend_synthesis(
            synthesis["2.3"],
            _render_claim_group(claims, {"contribution"}, source, verified_pages),
        ),
        "data_materials": _prepend_synthesis(
            synthesis["3.1"],
            _render_claim_group(claims, {"data", "material", "preprocessing"}, source, verified_pages),
        ),
        "methods": _prepend_synthesis(
            synthesis["3.2"],
            _render_claim_group(claims, {"method"}, source, verified_pages),
        ),
        "method_steps": "\n".join(
            f"{index}. {claim['claim_text_zh']} {_claim_marker(claim, source, verified_pages)}"
            for index, claim in enumerate(_claims_by_type(claims, {"method"}), start=1)
        ) or "**原文未说明**",
        "models": _prepend_synthesis(
            synthesis["3.3"],
            _render_models(claims, source, verified_pages),
        ),
        "equations_metrics": _prepend_synthesis(
            synthesis["3.4"],
            _render_equations_metrics(claims, source, verified_pages),
        ),
        "experiments": _prepend_synthesis(
            synthesis["3.5"],
            _render_experiments(claims, source, verified_pages),
        ),
        "results": _prepend_synthesis(
            synthesis["4"],
            _render_deep_results(claims, source, verified_pages),
        ),
        "visual_table_rows": visual_rows,
        "visual_details": visual_details,
        "discussion": _prepend_synthesis(
            synthesis["6.1"],
            _render_claim_group(
                claims,
                {"interpretation", "discussion", "hypothesis"},
                source,
                verified_pages,
            ),
        ),
        "conclusions": _prepend_synthesis(
            synthesis["6.2"],
            _render_claim_group(claims, {"conclusion"}, source, verified_pages),
        ),
        "limitations": _prepend_synthesis(
            synthesis["6.3"],
            _render_claim_group(claims, {"limitation", "future_work"}, source, verified_pages),
        ),
        "research_value": _render_claim_group(
            claims,
            {"learning_value"},
            source,
            verified_pages,
            empty="**待用户补充**",
        ),
        "idea_125": (
            _render_claim_group(
                [learning_claims[0]],
                {"learning_value"},
                source,
                verified_pages,
            )
            if learning_claims
            else optional_learning_placeholder
        ),
        "visuals_125": "\n".join(
            f"{index}. **{figure['figure_label']}**：{figure['selection_reason']}"
            for index, figure in enumerate(figures.get("selected", [])[:2], start=1)
        ) or "**不适用**",
        "expressions": expressions,
        "terms": _render_claim_group(
            claims,
            {"term"},
            source,
            verified_pages,
            empty=optional_learning_placeholder,
        ),
        "evidence_quotes": _render_evidence_quotes(evidence, claims),
        "references": _render_claim_group(
            claims,
            {"reference"},
            source,
            verified_pages,
            empty=optional_learning_placeholder,
        ),
        "validation_comment": (
            f"<!-- litanchor:validation template={FINAL_TEMPLATE_ID}@{FINAL_TEMPLATE_VERSION}; "
            f"run={run_record.get('run_id')}; evidence={len(evidence)}; claims={len(claims)}; "
            f"status={status}; pdf_sha256={pdf.get('sha256')} -->"
        ),
    }
    rendered = template
    for key, value in context.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
    return rendered.rstrip() + "\n"


def render_markdown(
    source: dict[str, Any],
    evidence: list[Any],
    claims: list[Any],
    figures: dict[str, Any],
    run_record: dict[str, Any],
    status: str,
    section_synthesis: dict[str, Any] | None = None,
    visual_analysis: dict[str, Any] | None = None,
) -> str:
    if run_record.get("reading_mode") in {"deep", "internalize"}:
        return render_deep_markdown(
            source,
            evidence,
            claims,
            figures,
            run_record,
            status,
            section_synthesis,
            visual_analysis,
        )
    return render_skim_markdown(source, evidence, claims, figures, run_record, status)


def build_run(run_dir: Path, output_path: Path | None = None) -> tuple[Path, dict[str, Any]]:
    """Validate ledgers and render a non-overwriting Markdown preview."""
    run_dir = run_dir.resolve()
    result, source, evidence, claims, figures, coverage_receipt = validate_run(run_dir)
    validation_path = run_dir / "validation.json"
    coverage_path = run_dir / "coverage_receipt.json"
    atomic_write_json(coverage_path, coverage_receipt)
    if result["status"] == "blocked":
        atomic_write_json(validation_path, result)
        raise PipelineError(f"Validation blocked note generation; inspect {validation_path}")

    run_record = load_json(run_dir / "run.json")
    destination = (output_path or (run_dir / "preview.md")).resolve()
    if destination.exists():
        raise PipelineError(f"Refusing to overwrite existing note: {destination}")
    section_synthesis_path = run_dir / "section-synthesis.json"
    section_synthesis = (
        load_json(section_synthesis_path)
        if section_synthesis_path.is_file()
        else None
    )
    visual_analysis_path = run_dir / "visual-analysis.json"
    visual_analysis = (
        load_json(visual_analysis_path)
        if visual_analysis_path.is_file()
        else None
    )
    markdown = render_markdown(
        source,
        evidence,
        claims,
        figures,
        run_record,
        result["status"],
        section_synthesis,
        visual_analysis,
    )
    required_markers = ("---\n", "<!-- litanchor:user:start -->", "<!-- litanchor:user:end -->")
    format_findings: list[dict[str, str]] = []
    if not all(marker in markdown for marker in required_markers):
        format_findings.append(
            {
                "issue_type": "markdown_contract_failed",
                "message": "Generated Markdown is missing frontmatter or protected user markers.",
            }
        )
    if run_record.get("reading_mode") in {"deep", "internalize"}:
        format_findings.extend(validate_final_markdown(markdown))
        format_findings.extend(
            validate_cross_section_consistency(
                markdown,
                claims,
                resolve_paper_type(run_dir, source),
            )
        )
        format_findings.extend(validate_numeric_rendering_integrity(markdown))
        format_findings.extend(
            validate_table_sentence_rendering_integrity(markdown)
        )
        format_findings.extend(validate_duplicated_section_content(markdown))
    if format_findings:
        for index, finding in enumerate(format_findings, start=1):
            result["issues"].append(
                _issue(
                    f"V-F{index:03d}",
                    "blocker",
                    finding["issue_type"],
                    finding["message"],
                )
            )
        result["status"] = "blocked"
        result["statistics"]["blocker_count"] += len(format_findings)
        result["quality"]["format_valid"] = False
        atomic_write_json(validation_path, result)
        raise PipelineError(
            f"Generated Markdown failed the Final-template contract; inspect {validation_path}"
        )
    atomic_write_text(destination, markdown, overwrite=False)
    result["files"]["markdown_note"] = str(destination)
    result["quality"]["duplicated_section_content"] = True
    result["quality"]["format_valid"] = True
    result["quality"]["markdown_sha256"] = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
    atomic_write_json(validation_path, result)
    run_record["status"] = result["status"]
    run_record["completed"] = utc_now()
    run_record.setdefault("artifacts", {})["markdown_note"] = str(destination)
    run_record["artifacts"]["validation"] = str(validation_path)
    run_record["artifacts"]["coverage_receipt"] = str(coverage_path)
    run_record["artifacts"]["figures"] = str(run_dir / "figures.json")
    atomic_write_json(run_dir / "run.json", run_record)
    return destination, result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LitAnchor local manual-PDF pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare", help="preflight and extract a local PDF")
    prepare.add_argument("pdf", type=Path)
    prepare.add_argument("--output-root", type=Path, default=Path("runtime/runs"))
    prepare.add_argument("--mode", choices=("skim", "deep", "internalize"), default="deep")
    prepare.add_argument("--title")
    prepare.add_argument("--author", action="append", default=[])
    prepare.add_argument("--year", type=int)
    prepare.add_argument("--journal")
    prepare.add_argument("--doi")
    build = subparsers.add_parser("build", help="validate ledgers and render a Markdown preview")
    build.add_argument("run_dir", type=Path)
    build.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "prepare":
            run_dir, bundle = prepare_pdf(
                args.pdf,
                args.output_root,
                reading_mode=args.mode,
                title=args.title,
                authors=args.author,
                year=args.year,
                journal=args.journal,
                doi=args.doi,
            )
            print(json.dumps({"run_dir": str(run_dir), "preflight_status": bundle["pdf"]["preflight_status"]}, ensure_ascii=False))
            return 0 if bundle["pdf"]["preflight_status"] in {"PASS", "PASS_WITH_WARNINGS"} else 2
        destination, result = build_run(args.run_dir, args.output)
        print(json.dumps({"markdown_note": str(destination), "status": result["status"]}, ensure_ascii=False))
        return 0
    except PipelineError as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
