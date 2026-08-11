# Release checklist

Current public candidate: `v1.0.0-rc1` (published 2026-08-11).

Historical release decisions are preserved in GitHub Releases, Git Tags and
`CHANGELOG.md`. This file tracks only the active path from the public release
candidate to stable `v1.0.0`.

## RC1 completed

- [x] Freeze Paper Template v1.0 and the semantic workflow.
- [x] Complete frozen holdouts plus one separate source-closed unseen paper.
- [x] User-review the final unseen note and split-page figure crops.
- [x] Pass 180 repository tests, Skill validation, Python compilation, 51
      Markdown links, privacy, anti-leak and compaction audits.
- [x] Pass install, setup, direct-PDF run-plan, upgrade, rollback and uninstall
      in three isolated Windows application profiles.
- [x] Build the 57-file package twice with an identical SHA-256 digest.
- [x] Pass PR #15's complete 10-check GitHub Actions matrix.
- [x] Publish tag and GitHub Pre-release `v1.0.0-rc1` with the verified ZIP,
      checksum and package manifest.

## Stable v1.0.0 gate

- [ ] Accept only release-blocking fidelity, security, privacy, data-protection
      or supported-path installation fixes during the RC period.
- [ ] Triage public RC feedback and confirm there is no unresolved blocker.
- [ ] Freeze the exact stable candidate and run one final source-closed smoke
      test without changing the rules afterward.
- [ ] Rerun the full CI matrix, release audit and deterministic package build on
      the exact stable candidate.
- [ ] Review stable release notes, tag `v1.0.0` and publish the normal GitHub
      Release only after every gate passes.

New features, template preferences and broader integrations remain deferred to
the post-v1.0 roadmap.
