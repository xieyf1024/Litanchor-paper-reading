# Evaluation

## Current phase

v0.2 retains the v0.1 repository/Skill contract tests and adds local pipeline tests for blank and corrupt PDFs, page-level extraction, schema invariants, quote/page traceability, numeric fidelity, preflight warning propagation and non-overwriting Markdown rendering.

One real-PDF smoke run verifies the vertical path on `Attention Is All You Need`: 15 physical pages were extracted, three abstract EvidenceUnits and three Chinese ClaimRecords were validated, and a private Markdown preview was generated. This is a pipeline smoke test, not a full-paper accuracy score.

All six local benchmark PDFs also complete native-text preflight with their warning pages preserved; see `evals/reports/corpus-preflight.md`.

A five-page whole-paper `skim` forward test covers research question, gap, method, core results, one key figure, limitations, speculative wording and conclusions; see `evals/reports/full-paper-forward-test.md`. The test remains distinct from an independently annotated gold evaluation.

The local PDFs are excluded from Git. Their non-redistributable inventory is documented in `evals/PDF_CORPUS.md` with titles, DOI where known, page counts, SHA-256 hashes and intended stress dimensions.

## Gold annotation plan

For each public benchmark paper, annotate:

- research question, background and gap;
- data, materials, models, method steps, parameters and metrics;
- core results, limitations and conclusions;
- important figures, tables and equations;
- physical PDF page, exact evidence excerpt and author modality;
- parser failures and pages requiring visual review.

At least two papers should receive independent double annotation before disagreements are reconciled.

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

## v0.2 verification

Run:

```powershell
python -m unittest discover -s tests -v
```

Install `requirements.txt` before running the complete suite; otherwise dependency-specific PDF tests are explicitly skipped. Also run the official Skill validator against `skills/litanchor-paper-reading/`.
