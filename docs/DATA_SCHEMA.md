# Data schema

The canonical machine-readable contracts live under `skills/litanchor-paper-reading/schemas/`. All schemas use JSON Schema Draft 2020-12.

## Objects

| Object | File | Purpose |
|---|---|---|
| SourceBundle | `source-bundle.schema.json` | One resolved paper, metadata, PDF identity, acquisition method and page records |
| EvidenceUnit | `evidence-unit.schema.json` | Traceable original-language evidence bound to one physical PDF page |
| ClaimRecord | `claim-record.schema.json` | A Chinese factual claim, epistemic status and evidence mapping |
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
  "claim_text_zh": "作者报告了该结果。",
  "claim_type": "result",
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

The schemas intentionally define contracts rather than extraction implementations in v0.1.

## Runtime file convention

The v0.2 local pipeline stores `evidence.json` as a JSON array of EvidenceUnit objects and `claims.json` as a JSON array of ClaimRecord objects. Each element is checked against the corresponding object contract and cross-checked against SourceBundle physical pages before rendering. Runtime ledgers remain private and are excluded from Git.
