# MinerU Flash structure-enhancement evaluation

Date: 2026-07-23  
Candidate: `v0.4.1-candidate`

## Scope

The official `mineru-open-sdk==0.2.5` was installed as an optional dependency and its token-free Flash/Quick Parse path was run sequentially after explicit consent on three public test PDFs. The adapter enforced the current 10 MiB and 20-page limits and saved request, response, privacy and alignment artifacts. MinerU blocks were never marked as authoritative evidence.

| Paper | PDF pages | Size | MinerU blocks | Exact page alignment | Fuzzy | Unmatched |
|---|---:|---:|---:|---:|---:|---:|
| Attention Is All You Need | 15 | 2.11 MiB | 130 | 70 | 54 | 6 |
| Neoproterozoic Snowball Earth | 5 | 0.19 MiB | 80 | 32 | 47 | 1 |
| Multi-year ENSO across the Holocene | 19 | 3.67 MiB | 145 | 81 | 61 | 3 |

## Findings

- Flash improved heading/paragraph order and supplied useful structure candidates.
- Most blocks could be aligned exactly or fuzzily to one PyMuPDF physical page.
- Formula and table transcription was not consistently reliable enough for direct evidence.
- Flash returned Markdown rather than publication-ready figure assets; key images still came from high-resolution PyMuPDF rendering of the original PDF.
- Every unmatched block remained excluded from `evidence.json`.

## Decision

Retain MinerU Flash as an optional, consent-gated structure-enhancement layer. PyMuPDF and the original PDF remain authoritative for page numbers, quotations, numbers and final visual evidence. Do not use the paid precision API and do not require a user Token.
