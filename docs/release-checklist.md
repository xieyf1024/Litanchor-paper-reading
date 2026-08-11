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

## v0.6.0-beta.2 Public Beta stabilization

- [x] Preserve the frozen v0.6 evaluation manifests and paper-content boundary.
- [x] Add separate public issue forms for installation, runtime/PDF and note-quality failures.
- [x] Add an allowlist-based redacted doctor support bundle.
- [x] Add semantic intent-regression cases without production phrase matching.
- [x] Add lifecycle interruption, preservation and Vault non-interference tests.
- [x] Add the release-time Skill compaction audit.
- [x] Remove the redundant pypdf runtime and unify PDF preparation on PyMuPDF.
- [x] Keep core, optional MinerU and development dependencies separate with minimum-only constraints.
- [x] Replace the clipped single-row Mermaid flow with centered staged diagrams.
- [x] Complete the 158-test local gate, Skill validation, compilation, link/privacy audits, release build and one real isolated Windows lifecycle smoke run.
- [x] Complete GitHub Actions on the exact candidate commit.
- [x] Select defect-driven `v0.6.0-beta.2`: repair now clears a stale activation backup after an interrupted update, with a regression test.

## v0.6.0-beta.3 Note Experience & Paper Template v1.0 Freeze

Date prepared: 2026-08-10

### Content-contract freeze

- [x] Split the public `Paper Template.md` contract from the private Runtime
      renderer.
- [x] Freeze mode scope: `skim` Section 1, `deep` Sections 1–6, and
      `internalize` Sections 1–8.
- [x] Freeze the 16-field frontmatter Schema and represent mode only through
      one mode tag beside `LitAnchor`.
- [x] Keep Evidence IDs and exact excerpts in private sidecars; expose only
      compact linked `p.x` locators in the reader note.
- [x] Add paper-type analytical lenses, experiment evidence chains,
      conclusion boundaries, provenance labels, and internalize research-idea
      gates without adding paper-specific rules.
- [x] Preserve page-grounded formal export, PyMuPDF evidence authority,
      consent-aware MinerU enhancement, contained writes, and no overwrite.

### Local candidate gates

- [x] Complete the 173-test repository suite on the local beta.3 candidate.
- [x] Verify clean generated Markdown source with no internal HTML comments,
      no Section 6.5, and no internal experiment-completion placeholder.
- [x] Reproduce and fix vertically adjacent Figure 1/2 and Figure 8/9 crops on
      an original PDF; the corrected Figure 2 and Figure 9 crops pass visual
      inspection without paper-specific rules.
- [x] Complete Skill validation, source compilation, Markdown-link, anti-leak/privacy,
      release-package, and diff-whitespace checks.
- [x] Verify the built package version, 57-file manifest, checksum, install
      payload, retired-template exclusion, and deterministic two-build hash.
- [x] Review at least one `skim`, one `deep`, and one `internalize` note in
      Obsidian; the three notes should cover distinct paper-analysis demands.
- [x] Sync the local Obsidian `Paper Template.md` copy to the tested Paper
      Template v1.0 content contract after the final Section 6.5 and
      source-comment cleanup. Obsidian may normalize table-column spacing, so
      verify headings, fields and alignment markers rather than requiring a
      byte-identical hash; retain the previous copy as a private rollback backup.

### Publication gates

- [x] Commit and push `codex/v0.6-beta3-paper-analysis`.
- [x] Create a pull request and complete the Windows Python 3.10–3.14 GitHub
      Actions matrix on the exact candidate commit.
- [x] Merge to `main`, tag `v0.6.0-beta.3`, and publish the verified ZIP,
      checksum, and package manifest as a GitHub Pre-release.
- [x] Freeze beta.3 feedback before deciding whether the next version is a
      narrow patch or `v1.0.0-rc1`; do not reopen the template without a
      release-blocking defect.

## v1.0.0-rc1 preparation

- [x] Run all three papers named in the frozen checklist under the frozen
      content pipeline; record them as regression cases after evaluation.
- [x] Run one separate unseen paper without a reference note or prefilled
      Evidence/Claim ledger.
- [x] Reproduce a reliable blocker for captions separated from figure plates,
      then fix it generically with explicit caption/plate provenance and retain
      the same crop-quality gate.
- [x] Document engineering, generalization, controlled-failure and human-review
      evidence separately in `v1.0.0-rc1-frozen-validation.md`.
- [x] Complete the install/read lifecycle in three isolated Windows application
      profiles: normal English path with real core dependencies, Chinese/Vault
      path, and interrupted-install recovery. Record that these are not three
      independent users.
- [x] Verify a direct local-PDF to standalone-Markdown run plan without Zotero
      or Obsidian configuration, and prepare all 38 physical pages of the final
      unseen PDF through that route.
- [x] Pass 180 repository tests, Skill validation, compilation, 51 local
      Markdown links, privacy/anti-leak and Skill compaction audits locally.
- [x] User-review the final unseen note and its two split-page figure crops in
      the Obsidian test Inbox.
- [x] Rerun CI, privacy, anti-leak, packaging, upgrade, rollback and uninstall
      checks on the exact RC candidate commit; PR #15 passed the complete
      10-check GitHub Actions matrix before merge.
- [x] Review and approve the RC release notes.
- [x] Tag and publish `v1.0.0-rc1` as a GitHub Pre-release after the exact
      candidate CI passes, with the verified ZIP, checksum and package
      manifest attached.
