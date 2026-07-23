# Evaluation

## Current phase

v0.4.1 candidate retains the v0.4 integration tests and adds first-author rendering, verified physical-page links without a `p.1` fallback, deep-reading coverage receipts, universal visual selection, PyMuPDF crop quality/provenance gates, an optional consent-gated MinerU Flash adapter, overwrite refusal and AGPL distribution checks.

One real-PDF smoke run verifies the vertical path on `Attention Is All You Need`: 15 physical pages were extracted, three abstract EvidenceUnits and three Chinese ClaimRecords were validated, and a private Markdown preview was generated. This is a pipeline smoke test, not a full-paper accuracy score.

All six local benchmark PDFs also complete native-text preflight with their warning pages preserved; see `evals/reports/corpus-preflight.md`.

A five-page whole-paper `skim` forward test covers research question, gap, method, core results, one key figure, limitations, speculative wording and conclusions; see `evals/reports/full-paper-forward-test.md`. The test remains distinct from an independently annotated gold evaluation.

A separate v0.3 integration smoke test resolves that same public paper from the live Zotero Local API, confirms that its attachment hash matches the corpus inventory, validates five abstract-grounded claims, generates verified Zotero page links, and writes one note plus four sidecars only under the authorized test root. A repeated export is blocked and the exported note hash matches validation; see `evals/reports/zotero-obsidian-smoke.md`.

The local PDFs are excluded from Git. Their non-redistributable inventory is documented in `evals/PDF_CORPUS.md` with titles, DOI where known, page counts, SHA-256 hashes and intended stress dimensions.

All six corpus papers were independently resolved from the live Zotero `[AI]` or `[XMU]` collections and matched to the inventory hashes; see `evals/reports/zotero-six-paper-resolution.md`. Private Item/Attachment Keys remain outside the public repository.

Three detailed notes in the authorized Obsidian test Inbox are treated as **AI-assisted references**, not gold labels. They help define coverage and annotation fields but cannot score the system that generated them. The promotion checklist is in `evals/gold/AI_ASSISTED_REFERENCE_GUIDE.md`. The Attention note was also checked against the original PDF and a user-selected Bilibili explainer; see `evals/reports/attention-reference-review.md`.

The remaining three PDFs now have blind `deep` candidates with coverage receipts and verified key visuals. See `evals/reports/v0.4.1-blind-test.md`. The current six-paper status deliberately distinguishes three silver calibration references from three blind outputs; see `evals/reports/v0.4.1-six-paper-status.md`. MinerU Flash results are reported separately in `evals/reports/mineru-flash-fusion.md`.

## Gold annotation plan

For each public benchmark paper, annotate:

- research question, background and gap;
- data, materials, models, method steps, parameters and metrics;
- core results, limitations and conclusions;
- important figures, tables and equations;
- physical PDF page, exact evidence excerpt and author modality;
- parser failures and pages requiring visual review.

At least two papers should receive independent double annotation before disagreements are reconciled.

An existing AI-assisted note may become a gold annotation only after a human independently checks each selected claim against the original PDF, verifies physical pages and quotations, labels modality and scope, records parser failures, and resolves disagreements without using the candidate output as the sole answer key.

## Metrics and MVP gates

| Metric | Definition | Gate |
|---|---|---:|
| Core claim evidence coverage | supported core factual claims / all core factual claims | 100% |
| Unsupported severe claims | count per paper | 0 |
| Page reference accuracy | correct physical-page references / all references | >=99% |
| Numeric fidelity | correct values, units, errors, ranges and conditions / checked items | >=99.5% |
| Core numeric errors | count per paper | 0 |
| Modality fidelity | claims that do not strengthen author certainty / checked claims | >=98% |
| Research-question recall | recovered gold questions / gold questions | >=95% |
| Method-step recall | recovered gold steps / gold steps | >=90% |
| Core-result recall | recovered gold results / gold results | >=95% |
| Important-visual coverage | registered key visuals / gold key visuals | >=90% |
| Blocker detection | correctly reported blocker cases / gold blockers | 100% |
| YAML/Markdown validity | valid formal exports / all formal exports | 100% |

## Integration cases

- exact title, citekey, DOI and Item Key match;
- ambiguous title candidates;
- missing/encrypted/scanned/corrupt PDF;
- Zotero unavailable or Local API disabled;
- missing Obsidian directory and filename collision;
- formula, table and multi-column extraction failure;
- regeneration after a user edits the protected note region.

## Controlled-evolution gate

A candidate patch may be promoted only when it fixes a reproducible target case, introduces a regression test, preserves every hard reliability rule, does not increase permissions, shows no retained-set regression and receives maintainer approval. A single personal preference belongs in local configuration rather than the shared Skill.

## v0.4 verification

Run:

```powershell
python -m unittest discover -s tests -v
```

Install `requirements.txt` before running the complete suite; otherwise dependency-specific PDF tests are explicitly skipped. Also run the official Skill validator against `skills/litanchor-paper-reading/`.
