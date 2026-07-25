# Six-paper Zotero resolution

- Date: 2026-07-23
- Access: Zotero Local API, loopback-only, read-only
- Collections searched: `[AI]`, `[XMU]` and the `[XMU]` child collection
  containing the test paper
- Zotero writes: 0
- PDF modifications: 0

| Collection | First author | Paper | Pages | Corpus hash match |
|---|---|---|---:|---|
| `[AI]` | Ashish Vaswani | Attention Is All You Need | 15 | yes |
| `[AI]` | Kaiming He | Deep Residual Learning for Image Recognition | 9 | yes |
| `[XMU]` child | H. Goosse | Description of the Earth system model of intermediate complexity LOVECLIM version 1.2 | 31 | yes |
| `[XMU]` | Zhengyao Lu | Increased frequency of multi-year El Niño–Southern Oscillation events across the Holocene | 19 | yes |
| `[XMU]` child | William T. Hyde | Neoproterozoic 'snowball Earth' simulations with a coupled climate/ice-sheet model | 5 | yes |
| `[XMU]` child | Constantin Bône | Separation of Internal and Forced Variability of Climate Using a U-Net | 20 | yes |

Each resolved local attachment SHA-256 equals the corresponding value in
`evals/PDF_CORPUS.md`. The ENSO and U-Net titles required punctuation-free
query retries because Zotero tokenization did not return the exact title for
the original Unicode punctuation. Final acceptance still required an exact
normalized title, so the fallback did not become fuzzy matching.

Private Zotero Item Keys, Attachment Keys and local storage paths are excluded
from this public report. They are recorded only in the authorized private
Obsidian link manifest.
