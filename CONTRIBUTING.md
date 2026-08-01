# Contributing to LitAnchor

Thanks for helping improve LitAnchor. Contributions should strengthen a reusable, paper-independent workflow rather than encode answers from a particular test paper.

## Before opening an issue

- Search existing issues and the current [roadmap](docs/ROADMAP.md).
- Run `./litanchor.ps1 doctor` when the problem concerns installation, Zotero, MinerU or Obsidian.
- Remove paper text, private annotations, local paths, usernames, API keys and Vault contents from logs.
- Do not upload copyrighted paper PDFs unless you have the right to redistribute them.

## Development setup

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt -r requirements-dev.txt
$env:PYTHONUTF8 = "1"
.\.venv\Scripts\python -m unittest discover -s tests -v
.\.venv\Scripts\python tools\validate_skill.py
.\.venv\Scripts\python tools\audit_release.py
.\.venv\Scripts\python tools\check_markdown_links.py
```

Use `requirements-mineru.txt` only when a test explicitly needs the optional MinerU SDK.

## Pull requests

- Keep changes focused and explain the user-visible outcome.
- Add a regression test for behavioral fixes.
- Preserve the Evidence → Claim → SectionSynthesis boundary.
- Keep PyMuPDF authoritative for physical pages, quotations and visual provenance.
- Do not weaken no-overwrite, path containment, consent, fidelity or recall gates.
- Do not add paper titles, DOI values, answers, figure numbers or paper-specific branches to the distributable Skill.
- Put deterministic behavior in scripts, schemas or tests; keep `SKILL.md` concise.
- Update public documentation only when behavior or supported scope changes.

## Evaluation data

Public evaluation manifests should contain only the minimum metadata needed to reproduce the test boundary. PDFs, generated notes, Evidence/Claim ledgers and private user feedback remain local unless redistribution is explicitly permitted.

Development cases may guide fixes. Frozen holdouts must not be inspected or used to change rules before their release decision. Once a holdout drives a change, reclassify it as development data.

## Security and privacy

Do not include secrets or private research material in a public issue. For a suspected credential, path-containment, overwrite or unintended-upload vulnerability, open a minimal redacted report and clearly mark it as a security/privacy concern.
