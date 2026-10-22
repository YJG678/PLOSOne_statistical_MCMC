# Reproducing the manuscript

The archive contains the complete source, locked environment description,
simulation scripts, validation scripts, generated summaries, figures, and
manuscript build files.

## One command

From the archive root, run:

```bash
chmod +x reproduce.sh
./reproduce.sh
```

The reference run takes approximately 15--20 minutes on the locked reference
container. It reruns the finite-state
checks, Experiments A--C, the matched-work Gaussian-mixture benchmark, every
validation check, all figures, and the manuscript build. The command fails if
the exact software lock is not satisfied, a validation fails, the manuscript
does not have 26 pages and 40 bibliography entries, removed-application text
reappears, a transcription token is visible, a citation or cross-reference is
unresolved, or an overfull box is present.

## Environment

- `reproducibility/environment.lock.json` records the operating system,
  Python, TeX, Poppler, and archive-tool versions.
- `reproducibility/requirements-lock.txt` pins every direct and transitive
  Python dependency used by the computations and figures.
- `reproducibility/environment_check.py` verifies the lock before any
  confirmatory computation begins.

The reference environment uses Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0,
Matplotlib 3.10.8, latexmk 4.83, and pdfTeX 1.40.25.

## Outputs and nondeterminism

The scientific CSV and JSON files listed in
`reproducibility/deterministic_outputs.txt` are required to reproduce bitwise.
Their hashes are written to `reproducibility/deterministic_outputs.sha256`.
This list includes the parameters and plotted numerical values for the
three-panel theorem landscape in `stage8_outputs/theory_landscapes.json`.
Target-evaluation counts are deterministic. Wall times in
`work_accounting.csv` and `work_summary.csv` are deliberately excluded from
bitwise comparison because they are machine-dependent; they must remain
positive and the validation checks their work identities.

`reproducibility/reproduction_report.json` is the final machine-readable status
record. `reproducibility/reproduction.log` is the full one-command log, and
`stage6_manuscript/final_compilation.log` is the final LaTeX-pass log.

The distributed archive also contains the completed independent reference run
as `reproducibility/independent_rerun_report.md` and its associated log, JSON
checks, deterministic-output hashes, and separate wall-time summary.
