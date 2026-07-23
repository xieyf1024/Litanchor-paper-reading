#!/usr/bin/env python3
"""Deterministic local PDF preparation, validation, and note rendering for LitAnchor."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "0.1"
SKILL_VERSION = "0.4.1-candidate"
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
    "research_question", "background", "research_gap", "hypothesis", "data", "material",
    "model", "method_step", "parameter", "metric", "result", "figure", "table", "equation",
    "discussion", "limitation", "uncertainty", "conclusion",
}
CLAIM_TYPES = {"question", "background", "gap", "method", "result", "interpretation", "hypothesis", "limitation", "conclusion"}
EPISTEMIC_STATUSES = {"observed", "supported", "interpreted", "hypothesized", "speculative", "unknown"}


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


class _ListHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


def _warning_code(message: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", message.lower()).strip("_")
    return f"pypdf_warning:{normalized[:120]}"


def _text_quality(text: str) -> int:
    tokens = re.findall(r"\S+", text)
    long_tokens = sum(len(token) >= 35 for token in tokens)
    replacement_characters = text.count("\ufffd")
    return len(tokens) - (long_tokens * 25) - (replacement_characters * 10)


def _extract_page_text(page: Any) -> tuple[str, list[str]]:
    warnings: list[str] = []
    logger = logging.getLogger("pypdf")
    handler = _ListHandler()
    logger.addHandler(handler)
    try:
        layout_text = page.extract_text(extraction_mode="layout") or ""
    except (TypeError, ValueError, NotImplementedError):
        layout_text = ""
        warnings.append("layout_extraction_unavailable")
    except Exception as exc:  # pypdf raises parser-specific exceptions here
        warnings.append(f"page_extraction_failed:{type(exc).__name__}")
        layout_text = ""
    finally:
        logger.removeHandler(handler)
    for message in handler.messages:
        warnings.append(_warning_code(message))
    try:
        plain_text = page.extract_text() or ""
    except Exception:
        plain_text = ""
    layout_column_gaps = sum(bool(re.search(r"\S {20,}\S", line)) for line in layout_text.splitlines())
    if plain_text and layout_column_gaps >= 2:
        text = plain_text
        warnings.append("multicolumn_layout_detected_plain_order_used")
    elif _text_quality(plain_text) > _text_quality(layout_text):
        text = plain_text
    else:
        text = layout_text or plain_text
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
        from pypdf import PdfReader
    except ImportError as exc:
        raise PipelineError(
            "pypdf is required. Install the repository requirements before preparing a PDF."
        ) from exc

    digest = sha256_file(pdf_path)
    reader_logger = logging.getLogger("pypdf")
    reader_handler = _ListHandler()
    reader_logger.addHandler(reader_handler)
    try:
        reader = PdfReader(str(pdf_path), strict=False)
        page_count = len(reader.pages)
        _ = getattr(reader, "metadata", None)  # Force parser warnings without trusting metadata values.
    except Exception as exc:
        raise PipelineError(f"PDF cannot be parsed: {type(exc).__name__}: {exc}") from exc
    finally:
        reader_logger.removeHandler(reader_handler)
    if page_count < 1:
        raise PipelineError("PDF contains no pages")

    run_dir = unique_run_dir(output_root.resolve(), digest)
    paper_id = f"pdf-{digest[:16]}"
    resolved_authors = list(authors or [])

    pages: list[dict[str, Any]] = []
    pdf_warnings: list[str] = [_warning_code(message) for message in reader_handler.messages]
    if reader.is_encrypted:
        preflight_status = "BLOCKED"
        pdf_warnings.append("encrypted_pdf")
    else:
        for page_index, page in enumerate(reader.pages, start=1):
            text, page_warnings = _extract_page_text(page)
            pages.append(
                {
                    "page_index": page_index,
                    "printed_page": None,
                    "raw_text": text,
                    "extraction_method": "native_text",
                    "confidence": _page_confidence(text, page_warnings),
                    "warnings": page_warnings,
                }
            )
        readable_pages = sum(
            len(re.sub(r"\s+", "", page["raw_text"])) >= 80 for page in pages
        )
        coverage = readable_pages / page_count
        total_visible = sum(len(re.sub(r"\s+", "", page["raw_text"])) for page in pages)
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
    normalized = unicodedata.normalize("NFKC", text).replace("\u00ad", "")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    joined_hyphen = re.sub(r"(?<=\w)-\s+(?=\w)", "-", normalized)
    dehyphenated = re.sub(r"(?<=\w)-\s+(?=\w)", "", normalized)
    return {normalized, joined_hyphen, dehyphenated, dehyphenated.replace("-", "")}


def quote_is_traceable(quote: str, page_text: str) -> bool:
    return quote_match_kind(quote, page_text) != "unmatched"


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


def build_coverage_receipt(
    source: dict[str, Any],
    evidence: list[Any],
    run_record: dict[str, Any],
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
    reading_mode = run_record.get("reading_mode")
    if reading_mode == "deep":
        minimum_evidence_pages = min(3, page_count)
        minimum_sections = 1 if page_count == 1 else min(3, page_count)
        reaches_later_half = bool(
            evidence_pages
            and max(evidence_pages) >= max(1, math.ceil(page_count * 0.5))
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
        actual_match_kind = quote_match_kind(quote, pages[page_index].get("raw_text", ""))
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
            not isinstance(claim.get("claim_text_zh"), str)
            or not claim["claim_text_zh"].strip()
            or claim.get("claim_type") not in CLAIM_TYPES
            or claim.get("epistemic_status") not in EPISTEMIC_STATUSES
        ):
            add_issue("blocker", "invalid_claim_schema", f"Claim {claim_id} has invalid text, type, or epistemic status.", claim_id=claim_id)
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
        supporting_text = " ".join(str(item.get("quote_original", "")) for item in supporting)
        numeric_ok = True
        numeric_items = claim.get("numeric_items", [])
        if not isinstance(numeric_items, list):
            add_issue("blocker", "invalid_numeric_items", f"Claim {claim_id} numeric_items must be an array.", claim_id=claim_id)
            continue
        for numeric_item in numeric_items:
            numeric_checks += 1
            value = str(numeric_item.get("value_original", "")) if isinstance(numeric_item, dict) else ""
            unit = numeric_item.get("unit_original") if isinstance(numeric_item, dict) else None
            value_found = value and any(value in form for form in trace_forms(supporting_text))
            unit_found = unit is None or any(str(unit) in form for form in trace_forms(supporting_text))
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
            if not any(token in form for form in trace_forms(supporting_text)):
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

    coverage_receipt = build_coverage_receipt(source, evidence, run_record)
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
            "numeric_fidelity": numeric_passes / numeric_checks if numeric_checks else 1.0,
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
            "format_valid": False,
        },
    }
    return result, source, evidence, claims, figures, coverage_receipt


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    return json.dumps(value, ensure_ascii=False)


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


def render_markdown(
    source: dict[str, Any],
    evidence: list[Any],
    claims: list[Any],
    figures: dict[str, Any],
    run_record: dict[str, Any],
    status: str,
) -> str:
    metadata = source["metadata"]
    pdf = source["pdf"]
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
                    quote_lines = str(item["quote_original"]).splitlines() or [""]
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
                    f"- 图题：{figure['caption_original']}",
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
            f"{_escape_table(item['evidence_type'])} | {_escape_table(item['quote_original'])} |"
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
    markdown = render_markdown(
        source,
        evidence,
        claims,
        figures,
        run_record,
        result["status"],
    )
    required_markers = ("---\n", "<!-- litanchor:user:start -->", "<!-- litanchor:user:end -->")
    if not all(marker in markdown for marker in required_markers):
        raise PipelineError("Generated Markdown failed deterministic format checks")
    atomic_write_text(destination, markdown, overwrite=False)
    result["files"]["markdown_note"] = str(destination)
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
