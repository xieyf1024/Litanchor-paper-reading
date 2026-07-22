---
name: litanchor-paper-reading
description: Creates evidence-grounded Chinese close-reading notes from a single academic paper and prepares safe Zotero-to-Obsidian artifacts. Use when the user asks to skim, close-read, internalize, explain, validate, or export one paper from Zotero, a PDF, or an existing LitAnchor note, especially when page-level evidence, methods, figures, equations, limitations, or Obsidian Markdown are required.
---

# LitAnchor Paper Reading

## Enforce hard boundaries

- Treat the user-provided paper as the only factual source for the formal note.
- Write `原文未说明` for absent information, `不适用` for inapplicable fields, and `解析失败` for unreadable content. Never interchange them.
- Bind every factual claim to at least one verified Evidence ID and physical PDF page.
- Preserve numbers, units, variables, ranges, subjects, conditions, causality, scope, and author modality.
- Never upgrade discussion, interpretation, hypotheses, or speculation into observed fact.
- Block formal export when extraction or validation has a blocker/error.
- Keep Zotero read-only and never overwrite an existing Obsidian note.

Read `references/reliability-rules.md` completely before processing a paper.

## Select the path

1. Resolve one reading mode: `skim`, `deep` (default for explicit close-reading), or `internalize`.
2. Resolve exactly one source: verified Zotero item, local PDF, or an existing LitAnchor artifact set.
3. If Zotero or Obsidian is involved, read `references/integrations.md` completely.
4. If adapting the note to the user's study method or using `internalize`, read `references/reading-method.md` completely.
5. If recording feedback or improving the Skill, read `references/controlled-evolution.md` completely. Do not modify the formal Skill during a reading run.

## Execute the evidence-first workflow

Read `references/workflow.md` completely, then:

1. Register source identity, acquisition method, file hash, requested mode, and `external_knowledge_allowed=false`.
2. Preflight the PDF before analysis. Preserve physical page boundaries and report layout/OCR failures.
3. Map paper type and sections without inventing absent structure.
4. Extract original-language EvidenceUnits before writing Chinese claims.
5. Register core figures, tables, equations, and failed visual parsing explicitly.
6. Build ClaimRecords only from evidence; separate results, interpretations, hypotheses, and speculation.
7. Compose with `assets/paper-note.md`; do not freely summarize the full PDF at this stage.
8. Validate schema, traceability, pages, quotations, numbers, units, modality, Markdown, filename, and collision safety.
9. Show a preview, warnings, failed pages, and intended paths before any write.
10. Export only after explicit authorization and only to the authorized directory.

For a manual text-based PDF, use `scripts/litanchor_local.py` instead of rewriting extraction or validation code. Run `prepare` first, create `evidence.json` and `claims.json` only from the resulting `source-bundle.json`, then run `build`. Read the local-pipeline section in `references/workflow.md` before invoking it. A `FALLBACK_REQUIRED` or `BLOCKED` preflight status stops this native-text path.

Use the JSON Schemas under `schemas/` as the machine contracts. Do not loosen them to make invalid output pass.

## Keep evidence readable

- Show only Evidence ID, page, and optional verified Zotero link inline for ordinary claims.
- Add a collapsed evidence callout only for core conclusions, key numbers, definitions, limitations, or wording at risk of misinterpretation.
- Keep long or repeated evidence in the sidecar, not the main note.

## Return a complete handoff

Return:

- processing and validation status;
- the Markdown note or a clear reason it was blocked;
- evidence/claim/validation artifact paths when created;
- warnings and exact pages requiring human review;
- whether anything was written, where, and whether an existing file was preserved.

Use `assets/validation-report.md` for successful/warning reports and `assets/failure-report.md` for blocked runs.
