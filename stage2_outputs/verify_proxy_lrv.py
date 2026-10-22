#!/usr/bin/env python3
"""Exact checks for rare-mode proxy formulas and the stationary LRV envelope."""

from __future__ import annotations

import json
import math
from pathlib import Path


OUT = Path(__file__).with_name("proxy_lrv_verification.json")


def rare_mode_values(p: float, w: float) -> dict[str, float]:
    lam = 1.0 - w / p
    variance = p * (1.0 - p)
    acceptance = 1.0 - p + w
    lrv = variance * (2.0 * p / w - 1.0)
    lrv_from_eigenvalue = variance * (1.0 + lam) / (1.0 - lam)
    reverse_kl = ((1.0 - w) * math.log((1.0 - w) / (1.0 - p))
                  + w * math.log(w / p))
    return {
        "lambda": lam,
        "acceptance": acceptance,
        "lrv": lrv,
        "lrv_from_eigenvalue": lrv_from_eigenvalue,
        "reverse_kl": reverse_kl,
        "relative_lrv": lrv / variance,
    }


def finite_dispersion(variance: float, rho: float, n: int) -> float:
    return variance + 2.0 * sum((1.0 - k / n) * variance * rho**k for k in range(1, n))


def main() -> None:
    p = 0.04
    w = 0.0003
    values = rare_mode_values(p, w)
    assert math.isclose(values["lrv"], values["lrv_from_eigenvalue"], rel_tol=1e-13)

    joint_limits = []
    for exponent in range(1, 7):
        pj = 10.0 ** (-exponent)
        wj = pj**3
        current = rare_mode_values(pj, wj)
        joint_limits.append({"p": pj, "w": wj, **current})
    assert joint_limits[-1]["acceptance"] > 0.99999
    assert joint_limits[-1]["reverse_kl"] < 2e-6
    assert joint_limits[-1]["lrv"] > 1e5

    variance = 0.7
    rho = 0.83
    n = 75
    exact_d = finite_dispersion(variance, rho, n)
    exact_sigma = variance * (1.0 + rho) / (1.0 - rho)
    exact_error = abs(exact_d - exact_sigma)
    theorem_bound = 2.0 * variance * (
        rho / (n * (1.0 - rho) ** 2) + rho**n / (1.0 - rho)
    )
    assert exact_error <= theorem_bound + 1e-13

    output = {
        "status": "PASS",
        "rare_mode_fixed_case": {"p": p, "w": w, **values},
        "joint_limit_sequence_w_equals_p_cubed": joint_limits,
        "lrv_envelope_check": {
            "C": variance,
            "rho": rho,
            "n": n,
            "D_n": exact_d,
            "sigma_squared": exact_sigma,
            "absolute_error": exact_error,
            "theorem_upper_bound": theorem_bound,
        },
    }
    OUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
