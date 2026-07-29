# LitAnchor v0.6 roadmap

Status: `v0.6.0-beta.1` release candidate
Target: Agent-assisted setup and public-beta hardening

Implementation checkpoint:

- Phase 0 documentation synchronization: complete;
- Phase 1 machine manifest, user-local installer lifecycle and release builder:
  implemented and clean-profile tested with real dependency installation;
- Phase 2 setup, Vault discovery, run-plan and machine-readable doctor:
  implemented and tested against a real local Zotero API and isolated Obsidian
  test root;
- Phase 3 intent-based Agent entry: implemented; examples are not literal
  trigger strings;
- Phase 4 conditional MinerU route: complete on eligible whole documents,
  original-page-preserving long-document subsets and synthetic service-failure
  fallback;
- Phase 5 local and GitHub-hosted Windows CI validation: complete for Python
  3.10 through 3.14;
- Phase 6 frozen holdout and pathological public-beta gates: complete. Three
  release-eligible holdouts passed; cases that caused fixes or had prior
  exposure were not counted.

## Product outcome

v0.6 should hide the existing engineering steps behind two natural-language
intents. The following sentences are examples, not literal trigger strings:

```text
帮我安装 Skill：https://github.com/xieyf1024/Litanchor-paper-reading
```

```text
精读《论文标题》，并将笔记保存至 <Obsidian Vault 名称>。
```

The intended user already has the baseline in
`INSTALLATION_REQUIREMENTS.md`: a supported Windows system, a local Agent,
Python >=3.10, Zotero >=7, Obsidian and working network access. v0.6 is not an
operating-system bootstrapper. It automates LitAnchor-specific installation,
configuration, diagnosis and execution.

## Success definition

The two-intent flow is successful when:

- the user never has to type `pip`, create a virtual environment, copy the
  Skill, edit JSON or invoke a LitAnchor Python script;
- first-run questions are limited to the Vault, Inbox and MinerU consent;
- the Agent can explain and recover from a partial installation;
- a normal paper request runs from Zotero resolution through reviewed
  Obsidian export without manual ledger editing;
- ambiguous sources, collisions and reliability blockers stop with a specific
  action instead of silently guessing;
- installation, upgrade, rollback and uninstall never alter Zotero data or
  existing Vault notes.

## Phase 0 — documentation synchronization

Deliverables:

- synchronize current documents with the published v0.5.0 state;
- document the exact base environment and dependencies;
- separate the historical v0.2 design record from current specifications;
- keep roadmap decisions out of the operational `SKILL.md`.

Exit check:

- no current product, workflow, integration or release-checklist document
  describes v0.4.1 or v0.5 as an unfinished candidate;
- the active Skill contains only execution and reliability rules.

## Phase 1 — installation contract

Build one small, idempotent installer rather than a second application.

Deliverables:

1. A machine-readable install manifest containing:
   - Skill and release version;
   - supported Python versions;
   - core and conditional requirement files;
   - install, config and runtime path rules;
   - artifact checksums;
   - license and third-party notice locations;
   - supported installer actions.
2. One Windows bootstrap entry point that can:
   - download or consume a Release ZIP;
   - verify the checksum;
   - create a versioned user-local installation and virtual environment;
   - install the Skill into the detected Agent Skills directory;
   - install core dependencies and the user-selected MinerU dependency;
   - write an installation receipt.
3. Idempotent actions for:
   - `install`;
   - `upgrade`;
   - `repair`;
   - `rollback`;
   - `uninstall`.

Verification:

- a repeated install makes no duplicate environments or Skill copies;
- an interrupted install can resume or roll back;
- upgrade preserves local configuration;
- uninstall removes only LitAnchor-owned files.

## Phase 2 — setup and doctor

Provide structured diagnostics that an Agent can call and interpret.

The doctor should check:

- Windows and Python architecture/version;
- `pip`, `venv`, the LitAnchor virtual environment and dependency versions;
- installed Skill version versus runtime version;
- Zotero process and loopback Local API response;
- unique Zotero item/PDF resolution using a harmless diagnostic query or
  fixture;
- Obsidian Vault-name resolution, Inbox containment and write permission;
- Chinese characters, spaces and long paths;
- local config validity and MinerU consent;
- MinerU SDK availability and network reachability when enabled;
- available temporary/runtime space;
- filename collision and no-overwrite behavior.

Every result should be machine-readable and include:

```text
status
check_id
observed
expected
automatic_fix_available
user_action
```

Automatic repair is limited to LitAnchor-owned files and configuration.
Application settings or broader permissions require a user-facing instruction
or approval.

## Phase 3 — natural-language run entry

Keep the existing evidence-first pipeline and add a thin Agent-facing entry
contract:

```text
resolve Vault name and allowed Inbox
→ resolve one Zotero item and one local PDF
→ PyMuPDF physical-page baseline
→ consent-aware MinerU route
→ six reading passes
→ Evidence and Claim ledgers
→ SectionSynthesis and visual selection
→ fidelity and recall review
→ Final template
→ contained, non-overwriting Obsidian export
→ installation/run receipt
```

The Skill should interrupt only for a source ambiguity, multiple attachments,
an unresolved target collision, consent that has not been granted, an
unreadable required page or a quality blocker.

Verification:

- no facts are manually inserted into `evidence.json` or `claims.json`;
- the target Vault is resolved by name to one explicit path;
- all selected images exist and render through Vault-relative links;
- the exported note and sidecars match their validated hashes;
- rerunning the same request cannot overwrite the accepted note.

## Phase 4 — MinerU fusion evidence

MinerU is a conditional automated structure-enhancement stage. PyMuPDF remains
the authority for physical pages, quotations, coordinates, Zotero links and
final image crops.

Test both production routes:

### Eligible whole paper

- PDF at most 10 MiB and 20 pages;
- persistent consent triggers MinerU automatically;
- headings, reading order, captions and complex-element candidates are aligned
  to the PyMuPDF page bundle;
- the run records what the fusion changed.

### Long-paper subset

- PyMuPDF preflight identifies layout-anomalous, formula/table-dense or
  caption-dense pages;
- selected pages retain original physical-page identity;
- each compliant subset is parsed and aligned back to the full paper;
- unaligned blocks remain warnings and never become evidence.

Reliability cases:

- service timeout, rate limit, empty response and network loss;
- invalid or partial output;
- exact, fuzzy and unmatched alignment;
- same-hash cache reuse;
- automatic PyMuPDF-only continuation after MinerU failure.

A/B report:

```text
PyMuPDF only
vs.
PyMuPDF + MinerU fusion
```

Measure section-boundary accuracy, reading-order errors, caption recall,
formula/table candidate recall, alignment rate, runtime and manual corrections.
Fusion is accepted only when it improves at least one target measure without
reducing evidence fidelity.

## Phase 5 — CI and release artifact

Use GitHub-hosted Windows runners as clean LitAnchor environments:

- Windows Server 2022;
- Python 3.10 through 3.14, with newer versions admitted provisionally after
  capability probes;
- a temporary Agent Skills directory;
- a fresh virtual environment and local config;
- a temporary Vault with Chinese characters and spaces;
- a stub loopback Zotero API and synthetic PDFs.

Every pull request should run:

- repository tests;
- official Skill validation;
- Python compilation;
- JSON Schema checks;
- UTF-8 and Markdown-link checks;
- anti-leak and privacy audit;
- install, repeated-install, repair, upgrade, rollback and uninstall tests;
- a synthetic install-to-export integration test.

Each release should publish:

- a versioned ZIP;
- SHA-256 checksum;
- install manifest;
- changelog and release notes;
- license, notice and third-party dependency records.

## Phase 6 — evaluation without external testers

External testers are useful but are not a release prerequisite for this stage.
Use three independent validation surfaces:

### Existing development regression

Treat the existing nine test papers as known development/regression material.
They verify compatibility and prevent old failures from returning; they do not
count as unseen generalization evidence.

### Frozen holdout

Select at least three papers that have not contributed notes, rules, prompts or
paper-specific fixes. Freeze the Skill and rubric before running them. If their
results cause a rule change, move them to the development set and replace them
with new holdouts.

### Pathological fixtures

Use at least five synthetic or redistributable cases covering:

- two-column and cross-column reading order;
- formula/range-symbol corruption;
- dense tables and figure captions;
- scanned or low-text pages;
- long papers and Methods-after-References layouts.

On the developer’s existing Windows system, create a clean LitAnchor profile
with a new virtual environment, temporary config, temporary Skills directory
and temporary Vault. Run one additional live Zotero-to-Obsidian smoke test
after the isolated tests pass.

This validates installation independence without claiming that the whole
Windows machine or user is new. Post-release GitHub Issues can collect real
user experience and failure reports.

## v0.6 release gates

- two-intent flow succeeds without manual commands or ledger edits;
- Python 3.10 through 3.14 CI passes from fresh virtual environments;
- installer lifecycle tests pass and touch only LitAnchor-owned paths;
- Zotero and Obsidian synthetic integration plus one local live smoke pass;
- current regression set has no blocker or severe unsupported claim;
- at least three frozen holdouts pass the published rubric;
- page accuracy is at least 99%, core numeric fidelity at least 99.5%, Final
  template completeness 100% and no-overwrite success 100%;
- MinerU failure falls back safely on every eligible failure fixture;
- anti-leak, privacy, checksum, license and documentation checks pass.

## Version path to v1.0

### `v0.6.0-beta.1`

Publish the installer, doctor, natural-language entry contract, Windows CI,
release artifact and first MinerU A/B report. Invite issue reports without
requiring a private external-user program.

### `v0.6.0-beta.2` when needed

Fix reproducible installation or runtime failures through general rules and
regression tests. Keep paper-specific answers in evaluation artifacts only.

### `v1.0.0-rc1`

Freeze installation, Skill, schemas, templates and evaluation rubric. Run:

- the complete installer lifecycle on both CI Python versions;
- one clean local-profile install and live run;
- all development regressions;
- a fresh three-paper frozen holdout;
- the MinerU whole-paper, long-subset and fallback routes.

### `v1.0.0`

Promote the exact RC commit when two consecutive frozen runs show no critical
regression, the two-intent flow remains intact, release documentation and one
copyright-safe public demonstration are complete, and there is no data loss,
privacy leak or severe unsupported claim.

The public claim should stay precise:

> LitAnchor v1.0 is a Windows-first, Agent-installed Zotero-to-Obsidian
> single-paper deep-reading Skill for users with Python, Zotero, Obsidian and a
> local-capable Agent.

Release readiness is decided by these gates, not by a calendar date or a
required number of private beta testers.
