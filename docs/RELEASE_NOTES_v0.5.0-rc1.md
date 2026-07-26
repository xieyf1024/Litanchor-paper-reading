# LitAnchor v0.5.0-rc1 — Autonomous Deep Reading Pre-release

LitAnchor v0.5.0-rc1 is the first release candidate that runs the complete
single-paper deep-reading pipeline from a Zotero PDF to a reviewed
`Paper Template - Final` Obsidian note.

## Highlights

- PyMuPDF-authoritative physical pages, quotations, coordinates, Zotero links
  and original-PDF figure crops.
- Conditional MinerU Flash structure enhancement with three persistent local
  consent modes; MinerU output never becomes evidence without page alignment.
- Six explicit full-text reading passes followed by Evidence/Claim ledgers,
  cohesive section synthesis and independent fidelity/recall review.
- Paper-type-aware depth gates, including primary and secondary profiles.
- Complete all-figure inventory, 1–3 key visual selections, crop provenance and
  user visual/link acceptance before final promotion.
- Separate equation, metric and parameter claims; numeric, unit, modality,
  symbol and original-page verification gates.
- No-overwrite Obsidian export and local-only runtime/audit artifacts.

## Validation

- Official autonomous set: 6 papers, 81 physical pages, 182 EvidenceUnits,
  155 ClaimRecords and 15 selected visuals.
- Additional cross-domain generalization smoke test: 3 previously unseen
  papers, all regenerated from structured artifacts and accepted by the user.
- Extended renderer/quality regression: ResNet, LOVECLIM and climate U-Net.
- Automated suite: 116 passed, 0 failed.
- Skill validation, Python compilation, repository privacy and anti-leak
  audits: passed.

## Boundaries

- MinerU Flash is optional, token-free and subject to service limits. PyMuPDF
  remains authoritative.
- No Zotero MCP, Zotero write-back, bidirectional sync, paid MinerU API,
  multi-paper review or unattended release.
- Stable `v0.5.0` is intentionally withheld until a separate final unseen-paper
  smoke test passes without a blocker or severe fidelity error.
