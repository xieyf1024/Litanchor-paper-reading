# LitAnchor v0.6.0-beta.1

LitAnchor v0.6.0-beta.1 is the first Agent-installed, Windows-first public
beta. It keeps the v0.5 autonomous deep-reading pipeline and adds a lightweight
installation, setup, diagnosis and release layer.

## Highlights

- Intent-based Agent entry: users may express installation and single-paper
  deep-reading requests naturally; example sentences are not literal commands.
- Python `>=3.10` and Zotero `>=7` are minimums, not maximums. Tested versions
  are preferred, while newer versions run capability probes and emit warnings
  instead of being rejected by version number alone.
- Receipt-tracked install, repair, upgrade, rollback and uninstall operations
  touch only LitAnchor-owned paths.
- First-run setup resolves an Obsidian Vault by name, constrains the Inbox and
  stores one of three local MinerU consent modes.
- Machine-readable `doctor` checks Python, dependencies, Zotero Local API,
  Vault containment, path handling, MinerU readiness and collision risk.
- GitHub Actions validates Python 3.10 through 3.14 on Windows and builds a
  versioned ZIP, checksum and package manifest.
- MinerU runs automatically for eligible documents under persistent consent
  and uses page-preserving subsets for long/oversize papers. PyMuPDF remains
  the authority for evidence and pages.

## Validation

- 3 release-eligible frozen holdouts passed the published rubric.
- 39 physical pages produced 102 EvidenceUnits and 78 ClaimRecords.
- Page accuracy, numeric fidelity, evidence coverage and template completeness
  were all 100% for the deterministic holdout gates.
- 6 pathological PDF/failure fixtures passed.
- 150 repository tests, Skill validation, compilation, Markdown-link and
  anti-leak/privacy checks passed locally.
- MinerU added 2 section candidates and 12 figure candidates across the
  holdouts while creating zero authoritative EvidenceUnits.

## Scope

The beta supports a single local Zotero paper and a contained Obsidian export
on Windows with a local-capable Agent. It does not promise pure-web execution,
batch review, Zotero write-back, bidirectional synchronization or automatic
acceptance of notes without the existing review boundaries.
