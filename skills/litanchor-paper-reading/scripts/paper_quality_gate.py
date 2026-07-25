#!/usr/bin/env python3
"""Deterministic completeness checks for LitAnchor deep-reading notes."""

from __future__ import annotations

import math
import re
from typing import Any


FINAL_TEMPLATE_ID = "paper-template-final"
FINAL_TEMPLATE_VERSION = "1.0"
FINAL_TEMPLATE_NAME = "Paper Template - Final.md"

FINAL_REQUIRED_HEADINGS = (
    "## 1. 论文速览",
    "## 2. 背景、问题与贡献",
    "### 2.1 研究背景与前人工作",
    "### 2.2 研究缺口与研究问题",
    "### 2.3 贡献与创新",
    "## 3. 数据、材料与方法",
    "### 3.1 研究对象、数据或材料",
    "### 3.2 方法与研究设计",
    "### 3.3 关键模型、算法或技术环节",
    "### 3.4 核心公式与评价指标",
    "### 3.5 实验、比较与复现要点",
    "## 4. 核心结果与证据",
    "## 5. 重要图表",
    "## 6. 讨论、结论与限制",
    "### 6.1 作者如何解释结果",
    "### 6.2 核心结论",
    "### 6.3 局限性与不确定性",
    "## 7. 对研究与学习的价值",
    "### 7.2 125 提炼",
    "## 8. 术语、原文证据与滚雪球阅读",
    "### 8.3 值得继续追踪的参考文献",
)

DEEP_REQUIRED_GROUPS = {
    "一句话摘要": ({"summary"}, 1),
    "核心研究问题": ({"question"}, 1),
    "必要背景": ({"background", "prior_work"}, 1),
    "研究缺口": ({"gap"}, 1),
    "贡献与创新": ({"contribution"}, 1),
    "数据、材料与方法": (
        {
            "data",
            "material",
            "preprocessing",
            "method",
            "model",
            "equation",
            "metric",
            "experiment",
        },
        4,
    ),
    "核心结果": ({"result"}, 2),
    "作者解释与讨论": ({"interpretation", "discussion"}, 1),
    "局限性": ({"limitation"}, 1),
    "核心结论": ({"conclusion"}, 1),
}

PAPER_TYPE_ALIASES = {
    "method": "method-algorithm",
    "algorithm": "method-algorithm",
    "method/algorithm": "method-algorithm",
    "method-algorithm": "method-algorithm",
    "model": "model-description",
    "model description": "model-description",
    "model-description": "model-description",
    "empirical": "empirical-research",
    "empirical research": "empirical-research",
    "empirical-research": "empirical-research",
    "review": "review",
    "review paper": "review",
}

PAPER_TYPE_REQUIRED_GROUPS = {
    "method-algorithm": {
        "method_or_model": ({"method", "model"}, 2),
        "metric": ({"metric"}, 1),
        "experiment": ({"experiment"}, 1),
        "result": ({"result"}, 2),
    },
    "model-description": {
        "data_or_components": ({"data", "material", "model"}, 3),
        "model": ({"model"}, 2),
        "experiment": ({"experiment"}, 1),
        "result": ({"result"}, 2),
    },
    "empirical-research": {
        "data_or_material": ({"data", "material", "preprocessing"}, 1),
        "method_or_model": ({"method", "model"}, 2),
        "metric": ({"metric"}, 1),
        "experiment": ({"experiment"}, 2),
        "result": ({"result"}, 2),
    },
    "review": {
        "review_scope": ({"data", "material", "reference"}, 1),
        "synthesis_method": ({"method"}, 1),
        "result": ({"result"}, 2),
    },
}

INTERNALIZE_REQUIRED_GROUPS = {
    "learning_value": ({"learning_value"}, 1),
    "writing_expressions": ({"writing_expression"}, 5),
    "terms": ({"term"}, 1),
    "references": ({"reference"}, 1),
}

FINAL_SECTION_CLAIM_TYPES = {
    "3.1": {"data", "material", "preprocessing"},
    "3.2": {"method"},
    "3.3": {"model"},
    "3.4": {"equation", "metric"},
    "3.5": {"experiment"},
    "6.1": {"interpretation", "discussion", "hypothesis"},
    "6.2": {"conclusion"},
    "6.3": {"limitation", "future_work"},
}

DETAIL_REQUIRED_TYPES = {
    "contribution",
    "method",
    "model",
    "experiment",
    "result",
    "interpretation",
    "discussion",
    "limitation",
    "conclusion",
}

SENTENCE_BOUNDARY_EVIDENCE_TYPES = {
    "summary",
    "paper_type",
    "research_question",
    "background",
    "prior_work",
    "research_gap",
    "hypothesis",
    "contribution",
    "data",
    "material",
    "preprocessing",
    "model",
    "method_step",
    "experiment",
    "result",
    "discussion",
    "limitation",
    "uncertainty",
    "conclusion",
    "future_work",
    "term",
    "writing_expression",
    "reference",
}


def evidence_quote_completeness(
    evidence_type: str,
    quote: str,
) -> tuple[bool, str | None]:
    """Reject prose snippets that start or end inside a sentence."""
    if evidence_type not in SENTENCE_BOUNDARY_EVIDENCE_TYPES:
        return True, None
    text = quote.strip()
    if not text:
        return False, "The original quote is empty."
    first_alnum = next((character for character in text if character.isalnum()), "")
    if first_alnum.isalpha() and first_alnum != first_alnum.upper():
        return False, "The quote starts inside a sentence."
    stripped_end = text.rstrip("\"'”’)]}")
    if not stripped_end or stripped_end[-1] not in ".?!":
        return False, "The quote does not end at a sentence boundary."
    return True, None


def validate_cross_section_consistency(
    markdown: str,
    claims: list[Any],
    paper_type: Any = None,
) -> list[dict[str, str]]:
    """Reject formal sections that deny content already present in the ledger."""
    del paper_type
    issues: list[dict[str, str]] = []
    for section_id, claim_types in FINAL_SECTION_CLAIM_TYPES.items():
        if not any(_claim_type(claim) in claim_types for claim in claims):
            continue
        match = re.search(
            rf"^### {re.escape(section_id)}[^\n]*\n(?P<body>.*?)(?=^###? |\Z)",
            markdown,
            flags=re.MULTILINE | re.DOTALL,
        )
        body = match.group("body").strip() if match else ""
        if not body or body.startswith(("**原文未说明**", "**不适用**")):
            issues.append(
                {
                    "issue_type": "cross_section_consistency",
                    "message": (
                        f"Final section {section_id} denies or omits content that exists "
                        "in the Evidence/Claim Ledger."
                    ),
                }
            )
    return issues


def validate_numeric_rendering_integrity(markdown: str) -> list[dict[str, str]]:
    """Detect duplicated numeric suffixes introduced by Markdown rendering."""
    patterns = (
        r"%\s*%",
        r"(?:°|◦)\s*C\s*(?:°|◦)\s*C",
        r"\b(years?|months?|days?|hours?|hrs?|Ghz|GHz|Mhz|MHz|km|mm|cm)"
        r"\s*\1\b",
        r"\b(m|s)\s+\1\b",
    )
    matches = [
        match.group(0)
        for pattern in patterns
        for match in re.finditer(pattern, markdown, flags=re.IGNORECASE)
    ]
    if not matches:
        return []
    return [
        {
            "issue_type": "numeric_rendering_integrity",
            "message": (
                "Rendered numeric values contain duplicated unit suffixes: "
                + ", ".join(sorted(set(matches)))
            ),
        }
    ]


def validate_table_sentence_rendering_integrity(
    markdown: str,
) -> list[dict[str, str]]:
    """Reject mechanical punctuation joins inside rendered Markdown tables."""
    malformed = sorted(
        {
            match.group(0)
            for match in re.finditer(r"(?:。|！|？|；)\s*；", markdown)
        }
    )
    if not malformed:
        return []
    return [
        {
            "issue_type": "table_sentence_rendering_integrity",
            "message": (
                "Rendered table text contains mechanically duplicated punctuation: "
                + ", ".join(malformed)
            ),
        }
    ]


def evaluate_summary_completeness(
    claims: list[Any],
    evidence: list[Any],
) -> list[dict[str, str]]:
    """Require a deep-note summary to cover problem, method, and result evidence."""
    summaries = [
        claim
        for claim in claims
        if isinstance(claim, dict) and _claim_type(claim) == "summary"
    ]
    evidence_by_id = {
        str(item.get("evidence_id")): item
        for item in evidence
        if isinstance(item, dict) and item.get("evidence_id")
    }
    problems: list[str] = []
    if not summaries:
        problems.append("no summary claim exists")
    else:
        summary = summaries[0]
        text = re.sub(r"\s+", "", str(summary.get("claim_text_zh") or ""))
        evidence_ids = [
            str(item)
            for item in summary.get("evidence_ids", [])
            if str(item) in evidence_by_id
        ]
        evidence_types = {
            str(evidence_by_id[item].get("evidence_type") or "")
            for item in evidence_ids
        }
        groups = (
            {"research_question", "research_gap", "background", "summary"},
            {
                "method_step",
                "model",
                "data",
                "material",
                "preprocessing",
                "experiment",
            },
            {"result", "conclusion", "contribution"},
        )
        if len(text) < 80:
            problems.append(f"summary is too short ({len(text)}/80 characters)")
        if len(set(evidence_ids)) < 3:
            problems.append("summary uses fewer than three distinct EvidenceUnits")
        missing_groups = [
            label
            for label, group in zip(("problem", "method", "result"), groups)
            if not evidence_types & group
        ]
        if missing_groups:
            problems.append(
                "summary lacks " + ", ".join(missing_groups) + " evidence"
            )
    if not problems:
        return []
    return [
        {
            "issue_type": "summary_completeness",
            "message": "Deep-note summary failed: " + "; ".join(problems) + ".",
        }
    ]


def validate_page_semantic_coverage(
    page_classification: dict[str, Any],
    page_count: int,
) -> list[dict[str, str]]:
    """Require every non-reference physical page to receive semantic review."""
    pages = page_classification.get("pages")
    problems: list[str] = []
    if not isinstance(pages, list):
        problems.append("page-classification.json has no pages array")
        pages = []
    page_numbers = [
        item.get("page_index")
        for item in pages
        if isinstance(item, dict)
    ]
    expected = list(range(1, page_count + 1))
    if sorted(page_numbers) != expected or len(set(page_numbers)) != page_count:
        problems.append("physical-page classification is incomplete or duplicated")
    valid_classes = {
        "main_content",
        "references_only",
        "appendix",
        "supplementary_content",
        "extraction_failed",
    }
    for item in pages:
        if not isinstance(item, dict):
            continue
        page = item.get("page_index")
        classification = item.get("classification")
        if classification not in valid_classes:
            problems.append(f"p.{page} has invalid classification")
            continue
        required = item.get("semantic_review_required")
        reviewed = item.get("semantic_reviewed")
        if classification == "references_only":
            if required is not False or reviewed is not True:
                problems.append(f"p.{page} reference exclusion is not explicit")
            if not str(item.get("exclusion_reason") or "").strip():
                problems.append(f"p.{page} reference exclusion has no reason")
        else:
            if required is not True or reviewed is not True:
                problems.append(
                    f"p.{page} {classification} content was not semantically reviewed"
                )
            outcome = item.get("review_outcome")
            if outcome not in {"evidence_captured", "no_core_claims"}:
                problems.append(f"p.{page} has no valid semantic review outcome")
            if outcome == "evidence_captured" and not item.get("evidence_ids"):
                problems.append(f"p.{page} captured evidence but lists no Evidence ID")
            if (
                outcome == "no_core_claims"
                and not str(item.get("review_notes") or "").strip()
            ):
                problems.append(f"p.{page} no-core-claims decision has no rationale")
    if not problems:
        return []
    return [
        {
            "issue_type": "page_semantic_coverage",
            "message": "Physical-page semantic coverage failed: " + "; ".join(problems) + ".",
        }
    ]


def evaluate_visual_result_coverage(
    figures: dict[str, Any],
    claims: list[Any],
) -> list[dict[str, str]]:
    """Require a documented all-figure pass and a selected result visual when available."""
    candidates = figures.get("candidates_evaluated")
    selected = figures.get("selected")
    candidate_count = figures.get("candidate_count")
    problems: list[str] = []
    if figures.get("inventory_complete") is not True:
        problems.append("the all-figure inventory is not marked complete")
    if not isinstance(candidates, list):
        problems.append("candidates_evaluated is missing")
        candidates = []
    if not isinstance(candidate_count, int) or candidate_count != len(candidates):
        problems.append("candidate_count does not match candidates_evaluated")
    if not isinstance(selected, list):
        problems.append("selected is not an array")
        selected = []
    valid_roles = {"method", "result", "both", "context"}
    valid_decisions = {"selected", "rejected"}
    for candidate in candidates:
        if (
            not isinstance(candidate, dict)
            or candidate.get("visual_role") not in valid_roles
            or candidate.get("decision") not in valid_decisions
            or not str(candidate.get("reason") or "").strip()
        ):
            problems.append("each figure candidate needs role, decision, and reason")
            break
    selected_labels = {
        str(item.get("figure_label"))
        for item in selected
        if isinstance(item, dict)
    }
    evaluated_selected_labels = {
        str(item.get("figure_label"))
        for item in candidates
        if isinstance(item, dict) and item.get("decision") == "selected"
    }
    if selected_labels != evaluated_selected_labels:
        problems.append("selected figures do not match the all-figure decisions")

    has_result_claims = any(_claim_type(claim) == "result" for claim in claims)
    result_candidates = [
        item
        for item in candidates
        if isinstance(item, dict) and item.get("visual_role") in {"result", "both"}
    ]
    selected_result = any(
        isinstance(item, dict) and item.get("visual_role") in {"result", "both"}
        for item in selected
    )
    if has_result_claims and result_candidates and not selected_result:
        problems.append("a core result figure was evaluated but none was selected")
    if has_result_claims and not result_candidates and not str(
        figures.get("no_result_visual_reason") or ""
    ).strip():
        problems.append("no_result_visual_reason is required when no result figure exists")

    if not problems:
        return []
    return [
        {
            "issue_type": "visual_result_coverage",
            "message": "Visual Selection Pass failed: " + "; ".join(problems) + ".",
        }
    ]


def _claim_type(claim: Any) -> str:
    return str(claim.get("claim_type", "")) if isinstance(claim, dict) else ""


def _detail_points(claim: Any) -> list[str]:
    if not isinstance(claim, dict):
        return []
    points = claim.get("detail_points_zh", [])
    if not isinstance(points, list):
        return []
    return [str(point).strip() for point in points if str(point).strip()]


def claim_substantive_characters(claims: list[Any]) -> int:
    """Count human-note Chinese content without evidence quotations or machine fields."""
    chunks: list[str] = []
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        chunks.append(str(claim.get("claim_text_zh", "")))
        chunks.extend(_detail_points(claim))
        chunks.append(str(claim.get("conditions_zh", "") or ""))
    return len(re.sub(r"\s+", "", "".join(chunks)))


def canonical_paper_type(paper_type: Any) -> str | None:
    values = paper_type if isinstance(paper_type, list) else [paper_type]
    for value in values:
        normalized = re.sub(r"[_\s]+", " ", str(value or "").strip().casefold())
        if normalized in PAPER_TYPE_ALIASES:
            return PAPER_TYPE_ALIASES[normalized]
        hyphenated = normalized.replace(" ", "-")
        if hyphenated in PAPER_TYPE_REQUIRED_GROUPS:
            return hyphenated
    return None


def evaluate_deep_claims(
    claims: list[Any],
    page_count: int,
    paper_type: Any = None,
    reading_mode: str = "deep",
) -> list[dict[str, str]]:
    """Return blocking quality findings for a declared deep/internalize run."""
    issues: list[dict[str, str]] = []
    missing: list[str] = []
    for label, (claim_types, minimum) in DEEP_REQUIRED_GROUPS.items():
        count = sum(_claim_type(claim) in claim_types for claim in claims)
        if count < minimum:
            missing.append(f"{label}（{count}/{minimum}）")
    if missing:
        issues.append(
            {
                "issue_type": "deep_required_section_missing",
                "message": "Deep reading lacks required content groups: " + "；".join(missing),
            }
        )

    canonical_type = canonical_paper_type(paper_type)
    if canonical_type is None:
        issues.append(
            {
                "issue_type": "paper_type_required_sections",
                "message": (
                    "Deep reading requires one supported paper type: method-algorithm, "
                    "model-description, empirical-research, or review."
                ),
            }
        )
    else:
        profile_missing: list[str] = []
        for label, (claim_types, minimum) in PAPER_TYPE_REQUIRED_GROUPS[
            canonical_type
        ].items():
            count = sum(_claim_type(claim) in claim_types for claim in claims)
            if count < minimum:
                profile_missing.append(f"{label} ({count}/{minimum})")
        if profile_missing:
            issues.append(
                {
                    "issue_type": "paper_type_required_sections",
                    "message": (
                        f"{canonical_type} is missing required content groups: "
                        + ", ".join(profile_missing)
                    ),
                }
            )
        if "metric" in PAPER_TYPE_REQUIRED_GROUPS[canonical_type]:
            metric_count = sum(_claim_type(claim) == "metric" for claim in claims)
            if metric_count < PAPER_TYPE_REQUIRED_GROUPS[canonical_type]["metric"][1]:
                issues.append(
                    {
                        "issue_type": "metric_recall",
                        "message": (
                            f"{canonical_type} requires an evidence-grounded metric record."
                        ),
                    }
                )
        if "experiment" in PAPER_TYPE_REQUIRED_GROUPS[canonical_type]:
            experiment_count = sum(
                _claim_type(claim) == "experiment" for claim in claims
            )
            if experiment_count < PAPER_TYPE_REQUIRED_GROUPS[canonical_type][
                "experiment"
            ][1]:
                issues.append(
                    {
                        "issue_type": "experiment_recall",
                        "message": (
                            f"{canonical_type} requires more evidence-grounded experiment "
                            "or evaluation records."
                        ),
                    }
                )

    minimum_claims = min(24, max(12, math.ceil(max(page_count, 1) * 0.65)))
    minimum_details = min(18, max(6, math.ceil(max(page_count, 1) * 0.35)))
    detail_count = sum(len(_detail_points(claim)) for claim in claims)
    if len(claims) < minimum_claims or detail_count < minimum_details:
        issues.append(
            {
                "issue_type": "deep_content_recall_insufficient",
                "message": (
                    "Deep reading is too sparse for the source: "
                    f"{len(claims)}/{minimum_claims} claims and "
                    f"{detail_count}/{minimum_details} explanatory detail points."
                ),
            }
        )

    shallow = [
        str(claim.get("claim_id", "<unknown>"))
        for claim in claims
        if isinstance(claim, dict)
        and _claim_type(claim) in DETAIL_REQUIRED_TYPES
        and not _detail_points(claim)
        and not claim.get("numeric_items")
        and not str(claim.get("conditions_zh") or "").strip()
    ]
    if shallow:
        issues.append(
            {
                "issue_type": "deep_section_depth_insufficient",
                "message": (
                    "Core deep-reading claims have no explanation, conditions, or numeric detail: "
                    + ", ".join(shallow)
                ),
            }
        )

    minimum_chars = min(2400, max(600, max(page_count, 1) * 75))
    characters = claim_substantive_characters(claims)
    if characters < minimum_chars:
        issues.append(
            {
                "issue_type": "deep_substantive_content_too_short",
                "message": (
                    "Evidence-grounded Chinese analysis is too short for deep mode: "
                    f"{characters}/{minimum_chars} substantive characters."
                ),
            }
        )
    if reading_mode == "internalize":
        missing_internalize: list[str] = []
        for label, (claim_types, minimum) in INTERNALIZE_REQUIRED_GROUPS.items():
            count = sum(_claim_type(claim) in claim_types for claim in claims)
            if count < minimum:
                missing_internalize.append(f"{label} ({count}/{minimum})")
        if missing_internalize:
            issues.append(
                {
                    "issue_type": "internalize_required_sections",
                    "message": (
                        "Internalize mode is missing required learning-layer content: "
                        + ", ".join(missing_internalize)
                    ),
                }
            )
    return issues


def validate_final_markdown(markdown: str) -> list[dict[str, str]]:
    """Check the rendered deep note against the canonical Final template contract."""
    issues: list[dict[str, str]] = []
    missing = [heading for heading in FINAL_REQUIRED_HEADINGS if heading not in markdown]
    if missing:
        issues.append(
            {
                "issue_type": "final_template_heading_missing",
                "message": "Rendered note is missing Final-template headings: " + "；".join(missing),
            }
        )
    unresolved = sorted(set(re.findall(r"\{\{[a-zA-Z0-9_ -]+\}\}", markdown)))
    if unresolved:
        issues.append(
            {
                "issue_type": "unresolved_template_slot",
                "message": "Rendered note contains unresolved template slots: " + ", ".join(unresolved),
            }
        )
    for marker in ("<!-- litanchor:user:start -->", "<!-- litanchor:user:end -->"):
        if marker not in markdown:
            issues.append(
                {
                    "issue_type": "user_edit_marker_missing",
                    "message": f"Rendered note is missing protected user marker {marker}.",
                }
            )
    return issues
