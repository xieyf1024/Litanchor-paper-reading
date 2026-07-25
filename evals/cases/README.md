# Evaluation cases

Add small JSON case manifests here after the manual-PDF pipeline exists. Use synthetic text for deterministic failure cases and reference local papers by SHA-256 rather than committing the PDFs.

Required case fields: `case_id`, `paper_sha256`, `reading_mode`, `expected_preflight_status`, `expected_issues`, `gold_path`, and `split`.

`v0.5-blind-corpus.json` freezes the three v0.5 blind-test inputs. It records
only Zotero metadata and PDF fingerprints. Do not add reference notes,
pre-filled EvidenceUnits, pre-filled ClaimRecords, expected paper types, or
answer keys to this suite before the blind run is complete.
