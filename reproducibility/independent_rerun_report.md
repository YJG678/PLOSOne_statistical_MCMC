# Independent clean-rerun record

Run date: 2026-08-10  
Status: **PASS**  
Execution: fresh temporary copy; no stored oracle, decision, or certification
paths reused.

## Scope

The one-command driver reran:

1. the two finite-state theorem-verification scripts;
2. all 117 Experiment-A configurations with 5,000 meta-repetitions each;
3. Experiment B with two independent 10,000-path oracle batches, 100 disjoint
   223-path decisions per setting, and 551 independent certification paths;
4. the Experiment-C certification-power and null studies;
5. all validation scripts and publication figures; and
6. a clean BibTeX/LaTeX manuscript build.

## Results

- Locked environment: PASS.
- Stage-5 validation: PASS.
- Stage-7 validation: PASS.
- Final artifact validation: PASS.
- Manuscript at the time of this independent run: 24 pages and 46 bibliography
  entries.
- Undefined citations/references: none.
- Overfull boxes: none.
- Visible `sqrt` or `qquad` transcription tokens: none.
- Matched target evaluations: 3,000 per candidate path.
- Deterministic scientific outputs: all 14 files bitwise identical to the
  stored reference outputs.

The independent Experiment-B candidate-simulation times were 155.29 seconds
for local RWM, 280.98 seconds for transport independence, and 172.47 seconds
for parallel tempering. Every candidate received 385,659,000 target-density
evaluations across the recorded blocks. These timings are retained as
machine-specific descriptions and are not used as a portable efficiency
ranking.

## Records

- `independent_rerun.log`: complete command output.
- `independent_environment_check.json`: observed software and lock checks.
- `independent_artifact_check.json`: manuscript and validation checks.
- `independent_reproduction_report.json`: machine-readable aggregate status.
- `independent_manuscript.sha256`: checksum of the independently built PDF.
- `reference_deterministic_outputs.sha256` and
  `independent_deterministic_outputs.sha256`: bitwise comparison inputs.
- `independent_work_summary.csv`: independent target-work and timing record.

## Scope-revision addendum

On 2026-09-18 the unexecuted prospective application was removed.  A later
theory-focused reorganization separated the model, theorem statements, and
proofs and corrected Experiment A to propagate the occupation count jointly
with the terminal state.  The revised source was run through the complete
one-command workflow in the active workspace, producing a 24-page manuscript
with 40 cited entries and passing the removed-application and path-law checks.
The subsequent visualization revision added a TikZ theorem map and a
Python-generated theorem landscape, reflowing the current artifact to 26 pages
without changing any scientific claim or benchmark output.
The machine-readable `independent_*` files remain the historical record of the
earlier fresh-copy scientific rerun rather than being relabelled as a new
independent execution.
