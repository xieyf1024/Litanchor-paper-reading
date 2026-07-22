# Zotero and Obsidian integration

## Zotero acquisition

Use this order:

1. An already connected Zotero MCP with read-only operations.
2. A future Zotero 7 Local API adapter.
3. Zotero Web API read-only when explicitly configured.
4. User-provided PDF.

Do not install a connector during a reading run without approval. Do not read `zotero.sqlite` directly. Do not create, modify, tag or delete Zotero items.

Capture verified metadata, Item Key, attachment key, citekey, annotations and PDF identity. If the attachment key is verified, form page links as:

```text
zotero://open-pdf/library/items/<attachment-key>?page=<physical-page>
```

Never invent an Item Key, attachment key or page link.

## Obsidian export

- Accept one explicitly authorized output directory, preferably a dedicated Literature Inbox.
- Never scan, edit or reorganize the rest of the Vault.
- Validate Markdown, frontmatter, evidence references and filename before writing.
- Write a temporary file in the destination, then atomically rename only if the final path does not exist.
- When the destination exists, stop or create a clearly named candidate after user approval. Never overwrite automatically.
- Preserve the region between `<!-- litanchor:user:start -->` and `<!-- litanchor:user:end -->` during future regeneration.
- Write evidence sidecars to `.litanchor/<paper-id>/` only when that hidden directory is authorized.

Report every created path and confirm that no existing file was replaced.

