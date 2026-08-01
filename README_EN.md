# LitAnchor

> Anchor every insight to the source.

[![Release](https://img.shields.io/github/v/release/xieyf1024/Litanchor-paper-reading?include_prereleases&label=release)](https://github.com/xieyf1024/Litanchor-paper-reading/releases)
[![Windows CI](https://github.com/xieyf1024/Litanchor-paper-reading/actions/workflows/ci.yml/badge.svg)](https://github.com/xieyf1024/Litanchor-paper-reading/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-%E2%89%A53.10-3776AB?logo=python&logoColor=white)](docs/INSTALLATION_REQUIREMENTS.md)
[![License](https://img.shields.io/github/license/xieyf1024/Litanchor-paper-reading)](LICENSE)

[中文](README.md) · [Requirements](docs/INSTALLATION_REQUIREMENTS.md) · [Workflow](docs/WORKFLOW.md) · [Evaluation](docs/EVALUATION.md) · [Roadmap](docs/ROADMAP.md)

LitAnchor is a lightweight, evidence-first academic close-reading skill for graduate students and researchers. It resolves a single paper from Zotero, treats that paper as the only factual source, and writes a Chinese Obsidian note whose important claims remain traceable to physical PDF pages, source evidence, and Zotero links.

Current release: **v0.6.0-beta.1 Zero-Config Public Beta**. It targets local-capable agents on Windows. It is not yet an unattended product for every PDF or browser-only chat client.

## Two-step experience

The wording below is illustrative. Agents should route by intent, not literal commands.

```text
Install this skill for me: https://github.com/xieyf1024/Litanchor-paper-reading
```

```text
Deep-read “Paper title” and save the note to my Research Vault.
```

First-run setup may confirm only the Obsidian Vault, Literature Inbox, and MinerU consent mode. The agent then manages the isolated environment, dependencies, Zotero lookup, full-paper reading, validation, and contained export.

## Why it is not a generic AI summary

| Generic summary behavior | LitAnchor |
|---|---|
| Generates fluent prose directly from the document | Builds Evidence → Claim → SectionSynthesis before composing the note |
| Checks only what was written | Reviews both fidelity and important-content recall |
| Emits a page link even when location is uncertain | Rejects unverified pages as formal evidence |
| Often skips equations, metrics, and figures | Runs dedicated method, experiment, formula, and visual passes |
| Writes directly to the destination | Restricts writes to an authorized root and refuses overwrite by default |
| Mixes model knowledge with paper claims | Uses the supplied paper as the only factual source |

## Pipeline

```mermaid
flowchart LR
    A["Zotero / PDF"] --> B["PyMuPDF source baseline"]
    B --> C["Consent-controlled MinerU"]
    C --> D["Six-pass full-text reading"]
    D --> E["Evidence → Claim → SectionSynthesis"]
    E --> F["Visual and dual review"]
    F --> G["Authorized Obsidian Inbox"]
```

PyMuPDF remains authoritative for physical pages, quotations, coordinates, and visual provenance. MinerU can improve headings, reading order, captions, and complex-layout candidates, but its output must align back to the original PDF before it can support formal evidence.

## Reliability contract

- Use only the supplied paper for formal paper facts.
- Preserve the author's uncertainty and do not promote interpretation or speculation to fact.
- Bind factual claims to an Evidence ID and a verified physical PDF page.
- Preserve numbers, units, variables, ranges, and conditions.
- Report parsing failures and stop formal export on blockers.
- Keep Zotero read-only and Obsidian writes inside an authorized directory.
- Refuse overwrite by default and require local consent before external upload.

## Requirements

- Windows 10/11 x64;
- Python 3.10 or newer; CI currently covers 3.10–3.14;
- Zotero 7 or newer with local application communication enabled and a local PDF attachment;
- Obsidian Desktop with a local filesystem Vault;
- an agent capable of running local commands, reading/writing authorized paths, and downloading dependencies.

Python and Zotero have minimum versions, not arbitrary maximum versions. Newer untested versions are capability-probed by `doctor` and reported with a warning. See [installation requirements](docs/INSTALLATION_REQUIREMENTS.md).

## Agent and developer entry points

End users should prefer natural-language installation and reading requests. Agents and contributors can call:

```powershell
.\install.ps1 -Action Install
.\litanchor.ps1 doctor
.\litanchor.ps1 setup -Vault "Vault name" -Inbox "LitAnchor\00_Inbox" -MinerUConsent ask_each_time -CreateInbox
.\litanchor.ps1 run-plan -Paper "Paper title" -Vault "Vault name"
```

These are agent-facing execution interfaces, not manual steps required from every user. The installer manages only receipt-owned LitAnchor files and supports repair, upgrade, rollback, and confirmation-gated uninstall.

## Output

`deep` mode covers the research question, background and gap, data and preprocessing, methods and models, equations and metrics, experiments, results, author interpretation, limitations, and selected key visuals. Full evidence remains in sidecar records; the Markdown note keeps only compact locators and selected collapsed quotations.

## Public-beta evidence

v0.6.0-beta.1 passes Windows Python 3.10–3.14 CI, frozen holdout evaluation, pathological PDF/failure tests, MinerU component comparison, privacy checks, and deterministic release builds. Evaluation papers may teach reusable failure classes and workflow rules, never paper-specific answers in the distributable Skill.

- [v0.6 Public Beta validation](evals/reports/v0.6-public-beta-validation.md)
- [MinerU component A/B](evals/reports/v0.6-mineru-ab.md)
- [v0.6 metrics](evals/v0.6-public-beta-metrics.json)
- [Anti-leak audit](docs/anti-leak-audit.md)

## Current boundaries

- One paper per run; no batch review or knowledge graph.
- Native-text PDFs are the stable path; scans and pathological layouts may degrade or block.
- MinerU is an optional network service and never an authoritative evidence source.
- No Zotero write-back, bidirectional sync, or silent overwrite of existing Obsidian notes.
- Users should still review key visuals, locators, and notes intended for long-term use.

## Repository layout

```text
.
├── .github/                         # CI, dependency updates, issue forms
├── skills/litanchor-paper-reading/  # Installable skill and runtime resources
├── docs/                            # Product, workflow, architecture, roadmap
├── evals/                           # v0.6 manifests, rubrics, public reports
├── tests/                           # Automated regression tests
├── tools/                           # Build, validation, evaluation, audit tools
├── install.ps1                      # Windows installation lifecycle
├── litanchor.ps1                    # doctor, setup, and run-plan
└── litanchor-install.json           # Machine-readable installation contract
```

The installable skill contains only runtime instructions, scripts, schemas, references, and templates. Git tags, releases, and the [changelog](CHANGELOG.md) preserve project history without keeping obsolete previews in the current branch.

## Documentation and contributing

Use the [documentation index](docs/README.md) to find product, workflow, schema, integration, evaluation, privacy, and roadmap documents. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a contribution.

Do not submit paper PDFs, private Zotero data, Obsidian Vault contents, API keys, personal annotations, or runtime Evidence/Claim artifacts.

## License

[GNU Affero General Public License v3.0 only](LICENSE). See [THIRD_PARTY.md](THIRD_PARTY.md) and [NOTICE.md](NOTICE.md) for PyMuPDF licensing, MinerU service boundaries, and design references.
