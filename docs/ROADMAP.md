# Roadmap to a stable public release

Current version: `v0.6.0-beta.2 Zero-Config Public Beta`.

The next milestone is not a larger feature set. It is a stable, understandable and recoverable two-intent experience for users running a local-capable Agent on Windows:

```text
install LitAnchor from its GitHub repository
→ deep-read one Zotero paper into a named Obsidian Vault
```

The example wording is not a fixed command contract. Routing must recognize equivalent installation and single-paper reading requests.

## Stable-release priorities

### P0 — clean-environment installation

- Run install, doctor, setup, upgrade, rollback and uninstall in at least three clean Windows environments.
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

## Stable release gates

LitAnchor can move to `v1.0.0-rc1` when all of the following are true:

- clean-environment two-intent flow passes in three Windows profiles;
- repository tests, Skill validation, compilation, Markdown links, privacy and anti-leak audits pass in CI;
- severe unsupported claims, data overwrite and privacy leakage are zero;
- physical-page accuracy is at least 99% and core numeric errors are zero;
- supported-path end-to-end success is at least 90%;
- MinerU failure falls back without corrupting authoritative evidence;
- upgrade, rollback and uninstall affect only receipt-owned LitAnchor files;
- documentation clearly distinguishes supported, warning, partial and blocked outcomes.

After `v1.0.0-rc1`, run one final source-closed smoke test without changing the frozen rules. A clean result permits the stable `v1.0.0` release. External beta users are valuable but not a hard dependency; clean profiles, frozen holdouts and public issue feedback provide the fallback validation path.

## Deferred beyond v1.0

- Zotero write-back or bidirectional synchronization;
- batch processing and multi-paper literature reviews;
- knowledge graphs and automatic Vault-wide linking;
- paid MinerU APIs;
- unattended modification or publication of the formal Skill;
- support claims for browser-only agents without local filesystem and Shell access.
