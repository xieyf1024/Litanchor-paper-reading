# v1.0 RC anti-leak and privacy audit

Updated: 2026-08-11

## Scope

The release audit scans the distributable Skill instructions, references,
scripts, schemas and templates for evaluation-paper identities and answers,
private runtime paths, environment files, secrets and accidental PDF tracking.
It also checks that `SKILL.md` remains compact and references existing bundled
resources.

## Result

- No evaluation-paper title, DOI, paper-specific conclusion, page, figure
  choice or expected numerical answer occurs in the distributable Skill.
- No PDF, private note, Evidence/Claim ledger, Zotero key, runtime artifact,
  credential or real local configuration is tracked.
- Public evaluation files contain sanitized manifests, aggregate metrics,
  rubrics and reports only; the v0.6 evaluation corpus remains unchanged.
- The final source-closed paper and its generated artifacts remain in ignored
  private runtime storage.
- MinerU output remains a non-authoritative structure candidate; formal
  evidence returns to the original PDF through PyMuPDF.
- Secret-pattern, path-containment, evaluation-token and Skill-compaction
  checks pass in `tools/audit_release.py` and CI.

## Repository protections

- `runtime/`, `Test-PDF/`, `*.pdf`, `.env*`, temporary builds and private
  evolution records are ignored.
- Zotero access is loopback and read-only.
- MinerU consent is local configuration and is never committed.
- Public issue forms explicitly prohibit paper PDFs, full generated notes,
  private Zotero/Vault data, credentials and unredacted paths.

## Decision

**PASS.** No test-answer leakage, secret, private-paper artifact or unintended
upload blocks `v1.0.0-rc1`. Rerun this audit for every release candidate.
