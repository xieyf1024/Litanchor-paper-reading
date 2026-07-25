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

## Invariants

1. `external_knowledge_allowed` is always `false` for formal paper notes.
2. `page_index` is one-based and refers to the physical PDF page; `printed_page` is a separate optional string.
3. `EvidenceUnit.quote_original` must be a traceable excerpt, not a translation or paraphrase.
4. Every `ClaimRecord` requires at least one `evidence_id` and one page reference.
5. `observed`, `supported`, `interpreted`, `hypothesized` and `speculative` are distinct epistemic states; validation must prevent strengthening.
6. A `completed` NotePackage may be exported only when blocker count is zero and format validation passed.
7. Runtime artifacts and user feedback are private by default and must not be committed to the public repository.
8. A `deep` ClaimRecord may include `title_zh`, `detail_points_zh`, `conditions_zh`, `section_id` and `importance`; one terse string is not sufficient for a core method/result/discussion object.
9. `deep` and `internalize` must cover the required content groups before NotePackage can be completed. Use `原文未说明` only for absent paper facts, `不适用` for inapplicable fields, `本模式未生成` for learning-layer content omitted by `deep`, `待用户补充` for personal reflection and `解析失败` for unreadable content.

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

The v0.4.1 repair stores `evidence.json` and rich `claims.json` arrays, plus `figures.json` and `coverage_receipt.json`. Each claim/evidence pair is checked against SourceBundle physical pages before rendering. Deep mode additionally requires Final-template content groups, sufficient claim/detail density and substantive analysis; page dispersion alone is no longer completion evidence. SourceBundle retains all verified authors while Markdown frontmatter renders only the first author. A completed preview records `quality.markdown_sha256`; the Obsidian exporter recomputes it to reject post-validation changes. Runtime ledgers remain private and are excluded from Git.
