# Six-paper corpus preflight

- Date: 2026-07-22
- Runtime version: 0.2.0
- Operation: native-text preflight and physical-page extraction only
- PDFs modified: 0
- Obsidian writes: 0

| Paper | Status | Warning pages / condition |
|---|---|---|
| Attention Is All You Need | `PASS_WITH_WARNINGS` | multicolumn signal pp.1, 4, 6, 8-10; rotated text p.1 |
| Deep Residual Learning for Image Recognition | `PASS_WITH_WARNINGS` | multicolumn signal pp.1-9; rotated text pp.1, 5, 8; two control characters removed p.2 |
| LOVECLIM v1.2 | `PASS_WITH_WARNINGS` | multicolumn signal pp.1-31; suspicious ligature p.12; duplicate metadata key handled |
| Multi-year ENSO events across the Holocene | `PASS_WITH_WARNINGS` | multicolumn signal pp.1-11, 13-14, 19; rotated text pp.2-5 |
| Neoproterozoic snowball Earth simulations | `PASS_WITH_WARNINGS` | multicolumn and suspicious-ligature signals pp.1-5; rotated text pp.2-3 |
| Separation of Internal and Forced Variability Using a U-Net | `PASS_WITH_WARNINGS` | multicolumn signal pp.2-20 |

All six files produced the expected page count and SHA-256 identity listed in `evals/PDF_CORPUS.md`. A warning is preserved rather than silently upgraded to `PASS`; visual or equation analysis of the listed pages remains a later step.

ResNet PDF p.2 was additionally rendered and compared with extracted text. The native extraction preserved left-column-then-right-column reading order; two diagram control characters were removed and reported rather than retained as evidence text.
