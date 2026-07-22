# Evidence-first workflow

## 1. Parse the request

Record source query, output language, reading mode, write intent and overwrite policy. Set `external_knowledge_allowed` to `false`.

## 2. Resolve one paper

Prefer Item Key, citekey, DOI, exact title, then fuzzy title. Ask the user to choose when multiple plausible candidates remain. Never accept the first fuzzy result silently.

## 3. Build SourceBundle

Keep metadata, annotations, Zotero notes, attachment key, PDF path/content, hash, page count and acquisition method. Preserve original language and avoid summarization in this stage.

## 4. Preflight

Check PDF validity, encryption, page count, extractable-text coverage, likely scanning, corruption, column order and high-risk formula/table pages. Return `PASS`, `PASS_WITH_WARNINGS`, `FALLBACK_REQUIRED`, or `BLOCKED`.

## 5. Extract by page

Save one-based physical page, printed page if known, text blocks/coordinates where available, extraction method, confidence and warnings. Never concatenate an unpaged full-text blob.

## 6. Read in three passes

- Pass 1: title, abstract, headings, conclusion and the end of the introduction; map paper type, question, method and structure.
- Pass 2: extract section-scoped evidence for background, gap, hypotheses, data, materials, method steps, parameters, metrics, results, discussion, limitations and conclusions.
- Pass 3: reconstruct the argument as question -> importance -> prior gap -> method -> criteria -> results -> interpretation -> limits.

For a review paper, replace experiment-specific fields with review scope, search/selection method, synthesis method, evidence categories, agreements, disagreements and limitations. Do not force empirical fields.

## 7. Inspect core visuals

Register figures/tables/equations repeatedly cited in the text, supporting core results, defining the method or defining a metric. Record label, page, caption, role, supported claims, parse status and review requirement. Do not analyze decorative images.

## 8. Build ledgers

Create EvidenceUnits first. Then create Chinese ClaimRecords from those units. Preserve author modality and distinguish results from interpretations, hypotheses and speculation.

## 9. Compose

Render the relevant sections of `../assets/paper-note.md` from validated ledgers. Use `原文未说明`, `不适用` and `解析失败` precisely. Keep user-edit markers unchanged.

## 10. Validate and export

Run deterministic schema/page/quote/numeric/format checks before semantic support/modality/causality/scope review. If any blocker/error remains, produce the failure report. Otherwise show a preview and write only after authorization using the safe rules in `integrations.md`.

## 11. Record feedback

Create a FeedbackEvent for user corrections. Do not mutate the formal Skill or publish a patch during the paper-reading task.

