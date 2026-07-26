# EvolutionCandidate: cached structure provenance and page-review receipts

Date: 2026-07-25
Base version: `0.5.0-rc1`
Status: `proposed` — not promoted automatically

## Repeated problem

The release regression exposed two related audit risks:

1. a cached MinerU result can be reused safely only when the original PDF hash,
   physical-page mapping and earlier upload consent all match;
2. if structure fusion runs after semantic analysis, rebuilding the page map can
   erase the completed page-review receipt.

The current candidate preserves reviewed page records only when a later fusion
leaves their physical-page classification unchanged. It does not infer that an
unreviewed page was reviewed, infer permission to upload, or silently reuse
arbitrary cached output.

## Proposed next patch

- Detect an identical-PDF MinerU cache by full SHA-256, service mode and physical
  page mapping.
- Record the route as `reused_identical_pdf_cache`.
- Preserve reviewed page records whose classification did not change.
- Require explicit re-review for pages whose class or page mapping changed.
- Make the page-review decisions a first-class semantic artifact instead of an
  implicit mutation.
- Add a regression in which Methods resumes after References and cached fusion
  occurs both before and after semantic analysis.

## Promotion gate

The patch may be promoted only when:

- no network upload occurs during a cache-reuse test;
- mismatched hashes or page maps are blocked;
- extraction-failed pages cannot be marked reviewed;
- the official six-paper metrics do not regress;
- all repository, privacy and deterministic tests pass;
- a maintainer explicitly approves the candidate.
