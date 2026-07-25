# Page-link and deep-coverage diagnosis

- Date: 2026-07-23
- Candidate: `v0.4.1`
- Severity: P0
- Scope: six Zotero-resolved test PDFs and the current `LitAnchor-Test` Vault

## Finding

The six PDFs were not limited to page 1 during extraction. Their prepared
SourceBundles contain every physical page:

| Paper | PDF pages | Extracted pages | Verified evidence pages |
|---|---:|---:|---:|
| Attention Is All You Need | 15 | 15 | 0 |
| Deep Residual Learning for Image Recognition | 9 | 9 | 0 |
| LOVECLIM version 1.2 | 31 | 31 | 0 |
| Neoproterozoic Snowball Earth | 5 | 5 | 0 |
| Holocene multi-year ENSO | 19 | 19 | 0 |
| Climate U-Net | 20 | 20 | 0 |

All six `deep` runs stopped after PDF preparation. Their `evidence.json` and
`claims.json` ledgers were empty, so none was a completed deep-reading run.
The new coverage gate records `extraction_status=complete`,
`analysis_status=insufficient`, and `coverage_status=incomplete` for each run
and blocks formal export.

## Why the visible links all showed p.1

Three different artifacts had been conflated:

1. `00_六篇测试文献_Zotero链接清单.md` intentionally used p.1 as a PDF entry
   point, not as evidence.
2. The three AI-assisted reference notes also exposed one p.1 source-entry
   link while their textual page citations were not clickable.
3. The only pipeline-exported Snowball note was an earlier smoke test whose
   declared scope was five abstract-grounded claims. Those claims genuinely
   came from physical page 1; the report never claimed a completed `deep` run.

No `page_index or 1` or fixed renderer fallback was found in the runtime.
Physical pages are one-based throughout, and the renderer uses ClaimRecord
page references. The defect was missing deep ledgers and an ambiguous
source-entry UI, not a page-number arithmetic fallback.

## Candidate safeguards

- Require every EvidenceUnit to set `page_verified=true`.
- Accept formal page evidence only when deterministic matching is `exact` or
  `normalized`; fuzzy or unmatched text cannot produce a page link.
- Block `deep` runs that do not demonstrate multi-page, multi-section evidence
  extending into the later half of the paper.
- Generate `coverage_receipt.json` for successful and blocked builds.
- Export the coverage receipt with the note sidecars.
- Regression-test distinct verified links from physical pages 2, 5, and 10.
- Never replace an unknown page with p.1.

## Status

P0 diagnosis is complete. PDF extraction coverage is proven; deep semantic
coverage is not. The six runs remain blocked until evidence and claim ledgers
are populated and validated.
