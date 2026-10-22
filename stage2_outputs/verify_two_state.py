#!/usr/bin/env python3
"""Exact finite-state checks for the Stage-2 non-identifiability theorem."""

from __future__ import annotations

import itertools
import json
import math
from pathlib import Path


OUT = Path(__file__).with_name("two_state_verification.json")


def transition(p: float, eps: float) -> tuple[tuple[float, float], tuple[float, float]]:
    return ((1.0 - eps * p, eps * p),
            (eps * (1.0 - p), 1.0 - eps * (1.0 - p)))


def path_law(p: float, eps: float, n: int) -> dict[tuple[int, ...], float]:
    """Law of (X_0,...,X_n) for X_0=0 by exhaustive enumeration."""
    matrix = transition(p, eps)
    law: dict[tuple[int, ...], float] = {}
    for tail in itertools.product((0, 1), repeat=n):
        path = (0,) + tail
        probability = 1.0
        for x, y in zip(path[:-1], path[1:]):
            probability *= matrix[x][y]
        law[path] = probability
    assert math.isclose(sum(law.values()), 1.0, rel_tol=0.0, abs_tol=1e-14)
    return law


def product_law(law: dict[tuple[int, ...], float], copies: int) -> dict[tuple[tuple[int, ...], ...], float]:
    items = list(law.items())
    result: dict[tuple[tuple[int, ...], ...], float] = {}
    for selected in itertools.product(items, repeat=copies):
        paths = tuple(item[0] for item in selected)
        probability = math.prod(item[1] for item in selected)
        result[paths] = probability
    assert math.isclose(sum(result.values()), 1.0, rel_tol=0.0, abs_tol=1e-13)
    return result


def total_variation(q0: dict, q1: dict) -> float:
    keys = set(q0) | set(q1)
    return 0.5 * sum(abs(q0.get(key, 0.0) - q1.get(key, 0.0)) for key in keys)


def main() -> None:
    p = 0.2
    eps = 0.07
    n = 4
    copies = 3
    matrix = transition(p, eps)
    assert all(math.isclose(sum(row), 1.0, abs_tol=1e-15) for row in matrix)
    detailed_balance_left = (1.0 - p) * matrix[0][1]
    detailed_balance_right = p * matrix[1][0]
    assert math.isclose(detailed_balance_left, detailed_balance_right, abs_tol=1e-15)

    one_law = path_law(p, eps, n)
    zero_path = (0,) * (n + 1)
    enumerated_no_visit = one_law[zero_path] ** copies
    formula_no_visit = (1.0 - eps * p) ** (copies * n)
    assert math.isclose(enumerated_no_visit, formula_no_visit, rel_tol=1e-13)

    alpha = 0.05
    eps_false_precision = min(1.0, (1.0 - (1.0 - alpha) ** (1.0 / (copies * n))) / p)
    false_precision_probability = (1.0 - eps_false_precision * p) ** (copies * n)
    assert false_precision_probability >= 1.0 - alpha - 1e-14

    p0 = 0.25
    p1 = 0.75
    eta = 0.08
    tv_n = 3
    tv_copies = 2
    eps_tv = min(1.0, eta / (tv_copies * tv_n * p1))
    q0 = product_law(path_law(p0, eps_tv, tv_n), tv_copies)
    q1 = product_law(path_law(p1, eps_tv, tv_n), tv_copies)
    tv_exact = total_variation(q0, q1)
    common_atom_bound = 1.0 - (1.0 - eps_tv * p1) ** (tv_copies * tv_n)
    bernoulli_bound = tv_copies * tv_n * eps_tv * p1
    assert tv_exact <= common_atom_bound + 1e-14
    assert common_atom_bound <= bernoulli_bound + 1e-14

    output = {
        "status": "PASS",
        "row_sums": [sum(row) for row in matrix],
        "detailed_balance_residual": abs(detailed_balance_left - detailed_balance_right),
        "no_visit_enumerated": enumerated_no_visit,
        "no_visit_formula": formula_no_visit,
        "false_precision_alpha": alpha,
        "false_precision_epsilon": eps_false_precision,
        "false_precision_probability": false_precision_probability,
        "indistinguishability": {
            "p0": p0,
            "p1": p1,
            "fixed_target_gap": p1 - p0,
            "epsilon": eps_tv,
            "exact_total_variation": tv_exact,
            "common_atom_upper_bound": common_atom_bound,
            "Ln_epsilon_p1_bound": bernoulli_bound,
            "Le_Cam_max_error_lower_bound": 0.5 * (1.0 - tv_exact),
        },
    }
    OUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
