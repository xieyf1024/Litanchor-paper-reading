# Evaluation

## Current phase

v0.1 validates Skill structure, templates, schemas, repository privacy rules and test-corpus metadata. It does not report end-to-end paper-reading accuracy because the runtime pipeline is not implemented yet.

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

## v0.1 verification

Run:

```powershell
python -m unittest discover -s tests -v
```

Also run the official Skill validator against `skills/litanchor-paper-reading/`. Both checks must pass before the initial Git commit.

