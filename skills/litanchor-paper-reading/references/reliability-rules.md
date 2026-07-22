# Reliability rules

## Source closure

- Use only the supplied paper, its verified metadata, and user-provided annotations for formal claims.
- Do not browse for background, fill gaps from memory, or disguise general knowledge as paper content.
- Treat reference-list statements and cited prior work as other authors' views unless the paper explicitly adopts them.
- Keep optional learning questions separate from formal paper claims; do not answer them with external knowledge in the same note.

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

## Numeric and equation fidelity

Check signs, decimals, orders of magnitude, percentages, intervals, uncertainty, sample size, units, superscripts/subscripts, time/space scales and applicable conditions. If a symbol or formula is incomplete, preserve an image/page pointer and mark parsing partial or failed; do not reconstruct it from domain convention.

## Evidence display levels

- `inline`: Evidence ID, page and optional verified Zotero link only.
- `collapsed`: inline pointer plus a collapsed callout containing at most one or two necessary sentences.
- `sidecar`: complete evidence retained outside the reading note.

Default to `inline`. Use `collapsed` for core conclusions, key numbers, definitions, limitations and wording likely to be disputed. Use `sidecar` for long, repetitive or machine-only evidence.

## Validation severity

- `blocker`: invalid/unreadable PDF, large-scale extraction failure, invalid page, missing evidence for a core claim, untraceable quote, core numeric mismatch, unsafe output target or overwrite risk.
- `error`: contradiction, modality strengthening, wrong figure/equation mapping or incorrect variable definition. Prevent formal export.
- `warning`: partial visual/table parse, uncertain section boundary or missing printed page. Allow export only after user review.
- `info`: absence of an optional section or numbered equation.

After at most two object-scoped retries, stop and request human review. Never use fluent prose to hide insufficient evidence.

