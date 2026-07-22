# LitAnchor evaluation skeleton

The public repository contains only corpus metadata, annotation instructions and future evaluation contracts. Paper PDFs remain local and are ignored by Git.

## Layout

```text
evals/
├── PDF_CORPUS.md   # local filenames, DOI, hashes and stress dimensions
├── cases/          # public, non-copyrighted test inputs or synthetic failure cases
└── gold/           # human annotations that quote only the minimum necessary evidence
```

## Case design

Each future case should declare:

- stable case ID and paper hash;
- supported reading mode;
- expected preflight state;
- gold research question, method steps, core results and limitations;
- important figure/table/equation IDs;
- one-based physical PDF pages and minimal evidence excerpts;
- expected blockers/warnings;
- evaluation split (`development`, `retained`, or `hidden`).

Do not commit a complete paper, long copyrighted excerpts, private Zotero annotations or unpublished research material.

## Current verification

The repository-level tests validate contracts only. End-to-end quality metrics remain pending until phase 1 implements the manual-PDF pipeline.

