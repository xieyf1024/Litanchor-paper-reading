# LitAnchor v0.6.0-beta.3

`v0.6.0-beta.3` freezes the reader-facing note experience as **Paper Template
v1.0**. It is the final content-contract beta before the stable-release
candidate; it does not broaden LitAnchor into batch review, Zotero write-back,
or unattended publication.

## What changed

- Split the public `Paper Template.md` content contract from the private,
  slot-driven `Paper Template - Runtime.md` renderer.
- Defined mode-specific output: `skim` renders Section 1, `deep` Sections 1–6,
  and `internalize` Sections 1–8. Excluded sections are omitted.
- Froze the 16-field note-frontmatter contract. Reading mode appears only as
  one mode tag alongside `LitAnchor`; user-added tags remain preservable.
- Replaced reader-facing Evidence IDs and repeated excerpts with compact linked
  `p.x` locators. Exact evidence and Claim mappings remain in private sidecars.
- Added argument-aware analytical lenses, structured experiment evidence
  chains, explicit conclusion boundaries, and visible provenance labels for
  Agent analysis, hypotheses, and user content.
- Added source-grounded research-idea gates for `internalize`, including a
  falsifiable hypothesis, delta, validation design, failure modes, and novelty
  status.
- Embedded selected key visuals directly with their source subsection,
  selection reason, and a two-to-four-sentence interpretation.
- Kept skim-mode visual inventories private without requiring or exporting
  image assets that the Section 1-only reader note does not embed.
- Removed the duplicate note H1 and added readable, stable filename handling
  for long or filesystem-unsafe titles.
- Removed internal HTML comments from generated note source and removed the
  reader-facing Section 6.5; validation state remains available in sidecars and
  frontmatter.
- Distinguished supporting reproducibility records from core comparison
  experiments, preventing internal completion guidance from appearing in a
  reader note.
- Separated vertically adjacent figures using the preceding caption as a hard
  crop boundary, including vector-heavy figures that require a bounded-region
  fallback.
- Applied standard Markdown left alignment to text-heavy tables without adding
  a CSS dependency.

## Reliability boundaries

- PyMuPDF remains authoritative for physical pages, quotations, coordinates,
  and original-PDF crops.
- MinerU remains an optional, consent-aware structure enhancer and never becomes
  the formal Evidence source.
- Formal `deep` and `internalize` export requires full-paper coverage with
  page-grounded locators.
- Zotero remains read-only. Obsidian export remains contained, hash-verified,
  collision-checked, and non-overwriting.
- Paper facts still use the supplied paper only. External novelty search is a
  separate, explicitly authorized activity.

## Upgrade notes

- Existing notes are not rewritten automatically.
- New notes use `template_version: "1.0"` and the fixed frontmatter properties.
- Runtime Evidence/Claim/review sidecars remain private and are not copied into
  the reader note.
- Upgrade through the normal LitAnchor lifecycle so rollback remains available.

## Verification before publication

The release candidate must pass the complete repository suite, Skill/package
validation, Markdown-link and anti-leak/privacy audits, exact-version package
build, GitHub Actions matrix, and representative Obsidian note review. Release
results belong in `docs/release-checklist.md`; this file describes the intended
release contract rather than claiming unpublished results.
