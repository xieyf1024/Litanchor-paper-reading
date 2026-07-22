# Controlled evolution

LitAnchor evolution is feedback-driven, layered, evaluation-gated and reversible. It is not self-training and must never rewrite the formal Skill during a reading run.

## Layers

- Routing layer: frontmatter description, trigger boundaries, mode/source recognition and item matching.
- Instruction layer: `SKILL.md`, workflow, quality checks, output contract and failure policy.
- Resource layer: references, assets, schemas, deterministic scripts and evaluation cases.

## Process

1. Record the complete run trajectory and user feedback as evidence.
2. Diagnose the reproducible failure and separate shared rules from personal preferences.
3. Abstract feedback into a general rule; never paste one user's wording directly into `SKILL.md`.
4. Target the correct layer and create an isolated candidate patch.
5. Add a regression case and compare candidate versus current version.
6. Reject regressions, permission expansion, unrelated rules and uncontrolled verbosity.
7. Promote only after retained-set success and maintainer approval; commit, tag and retain rollback instructions.

Create a candidate when the same error appears in two independent cases, one severe reliability/data-safety failure occurs, a supported paper cannot be processed, or the user explicitly asks to generalize a rule. Keep single-paper quirks and personal style preferences in private local configuration.

## Candidate contents

Record candidate ID, base version, feedback/run IDs, target layer, reproducible problem, changed files, patch summary, evaluation before/after, regressions and status.

## Immutable policies

Never automatically change source closure, evidence requirements, export blocking, user-file protection, privacy, credentials, licenses, permission scope or release authority.

## Compaction

Before a minor release, or when rules duplicate/conflict or `SKILL.md` grows materially, merge redundant rules, move domain details into references, convert deterministic checks into code and remove prose already enforced by schemas. Preserve behavior with regression tests.
