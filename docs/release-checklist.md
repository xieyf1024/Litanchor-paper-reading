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
- [x] Anti-leak and repository privacy audit passed.
- [x] Full test suite: 110 passed, 0 failed.

## Pending before merge or release

- [ ] User reviews the six-paper metrics, failure taxonomy and Git diff.
- [ ] Draft PR is approved for merge.
- [ ] Version text is changed from development candidate to the chosen release
      identifier.

## GitHub decision

- Development branch push: **allowed**.
- Draft PR: **allowed**.
- Merge to `main`: **blocked on final Git diff review and PR approval**.
- Tag `v0.5.0-rc1`: **blocked until merge approval**.
- GitHub Pre-release: **blocked until tag approval**.
- Stable `v0.5.0`: **out of scope for this pass**.
