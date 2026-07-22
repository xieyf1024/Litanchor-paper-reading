# Integration design

## Current implementation status

v0.3 uses one lightweight dependency (`pypdf`) and the Python standard library. It connects to a running Zotero desktop client through the Local API and exports only to an explicitly authorized Obsidian test root. It installs no MCP server, Obsidian plugin, OCR model or background service.

## Zotero acquisition ladder

1. Use `scripts/zotero_local.py` with the Zotero Local API as the default lightweight local path.
2. Use an already connected Zotero MCP with read-only tools when cross-client tool standardization is needed.
3. Use Zotero Web API read-only when explicitly configured for a remote workflow.
4. Ask the user for a local PDF.

Never read `zotero.sqlite` directly in the default workflow. Never create, modify, tag or delete Zotero items in the MVP.

Match candidates in this order: Item Key, Better BibTeX citekey, DOI, exact normalized title, then fuzzy title. When multiple plausible matches remain, ask the user to choose.

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

## Deferred options and recommendation

- **Zotero MCP:** optional later, not a PDF parser and not required by the current local workflow. Add it only when Chat/Work/Codex need a shared MCP tool surface or richer Zotero operations.
- **Obsidian→Zotero:** implemented as page-level `zotero://open-pdf` links and requires no Obsidian plugin.
- **Zotero→Obsidian:** defer because it requires Zotero writes and stable Obsidian paths. It is not equivalent to the current traceability link.
- **Codex→Obsidian:** keep plain Markdown and filesystem export; do not require an Obsidian plugin.
- **PDF parsing:** keep local native extraction first. Evaluate PyMuPDF for coordinates/rendering, failed-page OCR and selected visual analysis next. MinerU Quick/Agent parsing should remain opt-in, used only after local failure and explicit external-upload consent; longer documents should stay on local parsing or a separately approved precision/local MinerU path.

No API keys, cookies, private Zotero database, production Vault or unpublished corpus should be committed.
