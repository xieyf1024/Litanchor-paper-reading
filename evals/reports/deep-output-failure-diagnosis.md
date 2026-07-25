# Deep-output failure diagnosis

Date: 2026-07-24
Affected candidate: `v0.4.1-candidate`
Severity: release blocker

## Reproduction

The ResNet, LOVECLIM and U-Net candidates use the simplified eleven-section renderer rather than `Paper Template - Final`. Their human-readable analysis is substantially shorter and structurally shallower than the three AI-assisted reference notes. U-Net also exports an empty discussion section.

## Code-path findings

1. `prepare_pdf()` creates empty `evidence.json` and `claims.json`. There is no automatic full-paper Evidence/Claim extractor in the local runtime.
2. The blind-test ledgers were manually curated fixtures. They were not produced by repeated section-specific model passes.
3. There is no per-type top-k limiter in code, but the manual fixtures contain only 11–12 claims. The sparse output is therefore not an API token truncation or LLM stopping issue.
4. There is no LLM call in `litanchor_local.py`; the runtime cannot independently recover omitted methods, experiments, equations, results or discussion.
5. The renderer bypassed the template asset and grouped each `claim_text_zh` into one Markdown bullet.
6. The old `deep` gate checked only evidence-page breadth, section count and whether evidence reached the later half. It did not check paper-template sections, content recall or explanatory depth.
7. Existing tests covered traceability, pages, numbers, crop provenance and safe export, but not Final-template headings, required deep content groups or section depth.

## Root cause

The primary failure is architectural: the knowledge representation and renderer were designed for traceable evidence summaries, while the product contract requires a structured graduate-level close-reading note. Deterministic reliability gates passed, but the product-quality contract was absent.

## Corrective action

- Preserve the three short notes as failed regression examples.
- Route `deep` and `internalize` through the canonical Final template.
- Expand ClaimRecord into a richer intermediate knowledge object.
- Require specialised extraction passes and an omission review.
- Block sparse or shallow deep ledgers before rendering or export.
- Keep gold comparison separate; deterministic density checks do not prove scientific completeness.
