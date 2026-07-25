# Autonomous deep-reading candidate

This path is experimental in v0.5. It converts a prepared single-paper run
into an auditable work package. It does not treat deterministic extraction as
semantic close reading.

## Blind-input boundary

Allowed inputs are Zotero metadata, the source PDF, the canonical Final
template, and fixed reliability rules. Do not load a reference note, gold
answer, prefilled Evidence/Claim Ledger, or prior paper-specific correction.

Every automatically extracted EvidenceUnit must declare:

```json
{"origin": "auto_extracted"}
```

Every ClaimRecord synthesized only from EvidenceUnits must declare:

```json
{"origin": "auto_synthesized"}
```

`curated`, `user`, or missing origins block an autonomous blind run.

## Start

```powershell
python scripts/autonomous_deep_reading.py start --run-dir "<prepared-run>"
```

Add `--allow-mineru-upload` only after explicit consent. This records a
MinerU route; it does not make MinerU authoritative.

The start command must produce:

- `pymupdf-pages.json`
- `sections.json`
- `paper-profile.json`
- `reading-passes.json`
- `figure-candidates.json`
- `mineru-plan.json`
- `fidelity-review.json`
- `recall-review.json`
- `autonomous-run.json`

The correct initial state is `awaiting_agent_analysis`.

## Semantic execution

Execute all reading passes against the full page set. Build EvidenceUnits
before ClaimRecords. Do not use top-k retrieval as a substitute for reading a
required section. A deep note must provide multiple evidence-backed details
for substantive method, experiment, result, and limitation sections when the
paper contains them.

MinerU may improve structure, reading order, captions, tables, equations, and
OCR candidates. Accept a MinerU block only after aligning it to an original
PyMuPDF physical page. Unmatched blocks are not evidence.

Materialize a semantic draft only after all reading passes:

```powershell
python scripts/autonomous_semantic.py `
  --run-dir "<prepared-run>" `
  --draft "<prepared-run>\semantic-draft.json"
```

The draft must record `reference_notes_used=false`,
`human_prefill_count=0`, and `human_edit_count=0` for a blind run. Evidence is
resolved against original PyMuPDF text blocks before any ClaimRecord can be
written.

## Independent review

The composer cannot approve its own output.

- `fidelity-review.json` checks every ClaimRecord against its EvidenceUnits,
  including page, number, unit, condition, modality, scope, causality, and
  attribution.
- `recall-review.json` checks the detected paper type and full section map for
  omitted data, methods, metrics, experiments, results, visuals, limitations,
  and conclusions.

Both reviews must be independent, have no unresolved blocker/error, and use
the paper-type content contract. A pending review blocks Final-template
composition and export.

## Page review and finalization

During the semantic passes, record one explicit review outcome for every
physical page. Pages with authoritative evidence receive
`evidence_captured`; reviewed pages without a core EvidenceUnit receive
`no_core_claims` and a rationale.
Reference-only pages retain their explicit exclusion. Extraction-failed pages
always block this step.

Run MinerU fusion before semantic review whenever possible. If a cached
same-hash result is fused later, an existing page-review record is preserved
only when the page's physical classification is unchanged; changed pages must
be reviewed again.

Then finalize:

```powershell
python scripts/autonomous_deep_reading.py finalize `
  --run-dir "<prepared-run>"
```

`finalize` validates SectionSynthesis, every selected visual, page coverage,
claim fidelity, numerical rendering, paper-type recall, Final-template
structure and Markdown integrity. A successful candidate can still remain
`completed_with_warnings` while user visual review is pending.

After the user checks the selected crops, layout and Zotero links:

```powershell
python scripts/autonomous_deep_reading.py accept-visual-review `
  --run-dir "<prepared-run>"
```

Only then may the contained, no-overwrite Obsidian exporter promote the
candidate to a final test note.
