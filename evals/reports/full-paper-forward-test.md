# Full-paper Skill forward test

- Date: 2026-07-22
- Runtime version: 0.2.0
- Input: local five-page `Neoproterozoic 'snowball Earth' simulations with a coupled climate/ice-sheet model` PDF
- Mode: `skim`
- Physical pages rendered and visually inspected: 5/5
- EvidenceUnits validated: 12
- ClaimRecords validated: 12
- Key figures registered: 1
- Numeric items checked: 9/9
- Evidence coverage: 100%
- Physical-page reference accuracy: 100%
- Numeric fidelity: 100%
- Declared modality fidelity: 100%
- Blocking issues: 0
- Output: private Markdown preview with warnings
- Obsidian writes: 0

The test exposed and then regression-tested five failure classes:

1. layout extraction interleaving the two columns;
2. non-text control characters in diagram labels;
3. broken `fi/fl` ligature glyphs requiring visual review;
4. untrusted PDF `Author` metadata naming an uploader rather than the paper authors;
5. quotation matching across mixed semantic and line-wrap hyphens.

The final run preserved warnings for all five pages, used left-column-then-right-column extraction, left authors empty unless explicitly provided, and produced a non-overwriting preview. This is a forward test of one complete `skim` run, not an independently annotated benchmark or a claim that the published MVP quality gates have been met.
