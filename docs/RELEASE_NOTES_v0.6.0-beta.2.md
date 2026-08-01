# LitAnchor v0.6.0-beta.2

Zero-Config Public Beta — 2026-08-01.

## What changed

- Added separate privacy-aware issue forms for installation, runtime/PDF and
  note-quality failures.
- Added `doctor --support-bundle`, which builds a redacted diagnostic ZIP from
  an explicit allowlist instead of copying local reports or configuration.
- Added semantic intent regression for equivalent installation, lifecycle and
  one-paper reading requests without turning examples into literal commands.
- Added interrupted-update repair, configuration preservation, Vault
  non-interference and isolated Windows lifecycle coverage.
- Added a release-time Skill compaction audit for entry length, duplicate
  long-form rules and missing referenced resources.
- Unified local PDF preparation on PyMuPDF and removed the redundant `pypdf`
  dependency. PyMuPDF remains the physical-page, text, coordinate, rendering,
  crop and formal-evidence authority.
- Added shared coordinate-aware ordering for multi-column PyMuPDF text blocks,
  including a regression that verifies both manual and autonomous paths.
- Kept optional MinerU and development dependencies outside the core install.
  All dependency files now specify minimum versions without artificial upper
  bounds; newer versions are checked by CI and capability probes.
- Replaced the wide one-line Mermaid pipeline with staged, centered diagrams
  that keep the complete Section Synthesis label visible.

## Compatibility

- Windows 10 or newer, x64.
- CPython 3.10 or newer; the release CI matrix covers 3.10 through 3.14.
- Zotero 7 or newer through the loopback Local API.
- Obsidian Desktop with a local filesystem Vault.
- MinerU remains optional, consent-controlled and non-authoritative.

Newer Python, Zotero and dependency versions are not rejected solely because
they are newer. `doctor`, runtime probes and CI determine whether the required
capabilities are available; untested versions receive a warning rather than a
false compatibility claim.

## Upgrade

Agents should use the repository lifecycle interface:

```powershell
.\install.ps1 -Action Upgrade
.\litanchor.ps1 doctor
```

The installer archives the previous receipt-owned version for rollback and
does not modify Zotero data or user notes. Existing Obsidian notes are never
silently overwritten.

## Known boundaries

- One paper per run; no batch review or Zotero write-back.
- Native-text PDFs are the stable path. Scans and pathological layouts may
  warn, fall back or block.
- MinerU requires a local consent choice and network availability. Failure
  falls back to the PyMuPDF baseline without weakening evidence provenance.
- This is a Public Beta rather than the final v1.0 stable release; supported
  environments and failure boundaries remain explicit.
