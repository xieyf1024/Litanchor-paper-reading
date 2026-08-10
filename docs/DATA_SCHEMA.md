# Data schema

The canonical machine-readable contracts live under `skills/litanchor-paper-reading/schemas/`. All schemas use JSON Schema Draft 2020-12.

## Objects

| Object | File | Purpose |
|---|---|---|
| SourceBundle | `source-bundle.schema.json` | One resolved paper, metadata, PDF identity, acquisition method and page records |
| EvidenceUnit | `evidence-unit.schema.json` | Traceable original-language evidence bound to one physical PDF page |
| ClaimRecord | `claim-record.schema.json` | An evidence-grounded intermediate knowledge object for Final-template composition |
| NotePackage | `note-package.schema.json` | Export status, artifact paths, issues and quality statistics |
| FeedbackEvent | `feedback-event.schema.json` | User correction or run failure for controlled evolution |
| PageClassification | `page-classification.schema.json` | Per-page semantic role, review status and extraction exclusions |
| CoverageReceipt | `coverage-receipt.schema.json` | Full-paper page and required-content coverage |
| MissingInformationCheck | `missing-information-check.schema.json` | Evidence that an “原文未说明” result was searched and reviewed |
| SectionSynthesis | `section-synthesis.schema.json` | Multi-claim, locally supported Final-template section composition |
| VisualSelection | `visual-selection.schema.json` | Full figure/table inventory and selected key visuals |
| VisualAnalysis | `visual-analysis.schema.json` | Caption/body/image-grounded analysis of selected visuals |
| FidelityReview | `fidelity-review.schema.json` | Independent claim-to-evidence fidelity review for an autonomous candidate |
| RecallReview | `recall-review.schema.json` | Independent paper-type content-recall review |
| NoteFrontmatter | `note-frontmatter.schema.json` | Fixed user-facing Obsidian properties, status enums, dates and mode-tag contract |

## Invariants

1. `external_knowledge_allowed` is always `false` for formal paper notes.
2. `page_index` is one-based and refers to the physical PDF page; `printed_page` is a separate optional string.
3. `EvidenceUnit.quote_original` must be a traceable excerpt, not a translation or paraphrase.
4. Every `ClaimRecord` requires at least one `evidence_id` and one page reference.
5. `observed`, `supported`, `interpreted`, `hypothesized` and `speculative` are distinct epistemic states; validation must prevent strengthening.
6. A `completed` NotePackage may be exported only when blocker count is zero and format validation passed.
7. Runtime artifacts and user feedback are private by default and must not be committed to the public repository.
8. A `deep` ClaimRecord may include `title_zh`, `detail_points_zh`, `conditions_zh`, `section_id` and `importance`; one terse string is not sufficient for a core method/result/discussion object.
9. Autonomous blind runs require `origin=auto_extracted` on EvidenceUnits and `origin=auto_synthesized` on ClaimRecords; curated/user/missing origins block completion.
10. Autonomous completion requires independent FidelityReview and RecallReview artifacts with no unresolved blocker/error.
11. `deep` and `internalize` must cover the required content groups before NotePackage can be completed. Use `原文未说明` only for absent paper facts, `不适用` for inapplicable fields, `待用户补充` for personal reflection and `解析失败` for unreadable content. Mode-excluded sections are omitted rather than rendered with placeholders.
12. A SectionSynthesis factual clause must be supported by the Evidence set declared for that section.
13. MinerU alignment is a structure hint; formal Evidence still requires `authoritative_source=pymupdf` and a verified physical page.
14. `provenance_class=paper` is the default for paper-grounded facts. `analysis`, `hypothesis`, and `user` must be visible in the human note and must not be rendered as author claims.
15. Every core `experiment` ClaimRecord requires an `evidence_chain` containing the tested claim, comparison/conditions, observed result, supported conclusion, and unsupported stronger interpretation.
16. Every `conclusion_boundary` ClaimRecord uses `provenance_class=analysis` and is kept separate from author-stated `limitation` records.
17. An `internalize` `research_idea` uses `provenance_class=hypothesis` and records the source observation, falsifiable hypothesis, delta, validation plan, at least two failure modes, and novelty-check status.
18. User-facing note frontmatter contains exactly 16 properties: `title`, `first_author`, `year`, `journal`, `doi`, `paper_type`, `keywords`, `source_coverage`, `locator_mode`, `validation_status`, `review_status`, `skill_version`, `template_version`, `created`, `updated`, and `tags`. The frozen reader contract is `Paper Template v1.0`, so generated notes use `template_version: "1.0"`.
19. `first_author` is one full-name scalar. The complete author list remains in SourceBundle. `keywords` comes only from the paper or Zotero and is rendered as one semicolon-delimited string; an absent source keyword list stays empty.
20. Reading mode is not a frontmatter property. `tags` always includes `LitAnchor` plus exactly one of `skim`, `deep`, or `internalize`; user-added tags are permitted and must never be removed by an automated update.
21. `created` and `updated` use `YYYY-MM-DD`. `review_status` is restricted to `unreviewed`, `review_pending`, or `reviewed` in the human note even when the private run record uses more detailed workflow states.

## Local configuration

The v0.6 Agent-facing setup writes a local-only configuration validated by
`schemas/local-config.schema.json`. It records:

- the selected Vault name and absolute path;
- one authorized child root and Literature Inbox;
- the read-only loopback Zotero API URL;
- the MinerU consent mode and fixed Flash eligibility limits;
- receipt-tracked installation/runtime paths when installed by the bootstrap.

The Inbox must be nested below a dedicated authorized root, which itself stays
inside the Vault. Installation state may be written before first-run setup, but
the configuration is not run-ready until the Obsidian, Zotero and MinerU
sections satisfy the schema. The file remains under
`%LOCALAPPDATA%\LitAnchor\config.json` and is never a repository artifact.

## Evidence and claim example

```json
{
  "evidence_id": "E-023",
  "evidence_type": "result",
  "page_index": 12,
  "section": "Results",
  "quote_original": "The reported sentence from the paper.",
  "epistemic_status": "observed",
  "contains_number": false,
  "contains_unit": false,
  "confidence": 0.98,
  "needs_review": false
}
```

```json
{
  "claim_id": "C-007",
  "claim_text_zh": "作者报告该方法在目标任务上优于所列基线。",
  "claim_type": "result",
  "title_zh": "核心比较结果",
  "detail_points_zh": [
    "说明比较对象、评价指标和结果方向。",
    "保留作者报告的不确定性与适用范围。"
  ],
  "section_id": "results",
  "importance": "core",
  "conditions_zh": "仅适用于论文给定的数据、模型设置和评价协议。",
  "epistemic_status": "observed",
  "evidence_ids": ["E-023"],
  "page_refs": [12],
  "numeric_items": [],
  "validation": {
    "traceable": true,
    "semantic_support": "pass",
    "numeric_fidelity": "pass",
    "modality_fidelity": "pass",
    "final_status": "pass"
  }
}
```

The schemas define contracts rather than inventing paper content. The Skill/agent is responsible for the specialised reading passes that populate the ledgers.

## Runtime file convention

The v0.5.0 autonomous run stores the page bundle, section map, reading-pass
packets, `evidence.json`, `claims.json`, `section_synthesis.json`,
`figures.json`, `visual_analysis.json`, `coverage_receipt.json`,
`fidelity_review.json`, `recall_review.json` and `run.json`. Each
claim/evidence pair is checked against SourceBundle physical pages before
rendering.

Deep mode requires Final-template content groups, sufficient claim/detail
density, substantive analysis, complete visual selection and passing
independent review; page dispersion alone is not completion evidence.
SourceBundle retains all verified authors and Zotero/source identifiers while
Markdown frontmatter renders only the fixed NoteFrontmatter contract. A completed preview records
`quality.markdown_sha256`; the Obsidian exporter recomputes it to reject
post-validation changes. Runtime ledgers remain private and are excluded from
Git.
