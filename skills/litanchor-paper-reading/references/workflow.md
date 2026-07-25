# Evidence-first workflow

## 1. Parse the request

Record source query, output language, reading mode, write intent and overwrite policy. Set `external_knowledge_allowed` to `false`.

## 2. Resolve one paper

Prefer Item Key, citekey, DOI, exact title, then fuzzy title. Ask the user to choose when multiple plausible candidates remain. Never accept the first fuzzy result silently.

## 3. Build SourceBundle

Keep metadata, full author list, annotations, Zotero notes, attachment key, PDF path/content, hash, page count and acquisition method. Preserve original language and avoid summarization in this stage. The human note frontmatter stores only the verified first author; never discard the complete SourceBundle author list.

## 4. Preflight

Check PDF validity, encryption, page count, extractable-text coverage, likely scanning, corruption, column order and high-risk formula/table pages. Return `PASS`, `PASS_WITH_WARNINGS`, `FALLBACK_REQUIRED`, or `BLOCKED`.

## 5. Extract by page

Save one-based physical page, printed page if known, text blocks/coordinates where available, extraction method, confidence and warnings. Never concatenate an unpaged full-text blob.

## 6. Read in specialised passes

- Pass 1 — structure: title, abstract, headings, conclusion and the end of the introduction; map paper type, question, method and argument.
- Pass 2 — background/question/contribution: extract necessary background, directly relevant prior work, research gap, question, scope and author-stated contributions.
- Pass 3 — data/method: extract data/materials, preprocessing, method steps, models, equations, metrics, experiments, baselines, ablations and reproducibility details.
- Pass 4 — results/visuals: extract independently verifiable results, numbers, conditions, figures, tables and equations that carry the core argument.
- Pass 5 — discussion/limits: separate observation from interpretation, hypotheses, limitations, conclusions and future work.
- Pass 6 — omission review: compare the ledger against the detected paper structure and `Paper Template - Final`; do not declare `deep` complete while a required content group is missing or represented by one unexplained sentence.

For a review paper, replace experiment-specific fields with review scope, search/selection method, synthesis method, evidence categories, agreements, disagreements and limitations. Do not force empirical fields.

For an autonomous candidate, `scripts/autonomous_deep_reading.py start`
materializes these passes as auditable work packets. PyMuPDF physical pages
are authoritative. The initial status is `awaiting_agent_analysis`; creating
the packets is not equivalent to completing the semantic reading.

## 7. Run the Visual Selection Pass

Every `deep` or `internalize` run must evaluate figures/tables/equations repeatedly cited in the text, supporting core results, defining the method or defining a metric. Select at most 1–3 indispensable objects; never choose by figure number or to fill a quota. Record label, page, caption, role, supported claims, parse status and review requirement. Do not analyze decorative or redundant images. If none qualifies, record the reason in `figures.json`.

For a selected figure, run `scripts/pdf_figures.py` against the original PDF. Verify the physical page and caption, inspect the PNG, retain its JSON provenance manifest, embed it with a Vault-relative wikilink, and add a verified Zotero page link. The crop must pass edge, source-hash, page, output-hash and human-review gates. A structure parser may locate a candidate, but the published image must be cropped from the original PDF. Ambiguous, clipped or contaminated geometry blocks automatic embedding.

## 8. Build ledgers

Create EvidenceUnits first. Then create Chinese ClaimRecords from those units. Preserve author modality and distinguish results from interpretations, hypotheses and speculation. For `deep`/`internalize`, use the expanded knowledge types and fill `title_zh`, `detail_points_zh`, `conditions_zh`, `section_id` and `importance` where relevant. ClaimRecords are intermediate knowledge objects, not the final note.

## 9. Compose

Render every formal `deep`/`internalize` note from `../assets/Paper Template - Final.md`. The renderer loads the asset and fills its named slots; it must not substitute a hard-coded summary outline. `skim` remains a separate compact output. Use `原文未说明` only for absent paper facts, `不适用` for inapplicable fields, `本模式未生成` for learning-layer content omitted by `deep`, `待用户补充` for personal reflection and `解析失败` for unreadable content. Keep user-edit markers unchanged.

## 10. Validate and export

Run deterministic schema/page/quote/numeric checks and the deep-reading gate before semantic support/modality/causality/scope review. The deep-reading gate checks required content groups, claim/detail density, Final-template headings and unresolved slots. It is a recall guard, not proof of scientific correctness; gold comparison remains necessary. If any blocker/error remains, produce the failure report. Otherwise show a preview and write only after authorization using the safe rules in `integrations.md`.

## 11. Record feedback

Create a FeedbackEvent for user corrections. Do not mutate the formal Skill or publish a patch during the paper-reading task.

## Local PDF pipeline

Use the bundled script for the current lightweight runtime slice:

```powershell
python scripts/litanchor_local.py prepare "paper.pdf" --output-root "runtime/runs" --mode deep
```

The command creates a private run directory containing `source-bundle.json`, empty `evidence.json`, empty `claims.json`, `figures.json`, and `run.json`. Deep/internalize runs leave visual selection `pending`; `build` blocks until it is completed. It never writes to Obsidian.

For a running Zotero desktop client with Local API enabled, use the read-only adapter instead:

```powershell
python scripts/zotero_local.py check
python scripts/zotero_local.py prepare --title "Exact paper title" --output-root "runtime/runs" --mode deep
```

Use exactly one title, DOI, citekey or Item Key selector. Zero/multiple exact items or PDF attachments block the run.

Continue only when preflight returns `PASS` or `PASS_WITH_WARNINGS`:

1. Read `source-bundle.json`, preserving physical page boundaries.
2. Complete the specialised reading passes before composing output.
3. Fill `evidence.json` with an array of objects conforming to `schemas/evidence-unit.schema.json`.
4. Fill `claims.json` with an array of rich objects conforming to `schemas/claim-record.schema.json`; do not cap each type at one item or use top-k retrieval as a substitute for section reading.
5. Complete `figures.json` under `schemas/visual-selection.schema.json`, with 0–3 selected objects and a reason when none qualifies.
6. Perform semantic support, scope, causality, numeric, modality and omission review before setting each claim validation status.
7. Build a preview:

```powershell
python scripts/litanchor_local.py build "runtime/runs/<run-id>"
```

`build` rejects missing fields, invalid IDs/pages, quotations not found on the cited physical page, missing Final-template content groups, sparse or shallow `deep` ledgers, incomplete visual selection, failed crop provenance, numeric values or units absent from the evidence, failed semantic status, unresolved template slots and an existing output path. It records the validated preview SHA-256. An unknown page is never rendered as `p.1`.

To crop an already verified key figure:

```powershell
python scripts/pdf_figures.py "paper.pdf" --page 3 --label "Figure 1" --output "runtime/figures/figure-1.png"
```

The command refuses overwrite and creates a JSON manifest beside the image.

After showing the preview and receiving write authorization, export only through:

```powershell
python scripts/export_obsidian.py "runtime/runs/<run-id>" --allowed-root "<test-root>" --inbox "<test-root>/00_Inbox" --confirm-export
```

Add `--allow-warnings` only after the warning pages have been reviewed. The exporter blocks an Inbox outside the authorized root, an altered preview, missing sidecars, a collision, or a repeated export.
