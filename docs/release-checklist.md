# v0.5 release checklist

Date: 2026-07-25
Candidate: `0.5.0-rc1`

## Passed

- [x] Six official autonomous papers completed without blockers or errors.
- [x] Three calibration papers and three blind papers use the same Final-template
      and deterministic content gates.
- [x] All six have complete page coverage, passing fidelity review and passing
      paper-type recall review.
- [x] All six have a complete all-figure inventory and 1–3 selected visuals.
- [x] Three blind notes passed user visual/link review and were exported without
      overwriting existing notes.
- [x] PyMuPDF remains the physical-page authority.
- [x] MinerU is fused for structure only; unmatched/fuzzy blocks never become
      formal evidence.
- [x] ResNet, LOVECLIM and U-Net pass the current deterministic gates as extended
      non-autonomous regressions.
- [x] Anti-leak and repository privacy audit passed.
- [x] Full test suite: 100 passed, 0 failed.

## Pending before merge or release

- [ ] User visually reviews Attention Figures 1/2 and their note layout/links.
- [ ] User visually reviews Snowball Earth Figures 2/4 and their note layout/links.
- [ ] User visually reviews Holocene ENSO Figures 2/4 and their note layout/links.
- [ ] User reviews the six-paper metrics, failure taxonomy and Git diff.
- [ ] Draft PR is approved for merge.
- [ ] Version text is changed from development candidate to the chosen release
      identifier.

## GitHub decision

- Development branch push: **allowed**.
- Draft PR: **allowed**.
- Merge to `main`: **blocked on the pending user gates above**.
- Tag `v0.5.0-rc1`: **blocked until merge approval**.
- GitHub Pre-release: **blocked until tag approval**.
- Stable `v0.5.0`: **out of scope for this pass**.
