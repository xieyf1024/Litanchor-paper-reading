# Roadmap to a stable public release

Current version: `v1.0.0-rc1`.

The frozen content/generalization review is recorded in
[`v1.0.0-rc1-frozen-validation.md`](v1.0.0-rc1-frozen-validation.md). The
RC work is frozen for public feedback; the note template and semantic workflow
stay unchanged unless a release-blocking fidelity, security, privacy or
data-protection defect is found.

The next milestone is not a larger feature set. It is a stable, understandable
and recoverable install-plus-read experience for users running a local-capable
Agent on Windows:

```text
install LitAnchor from its GitHub repository
→ deep-read one local PDF into Markdown
or deep-read one Zotero paper into a named Obsidian Vault
```

The example wording is not a fixed command contract. Routing must recognize equivalent installation and single-paper reading requests.

## Stable-release priorities

### P0 — isolated-environment installation

- Run install, doctor, setup, upgrade, rollback and uninstall in at least three
  isolated Windows application profiles. When independent users or machines
  are unavailable, label same-account profiles accurately and use public RC
  feedback as the independent-usability evidence.
- Cover a normal English path, a Chinese user/Vault path and an interrupted-install recovery path.
- Require no manual `pip`, JSON editing, Skill copying or intermediate-ledger repair from the user.
- Keep Python at `>=3.10` and Zotero at `>=7`; probe newer untested versions instead of imposing arbitrary maximum versions.

### P0 — end-to-end reliability

- Resolve one Zotero item and one local PDF without silently accepting ambiguous matches.
- Preserve PyMuPDF physical pages as the evidence authority.
- Automatically invoke MinerU for eligible files only under stored consent, and fall back safely on timeout, rate limit, empty output or network failure.
- Prove non-overwriting, path-contained Obsidian export and rollback behavior.

### P0 — frozen generalization checks

- Freeze the Skill, schemas, prompts and rubric before running new holdouts.
- Use at least three papers that were not used to shape the current rules.
- Do not expose reference notes or manually prefill Evidence/Claim records.
- If a holdout causes a workflow change, move it to development and replace it before making a final generalization claim.

### P1 — public usability

- Keep the repository homepage task-oriented and bilingual.
- Maintain issue forms that prevent accidental uploads of copyrighted PDFs, private notes or credentials.
- Turn recurring public failures into reproducible, paper-independent tests and controlled EvolutionCandidates.
- Publish a copyright-safe demonstration artifact when one is available.

## RC qualification evidence

`v1.0.0-rc1` was qualified against the following gates:

- isolated install/read lifecycle passes in three Windows application profiles,
  including one real core-dependency installation;
- repository tests, Skill validation, compilation, Markdown links, privacy and anti-leak audits pass in CI;
- severe unsupported claims, data overwrite and privacy leakage are zero;
- physical-page accuracy is at least 99% and core numeric errors are zero;
- supported-path end-to-end success is at least 90%;
- MinerU failure falls back without corrupting authoritative evidence;
- upgrade, rollback and uninstall affect only receipt-owned LitAnchor files;
- documentation clearly distinguishes supported, warning, partial and blocked outcomes.

The final unseen paper exposed captions separated from their figure plates.
The generic cropper now supports an explicitly verified caption-page and
plate-page binding, while keeping crop provenance, page identity and the same
quality gate. Ambiguous bindings remain blocked instead of being silently
accepted.

During the RC period, accept only release-blocking fidelity, security, privacy,
data-protection and supported-path installation fixes. Before stable `v1.0.0`,
freeze the exact candidate and run one final source-closed smoke test without
changing the rules. A clean result permits the stable release. Independent
users are valuable but not a hard dependency; isolated profiles, frozen
holdouts and public RC issue feedback provide the fallback validation path.

## Deferred beyond v1.0

- Zotero write-back or bidirectional synchronization;
- batch processing and multi-paper literature reviews;
- knowledge graphs and automatic Vault-wide linking;
- paid MinerU APIs;
- unattended modification or publication of the formal Skill;
- support claims for browser-only agents without local filesystem and Shell access.
