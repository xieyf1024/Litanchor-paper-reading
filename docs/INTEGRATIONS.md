# Integration design

## Current implementation status

The published v0.5.0 path connects to Zotero 7 through the loopback-only Local
API, builds a PyMuPDF-authoritative page baseline, applies the user’s local
MinerU consent policy and exports a reviewed note only to an explicitly
authorized Obsidian Vault subdirectory.

`pypdf` supports native-text preflight in the manual local path. PyMuPDF is the
authority for autonomous physical pages, quotations, coordinates, Zotero page
links, page renders and final figure crops. MinerU Open SDK is a conditional
structure enhancer whose results must align back to PyMuPDF pages.

## Active integration path

```text
Zotero 7 Local API or local PDF
→ one verified PDF
→ PyMuPDF page bundle
→ consent-aware MinerU structure candidates
→ autonomous deep-reading ledgers and reviews
→ Final-template Markdown and original-PDF images
→ contained Obsidian export
```

## Zotero acquisition

Use `scripts/zotero_local.py` with the Zotero Local API as the default path.
Use a user-provided local PDF when the paper is not acquired from Zotero.

Match in this order:

1. Item Key;
2. citekey;
3. DOI;
4. exact normalized title.

The title adapter may retry a punctuation-free prefix to handle Zotero search
tokenization, but final acceptance remains exact after normalization. Zero or
multiple exact matches and zero or multiple PDF attachments are blockers.

The adapter:

- accepts only a loopback HTTP `/api` endpoint;
- sends only `GET`;
- captures verified metadata, Item Key, attachment key, citekey and PDF
  identity;
- does not read `zotero.sqlite`;
- does not create, edit, tag or delete Zotero records.

## Zotero page links

When a verified attachment key is available, use:

```text
zotero://open-pdf/library/items/<attachment-key>?page=<physical-page>
```

Generate the link only after the evidence quotation and one-based physical page
have been verified against the original PDF.

## PDF parsing and MinerU fusion

Every autonomous run starts with PyMuPDF:

- file and page inventory;
- physical-page text and coordinates;
- section and figure candidates;
- authoritative quote matching;
- original-page rendering and cropping.

The local MinerU policy has three modes:

- `always_for_eligible_files`;
- `ask_each_time`;
- `never`.

For an eligible paper, the `start` workflow automatically calls MinerU Flash
when the stored policy permits it. The whole-file route checks at most 10 MiB
and 20 pages. A long paper uses page-preserving subsets selected from the
PyMuPDF baseline.

MinerU may improve:

- heading hierarchy;
- multi-column reading order;
- figure/table captions;
- formula, table and OCR candidates.

Every MinerU block is labelled `exact`, `fuzzy` or `unmatched` during alignment.
No MinerU text becomes an EvidenceUnit unless the corresponding content is
verified on an original PyMuPDF physical page. The final image is always
rendered or cropped from the original PDF.

## Key-figure export

Every `deep` or `internalize` note must complete a Visual Selection Pass:

1. inventory all detected figures and tables;
2. connect captions with body references;
3. select zero to three indispensable method/result visuals;
4. record a reason when none qualifies;
5. render or crop with `scripts/pdf_figures.py`;
6. verify source hash, page, caption, crop geometry, edges and output hash;
7. embed the accepted PNG with a Vault-relative Obsidian wikilink.

Ambiguous, clipped or contaminated crops remain review items and cannot enter
the final note.

## Obsidian export contract

- Resolve one explicit Vault root and one allowed child directory.
- Validate Markdown, frontmatter, evidence references, image targets and
  filename before writing.
- Verify the candidate Markdown SHA-256 immediately before export.
- Run all collision checks before creating any final file.
- Write temporary files in the destination and promote them atomically.
- Stop when the destination exists; never overwrite automatically.
- Preserve user-owned content markers during later regeneration.
- Write sidecars under `.litanchor/<paper-id>/` only inside the authorized
  location.
- Report every created path and confirm that no existing file was replaced.

Formal output:

```text
<paper-title>.md
_assets/<paper-slug>/<selected-figure>.png
.litanchor/<paper-id>/evidence.json
.litanchor/<paper-id>/claims.json
.litanchor/<paper-id>/section_synthesis.json
.litanchor/<paper-id>/fidelity_review.json
.litanchor/<paper-id>/recall_review.json
.litanchor/<paper-id>/run.json
```

## Local privacy

Keep API consent, user paths, PDFs, Zotero identifiers, generated notes,
feedback and runtime ledgers outside Git. The distributable repository contains
only code, general rules, schemas, templates, public examples and evaluation
metadata that is safe to publish.
