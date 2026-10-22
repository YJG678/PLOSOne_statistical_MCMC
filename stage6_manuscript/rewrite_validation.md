# Theory and computational statistics revision

Revision date: 2026-09-18

Current paper identity: finite-sample MCMC theory with exact and matched-work
computational benchmarks. Suggested primary target: *Electronic Journal of
Statistics* or a journal with a comparable theoretical-and-computational
statistics remit.

## Journal structure

The manuscript now has the requested seven numbered sections:

1. Introduction;
2. Literature Review;
3. Model;
4. Main Results;
5. Proofs;
6. Conclusion;
7. Appendix.

The model section defines the finite-horizon experiment, metastable families,
crossing events, conditioning sigma-fields, loss functions, and sample splits.
Section 4 contains theorem statements and computational results only. Section
5 gives the proofs in theorem order. Section 7 contains exact recursions,
calibration arithmetic, benchmark construction, stream accounting, and
reproducibility details.

## Mathematical revision

- All load-bearing arguments are written as displayed derivations.
- The reversible two-state invariance, common-path overlap, Le Cam testing
  reduction, rare-mode mode-chain eigenstructure, covariance summation,
  exact-binomial union bound, LRV truncation error, bounded-loss regret,
  certification coverage, power calculation, and workflow error budget are
  derived explicitly.
- Experiment A now propagates the joint law of the occupation count and
  terminal state. The simulated complete-path all-zero event therefore equals
  the theorem event exactly.
- The tuning count is stated from the general formula: 397 replicates for two
  candidates and seven components, and 418 for three candidates. Experiment B
  is not represented as an implementation of that independent tuning theorem.

## Scope and evidence

The unexecuted application has been removed from the submission. The empirical
record is restricted to three executed studies: the exact two-state benchmark,
the matched-work Gaussian-mixture benchmark, and the exact certification-power
benchmark. The mixture study remains explicitly labelled a benchmark-specific
screen-and-rank experiment with an oracle-challenger power diagnostic.

## Visual synthesis

- A native TikZ theorem map links the exact common-path identity to the
  information bound, the rare-mode eigenvalue to proxy failure, and the
  simultaneous screen to regret and certified deployment.
- A reproducible Python three-panel landscape evaluates the exact
  false-precision probability, the rare-mode proxy-separation sequence, and
  the distribution-free certification cost alongside observed power.
- All benchmark figures use a common journal-style visual system with
  colorblind-safe colors, serif typography, vector text, explicit panel
  labels, and restrained annotation.

## Build validation

- Clean `latexmk` build: 26 pages.
- References begin on page 25.
- 40 cited bibliography entries.
- No undefined references or citations.
- No overfull boxes or visible TeX transcription tokens.
- Six figures and four main-text tables.
- All 26 rendered pages visually inspected; no clipping, overlap, broken table,
  or illegible figure was found.

## Submission-stage items

Author metadata, acknowledgments, disclosures, classification codes, keywords,
and conversion to the selected journal class remain to be supplied at
submission.
