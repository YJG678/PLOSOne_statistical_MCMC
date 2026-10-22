#!/usr/bin/env python3
"""Executable Gate-2, tuning, and certification constants for Stage 2."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def binomial_cdf(k: int, n: int, p: float) -> float:
    return sum(math.comb(n, j) * p**j * (1.0 - p) ** (n - j) for j in range(k + 1))


def cp_upper(k: int, n: int, eta: float) -> float:
    if not 0 <= k <= n:
        raise ValueError("k must lie in 0,...,n")
    if not 0.0 < eta < 1.0:
        raise ValueError("eta must lie in (0,1)")
    if k == n:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        # The lower tail decreases with p.  We seek CDF=eta.
        if binomial_cdf(k, n, mid) > eta:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def required_zero_failure_replicates(eta: float, z_max: float) -> int:
    return math.ceil(math.log(eta) / math.log(1.0 - z_max))


def required_tuning_replicates(k_candidates: int, r_components: int,
                               delta: float, epsilon: float) -> int:
    return math.ceil(math.log(2.0 * k_candidates * r_components / delta)
                     / (2.0 * epsilon**2))


def tuning_radius(k_candidates: int, r_components: int,
                  delta: float, replicates: int) -> float:
    return math.sqrt(math.log(2.0 * k_candidates * r_components / delta)
                     / (2.0 * replicates))


def required_certification_replicates(delta: float, beta: float, gap: float) -> int:
    return math.ceil(2.0 * (math.sqrt(math.log(1.0 / delta))
                            + math.sqrt(math.log(1.0 / beta))) ** 2 / gap**2)


def main() -> None:
    delta_adq = 0.010
    z_max = 0.10
    primary_tests = 3 * 4
    tier_a_tests = 3 * 68
    u_0_12 = cp_upper(0, 12, 0.05)
    assert abs(u_0_12 - (1.0 - 0.05 ** (1.0 / 12.0))) < 1e-13

    primary_adq = required_zero_failure_replicates(delta_adq / primary_tests, z_max)
    tier_a_adq = required_zero_failure_replicates(delta_adq / tier_a_tests, z_max)
    assert primary_adq == 68
    assert tier_a_adq == 95

    primary_tuning = required_tuning_replicates(3, 7, 0.010, 0.10)
    tier_a_tuning = required_tuning_replicates(3, 71, 0.010, 0.10)
    assert primary_tuning == 418
    assert tier_a_tuning == 533

    legacy_tier_a_radius = tuning_radius(3, 71, 0.010, 2)
    cert = required_certification_replicates(0.015, 0.20, 0.20)
    assert cert == 551

    output = {
        "status": "PASS",
        "unadjusted_CP_upper_K0_L12_95pct": u_0_12,
        "gate2": {
            "delta": delta_adq,
            "z_max": z_max,
            "primary_tested_pairs": primary_tests,
            "primary_required_replicates_if_K0": primary_adq,
            "tierA_worst_case_tested_pairs": tier_a_tests,
            "tierA_required_replicates_if_K0": tier_a_adq,
        },
        "tuning": {
            "delta": 0.010,
            "uniform_error_target": 0.10,
            "primary_K3_R7_required_per_candidate": primary_tuning,
            "tierA_K3_R71_required_per_candidate": tier_a_tuning,
            "legacy_tierA_m2_radius": legacy_tier_a_radius,
        },
        "certification": {
            "delta": 0.015,
            "power": 0.80,
            "normalized_gap": 0.20,
            "required_paired_replicates": cert,
        },
    }

    (ROOT / "stage2_calibration.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    with (ROOT / "stage2_calibration.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["quantity", "value"])
        writer.writerow(["unadjusted_CP_upper_K0_L12_95pct", u_0_12])
        writer.writerow(["primary_gate2_required_L", primary_adq])
        writer.writerow(["tierA_worst_case_gate2_required_L", tier_a_adq])
        writer.writerow(["primary_tuning_required_per_candidate", primary_tuning])
        writer.writerow(["tierA_tuning_required_per_candidate", tier_a_tuning])
        writer.writerow(["legacy_tierA_m2_uniform_radius", legacy_tier_a_radius])
        writer.writerow(["weighted_certification_required_pairs", cert])
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
