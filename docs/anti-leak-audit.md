# v0.5 and v0.6 anti-leak and privacy audit

Updated: 2026-07-29
Branch: `codex/v0.6-zero-config-public-beta`

This is the release-time audit snapshot. The current branch subsequently
removed the old public v0.4.1 examples and copyrighted figure crops; the
underlying v0.6 evaluation manifests and audit rules remain unchanged.

## Scope

The audit searched the distributable Skill instructions, references, scripts,
schemas and templates for the official six papers, the three v0.4.1 extended
regressions, the three additional generalization papers, the final unseen smoke
paper, known DOI strings and paper-specific answer content.

## Result

- No evaluation-paper title or known DOI occurs in the distributable Skill.
- No paper-specific Evidence ID, conclusion, page number, figure choice or
  expected numerical answer occurs in `SKILL.md`, `references/`, `scripts/`,
  `schemas/` or `assets/`.
- Paper-specific content is confined to ignored runtime artifacts and the
  minimum tracked evaluation metadata/reports required for reproducibility.
- All six autonomous semantic drafts record
  `reference_notes_used=false`, `human_prefill_count=0` and
  `human_edit_count=0`.
- The three additional generalization notes were generated without reference
  notes or paper-specific branches. Their fixes were promoted only as generic
  schemas, workflow rules, validators and tests.
- The final unseen smoke test remained in ignored runtime storage. Its title,
  PDF, Evidence/Claim ledgers, generated note, figures and rubric report were
  not promoted into the distributable Skill.
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
- MinerU consent values are local configuration only and are excluded from the
  repository. Tests use an injected fake client rather than a live upload.

## v0.6 extension

- Evaluation tokens are now collected from every tracked JSON manifest under
  `evals/cases/`, including replacement holdouts, instead of only the original
  v0.5 corpus.
- The two holdouts that exposed generic failures were moved to development
  before fixes. Their content was not added to the distributable Skill.
- A replacement with a previously observed PDF hash was disqualified before
  semantic evaluation and replaced.
- The three release-eligible holdout notes, ledgers, figures and original PDFs
  remain in ignored runtime storage.
- The tracked v0.6 metrics contain aggregate evaluation evidence and case IDs;
  they do not contain Zotero item keys, attachment keys or local PDF paths.

## Decision

**PASS.** No test-answer leakage, secret or private-paper artifact blocks the
v0.6 candidate push. Any future example promoted from runtime must be
sanitized and explicitly reviewed before tracking.
