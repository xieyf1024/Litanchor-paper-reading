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
| Zotero | Zotero >=7 Desktop, optional | Supplies metadata and the local PDF for the integrated route |
| Zotero setting | Local application communication enabled, optional | Opens the loopback-only API for the integrated route |
| Paper source | One user-supplied local PDF or one Zotero item with a local PDF attachment | LitAnchor reads the original paper, not a retrieval summary |
| Obsidian | Obsidian Desktop 1.x with a local Vault, optional | Receives the integrated-route note, images and audit sidecars |
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
| `PyMuPDF` | `>=1.26` | PDF preflight, authoritative physical pages, text, coordinates, page rendering, subsets and figure crops |

All other imports used by the bundled scripts are from the Python standard
library.

LitAnchor intentionally does not depend on `pypdf`: both the manual and
autonomous paths use the same PyMuPDF physical-page baseline. The three
requirements files are not duplicates and should not be collapsed:

- `requirements.txt` keeps the default local runtime minimal;
- `requirements-mineru.txt` is installed only after MinerU is enabled;
- `requirements-dev.txt` is only for validation and release work.

They declare minimum versions without artificial upper bounds. Newer versions
are accepted only after CI or local capability probes complete; “installable”
does not silently mean “release-certified”.

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
| `mineru-open-sdk` | `>=0.2.5` | Flash structure, reading-order, heading and figure-caption candidates |

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

The direct PDF-to-Markdown route needs no Zotero or Obsidian setup. For the
integrated route, the Agent should need only these choices:

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

A later one-paper reading intent may be expressed as either:

```text
精读《论文标题》，并将笔记保存至 <Obsidian Vault 名称>。
```

```text
精读这篇 PDF，并生成 Markdown 笔记。
```

The `v1.0.0-rc1` release implements the manifest, user-local installer, setup,
doctor and run-plan contracts. Isolated-profile lifecycle checks, frozen
generalization checks and final user note review are complete. Public RC
feedback remains before the stable `v1.0.0` release. See `ROADMAP.md`.

For a shareable diagnostic, the Agent can run `litanchor.ps1 doctor
-SupportBundle`. The ZIP is allowlist-built and contains versions, check
statuses, stable error codes, MinerU routing and non-sensitive receipt fields.
It never copies the raw local configuration or doctor report and excludes
paper data, identifiers, notes, usernames, paths, Vault names and credentials.
