# Notices

Copyright (C) 2026 LitAnchor contributors.

LitAnchor is distributed under `AGPL-3.0-only`; the unmodified canonical license
text is in `LICENSE`. The license text is not tied to a LitAnchor release number
and must not be rewritten during routine version updates.

PyMuPDF is the sole core PDF runtime dependency. It provides local PDF
preflight, physical-page text and coordinates, page rendering, figure crops,
page-preserving subsets, and final evidence verification. PyMuPDF is available
under GNU Affero General Public License v3 or a separate commercial license
from Artifex. Users who cannot comply with the AGPL should independently assess
whether they require an Artifex commercial license.

MinerU Open SDK is an optional dependency, not part of the default install.
Under the locally stored consent policy, an eligible PDF or page-preserving
subset may be uploaded to the external MinerU Flash service. LitAnchor uses no
MinerU token, enforces the current 10 MiB and 20-page request limits, and treats
all MinerU output as non-authoritative structure candidates. Service
availability, limits, privacy terms, and parsing behavior remain controlled by
MinerU.

Dependency files use minimum-only version constraints. Newer releases are
accepted through capability probes and CI rather than assumed compatible.
Core, optional MinerU, and development requirements remain separate so a local
installation does not pull cloud or maintainer-only dependencies unnecessarily.

LitAnchor and its dependencies are provided without warranty. See
`THIRD_PARTY.md` for dependency purposes and design-reference boundaries.
