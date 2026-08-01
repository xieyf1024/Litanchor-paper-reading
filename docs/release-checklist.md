# Release checklist

This file records completed public release gates. Current next-version gates
are maintained in `ROADMAP.md`.

## v0.5.0

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
- [x] Push `codex/v0.5-stable-release`, create PR #3 and merge it into `main`.
- [x] Tag merge commit `94d7974` as `v0.5.0` and publish the normal GitHub
      Release.

## GitHub decision

- `v0.5.0-rc1` Pre-release: **completed**.
- Stable branch push and PR #3: **completed**.
- Stable `v0.5.0`: **published**.
- GitHub Actions: **added on the v0.6 development line**.

## v0.6.0-beta.1

Date: 2026-07-29

## Passed

- [x] Natural-language routing is intent-based; examples are not literal
      trigger strings.
- [x] Python `>=3.10` and Zotero `>=7` are minimum-version contracts with no
      arbitrary maximum; newer versions use capability probes and warnings.
- [x] Installer lifecycle, setup, doctor, run-plan and release artifact tests
      pass.
- [x] GitHub-hosted Windows CI passes on Python 3.10 through 3.14.
- [x] Three release-eligible frozen holdouts pass the published rubric.
- [x] Holdout cases that changed general rules were moved to development, and
      a previously exposed replacement was disqualified before evaluation.
- [x] Whole-document and selected-complex-page MinerU routes completed with
      original-page alignment and zero MinerU-authoritative EvidenceUnits.
- [x] Six pathological PDF/failure fixtures pass in the project environment.
- [x] MinerU timeout preserves the PyMuPDF baseline.
- [x] Final-template completeness, evidence coverage, page accuracy and
      numeric fidelity are 100% across the release-eligible holdouts.
- [x] Existing notes remain protected by contained no-overwrite export.

## Final branch actions

- [x] Run the 150-test local suite, Skill validation, compilation, Markdown
      links, anti-leak/privacy audit and release build on the exact candidate.
- [x] Push the candidate and update Draft PR #4.
- [x] Confirm GitHub Actions on the pushed candidate for Python 3.10 through
      3.14.
- [x] User approved the Draft PR result and authorized publication of
      `v0.6.0-beta.1`.
- [x] Merge PR #4, tag the merge commit and publish the verified ZIP, checksum
      and package manifest as a GitHub Pre-release.
