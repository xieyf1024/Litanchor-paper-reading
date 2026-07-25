# v0.5 anti-leak and privacy audit

Date: 2026-07-25
Branch: `codex/v0.5-autonomous-deep-reading`

## Scope

The audit searched the distributable Skill instructions, references, scripts,
schemas and templates for the nine evaluation-paper titles, known DOI strings
and paper-specific answer content.

## Result

- No evaluation-paper title or known DOI occurs in the distributable Skill.
- No paper-specific Evidence ID, conclusion, page number, figure choice or
  expected numerical answer occurs in `SKILL.md`, `references/`, `scripts/`,
  `schemas/` or `assets/`.
- Paper-specific content is confined to ignored runtime artifacts, evaluation
  reports, failed cases and public examples that are explicitly labeled as
  examples.
- All six autonomous semantic drafts record
  `reference_notes_used=false`, `human_prefill_count=0` and
  `human_edit_count=0`.
- Calibration reference notes were not used as semantic inputs; they remain
  silver references rather than machine-scored gold.
- MinerU produced zero authoritative EvidenceUnits. Aligned blocks were used
  only as section, ordering and figure hints.

## Repository privacy checks

- `runtime/`, `Test-PDF/`, `*.pdf`, `.env*` and private evolution data are
  ignored.
- `git ls-files` reports no tracked PDF, runtime artifact or real environment
  file.
- The repository secret-pattern scan found no committed API key, token or
  secret-shaped assignment.
- Zotero is accessed through the loopback Local API in read-only mode.
- No new MinerU upload was made during calibration regression; cached results
  were reused only for identical PDF hashes with prior consent receipts.

## Decision

**PASS.** No test-answer leakage or private-paper artifact blocks a development
branch push. Any future example promoted from runtime must be sanitized and
explicitly reviewed before tracking.
