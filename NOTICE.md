# Notices

LitAnchor uses PyMuPDF for local PDF inspection, rendering, and figure cropping.
PyMuPDF is available under the GNU Affero General Public License v3 or a
separate commercial license from Artifex.

LitAnchor is distributed under GNU AGPL v3 only. Users who cannot comply with
the AGPL should independently assess whether they require an Artifex commercial
license.

MinerU Open SDK is an optional dependency, not part of the default install.
When explicitly enabled for one document, the adapter uploads that PDF to the
external MinerU Flash service only after recorded user consent. It uses no
Token, enforces the current 10 MiB and 20-page limits, and treats MinerU output
as non-authoritative structure candidates. Service availability, limits,
privacy terms, and parsing behavior remain controlled by MinerU.

LitAnchor and its dependencies are provided without warranty. See
`THIRD_PARTY.md` for dependency purposes and design-reference boundaries.
