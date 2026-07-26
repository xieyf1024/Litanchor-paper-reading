# v0.5 failure taxonomy

Date: 2026-07-25
Candidate: `0.5.0-rc1`

| Failure class | How it was detected | Severity | Resolution in this candidate |
|---|---|---:|---|
| Sparse pseudo-deep output | ResNet, LOVECLIM and U-Net used the wrong template and sentence-level sections | Blocker | Final-template, paper-type, recall and section-depth gates remain mandatory; all three extended regressions pass |
| False `p.1` traceability | Earlier links used a default page instead of a verified physical page | Blocker | Links require `page_verified=true`; official six-paper page accuracy is 1.0 |
| Accepted-note export stayed a candidate | Accepted autonomous reviews were promoted in metadata but the exported filename/status remained candidate-like | Error | Export promotion now rebuilds and validates the final note without overwriting audit artifacts |
| Post-fusion page audit loss | A late MinerU fusion rebuilt page classification and cleared completed semantic-review flags | Blocker | Fusion now preserves an existing reviewed receipt only when the physical-page classification is unchanged; changed pages return to pending |
| References followed by resumed Methods | Nature-style papers place Methods after the reference list | Blocker | Classifier now resumes main content when an explicit Methods section follows References |
| Visual appendix after References | Attention appendices with figures were misclassified as references | Error | Visual appendices are recovered and remain part of semantic/visual review |
| Nature caption syntax | `Fig. 2 | ...` was missed by the figure inventory | Error | Figure discovery accepts the vertical-bar caption convention |
| Legitimate `mm` unit flagged as duplication | Duplicate-suffix logic treated the real millimetre unit as repeated text | Error | Numeric rendering gate distinguishes legitimate units from `%%`, `°C°C`, `yearsyears`, and similar corruption |
| Numeric trace normalization | Commas, ranges, symbols and translated variable names initially produced untraceable numeric items | Blocker | Claims were rebuilt with source-preserving values and atomic numeric items; official numeric fidelity is 1.0 |
| Summary omitted problem/method/result evidence | Holocene and LOVECLIM summaries were fluent but incomplete under the stricter contract | Blocker | Summary gate requires at least 80 substantive characters, three EvidenceUnits, and problem/method/result coverage |
| Figure-role vocabulary drift | Mechanism/uncertainty labels bypassed the canonical visual-role enum | Blocker | Roles are normalized to `method`, `result`, `both`, or `context` |
| Caption duplication in notes | The crop already contained an English caption while Markdown repeated the full caption | Presentation error | Note rendering keeps selection reason and Chinese interpretation instead of repeating the full caption |
| MinerU over-trust | Most aligned blocks are fuzzy and some calibration blocks are unmatched | Blocker if promoted | MinerU remains structure-only; authoritative evidence count is zero and every claim returns to PyMuPDF pages |
| Long or complex PDF warnings | Multi-column, rotated-text and glyph warnings remain in extended regressions | Warning | Warnings stay visible and require review; they are not converted to success or hidden |
| Incomplete method flow | A method paper described individual components but not the end-to-end generation and uncertainty pipeline | Error | Paper-type recall now requires a cohesive method workflow from inputs and representation through training, inference/decoding and output analysis |
| Method parameter mislabeled as metric | A conditional-generation trade-off parameter was rendered under evaluation metrics | Error | Claim type `parameter` is distinct from `equation` and `metric`; the Final-template section names all three explicitly |
| Damaged exponent or range typography | PDF text extraction flattened a superscript unit in a scientific range | Blocker if unverified | Corrected scientific symbols require an original-page verification receipt; normalized range spacing remains traceable to the extracted source token |
| Composite paper profile loss | A benchmark paper also behaved as method and empirical research | Error | Source/profile schemas now retain one primary paper type plus secondary benchmark/method profiles without weakening required sections |
| Combined claim under-cited | One result sentence combined two independently evidenced mechanisms | Blocker | A ClaimRecord may bind multiple EvidenceUnits; every factual clause must be covered before rendering |
| Reviewed warning-state promotion failed | A valid note with non-blocking extraction warnings could write the final note before its review status was updated | Error | Visual-review acceptance is idempotent and recovers a completed-with-warnings run without overwriting artifacts |

## Unresolved release risks

- The three v0.4.1 extended regressions are intentionally human-assisted; they are not evidence of autonomous blind performance.
- The current evaluation measures deterministic traceability and structured recall gates, not agreement with a fully human-verified gold corpus.
- Cached MinerU reuse is recorded, but automatic same-hash cache discovery remains a proposed follow-up rather than an implicit behavior.
- Stable `v0.5.0` still depends on one final completely unseen-paper smoke test
  after the release-candidate tag.
