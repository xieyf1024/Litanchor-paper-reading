# EvolutionCandidate: v0.4.1 reliability completion

Base version: `v0.4`  
Target version: `v0.4.1-candidate`  
Status: tested candidate; not promoted

## Problems and target layers

| Reproducible problem | Target layer | Candidate change |
|---|---|---|
| `p.1` entry/smoke links could be mistaken for evidence links | Instruction + validator | Require page-verified EvidenceUnits; remove unknown-page fallback |
| Deep extraction did not prove broad reading coverage | Validator + schema | Add `coverage_receipt.json` and deep coverage gates |
| Image handling was special-cased and crops could be clipped/contaminated | Workflow + crop script + template | Universal Visual Selection Pass and Crop Quality Gate |
| MinerU was designed but not implemented/tested | Optional adapter + evaluation | Token-free, consent-gated Flash adapter with page alignment |
| Three blind PDFs had no deep-note candidates | Evaluation | Generate three independent notes before reviewing errors |

## Acceptance evidence

- Regression tests render distinct verified links for p.2, p.5 and p.10.
- The three blind notes use multiple sections/pages and reach the papers' latter halves.
- Accepted crops match the original PDF and output image hashes and do not require human review.
- Three MinerU Flash runs completed; all blocks remain non-authoritative and unmatched blocks are excluded.
- Skill validation and the complete automated test suite pass.

## Remaining promotion gates

- User/domain review of the three blind notes.
- Human promotion of the three silver references to gold.
- Quantitative six-paper recall/fidelity scoring.
- Explicit maintainer approval after a no-regression comparison.

The private detailed candidate rationale remains under the ignored `evolution/candidates/` runtime area; this report contains only publishable, non-paper-specific conclusions.
