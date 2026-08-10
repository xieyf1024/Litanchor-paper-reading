# Zotero and Obsidian integration

## Zotero acquisition

Use this order:

1. `scripts/zotero_local.py` with the local, read-only Zotero API.
2. User-provided PDF.

Do not read `zotero.sqlite` directly. Do not create, modify, tag or delete Zotero items.

Capture verified metadata, Item Key, attachment key, citekey, annotations and PDF identity. If the attachment key is verified, form page links as:

```text
zotero://open-pdf/library/items/<attachment-key>?page=<physical-page>
```

Never invent an Item Key, attachment key or page link.

For the Local API path, run `scripts/zotero_local.py check`, then `prepare` with exactly one of `--item-key`, `--title`, `--doi`, or `--citekey`. Require one exact item and one PDF attachment. Do not use a non-loopback API URL.

## Obsidian export

- Accept one explicitly authorized output directory, preferably a dedicated Literature Inbox.
- Never scan, edit or reorganize the rest of the Vault.
- Validate Markdown, frontmatter, evidence references and filename before writing.
- Use the paper title as the readable note filename. Sanitize invalid Windows
  characters and shorten titles over 120 characters with a stable hash suffix;
  keep the complete title in frontmatter and do not render a duplicate H1.
- Write a temporary file in the destination, then atomically rename only if the final path does not exist.
- When the destination exists, stop or create a clearly named candidate after user approval. Never overwrite automatically.
- Never overwrite an existing note during regeneration; write a separately named candidate so user-authored content remains untouched.
- Write evidence sidecars to `.litanchor/<paper-id>/` only when that hidden directory is authorized.

Report every created path and confirm that no existing file was replaced.

Use `scripts/export_obsidian.py` after a successful `build`. Supply the authorized test root and child Inbox separately, add `--confirm-export`, and add `--allow-warnings` only after reviewing the warnings. The exporter must verify the Markdown hash and reject repeated exports.

## Key-figure assets

- Identify the figure and physical PDF page before cropping.
- Run `scripts/pdf_figures.py` against the original PDF; do not use an unverified parser-exported image as final evidence.
- Keep the generated JSON manifest with the image. It must contain the original PDF hash, physical page, caption, crop box, renderer and image hash.
- Embed the PNG directly under its Figure/Table heading. Follow it with the
  source subsection number/title and linked `p.x`, the selection reason, and a
  two-to-four-sentence interpretation.
- If automatic caption/image geometry is ambiguous, stop for visual review or use an explicit reviewed bounding box.
- MinerU may assist structure/label discovery only after explicit external-upload consent. Align every accepted result back to the original PDF; unmatched content is not evidence.
