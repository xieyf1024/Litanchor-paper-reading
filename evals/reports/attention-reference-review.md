# Attention AI-assisted reference review

- Date: 2026-07-23
- Authority for paper claims: original `Attention Is All You Need` PDF
- Auxiliary source: [Bilibili explainer selected by the user](https://www.bilibili.com/opus/1197329452166545431)
- Classification: AI-assisted quality reference; not human gold

## Conclusion

The existing note is substantially more complete and more source-disciplined
than the auxiliary explainer. It covers the research problem, architecture,
scaled dot-product and multi-head attention, masking, positional encoding,
residual/LayerNorm/FFN components, training setup, complexity comparison,
translation results, ablations, constituency parsing transfer, appendix
visualizations, limitations and important internal numeric inconsistencies.
No paper-grounded core topic identified from the explainer was missing.

The useful improvement is presentation rather than factual expansion: embed
original-PDF Figure 1 and Figure 2 beside the key-visual table and add verified
Zotero links. Figure 1 is the architecture overview; Figure 2 explains the
scaled dot-product and multi-head composition.

## Auxiliary-source coverage

The explainer is useful for learner-facing intuition about token
representations, Q/K/V, scaled dot-product attention, multi-head attention,
Add & Norm, feed-forward layers, masking, cross-attention and the
encoder-decoder flow. Those paper-relevant concepts are already represented
in the note.

The following explainer content was not imported into the formal evidence
layer:

- tokenization examples and beginning-of-sequence conventions not established
  by this paper;
- later-model context such as BERT, GPT and DeepSeek;
- the claim that normalization maps values into the interval 0–1;
- the suggestion that representations remain purely linear until the FFN.

The last two are misleading simplifications: LayerNorm is not min-max
normalization, and the attention block already contains a softmax
nonlinearity. External educational context may be added only in a separately
labelled learning section.

## Remaining human-gold work

- Independently annotate a retained subset of claims, rather than accepting
  this note as its own answer key.
- Double-check exact evidence excerpts, physical pages, modality and numeric
  conditions.
- Have a second reviewer adjudicate at least the retained double-annotation
  subset.
