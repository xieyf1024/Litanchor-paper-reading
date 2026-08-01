# Installation requirements

This document separates the environment a user must already have from the
dependencies that the LitAnchor installer or Agent should manage.

## Required user environment

Before asking an Agent to install LitAnchor, the user should have:

| Requirement | Supported baseline | Why it is needed |
|---|---|---|
| Operating system | Windows 10/11 x64 | The current scripts, paths and validation are Windows-first |
| Local Agent | Codex Desktop/CLI or an equivalent Agent with local Shell, filesystem and network access | Installation, Zotero access and Vault export require local execution |
| Shell | Windows PowerShell 5.1 or PowerShell 7 | Runs the current Windows commands and the planned bootstrap entry point |
| Python | CPython >=3.10 x64 with `pip` and `venv` | PyMuPDF and the optional MinerU SDK currently require Python 3.10 or newer |
| Zotero | Zotero >=7 Desktop | Supplies metadata and the local PDF through the Local API |
| Zotero setting | “Allow other applications on this computer to communicate with Zotero” enabled | Opens the loopback-only Local API |
| Paper attachment | One locally available PDF attachment on the target Zotero item | LitAnchor reads the original paper, not a retrieval summary |
| Obsidian | Obsidian Desktop 1.x with a local filesystem Vault | Receives the Markdown note, images and audit sidecars |
| Network | Access to GitHub and the Python package index | Downloads the release and Python packages |
| Permissions | User-level write access to the LitAnchor install directory and one chosen Vault subdirectory | Creates the environment, configuration, note and sidecars |

The public repository can be downloaded without a GitHub token. `git` and
GitHub CLI are useful for development or source-based installation, but they
are not runtime requirements for a Release ZIP installation.

LitAnchor uses minimum versions instead of fixed-version lockout:

- Python 3.10 is the floor. The current release CI verifies 3.10 through 3.14.
  A newer Python is not rejected solely because it is new; doctor reports it as
  provisional and probes `venv`, `pip` and installed dependencies.
- Zotero 7 is the floor. There is no configured maximum. A newer major version
  is treated as provisional until the Local API version, read-only health,
  unique item match and local PDF-resolution probes pass.
- “Provisional” means the local run may continue when all capability probes
  pass; it does not mean an untested version is silently advertised as
  release-certified.

## Python dependencies

### Core

Installed from `requirements.txt`:

| Package | Version range | Role |
|---|---:|---|
| `pypdf` | `>=6.0,<7.0` | Native-text PDF preflight and the manual local path |
| `PyMuPDF` | `>=1.26,<2.0` | Authoritative physical pages, coordinates, page rendering and figure crops |

All other imports used by the bundled scripts are from the Python standard
library.

### Development and release validation

The repository test suite uses Python’s standard-library `unittest`. The
official Skill validator additionally imports `PyYAML`; v0.6 pins it in
`requirements-dev.txt` rather than adding it to the runtime environment. Git
and GitHub CLI are release-maintainer tools, not LitAnchor runtime
dependencies.

### Conditional MinerU enhancement

Installed from `requirements-mineru.txt` when the user enables MinerU:

| Package | Version range | Role |
|---|---:|---|
| `mineru-open-sdk` | `>=0.2.5,<0.3` | Flash structure, reading-order, heading and figure-caption candidates |

MinerU Flash requires network access and explicit local consent. The current
whole-file route checks the service limit of at most 10 MiB and 20 pages; long
papers use page-preserving subsets selected from the PyMuPDF baseline. MinerU
output must align back to an original physical page before it can assist the
formal workflow.

## Local files and configuration

The installation and runtime need these user-local locations:

| Location | Purpose |
|---|---|
| Agent Skills directory, for example `%CODEX_HOME%\skills\litanchor-paper-reading` | Installed Skill package |
| A dedicated Python virtual environment | Isolates LitAnchor dependencies |
| `%LOCALAPPDATA%\LitAnchor\config.json` | Vault choices, install paths and MinerU consent |
| A user-selected Obsidian Vault subdirectory | Markdown note, selected images and `.litanchor` sidecars |
| A private runtime directory | Page bundles, ledgers, reviews and receipts |

Configuration, user papers, Zotero identifiers, generated notes and runtime
ledgers stay local and are not committed to the public repository.

## First-run choices

The Agent should need only these choices:

1. the default Obsidian Vault;
2. the Literature Inbox or another allowed child directory;
3. the MinerU consent mode: `always_for_eligible_files`, `ask_each_time`, or
   `never`.

Ambiguous Zotero matches, multiple PDF attachments, an existing target note,
an upload requiring confirmation, or a quality blocker may require an
additional decision during a run.

## v0.6 installation experience

The product contract is based on two intents, not two hard-coded sentences.
For example, an installation intent may be expressed as:

```text
帮我安装 Skill：https://github.com/xieyf1024/Litanchor-paper-reading
```

The Agent should then download a versioned Release artifact, verify its
checksum, create the virtual environment, install the core and selected
conditional dependencies, install the Skill, run diagnostics, collect the
three first-run choices and return an installation receipt.

A later one-paper reading intent may be expressed as:

```text
精读《论文标题》，并将笔记保存至 <Obsidian Vault 名称>。
```

The published `v0.6.0-beta.1` implements the manifest, user-local installer,
setup, doctor and run-plan contracts. Clean-profile repetition, frozen
generalization checks and public feedback remain before the stable v1.0
release. See `ROADMAP.md`.
