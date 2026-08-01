# Agent-installed setup and intent-based natural-language entry

Use this contract when the user asks to install, configure, diagnose, repair,
upgrade, roll back or run LitAnchor through an Agent.

## Route by meaning, not by a fixed sentence

The examples in this document are illustrative, not literal trigger strings or
commands that users must repeat. Infer the requested operation from the user's
meaning and conversation context. Do not require a literal phrase, exact
keyword order, regular-expression match, one language, or a particular
punctuation pattern.

Equivalent requests include short or conversational variants such as:

- install, set up, configure, repair, update or remove LitAnchor;
- read, analyze, closely read, summarize with evidence or make an Obsidian note
  for one named paper;
- identify the paper by title, DOI, citekey, Zotero Item Key or an unambiguous
  current-paper reference;
- express the Vault before or after the paper, or rely on the already configured
  default Vault.

Resolve one intent among `install`, `configure`, `doctor`, `upgrade`, `repair`,
`rollback`, `uninstall` and `read_one_paper`. Ask only when the intended
operation, paper identity, permission or write target is genuinely ambiguous.
Never infer a different paper or silently expand the configured write scope.

## Installation request

For a request such as:

```text
帮我安装 Skill：https://github.com/xieyf1024/Litanchor-paper-reading
```

the Agent should:

1. Prefer a tagged GitHub Release over a mutable branch archive.
2. Read `litanchor-install.json`, download the Windows ZIP and verify its
   SHA-256 against `SHA256SUMS.txt`.
3. Run `install.ps1 -Action Install` itself to install the lightweight core.
   Do not ask the user to type the
   command, create a virtual environment, run `pip`, copy the Skill or edit
   JSON.
4. Let the installer create only receipt-tracked user-local files and the one
   Agent Skills directory named `litanchor-paper-reading`.
5. Run `litanchor.ps1 doctor`.
6. If setup is incomplete, discover local Obsidian Vaults and ask only for:
   - one default Vault;
   - one child Literature Inbox;
   - one MinerU consent mode.
7. Run `litanchor.ps1 setup`. When the selected consent is not `never`, run
   `install.ps1 -Action Repair -IncludeMinerU` so the conditional SDK is
   installed without changing the Vault configuration.
8. Rerun doctor and report the receipt.

When diagnosis must be shared, run `litanchor.ps1 doctor -SupportBundle` (or
the Python entry point with `doctor --support-bundle`). The generated ZIP is
constructed from an explicit safe-field allowlist. It includes versions,
check statuses, stable error codes, the MinerU route and non-sensitive install
receipt fields; it excludes paper content and identifiers, notes, usernames,
local paths, Vault names, credentials and environment variables. Ask the user
to review the ZIP before attaching it to a public issue.

Pause for the user when Python is missing, an operating-system change or
broader permission is required, more than one Vault matches, or a destination
already contains an unmanaged Skill. Never copy a GitHub token into a
sandbox. Never loosen permissions on the whole Vault.

## Local configuration

The default configuration is:

```text
%LOCALAPPDATA%\LitAnchor\config.json
```

It is local-only and must not be committed. It stores the selected Vault,
authorized root, Inbox, read-only Zotero loopback URL, installed runtime and
MinerU consent. A configured Inbox must be a child of its authorized root,
which must itself remain inside the Vault.

Consent modes are:

- `always_for_eligible_files`: automatically use MinerU for eligible files;
- `ask_each_time`: pause before each external upload;
- `never`: stay local and use PyMuPDF only.

MinerU is an automated conditional structure enhancer, not an authority.
PyMuPDF remains authoritative for physical pages, quotations, coordinates,
Zotero links and final crops.

## Natural-language paper request

For a request such as:

```text
精读《论文标题》，并将笔记保存至 Xyf_Vault。
```

run `scripts/litanchor_setup.py run-plan` first. It must resolve the named
Vault to the already authorized explicit path. A different Vault requires
setup again; do not silently expand write scope.

The user does not need to say “精读” or “保存至” literally. A request that
clearly means “analyze this one paper using LitAnchor and put the resulting
note in my configured Obsidian target” follows the same path.

Then execute the existing autonomous workflow:

```text
one exact Zotero item and one local PDF
→ PyMuPDF physical-page baseline
→ consent-aware MinerU route
→ six reading passes
→ Evidence and Claim ledgers
→ SectionSynthesis and visual selection
→ fidelity and recall review
→ Final template
→ contained no-overwrite Obsidian export
```

Do not ask the user to run intermediate commands or edit ledgers. Interrupt
only for source ambiguity, multiple PDF attachments, missing per-run consent,
an unreadable required page, a quality blocker or a target collision.

After export, verify the note, assets and sidecars by their receipts. Opening
the note through an `obsidian://` link is optional and may require desktop
permission; failure to open the UI must not invalidate a successful export.

## Lifecycle safety

- A repeated install is idempotent.
- Repair changes only receipt-tracked LitAnchor files.
- Upgrade preserves local configuration and retains an immutable version
  archive for rollback.
- Rollback activates only an installed archived version.
- Uninstall requires explicit confirmation, verifies the active Skill hash and
  preserves configuration unless removal is explicitly requested.
- Existing Vault notes and Zotero data are never installation targets.
