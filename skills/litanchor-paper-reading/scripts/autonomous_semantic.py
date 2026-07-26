#!/usr/bin/env python3
"""Validate autonomous semantic artifacts before note composition."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from litanchor_local import page_quote_match_kind, quote_match_kind, utc_now
from paper_quality_gate import evidence_quote_completeness


class SemanticContractError(RuntimeError):
    """Raised when an autonomous semantic artifact violates the deep-reading contract."""


EVIDENCE_REQUIRED_FIELDS = {
    "evidence_id",
    "origin",
    "evidence_type",
    "page_index",
    "section",
    "block_id",
    "bounding_box",
    "quote_original",
    "context_before",
    "context_after",
    "epistemic_status",
    "epistemic_markers",
    "confidence",
    "extraction_confidence",
    "needs_review",
    "page_verified",
    "source_match_kind",
    "alignment_kind",
    "mineru_used_as",
    "authoritative_source",
}

CLAIM_REQUIRED_FIELDS = {
    "claim_id",
    "origin",
    "claim_text_zh",
    "claim_type",
    "section_target",
    "importance",
    "epistemic_status",
    "evidence_ids",
    "page_refs",
    "numeric_items",
    "conditions_zh",
    "validation",
}

DEPTH_MINIMUMS = {
    "summary": {"claims": 1, "characters": 40},
    "supporting": {"claims": 1, "characters": 70},
    "deep": {"claims": 2, "characters": 120},
}


def _normalized_clause(text: str) -> str:
    return re.sub(r"[\s。；！？!?]+$", "", re.sub(r"\s+", "", text)).strip()


def _paragraph_clauses(paragraphs: list[Any]) -> list[str]:
    clauses: list[str] = []
    for paragraph in paragraphs:
        clauses.extend(
            clause.strip()
            for clause in re.findall(r"[^。；！？!?]+[。；！？!?]?", str(paragraph))
            if _normalized_clause(clause)
        )
    return clauses


def _write_json(path: Path, payload: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def initialize_semantic_contracts(
    run_dir: Path,
    paper_profile: dict[str, Any],
) -> dict[str, str]:
    """Create empty, provenance-explicit semantic work packets for one blind run."""
    artifacts = {
        "section_synthesis": "section-synthesis.json",
        "missing_information_check": "missing-information-check.json",
        "visual_analysis": "visual-analysis.json",
        "semantic_generation": "semantic-generation.json",
    }
    _write_json(
        run_dir / artifacts["section_synthesis"],
        {
            "schema_version": "0.1",
            "paper_type": paper_profile["paper_type"],
            "origin": "auto_synthesized",
            "sections": [],
        },
    )
    _write_json(
        run_dir / artifacts["missing_information_check"],
        {"schema_version": "0.1", "checks": []},
    )
    _write_json(
        run_dir / artifacts["visual_analysis"],
        {"schema_version": "0.1", "inventory_complete": False, "analyses": []},
    )
    _write_json(
        run_dir / artifacts["semantic_generation"],
        {
            "schema_version": "0.1",
            "producer": "codex_agent",
            "status": "awaiting_agent_generation",
            "human_prefill_count": 0,
            "human_edit_count": 0,
            "reference_notes_used": False,
        },
    )
    return artifacts


def _raise_if(issues: list[str], label: str) -> None:
    if issues:
        raise SemanticContractError(f"{label}: " + "; ".join(issues))


def validate_authoritative_evidence(
    evidence: list[dict[str, Any]],
    pages: list[dict[str, Any]],
) -> None:
    """Require every final EvidenceUnit to resolve to one original PyMuPDF page."""
    if not evidence:
        raise SemanticContractError("Evidence Ledger is empty.")
    pages_by_index = {
        int(page["page_index"]): page
        for page in pages
        if isinstance(page, dict) and isinstance(page.get("page_index"), int)
    }
    issues: list[str] = []
    seen_ids: set[str] = set()
    for item in evidence:
        evidence_id = str(item.get("evidence_id") or "<unknown>")
        missing = sorted(EVIDENCE_REQUIRED_FIELDS - set(item))
        if missing:
            issues.append(f"{evidence_id} missing {', '.join(missing)}")
            continue
        if evidence_id in seen_ids:
            issues.append(f"duplicate {evidence_id}")
        seen_ids.add(evidence_id)
        if item.get("origin") != "auto_extracted":
            issues.append(f"{evidence_id} is not auto_extracted")
        if item.get("authoritative_source") != "pymupdf_page":
            issues.append(f"{evidence_id} is not authoritative PyMuPDF evidence")
        if item.get("mineru_used_as") not in {"structure_hint", "not_used"}:
            issues.append(f"{evidence_id} gives MinerU an evidentiary role")
        if item.get("alignment_kind") not in {"exact", "normalized"}:
            issues.append(f"{evidence_id} has non-authoritative alignment")
        if item.get("page_verified") is not True:
            issues.append(f"{evidence_id} page is not verified")
        if item.get("source_match_kind") not in {"exact", "normalized"}:
            issues.append(f"{evidence_id} quote is not traceable")
        if item.get("needs_review") is not False:
            issues.append(f"{evidence_id} still needs review")
        page_index = item.get("page_index")
        page = pages_by_index.get(page_index)
        if page is None:
            issues.append(f"{evidence_id} references missing page {page_index!r}")
            continue
        quote = str(item.get("quote_original") or "")
        actual_match = page_quote_match_kind(quote, page)
        if actual_match not in {"exact", "normalized"}:
            issues.append(f"{evidence_id} quote is absent from page {page_index}")
        elif item.get("source_match_kind") != actual_match:
            issues.append(
                f"{evidence_id} declares {item.get('source_match_kind')} "
                f"but page match is {actual_match}"
            )
        complete, reason = evidence_quote_completeness(
            str(item.get("evidence_type") or ""),
            quote,
        )
        if not complete:
            issues.append(f"{evidence_id} quote is incomplete ({reason})")
        for field in ("context_before", "context_after"):
            if not isinstance(item.get(field), str):
                issues.append(f"{evidence_id} {field} is not a string")
        bbox = item.get("bounding_box")
        if bbox is not None and (
            not isinstance(bbox, list)
            or len(bbox) != 4
            or not all(isinstance(value, (int, float)) for value in bbox)
        ):
            issues.append(f"{evidence_id} has an invalid bounding_box")
        confidence = item.get("extraction_confidence")
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            issues.append(f"{evidence_id} has invalid extraction_confidence")
    _raise_if(issues, "Authoritative Evidence validation failed")


def validate_claim_ledger(
    claims: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
) -> None:
    """Require synthesized claims to retain section, evidence, scope, and modality."""
    if not claims:
        raise SemanticContractError("Claim Ledger is empty.")
    evidence_by_id = {
        str(item.get("evidence_id")): item
        for item in evidence
        if isinstance(item, dict) and item.get("evidence_id")
    }
    issues: list[str] = []
    seen_ids: set[str] = set()
    for claim in claims:
        claim_id = str(claim.get("claim_id") or "<unknown>")
        missing = sorted(CLAIM_REQUIRED_FIELDS - set(claim))
        if missing:
            issues.append(f"{claim_id} missing {', '.join(missing)}")
            continue
        if claim_id in seen_ids:
            issues.append(f"duplicate {claim_id}")
        seen_ids.add(claim_id)
        if claim.get("origin") != "auto_synthesized":
            issues.append(f"{claim_id} is not auto_synthesized")
        evidence_ids = claim.get("evidence_ids")
        if not isinstance(evidence_ids, list) or not evidence_ids:
            issues.append(f"{claim_id} has no evidence")
            continue
        unknown = [item for item in evidence_ids if item not in evidence_by_id]
        if unknown:
            issues.append(f"{claim_id} references unknown evidence {unknown}")
            continue
        expected_pages = sorted(
            {int(evidence_by_id[item]["page_index"]) for item in evidence_ids}
        )
        if sorted(claim.get("page_refs") or []) != expected_pages:
            issues.append(f"{claim_id} page_refs do not match evidence")
        if not str(claim.get("section_target") or "").strip():
            issues.append(f"{claim_id} has no section_target")
        if claim.get("importance") not in {"core", "supporting", "context"}:
            issues.append(f"{claim_id} has invalid importance")
        if not re.search(r"[\u4e00-\u9fff]", str(claim.get("claim_text_zh") or "")):
            issues.append(f"{claim_id} has no Chinese synthesis")
    _raise_if(issues, "Claim Ledger validation failed")


def validate_section_synthesis(
    synthesis: dict[str, Any],
    claims: list[dict[str, Any]],
    missing_information_checks: list[dict[str, Any]],
) -> None:
    """Block one-line pseudo-deep output and unsupported absence declarations."""
    if synthesis.get("origin") != "auto_synthesized":
        raise SemanticContractError("SectionSynthesis origin must be auto_synthesized.")
    sections = synthesis.get("sections")
    if not isinstance(sections, list) or not sections:
        raise SemanticContractError("SectionSynthesis has no sections.")
    claim_by_id = {
        str(claim.get("claim_id")): claim
        for claim in claims
        if isinstance(claim, dict) and claim.get("claim_id")
    }
    missing_by_section = {
        str(item.get("section_target")): item
        for item in missing_information_checks
        if isinstance(item, dict) and item.get("section_target")
    }
    issues: list[str] = []
    for section in sections:
        target = str(section.get("section_target") or "<unknown>")
        status = section.get("status")
        if status in {"source_silent", "not_applicable"}:
            check = missing_by_section.get(target)
            if (
                not isinstance(check, dict)
                or check.get("status") not in {"confirmed_absent", "confirmed_not_applicable"}
                or not check.get("searched_pages")
                or not check.get("search_terms")
            ):
                issues.append(f"{target} declares absence without a search record")
            continue
        if status != "present":
            issues.append(f"{target} has invalid status {status!r}")
            continue
        depth = str(section.get("depth_requirement") or "")
        minimum = DEPTH_MINIMUMS.get(depth)
        if minimum is None:
            issues.append(f"{target} has invalid depth requirement")
            continue
        claim_ids = section.get("claim_ids")
        paragraphs = section.get("paragraphs_zh")
        if not isinstance(claim_ids, list) or len(set(claim_ids)) < minimum["claims"]:
            issues.append(
                f"{target} has fewer than {minimum['claims']} distinct claims"
            )
            continue
        unknown = [claim_id for claim_id in claim_ids if claim_id not in claim_by_id]
        if unknown:
            issues.append(f"{target} references unknown claims {unknown}")
        if not isinstance(paragraphs, list) or not paragraphs:
            issues.append(f"{target} has no synthesized prose")
            continue
        character_count = len(re.sub(r"\s+", "", "".join(map(str, paragraphs))))
        if character_count < minimum["characters"]:
            issues.append(
                f"{target} synthesis is too shallow "
                f"({character_count} < {minimum['characters']} characters)"
            )
        reachable_evidence = {
            str(evidence_id)
            for claim_id in claim_ids
            for evidence_id in claim_by_id.get(claim_id, {}).get("evidence_ids", [])
        }
        declared_evidence = {
            str(evidence_id) for evidence_id in section.get("evidence_ids", [])
        }
        if declared_evidence != reachable_evidence:
            issues.append(
                f"{target} evidence_ids do not equal the EvidenceUnits reachable "
                "from its declared claims"
            )
        clause_support = section.get("clause_support")
        if not isinstance(clause_support, list) or not clause_support:
            issues.append(f"{target} has no clause-level evidence coverage")
            continue
        support_by_clause: dict[str, list[dict[str, Any]]] = {}
        for support in clause_support:
            if not isinstance(support, dict):
                issues.append(f"{target} has an invalid clause-support record")
                continue
            clause_text = str(support.get("clause_text_zh") or "")
            evidence_ids = support.get("evidence_ids")
            if (
                not _normalized_clause(clause_text)
                or not isinstance(evidence_ids, list)
                or not evidence_ids
            ):
                issues.append(f"{target} has an empty clause-support record")
                continue
            unknown_evidence = [
                evidence_id
                for evidence_id in evidence_ids
                if evidence_id not in declared_evidence
            ]
            if unknown_evidence:
                issues.append(
                    f"{target} clause support references undeclared evidence "
                    f"{unknown_evidence}"
                )
            support_by_clause.setdefault(_normalized_clause(clause_text), []).append(
                support
            )
        uncovered = [
            clause
            for clause in _paragraph_clauses(paragraphs)
            if _normalized_clause(clause) not in support_by_clause
        ]
        if uncovered:
            issues.append(
                f"{target} has factual clauses without declared Evidence support: "
                + " | ".join(uncovered)
            )
    _raise_if(issues, "SectionSynthesis validation failed")


def validate_visual_analysis(
    visual_analysis: dict[str, Any],
    figures: dict[str, Any],
    claims: list[dict[str, Any]],
) -> None:
    """Require every selected visual to have a checked, claim-linked analysis."""
    if visual_analysis.get("inventory_complete") is not True:
        raise SemanticContractError("Visual inventory is not complete.")
    selected = figures.get("selected", [])
    analyses = visual_analysis.get("analyses")
    if not isinstance(selected, list) or not isinstance(analyses, list):
        raise SemanticContractError("Visual artifacts must contain arrays.")
    selected_labels = {
        str(item.get("figure_label"))
        for item in selected
        if isinstance(item, dict) and item.get("figure_label")
    }
    analysis_by_label = {
        str(item.get("figure_label")): item
        for item in analyses
        if isinstance(item, dict) and item.get("figure_label")
    }
    claim_ids = {
        str(item.get("claim_id"))
        for item in claims
        if isinstance(item, dict) and item.get("claim_id")
    }
    issues: list[str] = []
    if set(analysis_by_label) != selected_labels:
        issues.append("selected figures and visual analyses do not match")
    for label in selected_labels:
        item = analysis_by_label.get(label, {})
        if item.get("crop_validation_status") != "pass":
            issues.append(f"{label} crop did not pass")
        if item.get("origin") != "auto_synthesized":
            issues.append(f"{label} analysis has invalid origin")
        if not str(item.get("caption_original") or "").strip():
            issues.append(f"{label} has no caption")
        if len(str(item.get("interpretation_zh") or "").strip()) < 60:
            issues.append(f"{label} interpretation is too shallow")
        if len(str(item.get("reading_cautions") or "").strip()) < 20:
            issues.append(f"{label} has no substantive reading caution")
        supported_claims = item.get("supported_claim_ids")
        if not isinstance(supported_claims, list) or not supported_claims:
            issues.append(f"{label} has no supported claims")
        elif unknown := [
            claim_id for claim_id in supported_claims if claim_id not in claim_ids
        ]:
            issues.append(f"{label} references unknown claims {unknown}")
    _raise_if(issues, "VisualAnalysis validation failed")


def _clean_source_text(text: str) -> str:
    text = re.sub(r"(?<=[A-Za-z])-\s*\n\s*(?=[a-z])", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _source_context(
    page: dict[str, Any],
    block_id: str | None,
) -> tuple[str, str, list[float] | None]:
    blocks = [
        block
        for block in page.get("text_blocks", [])
        if isinstance(block, dict) and block.get("block_type") == "text"
    ]
    index = next(
        (
            position
            for position, block in enumerate(blocks)
            if block.get("block_id") == block_id
        ),
        None,
    )
    if index is None:
        return "", "", None
    before = _clean_source_text(str(blocks[index - 1].get("text", ""))) if index else ""
    after = (
        _clean_source_text(str(blocks[index + 1].get("text", "")))
        if index + 1 < len(blocks)
        else ""
    )
    bbox = blocks[index].get("bbox")
    return before, after, list(bbox) if isinstance(bbox, list) else None


def materialize_semantic_ledgers(
    run_dir: Path,
    draft_path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Resolve an agent semantic draft against original PyMuPDF pages."""
    run_dir = run_dir.resolve()
    draft = json.loads(draft_path.resolve().read_text(encoding="utf-8"))
    pages = json.loads((run_dir / "pymupdf-pages.json").read_text(encoding="utf-8"))
    pages_by_index = {
        int(page["page_index"]): page
        for page in pages
        if isinstance(page, dict) and isinstance(page.get("page_index"), int)
    }
    evidence: list[dict[str, Any]] = []
    for seed in draft.get("evidence", []):
        page_index = int(seed["page_index"])
        page = pages_by_index.get(page_index)
        if page is None:
            raise SemanticContractError(
                f"{seed.get('evidence_id')} references absent page {page_index}."
            )
        quote = _clean_source_text(str(seed["quote_original"]))
        source_match = page_quote_match_kind(quote, page)
        matching_block = next(
            (
                block
                for block in page.get("text_blocks", [])
                if isinstance(block, dict)
                and block.get("block_type") == "text"
                and quote_match_kind(quote, str(block.get("text") or ""))
                in {"exact", "normalized"}
            ),
            None,
        )
        if source_match not in {"exact", "normalized"} or matching_block is None:
            raise SemanticContractError(
                f"{seed.get('evidence_id')} quote is not traceable on page {page_index}."
            )
        block_id = str(matching_block["block_id"])
        context_before, context_after, bbox = _source_context(page, block_id)
        markers = [
            marker
            for marker in (
                "may",
                "might",
                "could",
                "suggest",
                "likely",
                "potentially",
                "hypothesize",
                "hope",
                "expect",
            )
            if re.search(rf"\b{marker}\w*\b", quote, flags=re.IGNORECASE)
        ]
        evidence_item = {
                "evidence_id": seed["evidence_id"],
                "origin": "auto_extracted",
                "evidence_type": seed["evidence_type"],
                "page_index": page_index,
                "printed_page": page.get("printed_page"),
                "section": seed["section"],
                "block_id": block_id,
                "bounding_box": bbox,
                "quote_original": quote,
                "context_before": context_before,
                "context_after": context_after,
                "epistemic_status": seed["epistemic_status"],
                "epistemic_markers": markers,
                "contains_number": bool(re.search(r"\d", quote)),
                "contains_unit": bool(
                    re.search(
                        r"(?:%|epochs?|hours?|points?|patches?|pixels?|blocks?)\b",
                        quote,
                        flags=re.IGNORECASE,
                    )
                ),
                "contains_variable": bool(seed.get("contains_variable", False)),
                "confidence": 1.0 if source_match == "exact" else 0.98,
                "extraction_confidence": 1.0 if source_match == "exact" else 0.98,
                "needs_review": False,
                "page_verified": True,
                "source_match_kind": source_match,
                "alignment_kind": source_match,
                "mineru_used_as": "structure_hint",
                "authoritative_source": "pymupdf_page",
                "issues": [],
            }
        symbol_verification = seed.get("symbol_verification")
        if isinstance(symbol_verification, dict):
            evidence_item["symbol_verification"] = symbol_verification
        evidence.append(evidence_item)
    validate_authoritative_evidence(evidence, pages)
    evidence_by_id = {item["evidence_id"]: item for item in evidence}
    claims: list[dict[str, Any]] = []
    for seed in draft.get("claims", []):
        evidence_ids = list(seed["evidence_ids"])
        pages_for_claim = sorted(
            {int(evidence_by_id[item]["page_index"]) for item in evidence_ids}
        )
        claims.append(
            {
                **seed,
                "origin": "auto_synthesized",
                "page_refs": pages_for_claim,
                "numeric_items": list(seed.get("numeric_items", [])),
                "conditions_zh": seed.get("conditions_zh"),
                "validation": {
                    "traceable": True,
                    "semantic_support": "warning",
                    "numeric_fidelity": "pass",
                    "modality_fidelity": "warning",
                    "final_status": "warning",
                },
            }
        )
    validate_claim_ledger(claims, evidence)
    _write_json(run_dir / "evidence.json", evidence)
    _write_json(run_dir / "claims.json", claims)
    generation_path = run_dir / "semantic-generation.json"
    generation = json.loads(generation_path.read_text(encoding="utf-8"))
    generation.update(
        {
            "status": "ledgers_materialized",
            "draft_file": draft_path.resolve().name,
            "evidence_count": len(evidence),
            "claim_count": len(claims),
            "completed": utc_now(),
        }
    )
    _write_json(generation_path, generation)
    return evidence, claims


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Resolve and validate autonomous semantic artifacts"
    )
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--draft", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        evidence, claims = materialize_semantic_ledgers(args.run_dir, args.draft)
        print(
            json.dumps(
                {
                    "status": "completed",
                    "evidence_count": len(evidence),
                    "claim_count": len(claims),
                },
                ensure_ascii=False,
            )
        )
        return 0
    except (OSError, KeyError, ValueError, SemanticContractError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
