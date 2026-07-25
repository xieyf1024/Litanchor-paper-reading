# Changelog

## Unreleased — v0.5 Autonomous Deep Reading

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
- Release-candidate merge/tag remains blocked until the three calibration notes
  receive user visual review.

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
