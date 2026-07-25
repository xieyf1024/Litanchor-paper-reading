#!/usr/bin/env python3
"""Stage a single-paper autonomous LitAnchor deep-reading run."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from litanchor_local import (  # noqa: E402
    PipelineError,
    atomic_write_json,
    load_json,
    sha256_file,
    utc_now,
)


AUTONOMOUS_VERSION = "0.5.0-dev"
ALLOWED_AUTONOMOUS_ORIGINS = {"auto_extracted", "auto_synthesized"}
PAPER_TYPE_REQUIRED_CONTENT: dict[str, list[str]] = {
    "method-algorithm": [
        "question",
        "contribution",
        "method",
        "model",
        "metric",
        "experiment",
        "result",
        "limitation",
    ],
    "model-description": [
        "question",
        "model",
        "method",
        "metric",
        "experiment",
        "result",
        "limitation",
    ],
    "empirical-research": [
        "question",
        "data",
        "method",
        "metric",
        "experiment",
        "result",
        "limitation",
    ],
    "review": [
        "question",
        "method",
        "result",
        "limitation",
    ],
}


class AutonomousPipelineError(PipelineError):
    """Raised when an autonomous run would violate blind or evidence policy."""


SECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("abstract", re.compile(r"^abstract$", re.IGNORECASE)),
    ("introduction", re.compile(r"^(?:\d+(?:\.\d+)*[.)]?\s*)?introduction$", re.IGNORECASE)),
    ("background", re.compile(r"^(?:\d+(?:\.\d+)*[.)]?\s*)?(?:background|motivation)$", re.IGNORECASE)),
    (
        "related-work",
        re.compile(
            r"^(?:\d+(?:\.\d+)*[.)]?\s*)?(?:related work|previous work|prior work)$",
            re.IGNORECASE,
        ),
    ),
    (
        "methods",
        re.compile(
            r"^(?:\d+(?:\.\d+)*[.)]?\s*)?(?:methods?|methodology|materials and methods)$",
            re.IGNORECASE,
        ),
    ),
    (
        "model",
        re.compile(
            r"^(?:\d+(?:\.\d+)*[.)]?\s*)?(?:model|model description|model components|architecture|approach)$",
            re.IGNORECASE,
        ),
    ),
    (
        "experiments",
        re.compile(
            r"^(?:\d+(?:\.\d+)*[.)]?\s*)?(?:experiments?|experimental setup|evaluation)$",
            re.IGNORECASE,
        ),
    ),
    (
        "results",
        re.compile(
            r"^(?:\d+(?:\.\d+)*[.)]?\s*)?(?:results?|results and discussion)$",
            re.IGNORECASE,
        ),
    ),
    ("discussion", re.compile(r"^(?:\d+(?:\.\d+)*[.)]?\s*)?discussion$", re.IGNORECASE)),
    (
        "limitations",
        re.compile(
            r"^(?:\d+(?:\.\d+)*[.)]?\s*)?(?:limitations?|uncertaint(?:y|ies))$",
            re.IGNORECASE,
        ),
    ),
    (
        "conclusion",
        re.compile(
            r"^(?:\d+(?:\.\d+)*[.)]?\s*)?(?:conclusions?|summary and conclusions?)$",
            re.IGNORECASE,
        ),
    ),
    ("references", re.compile(r"^(?:references|bibliography)$", re.IGNORECASE)),
    (
        "appendix",
        re.compile(r"^(?:appendix|supplementary (?:material|information))(?:\s+[A-Z0-9].*)?$", re.IGNORECASE),
    ),
]


def _visible_characters(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def _block_text(block: dict[str, Any]) -> str:
    lines: list[str] = []
    for line in block.get("lines", []):
        spans = line.get("spans", []) if isinstance(line, dict) else []
        value = "".join(str(span.get("text", "")) for span in spans if isinstance(span, dict))
        if value.strip():
            lines.append(value.strip())
    return "\n".join(lines)


def _leading_styled_heading(block: dict[str, Any]) -> str | None:
    spans = [
        span
        for line in block.get("lines", [])
        if isinstance(line, dict)
        for span in line.get("spans", [])
        if isinstance(span, dict) and str(span.get("text", "")).strip()
    ]
    if not spans:
        return None
    first = spans[0]
    first_font = str(first.get("font", ""))
    first_flags = int(first.get("flags", 0))
    styled = (
        bool(re.search(r"(?:bold|italic|semibold|demi)", first_font, re.IGNORECASE))
        or bool(first_flags & 2)
        or bool(first_flags & 16)
    )
    if not styled:
        return None
    values: list[str] = []
    for span in spans:
        if (
            str(span.get("font", "")) != first_font
            or int(span.get("flags", 0)) != first_flags
        ):
            break
        values.append(str(span.get("text", "")).strip())
    candidate = re.sub(r"\s+", " ", " ".join(values)).strip()
    return candidate if 4 <= len(candidate) <= 150 else None


def extract_pymupdf_pages(pdf_path: Path) -> list[dict[str, Any]]:
    """Extract authoritative physical-page text, blocks, and coordinates."""
    try:
        import pymupdf
    except ImportError as exc:
        raise AutonomousPipelineError(
            "PyMuPDF is required for the v0.5 authoritative page baseline."
        ) from exc

    pages: list[dict[str, Any]] = []
    try:
        document = pymupdf.open(pdf_path)
    except Exception as exc:
        raise AutonomousPipelineError(
            f"PyMuPDF could not open the source PDF: {type(exc).__name__}: {exc}"
        ) from exc
    try:
        for page_index, page in enumerate(document, start=1):
            text = page.get_text("text", sort=True).strip()
            page_dict = page.get_text("dict", sort=True)
            text_blocks: list[dict[str, Any]] = []
            for block_index, block in enumerate(page_dict.get("blocks", [])):
                if not isinstance(block, dict):
                    continue
                bbox = block.get("bbox")
                text_blocks.append(
                    {
                        "block_id": f"P{page_index}-B{block_index + 1}",
                        "block_type": "text" if block.get("type") == 0 else "image",
                        "bbox": [round(float(value), 3) for value in bbox]
                        if isinstance(bbox, (list, tuple)) and len(bbox) == 4
                        else None,
                        "text": _block_text(block) if block.get("type") == 0 else "",
                        "heading_candidate": (
                            _leading_styled_heading(block)
                            if block.get("type") == 0
                            else None
                        ),
                    }
                )
            warnings: list[str] = []
            visible = _visible_characters(text)
            if visible == 0:
                warnings.append("empty_page_text")
            elif visible < 80:
                warnings.append("sparse_page_text")
            replacement_ratio = text.count("\ufffd") / max(len(text), 1)
            if replacement_ratio > 0.005:
                warnings.append("replacement_character_rate_high")
            confidence = 1.0 if visible >= 200 else 0.75 if visible >= 80 else 0.4 if visible else 0.0
            if warnings:
                confidence = max(0.0, confidence - 0.1 * len(warnings))
            pages.append(
                {
                    "page_index": page_index,
                    "printed_page": None,
                    "raw_text": text,
                    "text_blocks": text_blocks,
                    "page_width": round(float(page.rect.width), 3),
                    "page_height": round(float(page.rect.height), 3),
                    "extraction_method": "pymupdf_native",
                    "confidence": round(confidence, 2),
                    "warnings": warnings,
                }
            )
    finally:
        document.close()
    return pages


def _normalized_section_type(line: str) -> str | None:
    candidate = re.sub(r"\s+", " ", line.strip())
    candidate = candidate.rstrip(" .:")
    if not candidate or len(candidate) > 100:
        return None
    for section_type, pattern in SECTION_PATTERNS:
        if pattern.fullmatch(candidate):
            return section_type
    return None


def _classify_freeform_heading(title: str) -> str | None:
    normalized = _normalized_section_type(title)
    if normalized is not None:
        return normalized
    value = re.sub(
        r"^(?:[A-Z]|\d+)(?:\.\d+)*[.)]?\s*",
        "",
        re.sub(r"\s+", " ", title.strip()),
        flags=re.IGNORECASE,
    ).casefold()
    if "related work" in value or "previous work" in value:
        return "related-work"
    if any(token in value for token in ("experiment", "evaluation", "benchmark")):
        return "experiments"
    if "simulation overview" in value:
        return "experiments"
    if "component" in value and "capabilit" in value:
        return "model"
    if any(
        token in value
        for token in (
            "approach",
            "method",
            "implementation",
            "reconstruction",
            "splicing",
            "data and",
        )
    ):
        return "methods" if "approach" not in value else "model"
    if any(token in value for token in ("result", "comparison", "variability", "performance")):
        return "results"
    if "limitation" in value or "uncertaint" in value:
        return "limitations"
    if "discussion" in value and "conclusion" not in value:
        return "discussion"
    if any(token in value for token in ("conclusion", "future direction", "summary")):
        return "conclusion"
    if "supplement" in value or "appendix" in value:
        return "appendix"
    return None


def detect_sections(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build a conservative page-level section map from visible headings."""
    detected: list[dict[str, Any]] = []
    for page in pages:
        page_index = int(page["page_index"])
        seen_on_page: set[tuple[str, str]] = set()
        for line in str(page.get("raw_text", "")).splitlines():
            normalized_type = _normalized_section_type(line)
            if normalized_type is None:
                continue
            original = re.sub(r"\s+", " ", line.strip())
            identity = (normalized_type, original.casefold())
            if identity in seen_on_page:
                continue
            seen_on_page.add(identity)
            detected.append(
                {
                    "section_id": f"S-{len(detected) + 1:03d}",
                    "title_original": original,
                    "normalized_type": normalized_type,
                    "start_page": page_index,
                    "end_page": page_index,
                    "confidence": 0.9,
                    "source": "pymupdf_heading",
                }
            )
        for block in page.get("text_blocks", []):
            if not isinstance(block, dict) or block.get("block_type") != "text":
                continue
            candidate = str(block.get("heading_candidate") or "").strip()
            if not candidate:
                continue
            normalized_type = _classify_freeform_heading(candidate)
            identity = (normalized_type or "", candidate.casefold())
            if normalized_type is None or identity in seen_on_page:
                continue
            seen_on_page.add(identity)
            detected.append(
                {
                    "section_id": f"S-{len(detected) + 1:03d}",
                    "title_original": candidate,
                    "normalized_type": normalized_type,
                    "start_page": page_index,
                    "end_page": page_index,
                    "confidence": 0.75,
                    "source": "pymupdf_block_heading",
                }
            )
    if not detected and pages:
        return [
            {
                "section_id": "S-001",
                "title_original": "Document",
                "normalized_type": "document",
                "start_page": 1,
                "end_page": int(pages[-1]["page_index"]),
                "confidence": 0.3,
                "source": "fallback_document",
            }
        ]
    for index, section in enumerate(detected):
        next_start = (
            int(detected[index + 1]["start_page"])
            if index + 1 < len(detected)
            else int(pages[-1]["page_index"])
        )
        section["end_page"] = max(int(section["start_page"]), next_start)
    return detected


def fuse_mineru_sections(
    run_dir: Path,
    mineru_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Use aligned MinerU headings to enhance, never replace, the page map."""
    run_dir = run_dir.resolve()
    mineru_dir = (mineru_dir or run_dir / "mineru").resolve()
    markdown = (mineru_dir / "mineru_raw.md").read_text(encoding="utf-8")
    alignment = load_json(mineru_dir / "alignment.json")
    privacy = load_json(mineru_dir / "privacy_receipt.json")
    plan = load_json(run_dir / "mineru-plan.json")
    if privacy.get("consent_external_upload") is not True:
        raise AutonomousPipelineError("MinerU result lacks upload-consent provenance.")
    selected_pages = list(plan.get("selected_original_pages", []))
    reported_pages = privacy.get("original_physical_pages")
    if reported_pages is None and plan.get("route") == "whole_document":
        source = load_json(run_dir / "source-bundle.json")
        if privacy.get("source_pdf_sha256") == source.get("pdf", {}).get("sha256"):
            reported_pages = selected_pages
    if list(reported_pages or []) != selected_pages:
        raise AutonomousPipelineError(
            "MinerU result original-page mapping differs from mineru-plan.json."
        )

    positioned_blocks: list[tuple[int, dict[str, Any]]] = []
    search_start = 0
    for block in alignment.get("blocks", []):
        if not isinstance(block, dict):
            continue
        text = str(block.get("text", ""))
        position = markdown.find(text, search_start)
        if position < 0:
            position = markdown.find(text)
        if position >= 0:
            positioned_blocks.append((position, block))
            search_start = position + len(text)

    enhanced: list[dict[str, Any]] = []
    for match in re.finditer(r"(?m)^#{1,6}\s+(.+?)\s*$", markdown):
        title = match.group(1).strip()
        section_type = _classify_freeform_heading(title)
        if section_type is None:
            continue
        following = next(
            (
                block
                for position, block in positioned_blocks
                if position > match.end()
                and block.get("status") in {"exact", "fuzzy"}
                and isinstance(block.get("pdf_page"), int)
            ),
            None,
        )
        if following is None:
            continue
        enhanced.append(
            {
                "section_id": "",
                "title_original": title,
                "normalized_type": section_type,
                "start_page": int(following["pdf_page"]),
                "end_page": int(following["pdf_page"]),
                "confidence": 0.85 if following["status"] == "exact" else 0.7,
                "source": "mineru_aligned_heading",
                "alignment_status": following["status"],
                "authoritative_evidence": False,
            }
        )

    existing = load_json(run_dir / "sections.json")
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str, int]] = set()
    for section in [*existing, *enhanced]:
        if not isinstance(section, dict):
            continue
        identity = (
            str(section.get("normalized_type", "")),
            str(section.get("title_original", "")).casefold(),
            int(section.get("start_page", 0)),
        )
        if identity in seen:
            continue
        seen.add(identity)
        merged.append(dict(section))
    merged.sort(key=lambda item: (int(item.get("start_page", 0)), str(item.get("title_original", ""))))
    auto_run = load_json(run_dir / "autonomous-run.json")
    page_count = int(auto_run.get("page_count") or max(selected_pages, default=1))
    for index, section in enumerate(merged):
        section["section_id"] = f"S-{index + 1:03d}"
        next_page = (
            int(merged[index + 1]["start_page"])
            if index + 1 < len(merged)
            else page_count
        )
        section["end_page"] = max(int(section["start_page"]), next_page)
    atomic_write_json(run_dir / "sections.json", merged)

    plan["status"] = "completed"
    plan["output_dir"] = str(mineru_dir)
    plan["alignment_statistics"] = alignment.get("statistics", {})
    plan["authoritative_evidence_created"] = False
    atomic_write_json(run_dir / "mineru-plan.json", plan)
    auto_run["mineru"] = plan
    auto_run["sections"] = {
        "count": len(merged),
        "pymupdf_and_mineru_fused": True,
    }
    profile = load_json(run_dir / "paper-profile.json")
    reading_passes = build_reading_passes(page_count, merged, profile)
    atomic_write_json(run_dir / "reading-passes.json", reading_passes)
    auto_run["passes"] = reading_passes
    atomic_write_json(run_dir / "autonomous-run.json", auto_run)
    return merged


def classify_paper_type(
    metadata: dict[str, Any],
    sections: list[dict[str, Any]],
    pages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Classify without using a pre-filled gold label."""
    title = str(metadata.get("title", "")).casefold()
    section_types = {str(item.get("normalized_type", "")) for item in sections}
    lead_text = " ".join(str(page.get("raw_text", "")) for page in pages[:2]).casefold()
    signals: list[str] = []

    if re.search(r"\b(review|survey|systematic review|meta-analysis)\b", title):
        paper_type = "review"
        confidence = 0.95
        signals.append("review_term_in_title")
    elif (
        "model" in title
        and re.search(r"\b(framework|description|system|version|component)\b", title)
    ) or (
        "model" in section_types
        and re.search(r"\b(model components?|model description|coupled model)\b", lead_text)
    ):
        paper_type = "model-description"
        confidence = 0.9
        signals.append("model_framework_or_description")
    elif re.search(
        r"\b(algorithms?|methods?|architectures?|networks?|autoencoders?|learners?|learning)\b",
        title,
    ) or (
        "experiments" in section_types
        and (
            bool({"methods", "model"} & section_types)
            or re.search(r"\b(we propose|we present|our method|architecture)\b", lead_text)
        )
    ):
        paper_type = "method-algorithm"
        confidence = 0.85
        signals.append("method_or_architecture_signal")
    elif {"methods", "results"} & section_types:
        paper_type = "empirical-research"
        confidence = 0.8
        signals.append("methods_or_results_sections")
    else:
        paper_type = "empirical-research"
        confidence = 0.45
        signals.append("default_research_profile")
    return {
        "schema_version": "0.1",
        "paper_type": paper_type,
        "confidence": confidence,
        "signals": signals,
        "origin": "auto_synthesized",
    }


def _pages_for_sections(
    sections: list[dict[str, Any]],
    accepted_types: set[str],
    fallback_pages: list[int],
) -> list[int]:
    pages: set[int] = set()
    for section in sections:
        if section.get("normalized_type") not in accepted_types:
            continue
        pages.update(
            range(int(section["start_page"]), int(section["end_page"]) + 1)
        )
    return sorted(pages) or fallback_pages


def build_reading_passes(
    page_count: int,
    sections: list[dict[str, Any]],
    paper_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Create six explicit, auditable reading work packets."""
    all_pages = list(range(1, page_count + 1))
    lead_pages = list(range(1, min(page_count, 4) + 1))
    problem_pages = _pages_for_sections(
        sections,
        {"abstract", "introduction", "background", "related-work"},
        lead_pages,
    )
    method_pages = _pages_for_sections(
        sections,
        {"methods", "model", "experiments"},
        all_pages,
    )
    result_pages = _pages_for_sections(
        sections,
        {"results", "discussion", "limitations", "conclusion"},
        all_pages,
    )
    return [
        {
            "pass_id": "pass-1-structure",
            "purpose": "paper type, sections, and argument spine",
            "source_pages": all_pages,
            "required_outputs": ["paper-profile.json", "sections.json"],
        },
        {
            "pass_id": "pass-2-problem",
            "purpose": "background, prior work, gap, question, and contribution",
            "source_pages": problem_pages,
            "required_evidence_types": [
                "background",
                "prior_work",
                "research_gap",
                "research_question",
                "contribution",
            ],
        },
        {
            "pass_id": "pass-3-method",
            "purpose": "data, materials, method, model, equation, metric, and experiment",
            "source_pages": method_pages,
            "required_evidence_types": [
                "data",
                "material",
                "preprocessing",
                "model",
                "method_step",
                "equation",
                "metric",
                "experiment",
            ],
        },
        {
            "pass_id": "pass-4-results",
            "purpose": "results, visuals, discussion, limitations, and conclusions",
            "source_pages": result_pages,
            "required_evidence_types": [
                "result",
                "figure",
                "table",
                "discussion",
                "limitation",
                "conclusion",
            ],
        },
        {
            "pass_id": "pass-5-ledgers",
            "purpose": "deduplicate evidence and synthesize claims without new facts",
            "source_pages": all_pages,
            "required_outputs": ["evidence.json", "claims.json"],
            "allowed_origins": sorted(ALLOWED_AUTONOMOUS_ORIGINS),
        },
        {
            "pass_id": "pass-6-compose-review",
            "purpose": "compose Paper Template - Final and run independent fidelity and recall reviews",
            "source_pages": all_pages,
            "required_outputs": [
                "fidelity-review.json",
                "recall-review.json",
                "candidate-note.md",
            ],
            "paper_type": paper_profile["paper_type"],
        },
    ]


FIGURE_CAPTION_PATTERN = re.compile(
    r"(?im)^\s*(?:fig(?:ure)?\.?)\s*([A-Za-z0-9]+)\s*[.:]\s*(.+)$"
)


def discover_figure_candidates(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates_by_label: dict[str, dict[str, Any]] = {}
    full_text = "\n".join(str(page.get("raw_text", "")) for page in pages)
    for page in pages:
        text = str(page.get("raw_text", ""))
        for match in FIGURE_CAPTION_PATTERN.finditer(text):
            label = f"Figure {match.group(1)}"
            caption = re.sub(r"\s+", " ", match.group(2).strip())
            existing = candidates_by_label.get(label)
            if existing is None or len(caption) > len(existing["caption_original"]):
                candidates_by_label[label] = {
                    "visual_id": f"V-{len(candidates_by_label) + 1:03d}",
                    "label": label,
                    "page_index": int(page["page_index"]),
                    "caption_original": caption,
                    "text_reference_count": len(
                        re.findall(rf"\b{re.escape(label)}\b", full_text, re.IGNORECASE)
                    ),
                    "selection_status": "candidate",
                    "origin": "auto_extracted",
                }
    return list(candidates_by_label.values())


def validate_autonomous_origins(
    evidence: list[dict[str, Any]],
    claims: list[dict[str, Any]],
) -> None:
    violations: list[str] = []
    for record in evidence:
        if record.get("origin") not in ALLOWED_AUTONOMOUS_ORIGINS:
            violations.append(str(record.get("evidence_id", "<unknown-evidence>")))
    for record in claims:
        if record.get("origin") not in ALLOWED_AUTONOMOUS_ORIGINS:
            violations.append(str(record.get("claim_id", "<unknown-claim>")))
    if violations:
        raise AutonomousPipelineError(
            "Blind autonomous run contains disallowed or missing origins: "
            + ", ".join(violations)
        )


def _write_review_contracts(
    run_dir: Path,
    paper_profile: dict[str, Any],
) -> None:
    paper_type = str(paper_profile["paper_type"])
    required_content = PAPER_TYPE_REQUIRED_CONTENT.get(
        paper_type,
        PAPER_TYPE_REQUIRED_CONTENT["empirical-research"],
    )
    fidelity_review = {
        "schema_version": "0.1",
        "reviewer_role": "fidelity-reviewer",
        "independent_from_composer": True,
        "checked_claim_ids": [],
        "findings": [],
        "final_status": "pending",
    }
    recall_review = {
        "schema_version": "0.1",
        "reviewer_role": "recall-reviewer",
        "independent_from_composer": True,
        "paper_type": paper_type,
        "required_content_groups": required_content,
        "observed_content_groups": [],
        "missing_content_groups": required_content,
        "findings": [],
        "final_status": "pending",
    }
    atomic_write_json(run_dir / "fidelity-review.json", fidelity_review)
    atomic_write_json(run_dir / "recall-review.json", recall_review)


def validate_independent_reviews(run_dir: Path) -> None:
    """Block completion until two independent review contracts are satisfied."""
    run_dir = run_dir.resolve()
    evidence = load_json(run_dir / "evidence.json")
    claims = load_json(run_dir / "claims.json")
    profile = load_json(run_dir / "paper-profile.json")
    fidelity = load_json(run_dir / "fidelity-review.json")
    recall = load_json(run_dir / "recall-review.json")
    if not isinstance(evidence, list) or not isinstance(claims, list):
        raise AutonomousPipelineError("Autonomous ledgers must be JSON arrays.")
    validate_autonomous_origins(evidence, claims)

    if (
        fidelity.get("reviewer_role") != "fidelity-reviewer"
        or fidelity.get("independent_from_composer") is not True
        or fidelity.get("final_status") not in {"pass", "warning"}
    ):
        raise AutonomousPipelineError(
            "Fidelity review is missing, non-independent, or incomplete."
        )
    expected_claim_ids = {
        str(claim.get("claim_id"))
        for claim in claims
        if isinstance(claim, dict) and claim.get("claim_id")
    }
    checked_claim_ids = {
        str(claim_id) for claim_id in fidelity.get("checked_claim_ids", [])
    }
    if checked_claim_ids != expected_claim_ids:
        raise AutonomousPipelineError(
            "Fidelity review must check every autonomous ClaimRecord exactly once."
        )

    expected_required = set(
        PAPER_TYPE_REQUIRED_CONTENT.get(
            str(profile.get("paper_type")),
            PAPER_TYPE_REQUIRED_CONTENT["empirical-research"],
        )
    )
    required = set(map(str, recall.get("required_content_groups", [])))
    observed = set(map(str, recall.get("observed_content_groups", [])))
    missing = set(map(str, recall.get("missing_content_groups", [])))
    if (
        recall.get("reviewer_role") != "recall-reviewer"
        or recall.get("independent_from_composer") is not True
        or recall.get("final_status") not in {"pass", "warning"}
        or required != expected_required
        or missing
        or not required.issubset(observed)
    ):
        raise AutonomousPipelineError(
            "Recall review is missing, non-independent, incomplete, or uses "
            "the wrong paper-type content contract."
        )
    blocking_findings = [
        finding
        for review in (fidelity, recall)
        for finding in review.get("findings", [])
        if isinstance(finding, dict)
        and finding.get("severity") in {"blocker", "error"}
    ]
    if blocking_findings:
        raise AutonomousPipelineError(
            "Independent review contains unresolved blocker/error findings."
        )


def _mineru_plan(
    pdf_path: Path,
    pages: list[dict[str, Any]],
    figure_candidates: list[dict[str, Any]],
    allow_upload: bool,
) -> dict[str, Any]:
    whole_eligible = (
        len(pages) <= 20 and pdf_path.stat().st_size <= 10 * 1024 * 1024
    )
    if not allow_upload:
        route = "disabled_without_upload_consent"
        selected_pages: list[int] = []
    elif whole_eligible:
        route = "whole_document"
        selected_pages = list(range(1, len(pages) + 1))
    else:
        warning_pages = {
            int(page["page_index"]) for page in pages if page.get("warnings")
        }
        visual_pages = {
            int(candidate["page_index"]) for candidate in figure_candidates
        }
        selected_pages = sorted(warning_pages | visual_pages)[:6]
        route = "selected_complex_pages" if selected_pages else "not_required"
    return {
        "schema_version": "0.1",
        "upload_consent": allow_upload,
        "whole_document_eligible": whole_eligible,
        "route": route,
        "selected_original_pages": selected_pages,
        "status": "pending" if allow_upload and selected_pages else "not_started",
        "policy": (
            "MinerU is structure-only. Every accepted EvidenceUnit must be "
            "verified against the original PyMuPDF physical page."
        ),
    }


def _require_empty_blind_ledgers(run_dir: Path) -> None:
    evidence = load_json(run_dir / "evidence.json")
    claims = load_json(run_dir / "claims.json")
    if evidence or claims:
        raise AutonomousPipelineError(
            "Autonomous blind start requires empty evidence.json and claims.json."
        )


def build_autonomous_plan(
    run_dir: Path,
    *,
    allow_mineru_upload: bool,
) -> dict[str, Any]:
    """Create all non-semantic work packets without pre-filling the ledgers."""
    run_dir = run_dir.resolve()
    _require_empty_blind_ledgers(run_dir)
    source = load_json(run_dir / "source-bundle.json")
    run_record = load_json(run_dir / "run.json")
    pdf_path = Path(source["pdf"]["path"]).resolve()
    if sha256_file(pdf_path) != source["pdf"]["sha256"]:
        raise AutonomousPipelineError("Source PDF hash changed after preparation.")

    pages = extract_pymupdf_pages(pdf_path)
    expected_pages = int(source["pdf"]["page_count"])
    if len(pages) != expected_pages:
        raise AutonomousPipelineError(
            f"PyMuPDF page count mismatch: {len(pages)} != {expected_pages}."
        )
    sections = detect_sections(pages)
    paper_profile = classify_paper_type(
        source.get("metadata", {}),
        sections,
        pages,
    )
    reading_passes = build_reading_passes(len(pages), sections, paper_profile)
    figure_candidates = discover_figure_candidates(pages)
    mineru_plan = _mineru_plan(
        pdf_path,
        pages,
        figure_candidates,
        allow_mineru_upload,
    )

    source["pages"] = pages
    source["pdf"]["authoritative_text_engine"] = "PyMuPDF"
    source["pdf"]["authoritative_page_count_verified"] = True
    source["pdf"]["pymupdf_extracted_at"] = utc_now()
    atomic_write_json(run_dir / "source-bundle.json", source)
    atomic_write_json(run_dir / "pymupdf-pages.json", pages)
    atomic_write_json(run_dir / "sections.json", sections)
    atomic_write_json(run_dir / "paper-profile.json", paper_profile)
    atomic_write_json(run_dir / "reading-passes.json", reading_passes)
    atomic_write_json(run_dir / "figure-candidates.json", figure_candidates)
    atomic_write_json(run_dir / "mineru-plan.json", mineru_plan)
    _write_review_contracts(run_dir, paper_profile)

    autonomous_run = {
        "schema_version": "0.1",
        "autonomous_version": AUTONOMOUS_VERSION,
        "run_id": run_record.get("run_id", run_dir.name),
        "paper_id": source.get("paper_id"),
        "status": "awaiting_agent_analysis",
        "baseline_engine": "PyMuPDF",
        "page_count": len(pages),
        "paper_type": paper_profile["paper_type"],
        "passes": reading_passes,
        "blind_input_policy": {
            "reference_notes_allowed": False,
            "prefilled_ledgers_allowed": False,
            "allowed_origins": sorted(ALLOWED_AUTONOMOUS_ORIGINS),
        },
        "mineru": mineru_plan,
        "artifacts": {
            "source_bundle": "source-bundle.json",
            "pymupdf_pages": "pymupdf-pages.json",
            "sections": "sections.json",
            "paper_profile": "paper-profile.json",
            "reading_passes": "reading-passes.json",
            "figure_candidates": "figure-candidates.json",
            "mineru_plan": "mineru-plan.json",
            "evidence": "evidence.json",
            "claims": "claims.json",
            "fidelity_review": "fidelity-review.json",
            "recall_review": "recall-review.json",
        },
        "created": utc_now(),
    }
    atomic_write_json(run_dir / "autonomous-run.json", autonomous_run)
    run_record["skill_version"] = AUTONOMOUS_VERSION
    run_record["status"] = "awaiting_agent_analysis"
    run_record["autonomous_generation"] = True
    run_record["generation_mode"] = "autonomous_candidate"
    run_record["review_status"] = "pending_independent_review"
    run_record.setdefault("artifacts", {}).update(autonomous_run["artifacts"])
    atomic_write_json(run_dir / "run.json", run_record)
    return autonomous_run


def _start_from_zotero(args: argparse.Namespace) -> Path:
    from zotero_local import ZoteroLocalClient, prepare_zotero_item

    selectors = ("item_key", "title", "doi", "citekey")
    selector = next(name for name in selectors if getattr(args, name))
    client = ZoteroLocalClient(args.base_url)
    run_dir, _bundle = prepare_zotero_item(
        client,
        selector,
        getattr(args, selector),
        args.output_root,
        reading_mode="deep",
        attachment_key=args.attachment_key,
    )
    return run_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stage one Zotero/PDF paper for v0.5 autonomous deep reading"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    start = subparsers.add_parser("start")
    source_group = start.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--run-dir", type=Path)
    source_group.add_argument("--item-key")
    source_group.add_argument("--title")
    source_group.add_argument("--doi")
    source_group.add_argument("--citekey")
    start.add_argument("--attachment-key")
    start.add_argument("--output-root", type=Path, default=Path("runtime/runs"))
    start.add_argument("--base-url", default="http://127.0.0.1:23119/api")
    start.add_argument("--allow-mineru-upload", action="store_true")

    status = subparsers.add_parser("status")
    status.add_argument("--run-dir", type=Path, required=True)
    fuse = subparsers.add_parser("fuse-mineru")
    fuse.add_argument("--run-dir", type=Path, required=True)
    fuse.add_argument("--mineru-dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "start":
            run_dir = args.run_dir or _start_from_zotero(args)
            plan = build_autonomous_plan(
                run_dir,
                allow_mineru_upload=args.allow_mineru_upload,
            )
            print(
                json.dumps(
                    {
                        "run_dir": str(run_dir.resolve()),
                        "status": plan["status"],
                        "paper_type": plan["paper_type"],
                        "page_count": plan["page_count"],
                        "mineru_route": plan["mineru"]["route"],
                    },
                    ensure_ascii=False,
                )
            )
        elif args.command == "status":
            plan = load_json(args.run_dir.resolve() / "autonomous-run.json")
            print(json.dumps(plan, ensure_ascii=False, indent=2))
        else:
            sections = fuse_mineru_sections(args.run_dir, args.mineru_dir)
            print(
                json.dumps(
                    {
                        "run_dir": str(args.run_dir.resolve()),
                        "status": "completed",
                        "section_count": len(sections),
                        "authoritative_evidence_created": False,
                    },
                    ensure_ascii=False,
                )
            )
        return 0
    except PipelineError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
