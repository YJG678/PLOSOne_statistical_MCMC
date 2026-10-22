# Matched-work Experiment B repair

This archive supersedes the equal-sweep Experiment B comparison.

## Primary work unit

Every candidate receives exactly 3,000 target-density evaluations per path:

| Candidate | Sweeps per path | Target evaluations per sweep | Target evaluations per path |
|---|---:|---:|---:|
| local RWM | 3,000 | 1 | 3,000 |
| transport independence | 3,000 | 1 | 3,000 |
| five-rung parallel tempering | 600 | 5 | 3,000 |

Swap decisions reuse cached target values. Across the two oracle batches, the
decision stream, and the certification stream, each candidate receives
385,659,000 target evaluations. Offline training consumes no target
evaluations in this analytic benchmark.

## Independent streams and result

- Oracle: two disjoint batches of 10,000 paths per candidate and setting.
- Decision: 100 disjoint 223-path units per setting.
- Certification: 551 further paths per candidate and setting.
- The three base seeds are 326000001, 325000001, and 327000001.

Both oracle batches and their combination select transport independence in all
three settings. The smallest combined best--second gap is 20.11 Monte Carlo
standard errors. All 300 matched-work decision units select that oracle; there
are no false selections, aborts, or oracle exclusions, giving an exact
one-sided 95% false-selection bound of `[0, 0.0122]`. These 300 units supersede
the preliminary 60-unit counts and interval `[0.261, 0.518]`.

Within a decision unit, the same 223 paths determine eligibility and empirical
dispersion ranking. The manuscript therefore calls this a benchmark-specific
screen-and-rank rule, not an implementation of its disjoint sample-split
theorem. Likewise, the 551-path block compares an oracle-resolved challenger
and is reported as a power diagnostic rather than an operational deployment
experiment. None of the three settings passes that diagnostic.

The prior equal-600-sweep selection counts are withdrawn because parallel
tempering received five times the target-evaluation work. They must not be
interpreted as an efficiency comparison.

## Wall time

`work_accounting.csv` and `work_summary.csv` report candidate-simulation wall
times and the execution environment. These timings disclose proposal-density
and swap overhead omitted by the target-evaluation metric, but they are
machine-specific descriptions rather than a portable efficiency ranking.

Run `./reproduce.sh` from the archive root to verify the locked environment,
rerun every benchmark and figure, execute the independent-oracle, Gate-2, and
matched-work checks, and rebuild the manuscript. The authoritative manuscript
is `stage6_manuscript/main.pdf`; the clean-rerun record is under
`reproducibility/`.
The same directory contains the independent proof review, line-by-line
response, updated theorem ledger, and fresh-copy reproduction records.
