# Changelog

## Unreleased

- Reworked the bilingual repository landing pages around the two-intent public
  experience, reliability contract, current boundaries and public-beta proof.
- Added a current documentation index, stable-release roadmap, contribution
  guide and privacy-aware GitHub issue forms.
- Removed obsolete v0.4.1 previews, paper figure crops, failed sparse outputs,
  repair reports, the superseded early project specification and raw personal
  reading/template source notes from the current branch. Git tags and releases
  continue to preserve version history.
- Kept the v0.6 evaluation manifests, frozen holdouts, pathological fixtures,
  rubrics, metrics and validation reports unchanged.
- Clarified that the distilled reading method is an optional project-authored
  heuristic for `internalize`, not a factual source or reliability rule.

## v0.6.0-beta.1 — 2026-07-29 — Zero-Config Public Beta

- Synchronized the current product, integration, workflow, schema, evaluation
  and release-checklist documents with the published v0.5.0 state.
- Documented the supported Windows/Python/Zotero/Obsidian baseline and the
  minimum-version, capability-probed compatibility policy.
- Added the v0.6 Agent-assisted installation and public-beta hardening roadmap.
- Removed unused integration comparisons from the active Skill reference and
  current user-facing boundaries while retaining historical specifications as
  clearly marked records.
- Added a machine-readable installation manifest, receipt-tracked user-local
  installer, idempotent install/upgrade/repair, archived rollback and
  confirmation-gated uninstall.
- Added Obsidian Vault discovery by name, contained first-run setup, persistent
  MinerU consent, machine-readable doctor checks and an Agent-facing run plan.
- Added deterministic Windows release ZIP/checksum generation and Windows
  Python 3.10–3.14 GitHub Actions coverage.
- Made Agent entry intent-based instead of requiring two literal example
  sentences, and added provisional support for future Python/Zotero versions.
- Kept the public dependency split lightweight: two core PDF packages, one
  optional MinerU requirement and PyYAML only for development validation.
- Passed three release-eligible frozen holdouts under the pre-published v0.6
  rubric after moving two failure-driven cases to development and
  disqualifying one previously exposed replacement.
- Completed whole-document and page-preserving MinerU routes on the holdouts:
  236 of 265 blocks aligned to PyMuPDF pages, two section candidates and twelve
  figure candidates were added, and zero authoritative EvidenceUnits came
  from MinerU.
- Passed six synthetic pathological PDF/failure cases, including two-column
  order, scan fallback, mixed blank pages, long documents,
  Methods-after-References and MinerU timeout fallback.
- Expanded the anti-leak audit to include titles and DOIs from every tracked
  evaluation manifest rather than only the original v0.5 corpus.
- Made GitHub Actions fetch complete Git history so frozen-evaluation ancestry
  checks remain reproducible on pull-request runners.

## v0.5.0 — 2026-07-26 — Autonomous Deep Reading

- Promoted the autonomous deep-reading pipeline after the release candidate,
  six-paper evaluation and three additional cross-domain generalization cases.
- Passed a final fully unseen, source-closed smoke test under the frozen
  workflow and rubric with no severe fidelity failure.
- Kept the release paper-independent: no test title, answer, reference note or
  paper-specific branch was added to the distributable Skill.
- Preserved PyMuPDF as the physical-page and evidence authority while keeping
  MinerU Flash as a consent-controlled, non-authoritative structure enhancer.
- Kept visual acceptance, no-overwrite Obsidian export, local-only consent and
  runtime privacy boundaries unchanged.
- Stable release gate: 116 repository tests, Skill validation, Python
  compilation and anti-leak/privacy checks passed locally.

## v0.5.0-rc1 — 2026-07-26 — Autonomous Deep Reading Pre-release

- Froze a three-paper blind corpus using only Zotero metadata, original PDFs
  and the canonical Final template.
- Added a PyMuPDF-authoritative autonomous work-packet command with automatic
  paper-type classification, section discovery and six explicit reading
  passes.
- Added blind-run origin controls: only `auto_extracted` EvidenceUnits and
  `auto_synthesized` ClaimRecords can enter an autonomous candidate.
- Added separate fidelity and recall review contracts. Pending or incomplete
  reviews cannot represent a completed deep-reading run.
- Added token-free MinerU Flash routing for whole eligible papers and
  page-preserving subsets of long PDFs; all MinerU content remains
  non-authoritative until aligned to an original PyMuPDF physical page.
- Added three persistent local MinerU consent modes
  (`always_for_eligible_files`, `ask_each_time`, `never`) and automatic
  structure fusion for eligible files; the selected mode is never committed.
- Added page-verified autonomous semantic materialization, complete
  SectionSynthesis, independent fidelity/recall review, all-figure selection,
  crop validation and Final-template candidate generation.
- Added explicit page-review receipts and preserved already-reviewed pages when
  a later MinerU fusion leaves their physical-page classification unchanged.
- Fixed Nature-style Methods-after-References layouts, visual appendices after
  references, `Fig. N |` captions, legitimate `mm` units and accepted-note
  export promotion.
- Completed the official six-paper autonomous evaluation with 182 EvidenceUnits,
  155 ClaimRecords, 15 selected visuals, zero blockers and all deterministic
  quality metrics at 1.0.
- Rebuilt ResNet, LOVECLIM and climate U-Net as extended non-autonomous
  regressions; the stricter summary gate caught and blocked a shallow LOVECLIM
  overview until its evidence-backed summary was corrected.
- Added cross-paper metrics, failure taxonomy, anti-leak audit, release
  checklist and a non-promoted EvolutionCandidate.
- Added paper-independent checks for range-symbol corruption, metadata/type
  consistency, generic claim headings and duplicated section content.
- Added primary plus secondary paper profiles, a distinct `parameter` claim
  type, original-page scientific-symbol receipts, multi-evidence combined
  claims and idempotent acceptance of reviewed warning-state notes.
- Compacted `SKILL.md` to the permanent workflow contract; detailed rules,
  deterministic behavior and templates remain in `references/`, `scripts/`
  and `assets/`.
- All six official notes passed user review for key visuals, layout and Zotero
  links. Three additional unseen cross-domain papers also passed structured
  regeneration and user review without adding paper-specific rules.
- Full repository regression: 116 tests passed; Skill validation, compilation,
  privacy and anti-leak audits passed.

## v0.4.1 — 2026-07-25 — Deep Reading Pipeline Pre-release

- Reclassified the previous ResNet, LOVECLIM and U-Net outputs as failed deep-reading examples rather than accepted blind notes.
- Added the canonical slot-driven `Paper Template - Final` asset for all `deep` and `internalize` notes.
- Expanded ClaimRecord types and added structured titles, explanatory details, conditions, section IDs and importance.
- Added deterministic deep-reading gates for required content groups, content recall, section depth and Final-template conformance.
- Kept `skim` output separate from the Final deep-reading template.
- Added regression tests proving that a sparse one-claim ledger is blocked and a rich ledger renders the complete Final template.
- Reprepared and rebuilt ResNet, LOVECLIM and climate U-Net as real-paper forward-validation cases; all three now pass Final-template, multi-page traceability, content-recall, section-depth, quote-completeness, numeric-rendering, cross-section consistency and paper-type gates.
- Fixed duplicated numeric suffixes, rejected incomplete evidence quotations, mapped data/metrics/experiments into the correct Final-template sections and required an all-figure inventory with both method and result coverage where available.
- Added result visuals for the three repaired examples: ResNet Figure 6, LOVECLIM Figure 21 and U-Net Figure 7.
- Published the release as a GitHub Pre-release because the local runtime still requires the specialised reading passes to populate the ledgers.
- Automatic multi-pass full-text deep reading, automatic PyMuPDF–MinerU fusion and independent semantic review are explicitly deferred to v0.5.
