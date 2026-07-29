---
name: litanchor-paper-reading
description: Installs, configures, diagnoses, upgrades, or runs LitAnchor and creates evidence-grounded Chinese close-reading notes from one academic paper with safe Zotero-to-Obsidian export. Use when the user's intent is to set up LitAnchor or to skim, close-read, internalize, explain, validate, or export a paper from Zotero, a PDF, or an existing LitAnchor run, regardless of exact wording.
---

# LitAnchor Paper Reading

## Enforce the permanent contract

- Treat the supplied paper as the only factual source for the formal note.
- Bind every factual claim to verified original-language evidence and a one-based physical PDF page.
- Preserve numbers, units, variables, ranges, subjects, conditions, causality, scope, attribution, and author modality.
- Keep observations, author interpretations, hypotheses, speculation, limitations, and external learning separate.
- Distinguish `原文未说明`, `不适用`, `本模式未生成`, `待用户补充`, and `解析失败`.
- Block formal export on extraction, evidence, content, format, permission, or collision errors.
- Keep Zotero read-only and never overwrite an existing Obsidian note.
- Use evaluation papers only to discover general failure classes; never encode their answers or paper-specific corrections in the Skill.

Read `references/reliability-rules.md` and `references/workflow.md` completely for every paper.

## Load only the resources needed

- Zotero acquisition, Obsidian export, or visual assets: read `references/integrations.md`.
- `internalize` mode or adaptation to the user's study method: read `references/reading-method.md`.
- Autonomous full-paper execution: read `references/autonomous-deep-reading.md`.
- Feedback-driven Skill changes: read `references/controlled-evolution.md`.
- Installation, setup, doctor, Vault-name resolution, or the two-intent public flow: read `references/zero-config.md`.

Keep detailed rules in `references/`, deterministic behavior in `scripts/`, output templates and reusable material in `assets/`, and machine contracts in `schemas/`.

## Execute the evidence-first workflow

1. Resolve one mode (`skim`, `deep`, or `internalize`) and exactly one paper.
2. Record source identity, metadata, file hash, physical page count, write intent, and `external_knowledge_allowed=false`.
3. Preflight and extract the complete PDF by physical page. Stop on unreadable required pages.
4. Map paper type and structure, then read all relevant pages in separate structure, method, result/visual, discussion/limit, and omission-review passes.
5. Build EvidenceUnits before ClaimRecords. Never use retrieval snippets or one short claim as a substitute for reading a required section.
6. For `deep` and `internalize`, evaluate the complete visual inventory and select zero to three indispensable method or result visuals. Record a reason when none qualifies.
7. Compose from `assets/Paper Template - Final.md`; use a separate compact structure for `skim`.
8. Run deterministic schema, page, quotation, numeric, symbol, content-recall, visual, Markdown, filename, and collision checks, followed by independent fidelity and recall review where required.
9. Show the preview, warnings, failed pages, and intended paths. Write only after explicit authorization.

Use the bundled scripts rather than reimplementing their behavior:

- `scripts/zotero_local.py`: exact, loopback-only Zotero acquisition.
- `scripts/litanchor_local.py`: manual PDF preparation, validation, and rendering.
- `scripts/autonomous_deep_reading.py` and `scripts/autonomous_semantic.py`: autonomous full-paper work packets, ledger materialization, independent review, and finalization.
- `scripts/mineru_adapter.py`: policy-gated, non-authoritative MinerU structure enhancement.
- `scripts/pdf_figures.py`: original-PDF figure rendering and crop provenance.
- `scripts/export_obsidian.py`: contained, hash-checked, no-overwrite export.
- `scripts/paper_quality_gate.py`: deterministic publication blockers.
- `scripts/litanchor_setup.py`: local Vault discovery, first-run configuration, doctor checks, and run-plan resolution.

Use the JSON Schemas under `schemas/` as the machine contracts. Do not loosen contracts to make invalid output pass.

## Return a complete handoff

Report:

- processing, coverage, review, and validation status;
- the note path or the exact blocking reason;
- evidence, claim, visual, validation, and run artifact paths;
- warnings and physical pages needing human review;
- every write target and confirmation that no existing file was replaced.

Use `assets/validation-report.md` for successful or warning outcomes and `assets/failure-report.md` for blocked runs.
