# Evaluation

## Current phase

`v1.0.0-rc1` is the current public release candidate. It retains the v0.5.0
autonomous deep-reading baseline and adds Agent-assisted installation,
Windows Python 3.10–3.14 CI, frozen holdouts, pathological PDF/failure cases,
MinerU component comparison, lifecycle recovery, semantic intent regression,
redacted support bundles, deterministic Release packaging, mode-specific note
rendering and deterministic frontmatter/content-contract gates.

Release evidence:

- six official autonomous papers: 81 physical pages, 182 EvidenceUnits,
  155 ClaimRecords and 15 selected visuals;
- three extended non-autonomous renderer/quality regressions;
- three cross-domain generalization runs regenerated from structured artifacts
  and accepted by the user;
- one separate source-closed unseen smoke test under the frozen workflow and
  rubric;
- the complete repository suite plus Skill validation, compilation,
  Markdown-link, privacy and anti-leak checks for the RC freeze;
- the final unseen note and its split-page figure crops accepted by the user.

See `v1.0.0-rc1-frozen-validation.md`, `../evals/cross-paper-metrics.json`,
`../evals/failure-taxonomy.md`, `../evals/v0.6-public-beta-metrics.json`,
`../evals/reports/v0.6-public-beta-validation.md` and
`release-checklist.md`.

The local PDFs and private runtime artifacts are excluded from Git. Their safe
inventory is documented in `../evals/PDF_CORPUS.md`.

## Corpus roles

### Development regression

All papers already used to design, debug or inspect LitAnchor are development
material. They may be rerun after every change to catch regressions, but they
do not provide unseen generalization evidence.

### Frozen holdout

For v0.6, select at least three papers that have not contributed reference
notes, prompt changes, quality rules or paper-specific fixes. Freeze the Skill,
schemas, templates and rubric before running them.

If a holdout result causes a rule change, move that paper into the development
set and choose a replacement holdout for the next release decision.

### Pathological PDF fixtures

Use synthetic or redistributable fixtures for deterministic failure coverage:

- two-column and cross-column reading order;
- formula, range-symbol and unit corruption;
- dense tables and figure captions;
- scanned or low-text pages;
- long papers, page subsets and Methods-after-References layouts.

These fixtures test parsing, routing and failure detection. They do not count
as scientific-content accuracy scores.

## Gold annotation guidance

For a content-scored public paper, annotate:

- research question, background and gap;
- data, materials, models, method steps, parameters and metrics;
- core results, limitations and conclusions;
- important figures, tables and equations;
- physical PDF page, exact evidence excerpt and author modality;
- parser failures and pages requiring visual review.

An AI-assisted note may become a gold annotation only after a human checks the
selected claims against the original PDF, verifies physical pages and
quotations, labels modality and scope and resolves disagreements without using
the candidate output as the sole answer key.

## Quality gates

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
| Final-template completeness | required Final headings present / required headings | 100% |
| Required deep content groups | groups meeting per-paper contract / required groups | 100% |
| Core section depth | core claims with explanation/conditions/numeric context / core claims | 100% |
| Blocker detection | correctly reported blocker cases / gold blockers | 100% |
| YAML/Markdown validity | valid formal exports / all formal exports | 100% |
| Existing-note protection | blocked or candidate exports / all collisions | 100% |

## Installation and integration evaluation for v0.6

External testers and a second physical Windows machine are not mandatory for
the v0.6 release gate. Use:

1. GitHub-hosted Windows runners with Python 3.10 through 3.14;
2. fresh virtual environments, temporary Agent Skills directories, temporary
   configuration and temporary Vaults;
3. a stub loopback Zotero API plus synthetic PDFs in CI;
4. three isolated local application profiles on the maintainer’s Windows
   system, including real core dependencies, non-ASCII paths and interrupted
   activation recovery;
5. one live Zotero-to-Obsidian smoke run after synthetic tests pass.

Cover:

- first install, repeated install and interrupted install;
- repair, upgrade, rollback and uninstall;
- Chinese characters, spaces and long paths;
- Zotero unavailable, Local API disabled, ambiguous items and multiple PDFs;
- missing Vault, invalid Inbox and filename collision;
- MinerU consent, timeout, rate limit, empty result and PyMuPDF fallback;
- formula, table, multi-column and low-text extraction failure;
- regeneration after user-owned note content exists.

This proves lifecycle isolation and controlled failure behavior without
claiming that a completely new Windows user or outside beta cohort has been
tested. Public issue reports can extend the evidence after release.

## Controlled-evolution gate

A candidate patch may be promoted only when it:

- fixes a reproducible general problem;
- adds a regression case;
- preserves every hard reliability rule;
- does not increase permissions;
- shows no retained-set regression;
- contains no test-paper answer or paper-specific branch;
- receives maintainer approval.

Personal preferences stay in local configuration.

## Verification

Run:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q skills tests
```

Install `requirements.txt` before the complete suite; dependency-specific PDF
tests are otherwise skipped. Also run the official Skill validator against
`skills/litanchor-paper-reading/`, the repository anti-leak/privacy audit and
the release checklist.
