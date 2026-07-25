# AI-assisted reference to human gold

The three detailed notes currently stored in the private Obsidian test Inbox are
quality-reference material, not gold answers. Use them to decide what a strong
close-reading note should cover, then verify selected items independently
against the original PDF.

## Required provenance

- Record the exact PDF SHA-256, Zotero Item/Attachment identity and one-based
  physical page convention.
- Keep the full author list in SourceBundle; render only the verified first
  author in note frontmatter.
- Distinguish original-PDF evidence, parser output, external explanation and
  human interpretation.

## Minimum human checks per paper

- One central research question and the stated research gap.
- Three to six method steps with important parameters, data and conditions.
- Three to six core results with scope and author modality preserved.
- Two to four key numeric items including units, ranges/errors and conditions.
- One to three limitations or uncertainties.
- One or two key equations when central to the paper.
- Two key visuals with label, physical page, caption, role and expected
  interpretation.
- An exact or normalized original-language evidence excerpt for every selected
  claim, plus a traceability verdict.

## Key-visual checks

- Select a visual because it defines the method or supports a core result, not
  because it is decorative.
- Crop the displayed image from the original PDF and retain the generated JSON
  manifest.
- Confirm the crop contains the full intended panel(s) and caption without
  accidentally including a neighboring figure.
- Add a verified Zotero physical-page link.
- Treat numbers and symbols read only by a vision model as provisional until
  checked on the original page.

## External-source rule

An explainer, blog, video or textbook may reveal a missing teaching point or
possible misunderstanding. It cannot establish what the paper claims. Any
suggested addition must be found in the original PDF before it enters the
paper-evidence layer; otherwise label it as external learning context.

## Promotion gate

Promote an AI-assisted reference to gold only after:

1. a human completes the checks without treating the candidate note as the
   sole answer key;
2. every selected claim has a verified page and evidence excerpt;
3. numeric, modality, causality and scope checks pass;
4. parser failures and unresolved disagreements are recorded; and
5. a second reviewer independently checks at least the retained double-annotated
   subset.
