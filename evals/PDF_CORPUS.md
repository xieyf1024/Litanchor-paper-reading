# Local PDF corpus inventory

The following files exist only in the local `Test-PDF/` directory and are excluded from Git. Metadata was inspected read-only on 2026-07-22. SHA-256 identifies the exact local file used for future regression runs.

| Paper | DOI / stable identifier | PDF pages | SHA-256 | Intended stress dimensions |
|---|---|---:|---|---|
| Attention Is All You Need | `10.48550/arXiv.1706.03762` | 15 | `bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697` | two-column order, equations, model architecture, experiment tables |
| Deep Residual Learning for Image Recognition | `10.1109/CVPR.2016.90` | 9 | `51b5de45eb0b558b19c3affe49503cff50cb170a32de602983d6e2ec286942a7` | two-column order, method claims, architecture figures, ablation/results tables |
| Description of the Earth system model of intermediate complexity LOVECLIM version 1.2 | `10.5194/gmd-3-603-2010` | 31 | `c4738e93422406111a9fdb108fb0265d6580d77901654648ca0997d88a11c02d` | long model-description paper, subsystems, parameters, equations, dense figures |
| Increased frequency of multi-year El Niño-Southern Oscillation events across the Holocene | `10.1038/s41561-025-01670-y` | 19 | `71ac517b23241947c5c99170573cf4dcda18a0a125dec159414b8fe5f48da0e5` | proxy/model evidence, time-series figures, uncertainty, recent journal layout |
| Neoproterozoic 'snowball Earth' simulations with a coupled climate/ice-sheet model | `10.1038/35013005` | 5 | `ef443959d2c2d7fc2cef5b32791bbc03f9c3701ed55aa7b3bb9064e46b806f48` | dense Nature layout, coupled-model assumptions, figures, hypothesis/modality fidelity |
| Separation of Internal and Forced Variability of Climate Using a U-Net | `10.1029/2023MS003964` | 20 | `4c31db5f17c7df0e0ae687e4e5ac20e430b0d4b5fedc40ad1ce5550ea45b650a` | machine-learning plus climate domain, architecture, metrics, forced/internal interpretation |

## Known corpus gap

All six current files expose extractable text. The corpus still needs a legally redistributable synthetic or public-domain negative fixture for scanned, encrypted, corrupt or deliberately garbled PDF detection. Do not mislabel a normal paper as that failure case.

