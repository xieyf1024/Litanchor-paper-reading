# Zotero-to-Obsidian integration smoke test

- Date: 2026-07-22
- Runtime version: 0.3.0
- Zotero connector: desktop Local API v3, loopback-only, `GET` only
- Input: public five-page Snowball Earth test paper already listed in `evals/PDF_CORPUS.md`
- Resolution: one exact normalized title match and one PDF child attachment
- PDF identity: attachment SHA-256 matched the corpus inventory
- Preflight: `PASS_WITH_WARNINGS`; all warning pages remained visible for review
- Scope: five abstract-grounded EvidenceUnits and ClaimRecords, not a full-paper gold evaluation
- Deterministic validation: evidence coverage 100%, physical-page accuracy 100%, numeric fidelity 100%, blockers 0
- Zotero links: verified Item/attachment keys populated; page link generated without recording private keys in this report
- Obsidian export: one Markdown note plus four sidecars under the authorized test root
- Safety checks: explicit warning acceptance, explicit confirmation, root containment, preview SHA-256 match, no overwrite
- Repeat export: blocked before writing
- Existing files replaced: 0

The running Obsidian CLI could not attach to the desktop instance, so this test verifies Obsidian-flavored Markdown syntax, frontmatter, callout/user markers, exported file identity and filesystem containment rather than claiming a screenshot-based reading-view test.
