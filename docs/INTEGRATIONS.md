# Integration design

## Current implementation status

v0.1 installs no MCP server, Python package, Obsidian plugin, OCR model or background service. It only defines contracts and safe routing. Any unavailable connector must be reported, never simulated.

## Zotero acquisition ladder

1. Use an already connected Zotero MCP with read-only tools.
2. Use Zotero 7 Local API through a future thin adapter.
3. Use Zotero Web API read-only when explicitly configured.
4. Ask the user for a local PDF.

Never read `zotero.sqlite` directly in the default workflow. Never create, modify, tag or delete Zotero items in the MVP.

Match candidates in this order: Item Key, Better BibTeX citekey, DOI, exact normalized title, then fuzzy title. When multiple plausible matches remain, ask the user to choose.

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

## Zotero page links

When a verified attachment key is available, use:

```text
zotero://open-pdf/library/items/<attachment-key>?page=<physical-page>
```

Do not generate a link from an unverified key.

## Information needed before phase 1

- Zotero version and whether Zotero 7 Local API is enabled.
- Whether Better BibTeX is installed and a few non-sensitive test citekeys/Item Keys.
- Whether installing Zotero MCP is permitted; if so, preferred D-drive installation location.
- The exact future `Literature Inbox` inside the test Vault.
- Whether the desktop environment can expose Zotero tools directly to Codex.

No API keys, cookies, private Zotero database, production Vault or unpublished corpus should be committed.
