# v0.5 release checklist

Date: 2026-07-26
Candidate: `0.5.0-rc1`

## Passed

- [x] Six official autonomous papers completed without blockers or errors.
- [x] Three calibration papers and three blind papers use the same Final-template
      and deterministic content gates.
- [x] All six have complete page coverage, passing fidelity review and passing
      paper-type recall review.
- [x] All six have a complete all-figure inventory and 1–3 selected visuals.
- [x] All six official notes passed user visual/link review; accepted notes were
      promoted without overwriting existing notes or audit sidecars.
- [x] PyMuPDF remains the physical-page authority.
- [x] MinerU is fused for structure only; unmatched/fuzzy blocks never become
      formal evidence.
- [x] ResNet, LOVECLIM and U-Net pass the current deterministic gates as extended
      non-autonomous regressions.
- [x] Three additional unseen generalization papers passed the same structured
      pipeline and user review without paper-specific Skill rules.
- [x] Generic fixes from the generalization run were regenerated from
      structured artifacts rather than hand-editing final Markdown.
- [x] Persistent local MinerU consent modes and automatic eligible-file routing
      are covered by regression tests; no consent value is committed.
- [x] Anti-leak and repository privacy audit passed.
- [x] Full test suite: 116 passed, 0 failed.
- [x] Skill package validation and Python compilation checks passed.
- [x] User approved the reviewed generalization notes and final release steps.

## Pending before merge or release

- [ ] Push the freeze commit and mark the Draft PR ready.
- [ ] Confirm GitHub CI passes on the exact pushed commit.
- [ ] Merge that commit to `main`, tag `v0.5.0-rc1` and publish the Pre-release.

## GitHub decision

- Development branch push: **allowed**.
- PR ready and merge after green CI: **allowed**.
- Tag `v0.5.0-rc1` and GitHub Pre-release after merge: **allowed**.
- Stable `v0.5.0`: **blocked on the final unseen-paper smoke test**.
