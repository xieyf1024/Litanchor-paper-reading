# Local pipeline smoke test

- Date: 2026-07-22
- Skill/runtime version: 0.2.0
- Input: local `Attention Is All You Need` PDF identified by the SHA-256 in `evals/PDF_CORPUS.md`
- Mode: `skim`
- Scope: pipeline mechanics only, using three claims grounded in the abstract
- PDF physical pages extracted: 15
- Preflight: passed with a page-1 rotated-text warning preserved for review
- EvidenceUnits validated: 3
- ClaimRecords validated: 3
- Quote/page traceability: 3/3
- Numeric items checked: 6/6
- Markdown preview: generated in the private, Git-ignored runtime directory
- Obsidian writes: 0

This run does not measure full-paper recall, figure/equation understanding, or the published MVP quality gates. Those require gold annotations and complete-paper evaluation.
