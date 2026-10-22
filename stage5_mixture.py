#!/usr/bin/env python3
"""Experiment B: controlled Gaussian mixtures with a disjoint risk oracle.

The oracle, adequacy/decision, and certification streams are independent.
Each oracle is estimated from two independent 10,000-path batches; a setting
is declared oracle-resolved only when both batches and the combined estimate
select the same candidate and the combined best--second gap exceeds five
Monte Carlo standard errors.  Each decision applies the manuscript's frozen
Gate-2 design: 223 replicate paths, twelve directional candidate--event tests,
per-test error 1/1200, familywise error .01, and z_max=.10.
"""
from __future__ import annotations

import csv
import json
import math
import os
import platform
import time
from pathlib import Path

import numpy as np
from scipy.special import logsumexp
from scipy.stats import beta as beta_dist, norm

OUT = Path("stage5_outputs/experiment_B")
OUT.mkdir(parents=True, exist_ok=True)

TARGET_EVALUATIONS_PER_PATH = 3_000
SWEEPS = {
    "local_RWM": 3_000,
    "transport_independence": 3_000,
    "parallel_tempering": 600,
}
TARGET_EVALUATIONS_PER_SWEEP = {
    "local_RWM": 1,
    "transport_independence": 1,
    "parallel_tempering": 5,
}
L = 223
DECISION_REPETITIONS = 100
DECISION_PATHS = L * DECISION_REPETITIONS
ORACLE_BATCH_PATHS = 10_000
ORACLE_BATCHES = 2
CERTIFICATION_PATHS = 551

ORACLE_SEED = 326_000_001
DECISION_SEED = 325_000_001
CERTIFICATION_SEED = 327_000_001

SETTINGS = [
    ("B1", 2, 3.0, 0.20, 1.0),
    ("B2", 5, 5.0, 0.05, 4.0),
    ("B3", 10, 7.0, 0.01, 9.0),
]
ALGORITHMS = ["local_RWM", "transport_independence", "parallel_tempering"]


def make_rng(base_seed: int, setting_index: int, algorithm_index: int, batch: int = 0):
    return np.random.default_rng(
        np.random.SeedSequence([base_seed, setting_index, algorithm_index, batch])
    )


def cp_upper(k: int, sample_size: int, eta: float) -> float:
    return 1.0 if k == sample_size else float(
        beta_dist.ppf(1 - eta, k + 1, sample_size - k)
    )


def exact_binomial_interval(k: int, sample_size: int, alpha: float = 0.05):
    lo = 0.0 if k == 0 else float(beta_dist.ppf(alpha / 2, k, sample_size - k + 1))
    hi = 1.0 if k == sample_size else float(
        beta_dist.ppf(1 - alpha / 2, k + 1, sample_size - k)
    )
    return lo, hi


def logmix(x, p, separation, anisotropy):
    d = x.shape[-1]
    variances = np.ones(d)
    variances[-1] = anisotropy
    logdet = np.log(variances).sum()
    mean0 = np.zeros(d)
    mean0[0] = -separation / 2
    mean1 = -mean0
    a = np.log1p(-p) - 0.5 * (
        d * np.log(2 * np.pi) + logdet + ((x - mean0) ** 2 / variances).sum(-1)
    )
    b = np.log(p) - 0.5 * (
        d * np.log(2 * np.pi) + logdet + ((x - mean1) ** 2 / variances).sum(-1)
    )
    return np.logaddexp(a, b)


def sample_mix(rng, sample_size, d, weight, separation, anisotropy):
    component = rng.random(sample_size) < weight
    x = rng.normal(size=(sample_size, d))
    x[:, -1] *= math.sqrt(anisotropy)
    x[:, 0] += np.where(component, separation / 2, -separation / 2)
    return x


def run(setting, algorithm, sample_size, rng):
    """Return complete traces for one independently seeded simulation block."""
    _, d, separation, p, anisotropy = setting
    horizon = SWEEPS[algorithm]
    x = sample_mix(rng, sample_size, d, 0.0, separation, anisotropy)
    logp = logmix(x, p, separation, anisotropy)
    mode = np.empty((sample_size, horizon), np.uint8)
    event = np.empty((sample_size, horizon), np.uint8)
    smooth = np.empty((sample_size, horizon), np.float32)
    accepted = 0
    swaps = 0

    if algorithm == "parallel_tempering":
        inverse_temperatures = np.array([1.0, 0.55, 0.30, 0.16, 0.08])
        X = np.repeat(x[:, None, :], len(inverse_temperatures), axis=1)
        LP = np.repeat(logp[:, None], len(inverse_temperatures), axis=1)

    for t in range(horizon):
        if algorithm == "local_RWM":
            proposal = x + rng.normal(scale=0.8, size=x.shape)
            proposal_logp = logmix(proposal, p, separation, anisotropy)
            accept = np.log(rng.random(sample_size)) < proposal_logp - logp
            x[accept] = proposal[accept]
            logp[accept] = proposal_logp[accept]
            accepted += int(accept.sum())
        elif algorithm == "transport_independence":
            weight = max(0.002, p / 5)
            proposal = sample_mix(
                rng, sample_size, d, weight, separation, anisotropy
            )
            proposal_logp = logmix(proposal, p, separation, anisotropy)
            logq_proposal = logmix(proposal, weight, separation, anisotropy)
            logq_current = logmix(x, weight, separation, anisotropy)
            accept = np.log(rng.random(sample_size)) < (
                proposal_logp - logp + logq_current - logq_proposal
            )
            x[accept] = proposal[accept]
            logp[accept] = proposal_logp[accept]
            accepted += int(accept.sum())
        else:
            for j, inv_temp in enumerate(inverse_temperatures):
                proposal = X[:, j] + rng.normal(
                    scale=0.8 / math.sqrt(inv_temp), size=(sample_size, d)
                )
                proposal_logp = logmix(proposal, p, separation, anisotropy)
                accept = np.log(rng.random(sample_size)) < inv_temp * (
                    proposal_logp - LP[:, j]
                )
                X[accept, j] = proposal[accept]
                LP[accept, j] = proposal_logp[accept]
                accepted += int(accept.sum())
            parity = t % 2
            for j in range(parity, len(inverse_temperatures) - 1, 2):
                log_accept = (inverse_temperatures[j] - inverse_temperatures[j + 1]) * (
                    LP[:, j + 1] - LP[:, j]
                )
                accept = np.log(rng.random(sample_size)) < log_accept
                swaps += int(accept.sum())
                tmp_x = X[accept, j].copy()
                X[accept, j] = X[accept, j + 1]
                X[accept, j + 1] = tmp_x
                tmp_lp = LP[accept, j].copy()
                LP[accept, j] = LP[accept, j + 1]
                LP[accept, j + 1] = tmp_lp
            x = X[:, 0]
            logp = LP[:, 0]

        mode[:, t] = x[:, 0] > 0
        event[:, t] = x[:, 1] > 0.67448975
        smooth[:, t] = x[:, 1]

    denominator = sample_size * horizon * TARGET_EVALUATIONS_PER_SWEEP[algorithm]
    return mode, event, smooth, accepted / denominator, swaps


def oracle_row(setting, algorithm, losses_by_batch):
    batch_means = [float(losses.mean()) for losses in losses_by_batch]
    losses = np.concatenate(losses_by_batch)
    risk = float(losses.mean())
    mcse = float(losses.std(ddof=1) / math.sqrt(len(losses)))
    z99 = norm.ppf(0.995)
    return {
        "setting": setting[0],
        "algorithm": algorithm,
        "estimand": "mode",
        "oracle_paths": len(losses),
        "batch_paths": len(losses_by_batch[0]),
        "batch_1_risk": batch_means[0],
        "batch_2_risk": batch_means[1],
        "combined_risk": risk,
        "mcse": mcse,
        "ci99_lower": risk - z99 * mcse,
        "ci99_upper": risk + z99 * mcse,
    }


summary_rows = []
oracle_rows = []
oracle_resolution_rows = []
decision_rows = []
gate_rows = []
certification_rows = []
stream_rows = []
work_rows = []


def timed_run(setting, algorithm, sample_size, rng, stream, batch):
    started = time.perf_counter()
    result = run(setting, algorithm, sample_size, rng)
    elapsed = time.perf_counter() - started
    sweeps = SWEEPS[algorithm]
    evaluations_per_sweep = TARGET_EVALUATIONS_PER_SWEEP[algorithm]
    total_evaluations = sample_size * sweeps * evaluations_per_sweep
    work_rows.append(
        {
            "stream": stream,
            "setting": setting[0],
            "algorithm": algorithm,
            "batch": batch,
            "paths": sample_size,
            "sweeps_per_path": sweeps,
            "target_evaluations_per_sweep": evaluations_per_sweep,
            "target_evaluations_per_path": sweeps * evaluations_per_sweep,
            "total_target_evaluations": total_evaluations,
            "elapsed_seconds": elapsed,
            "seconds_per_path": elapsed / sample_size,
            "seconds_per_million_target_evaluations": elapsed * 1_000_000 / total_evaluations,
            "cpu_count": os.cpu_count(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "numpy": np.__version__,
        }
    )
    return result

for setting_index, setting in enumerate(SETTINGS):
    setting_id, d, separation, p, anisotropy = setting
    mode_truth = (1 - p) * norm.sf(separation / 2) + p * norm.cdf(separation / 2)
    event_truth = norm.sf(0.67448975 / math.sqrt(anisotropy))

    # Completely disjoint, duplicated oracle computation.
    setting_oracle = []
    for algorithm_index, algorithm in enumerate(ALGORITHMS):
        losses_by_batch = []
        for batch in range(ORACLE_BATCHES):
            rng = make_rng(ORACLE_SEED, setting_index, algorithm_index, batch)
            mode, _, _, _, _ = timed_run(
                setting, algorithm, ORACLE_BATCH_PATHS, rng, "oracle", batch + 1
            )
            losses_by_batch.append((mode.mean(1) - mode_truth) ** 2)
            stream_rows.append(
                {
                    "stream": "oracle",
                    "setting": setting_id,
                    "algorithm": algorithm,
                    "batch": batch + 1,
                    "base_seed": ORACLE_SEED,
                    "seed_components": f"{ORACLE_SEED}:{setting_index}:{algorithm_index}:{batch}",
                    "paths": ORACLE_BATCH_PATHS,
                    "sweeps_per_path": SWEEPS[algorithm],
                    "target_evaluations_per_path": TARGET_EVALUATIONS_PER_PATH,
                }
            )
        row = oracle_row(setting, algorithm, losses_by_batch)
        oracle_rows.append(row)
        setting_oracle.append(row)

    combined_winner = min(setting_oracle, key=lambda row: row["combined_risk"])
    batch_1_winner = min(setting_oracle, key=lambda row: row["batch_1_risk"])
    batch_2_winner = min(setting_oracle, key=lambda row: row["batch_2_risk"])
    ordered = sorted(setting_oracle, key=lambda row: row["combined_risk"])
    gap = ordered[1]["combined_risk"] - ordered[0]["combined_risk"]
    gap_mcse = math.sqrt(ordered[0]["mcse"] ** 2 + ordered[1]["mcse"] ** 2)
    gap_z = gap / gap_mcse
    resolved = (
        combined_winner["algorithm"]
        == batch_1_winner["algorithm"]
        == batch_2_winner["algorithm"]
        and gap_z >= 5
    )
    oracle_resolution_rows.append(
        {
            "setting": setting_id,
            "combined_winner": combined_winner["algorithm"],
            "batch_1_winner": batch_1_winner["algorithm"],
            "batch_2_winner": batch_2_winner["algorithm"],
            "best_risk": ordered[0]["combined_risk"],
            "second_best": ordered[1]["algorithm"],
            "second_best_risk": ordered[1]["combined_risk"],
            "best_second_gap": gap,
            "gap_mcse": gap_mcse,
            "gap_z_score": gap_z,
            "oracle_resolved": resolved,
        }
    )
    if not resolved:
        raise RuntimeError(f"Independent oracle was not resolved for {setting_id}")
    oracle = combined_winner["algorithm"]

    # Independent repeated-decision stream.
    decision_data = {}
    for algorithm_index, algorithm in enumerate(ALGORITHMS):
        rng = make_rng(DECISION_SEED, setting_index, algorithm_index)
        mode, event, smooth, acceptance, swaps = timed_run(
            setting, algorithm, DECISION_PATHS, rng, "decision", 1
        )
        decision_data[algorithm] = (mode, event, smooth)
        stream_rows.append(
            {
                "stream": "decision",
                "setting": setting_id,
                "algorithm": algorithm,
                "batch": 1,
                "base_seed": DECISION_SEED,
                "seed_components": f"{DECISION_SEED}:{setting_index}:{algorithm_index}:0",
                "paths": DECISION_PATHS,
                "sweeps_per_path": SWEEPS[algorithm],
                "target_evaluations_per_path": TARGET_EVALUATIONS_PER_PATH,
            }
        )
        for estimand, trace, truth in [
            ("mode", mode, mode_truth),
            ("event", event, event_truth),
            ("smooth", smooth, 0.0),
        ]:
            horizon = trace.shape[1]
            means = trace.mean(1)
            bias = float(means.mean() - truth)
            dispersion = float(means.var(ddof=1))
            mse = float(np.mean((means - truth) ** 2))
            if estimand != "smooth":
                transitions = np.abs(np.diff(trace.astype(np.int8), axis=1)).sum(1)
                mean_transitions = float(transitions.mean())
                zero_transition_fraction = float(np.mean(transitions == 0))
            else:
                mean_transitions = ""
                zero_transition_fraction = ""
            centered = trace.astype(float) - truth
            denominator = float(np.mean(centered * centered))
            tau = 1.0
            if denominator > 0:
                for lag in range(1, 51):
                    rho = float(
                        np.mean(centered[:, :-lag] * centered[:, lag:]) / denominator
                    )
                    if rho <= 0:
                        break
                    tau += 2 * rho
            ess = horizon / tau
            within = float(np.mean(trace.var(1, ddof=1)))
            between = float(horizon * means.var(ddof=1))
            varhat = (horizon - 1) / horizon * within + between / horizon
            rhat = math.sqrt(varhat / within) if within > 0 else float("nan")
            half_means = trace[:, : horizon // 2].mean(1)
            d_half = float((horizon // 2) * half_means.var(ddof=1))
            d_full = float(horizon * dispersion)
            plateau_ratio = d_full / d_half if d_half > 0 else float("inf")
            summary_rows.append(
                {
                    "setting": setting_id,
                    "dimension": d,
                    "separation": separation,
                    "minority_probability": p,
                    "anisotropy": anisotropy,
                    "algorithm": algorithm,
                    "sweeps": horizon,
                    "target_evaluations_per_path": TARGET_EVALUATIONS_PER_PATH,
                    "estimand": estimand,
                    "truth": truth,
                    "bias": bias,
                    "absolute_error": abs(bias),
                    "dispersion": dispersion,
                    "mse": mse,
                    "acceptance": acceptance,
                    "ess_per_path": ess,
                    "rhat": rhat,
                    "D_half": d_half,
                    "D_full": d_full,
                    "plateau_ratio": plateau_ratio,
                    "plateau_screen_pass": abs(plateau_ratio - 1) <= 0.25,
                    "mean_transitions": mean_transitions,
                    "zero_transition_fraction": zero_transition_fraction,
                }
            )

    for repetition in range(DECISION_REPETITIONS):
        block = slice(repetition * L, (repetition + 1) * L)
        dispersions = {
            algorithm: decision_data[algorithm][0][block].mean(1).var(ddof=1)
            for algorithm in ALGORITHMS
        }
        naive = min(ALGORITHMS, key=dispersions.get)
        eligible = []
        for algorithm in ALGORITHMS:
            passes = True
            for estimand, trace in zip(("mode", "event"), decision_data[algorithm][:2]):
                previous = trace[block, :-1]
                following = trace[block, 1:]
                for direction, crossed in (
                    ("entry_0_to_1", (previous == 0) & (following == 1)),
                    ("exit_1_to_0", (previous == 1) & (following == 0)),
                ):
                    failures = int(np.sum(~np.any(crossed, axis=1)))
                    upper = cp_upper(failures, L, 1 / 1200)
                    test_passes = upper <= 0.10
                    passes &= test_passes
                    gate_rows.append(
                        {
                            "setting": setting_id,
                            "decision_replicate": repetition,
                            "algorithm": algorithm,
                            "estimand": estimand,
                            "direction": direction,
                            "paths": L,
                            "zero_crossing_paths": failures,
                            "per_test_error": 1 / 1200,
                            "cp_upper": upper,
                            "z_max": 0.10,
                            "passed": test_passes,
                        }
                    )
            if passes:
                eligible.append(algorithm)
        gated = min(eligible, key=lambda algorithm: dispersions[algorithm]) if eligible else "ABORT"
        decision_rows.append(
            {
                "setting": setting_id,
                "decision_replicate": repetition,
                "oracle": oracle,
                "oracle_source": "disjoint_2x10000_path_stream",
                "naive": naive,
                "gated": gated,
                "eligible_count": len(eligible),
                "naive_error": naive != oracle,
                "gated_error": gated != oracle if gated != "ABORT" else "",
                "abort": gated == "ABORT",
                "screening_scope_loss": oracle not in eligible,
            }
        )

    # Independent certification stream, not drawn from either preceding block.
    certification_losses = {}
    for algorithm_index, algorithm in enumerate(ALGORITHMS):
        rng = make_rng(CERTIFICATION_SEED, setting_index, algorithm_index)
        mode, _, _, _, _ = timed_run(
            setting, algorithm, CERTIFICATION_PATHS, rng, "certification", 1
        )
        certification_losses[algorithm] = (mode.mean(1) - mode_truth) ** 2
        stream_rows.append(
            {
                "stream": "certification",
                "setting": setting_id,
                "algorithm": algorithm,
                "batch": 1,
                "base_seed": CERTIFICATION_SEED,
                "seed_components": f"{CERTIFICATION_SEED}:{setting_index}:{algorithm_index}:0",
                "paths": CERTIFICATION_PATHS,
                "sweeps_per_path": SWEEPS[algorithm],
                "target_evaluations_per_path": TARGET_EVALUATIONS_PER_PATH,
            }
        )
    improvement = certification_losses["local_RWM"] - certification_losses[oracle]
    radius = math.sqrt(2 * math.log(1 / 0.015) / len(improvement))
    lower_bound = float(improvement.mean() - radius)
    certification_rows.append(
        {
            "setting": setting_id,
            "challenger": oracle,
            "reference": "local_RWM",
            "replicates": len(improvement),
            "mean_improvement": float(improvement.mean()),
            "hoeffding_radius": radius,
            "lower_bound": lower_bound,
            "certified": lower_bound > 0,
        }
    )


def write_csv(name, rows):
    with (OUT / name).open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


write_csv("oracle_risk.csv", oracle_rows)
write_csv("oracle_resolution.csv", oracle_resolution_rows)
write_csv("estimand_metrics.csv", summary_rows)
write_csv("selection_repetitions.csv", decision_rows)
write_csv("gate2_tests.csv", gate_rows)
write_csv("certification.csv", certification_rows)
write_csv("stream_manifest.csv", stream_rows)
write_csv("work_accounting.csv", work_rows)

work_summary_rows = []
for algorithm in ALGORITHMS:
    rows = [row for row in work_rows if row["algorithm"] == algorithm]
    total_evaluations = sum(row["total_target_evaluations"] for row in rows)
    elapsed = sum(row["elapsed_seconds"] for row in rows)
    work_summary_rows.append(
        {
            "algorithm": algorithm,
            "sweeps_per_path": SWEEPS[algorithm],
            "target_evaluations_per_sweep": TARGET_EVALUATIONS_PER_SWEEP[algorithm],
            "target_evaluations_per_path": TARGET_EVALUATIONS_PER_PATH,
            "offline_training_target_evaluations": 0,
            "recorded_blocks": len(rows),
            "total_recorded_target_evaluations": total_evaluations,
            "total_elapsed_seconds": elapsed,
            "seconds_per_million_target_evaluations": elapsed * 1_000_000 / total_evaluations,
        }
    )
write_csv("work_summary.csv", work_summary_rows)

decision_count = len(decision_rows)
naive_false = sum(row["naive_error"] is True for row in decision_rows)
gated_false = sum(row["gated_error"] is True for row in decision_rows)
aborts = sum(row["abort"] is True for row in decision_rows)
scope_loss = sum(row["screening_scope_loss"] is True for row in decision_rows)
correct = decision_count - gated_false - aborts

summary = {
    "experiment": "B",
    "oracle_seed": ORACLE_SEED,
    "decision_seed": DECISION_SEED,
    "certification_seed": CERTIFICATION_SEED,
    "settings": len(SETTINGS),
    "oracle_batches_per_algorithm_setting": ORACLE_BATCHES,
    "oracle_paths_per_batch": ORACLE_BATCH_PATHS,
    "oracle_paths_per_algorithm_setting": ORACLE_BATCHES * ORACLE_BATCH_PATHS,
    "all_oracles_independently_resolved": all(
        row["oracle_resolved"] for row in oracle_resolution_rows
    ),
    "minimum_oracle_gap_z_score": min(
        row["gap_z_score"] for row in oracle_resolution_rows
    ),
    "decision_paths_per_algorithm_setting": DECISION_PATHS,
    "decision_repetitions_per_setting": DECISION_REPETITIONS,
    "decision_repetitions": decision_count,
    "matched_target_evaluations_per_path": TARGET_EVALUATIONS_PER_PATH,
    "sweeps_per_path": SWEEPS,
    "gate2_tests_per_decision": 12,
    "gate2_paths_per_test": L,
    "gate2_familywise_error": 0.01,
    "gate2_per_test_error": 1 / 1200,
    "gate2_z_max": 0.10,
    "naive_false_selections": naive_false,
    "naive_exact_95_interval": exact_binomial_interval(naive_false, decision_count),
    "gated_false_selections_excluding_aborts": gated_false,
    "gated_false_exact_95_interval": exact_binomial_interval(gated_false, decision_count),
    "protocol_aborts": aborts,
    "abort_exact_95_interval": exact_binomial_interval(aborts, decision_count),
    "correct_operational_selections": correct,
    "correct_exact_95_interval": exact_binomial_interval(correct, decision_count),
    "screening_scope_loss_count": scope_loss,
    "scope_loss_exact_95_interval": exact_binomial_interval(scope_loss, decision_count),
    "certification_paths_per_algorithm_setting": CERTIFICATION_PATHS,
    "certified_settings": sum(row["certified"] is True for row in certification_rows),
    "status": (
        "PASS_MATCHED_WORK_WITH_INDEPENDENT_ORACLE"
        if all(row["oracle_resolved"] for row in oracle_resolution_rows)
        and decision_count == 300
        else "FAIL"
    ),
}
(OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
