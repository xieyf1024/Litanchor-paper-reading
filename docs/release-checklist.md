# v0.5 release checklist

Date: 2026-07-26
Release: `0.5.0`

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
- [x] The `v0.5.0-rc1` freeze commit was merged to `main`, tagged and published
      as a GitHub Pre-release.
- [x] A separate fully unseen, source-closed paper passed the frozen rubric at
      98/100 with zero severe-failure signals.
- [x] Final unseen runtime artifacts and paper-specific answers remain outside
      the distributable Skill and Git history.

## Stable release actions

- [x] Run the 116-test local suite, Skill validation, compilation and anti-leak
      checks on the exact stable commit.
- [ ] Push `codex/v0.5-stable-release`, create and merge the stable PR.
- [ ] Tag the merge commit `v0.5.0` and publish a normal GitHub Release.

## GitHub decision

- `v0.5.0-rc1` Pre-release: **completed**.
- Stable branch push and PR: **allowed by the user**.
- Stable `v0.5.0`: **release gate passed; publish after exact-commit local
  validation**.
- GitHub Actions: **no workflow is configured in this repository; the recorded
  local release suite is the executable gate**.
