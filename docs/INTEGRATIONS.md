# Integration design

## Current implementation status

v0.4.1 candidate uses `pypdf` for native text preflight and PyMuPDF for original-page rendering and auditable figure crops. It connects to a running Zotero desktop client through the Local API and exports only to an explicitly authorized Obsidian test root. It installs no MCP server, Obsidian plugin, OCR model or background service. MinerU Open SDK is a separate optional dependency for consent-gated Flash structure enhancement.

## Zotero acquisition ladder

1. Use `scripts/zotero_local.py` with the Zotero Local API as the default lightweight local path.
2. Ask the user for a local PDF when Zotero is unavailable.

Never read `zotero.sqlite` directly in the default workflow. Never create, modify, tag or delete Zotero items in the MVP.

Match candidates in this order: Item Key, Better BibTeX citekey, DOI, then exact normalized title. The title adapter may retry punctuation-free prefixes to work around Zotero search tokenization, but final acceptance remains an exact normalized-title match. It never promotes a fuzzy candidate.

The implemented adapter accepts Item Key, citekey, DOI or exact normalized title. It blocks zero/multiple exact matches and zero/multiple PDF attachments instead of silently taking the first result. Its URL must be a loopback HTTP `/api` endpoint, and its request method is fixed to `GET`.

## Obsidian export contract

- Accept only an explicitly authorized output directory.
- Default to a dedicated `Literature Inbox`, not the complete Vault.
- Generate and validate a temporary file first.
- If the destination exists, create a candidate artifact or stop; never overwrite automatically.
- Preserve content between `litanchor:user:start` and `litanchor:user:end` markers.
- Write sidecars under `.litanchor/<paper-id>/` only after the user authorizes that location.

Formal output package:

```text
<paper-title>.md
.litanchor/<paper-id>/evidence.json
.litanchor/<paper-id>/claims.json
.litanchor/<paper-id>/validation.json
.litanchor/<paper-id>/run.json
```

The exporter also records and verifies the Markdown SHA-256. `completed_with_warnings` requires explicit warning acceptance. All collision checks run before writing, and a repeat export is blocked.

## Zotero page links

When a verified attachment key is available, use:

```text
zotero://open-pdf/library/items/<attachment-key>?page=<physical-page>
```

Do not generate a link from an unverified key.

## Key-figure export

Every deep/internalize note must complete a Visual Selection Pass. Select 1–3 figures only when they are indispensable to the method or main result; if none qualifies, record the reason. Use `scripts/pdf_figures.py` after the evidence-ledger step identifies a key figure and verifies its one-based physical PDF page. The script searches one caption, renders from the original PDF, expands suspicious borders, checks edge contact, and writes a sidecar manifest. If automatic geometry is ambiguous, stop and inspect the page before supplying an explicit bounding box. Cropped, contaminated or review-required images do not enter the note.

Embed the PNG with a Vault-relative Obsidian wikilink. Keep the manifest outside the human note, and include a verified `zotero://open-pdf` link beside the image. MinerU or another structure parser may suggest a label/page, but the final image must come from the original PDF.

## Deferred options and recommendation

- **Zotero MCP:** not required or supported by the project runtime. Zotero Local API remains the single official Zotero connector.
- **Obsidian→Zotero:** implemented as page-level `zotero://open-pdf` links and requires no Obsidian plugin.
- **Zotero→Obsidian:** defer because it requires Zotero writes and stable Obsidian paths. It is not equivalent to the current traceability link.
- **Codex→Obsidian:** keep plain Markdown and filesystem export; do not require an Obsidian plugin.
- **PDF parsing:** keep PyMuPDF and the original PDF as the page/visual evidence authority. `scripts/autonomous_deep_reading.py` applies the local `always_for_eligible_files`, `ask_each_time`, or `never` consent mode and automatically executes eligible token-free MinerU Flash routes (10 MiB, 20 pages). The local setting is never committed. MinerU output must align back to PyMuPDF pages; unmatched content cannot become evidence. This project does not use the paid precision API.

No API keys, cookies, private Zotero database, production Vault or unpublished corpus should be committed.
