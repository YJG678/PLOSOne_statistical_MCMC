# Stage 5 experiment report

Freeze: `CONTROLLED-BENCHMARK-2026-08-10-v2`  
Execution date: 2026-08-10  
Overall decision: **A passed; B passed after a matched-work rerun.**

## Experiment A — exact two-state metastability

The study used `p in {.5,.1,.01}`, 13 logarithmically spaced values of `n epsilon` from .01 to 100, `L in {4,16,64}`, horizon 200, and 5,000 independent meta-repetitions per configuration (seed 310000001). The Markov-binomial occupation count and terminal state were propagated jointly and sampled exactly. Thus the path average and the complete-path all-zero event are evaluated under the same finite path law without an off-by-one convention.

All 117 configurations passed the theorem check. The largest discrepancy between the simulated and exact all-zero false-precision probability was 3.05 Monte Carlo standard errors. At `L=16`, `p=.01`, the exact all-zero probability decreases from .9984 at `n epsilon=.01`, through .8521 at 1, to approximately `1.08e-7` at 100. In the first two cases every replicate estimate is frequently zero even though its error is .01.

Naive minimum-dispersion selection makes substantial errors in the metastable region. The calibrated transition screen prevents a naive false selection in 71 of 117 settings under the prespecified materiality criterion; for example at `L=16`, `p=.1`, `n epsilon=.01`, naive error is .987 while gated error is zero. Bias, `D(n)`, `R(n)`, MSE, transition-screen pass frequency, all-zero probability, and both decision errors are in `experiment_A/two_state_results.csv`.

## Experiment B — exactly normalized Gaussian mixtures

Three settings jointly vary dimension `(2,5,10)`, separation `(3,5,7)`, minority mixture weight `(.20,.05,.01)`, and within-mode anisotropy `(1,4,9)`. The event boundary is on the second coordinate and is independent of the first-coordinate mode partition. Its probability and all other target quantities are analytic. Each candidate--setting pair has three mutually independent simulation blocks. The risk oracle uses two independent batches of 10,000 paths (20,000 paths total), the protocol-aligned decision stream uses 22,300 paths arranged as 100 disjoint 223-path decisions, and certification uses a further 551 paths. The respective base seeds are 326000001, 325000001, and 327000001. Each decision applies twelve directional tests---mode entry/exit and scientific-event entry/exit for every candidate---with per-test error `1/1200`, familywise error `.01`, and `z_max=.10`.

Work is matched at exactly 3,000 target-density evaluations per path. Local RWM and transport independence use 3,000 sweeps with one target evaluation per sweep; five-rung parallel tempering uses 600 sweeps with five target evaluations per sweep. Swap decisions reuse cached target values. Across the oracle, decision, and certification blocks, every algorithm receives 385,659,000 recorded target evaluations. Recorded candidate-simulation times in the single sequential reference execution were 75.87 seconds for local RWM, 137.37 seconds for transport independence, and 88.02 seconds for parallel tempering. These times include proposal-density and swap overhead but are descriptive machine-specific measurements, not a portable efficiency ordering. The primary comparison is accuracy at matched target-evaluation work.

The candidates are a local random walk, an exact-MH independence proposal with a deliberately underweighted minority component, and five-temperature parallel tempering. The output separately reports mode-region error and event error, along with smooth-mean error, acceptance, a lag-window ESS summary, classical R-hat, transition totals, zero-transition frequencies, and half/full-horizon plateau ratios. These diagnostics are descriptive; R-hat and the plateau screen are not certificates.

The oracle is not estimated from decision data. In every setting both 10,000-path oracle batches select the same candidate as their 20,000-path combination. The smallest best-versus-second gap is 20.11 Monte Carlo standard errors. Transport independence is the independently resolved winner in B1--B3 at the matched target-evaluation budget.

Across 300 independent 223-path decision repetitions, both naive minimum-dispersion selection and the calibrated procedure select transport independence, the independently resolved oracle, in every repetition. The exact 95% upper bound for either false-selection frequency is .0122; the exact lower bound for the correct-selection frequency is .9878. There are no aborts and no oracle exclusions. All three candidates pass Gate 2 in B1--B2; only transport independence passes in B3. Thus Gate 2 remains estimand-specific without excluding the matched-work oracle.

The earlier equal-600-sweep analysis gave parallel tempering five times as many target evaluations as the other candidates. Its 36 naive errors, 16 gated errors, 100 aborts, and 100 oracle exclusions are withdrawn and are not evidence about comparative efficiency. Their disappearance under matched work is itself a negative-control result: a sweep is not a comparable work unit across these kernels.

The frozen distribution-free certification bound certifies none of the three settings: its radius is .1235, while observed improvements over local RWM are much smaller. This negative result is retained. Experiment B therefore demonstrates stable matched-work selection but **not** useful certification power at the frozen minimum-improvement scale.

## Acceptance assessment

| Criterion | Decision |
|---|---|
| Exact benchmark agrees within Monte Carlo uncertainty | Met in all 117 A configurations |
| Protocol prevents at least one naive false selection | Met in 71 A settings; the matched-work B comparison has no false selections to prevent |
| Controlled setting has nontrivial selection or certification power | Selection power met (300/300 correct decisions); certification power not met |
| Independent replicate units and pairing preserved | Met for A and B |
| Negative findings retained | Met: the equal-sweep B ranking is withdrawn and zero B certifications are retained |

The paper uses A as confirmatory theorem validation and B as a controlled
confirmatory benchmark with the stated limitations.  The independent
certification-power experiment is reported and validated separately in
`stage7_outputs/certification/`.
