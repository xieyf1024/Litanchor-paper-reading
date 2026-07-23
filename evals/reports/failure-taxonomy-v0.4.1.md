# Failure taxonomy for v0.4 completion

Date: 2026-07-23

| Failure class | Observed evidence | Severity | Candidate response |
|---|---|---|---|
| False page traceability | Existing index/smoke links looked like evidence links and all pointed to `p.1`; initial ledgers were empty | Blocker | Require verified EvidenceUnits, prohibit page fallback, emit `coverage_receipt.json` |
| Incomplete deep reading | A PDF could be fully extracted while analysis used too few pages/sections | Blocker | Require complete extraction, at least three evidence pages/sections, and later-half evidence |
| Cropped visual content | Attention Figure 2 lost its top edge | Error | Dynamic margins, edge checks, expansion retries, full-page/human-review fallback |
| Contaminated crop | ResNet Figure 4 included a preceding table fragment | Error | Reject the figure instead of embedding it |
| Visual special-casing | Initial image workflow was applied only to Attention | Product error | Mandatory Visual Selection Pass for every deep/internalize note |
| MinerU over-trust | Flash blocks can be fuzzy/unmatched and formula/table text can degrade | Blocker if promoted | Keep all MinerU blocks non-authoritative and align to PyMuPDF pages |
| Multi-column extraction risk | ResNet, U-Net and LOVECLIM triggered column-order notices | Warning | Preserve per-page warnings and require explicit warning acceptance |
| Glyph/control corruption | Rotated text, control characters and ligature artifacts occurred | Warning/error by location | Normalize deterministic artifacts; require visual review for affected formula/result pages |
| Obsidian CLI discovery | `Obsidian.com` could not discover the running Obsidian process | Integration warning | Use contained filesystem export; do not claim CLI verification |

No failure is converted into a silent success. Blockers stop export; warnings remain in validation and require explicit acceptance.
