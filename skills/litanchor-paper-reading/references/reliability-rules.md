# Reliability rules

## Source closure

- Use only the supplied paper, its verified metadata, and user-provided annotations for formal claims.
- Do not browse for background, fill gaps from memory, or disguise general knowledge as paper content.
- Treat reference-list statements and cited prior work as other authors' views unless the paper explicitly adopts them.
- Keep optional learning questions separate from formal paper claims; do not answer them with external knowledge in the same note.

Use provenance classes when content is not a direct paper claim:

- `[原文]`: the paper explicitly reports or claims the content.
- `[分析]`: a source-grounded boundary or interpretation produced by the Agent.
- `[假设]`: a testable but unverified explanation or research direction.
- `[用户]`: a connection or judgment supplied by the user.

Do not label Agent analysis as `[原文]` or write it in the user's voice. Omit the
`[原文]` prefix in ordinary prose to keep the note readable; show the other
labels whenever those classes appear.

## Evidence contract

- Store the shortest sufficient verbatim excerpt in the original language.
- Bind the excerpt to a one-based physical PDF page; keep printed page numbers separate.
- Normalize only whitespace, line breaks, and line-end hyphenation for trace checks. Never present a paraphrase as a quote.
- Require every factual ClaimRecord to reference at least one existing EvidenceUnit.
- Require core conclusions, key numbers, method conditions, equations and stated limitations to carry page references.

## Epistemic fidelity

Use these ordered labels:

1. `observed`: directly reported observation or result.
2. `supported`: the authors say evidence supports a claim.
3. `interpreted`: the authors' explanation of a result.
4. `hypothesized`: an explicit hypothesis.
5. `speculative`: a possibility or conjecture.

Never strengthen certainty. Preserve markers such as `may`, `might`, `could`, `suggest`, `likely`, `potentially`, and `we hypothesize` with appropriately cautious Chinese wording. Never change correlation into causation or a local result into a universal rule.

For every core conclusion, state the strongest interpretation supported by the
design and at least one plausible stronger interpretation that the evidence does
not establish. Keep this source-grounded conclusion-boundary analysis separate
from limitations explicitly acknowledged by the authors.

## Numeric and equation fidelity

Check signs, decimals, orders of magnitude, percentages, intervals, uncertainty, sample size, units, superscripts/subscripts, time/space scales and applicable conditions. If a symbol or formula is incomplete, preserve an image/page pointer and mark parsing partial or failed; do not reconstruct it from domain convention.

## Evidence display boundary

- Reader note: show only compact linked `p.x` locators. Do not expose Evidence IDs, duplicated page text, “打开” labels, or an evidence-index section.
- Private sidecars: retain Evidence IDs, complete excerpts, Claim mappings, physical pages, coordinates, and validation state.
- Preserve the sidecars even though they are not reader-facing; they are required for validation, regeneration, and audit.

## Validation severity

- `blocker`: invalid/unreadable PDF, large-scale extraction failure, invalid page, missing evidence for a core claim, untraceable quote, core numeric mismatch, unsafe output target or overwrite risk.
- `error`: contradiction, modality strengthening, wrong figure/equation mapping or incorrect variable definition. Prevent formal export.
- `warning`: partial visual/table parse, uncertain section boundary or missing printed page. Allow export only after user review.
- `info`: absence of an optional section or numbered equation.

After at most two object-scoped retries, stop and request human review. Never use fluent prose to hide insufficient evidence.

## Locator and source-coverage modes

- `page-grounded`: verified physical PDF pages are available. Only this mode may
  produce a formal `deep` or `internalize` note for Obsidian export.
- `structure-grounded`: reliable section, figure, table or equation identifiers
  exist but physical pages cannot be verified. Return a visibly partial analysis
  report without page links; do not export it as a formal note.
- `source-limited`: only metadata, abstract or user-provided excerpts are
  reliable. Return only supported fields and mark unseen content not assessable.

Unknown locations never default to page 1. Downgrading the deliverable is safer
than downgrading the evidence contract.
