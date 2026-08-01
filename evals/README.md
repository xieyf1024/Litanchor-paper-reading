# LitAnchor evaluation

The public repository contains corpus metadata, frozen manifests, annotation
guidance, rubrics, aggregate metrics and sanitized reports. Paper PDFs,
generated notes and runtime ledgers remain local and are ignored by Git.

## Layout

```text
evals/
├── PDF_CORPUS.md   # local corpus identity and stress dimensions
├── cases/          # split manifests and synthetic failure definitions
├── gold/           # annotation rules; no candidate-as-answer scoring
├── reports/        # sanitized release and component reports
├── rubrics/        # pre-published evaluation gates
└── *.json          # aggregate, non-private metrics
```

## Case design

Each case should declare:

- stable case ID and paper hash;
- supported reading mode;
- expected preflight state;
- gold research question, method steps, core results and limitations;
- important figure/table/equation IDs;
- one-based physical PDF pages and minimal evidence excerpts;
- expected blockers/warnings;
- evaluation split (`development`, `frozen_holdout`, or `pathological`).

Do not commit a complete paper, long copyrighted excerpts, private Zotero annotations or unpublished research material.

## Current verification

`v0.6.0-beta.1` includes frozen holdout evaluation, pathological PDF/failure
coverage, MinerU component A/B evidence and deterministic repository tests.
Start with:

- [`v0.6-public-beta-metrics.json`](v0.6-public-beta-metrics.json);
- [`rubrics/v0.6-public-beta.md`](rubrics/v0.6-public-beta.md);
- [`reports/v0.6-public-beta-validation.md`](reports/v0.6-public-beta-validation.md);
- [`reports/v0.6-mineru-ab.md`](reports/v0.6-mineru-ab.md).

Development cases can shape general rules. Frozen holdouts cannot. If a frozen
case causes a change, reclassify it as development and replace it before making
a release claim.
