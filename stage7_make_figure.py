#!/usr/bin/env python3
"""Publication figure for the independent certification experiment."""

import csv
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


NAVY = "#174A73"
TEAL = "#16827A"
ORANGE = "#D2693C"
SLATE = "#59636E"

mpl.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["DejaVu Serif"],
        "mathtext.fontset": "dejavuserif",
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.titleweight": "semibold",
        "axes.labelsize": 9,
        "legend.fontsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.7,
        "savefig.bbox": "tight",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)

rows = list(csv.DictReader(open("stage7_outputs/certification/certification_power.csv")))
rows.sort(key=lambda row: float(row["true_improvement"]))
x = np.array([float(r["true_improvement"]) for r in rows])
y = np.array([float(r["certification_power"]) for r in rows])
lo = np.array([float(r["ci95_lower"]) for r in rows])
hi = np.array([float(r["ci95_upper"]) for r in rows])

fig, ax = plt.subplots(figsize=(6.65, 3.95), layout="constrained")
radius = 0.1234663459
ax.axvspan(0, radius, color="#F3E6DE", alpha=0.7, zorder=0)
ax.errorbar(
    x,
    y,
    yerr=np.vstack((y - lo, hi - y)),
    fmt="o-",
    ms=5,
    mfc="white",
    mec=NAVY,
    mew=1.1,
    capsize=3,
    color=NAVY,
    label="observed certification power",
    zorder=3,
)
ax.axvline(radius, color=ORANGE, ls="--", lw=1.3, label="Hoeffding radius")
ax.axhline(0.8, color=SLATE, ls=":", lw=1.1, label="80% power")
ax.annotate(
    "transition across the\nfinite-sample radius",
    xy=(0.126177, 0.743),
    xytext=(0.155, 0.46),
    color=TEAL,
    fontsize=8,
    arrowprops={"arrowstyle": "->", "color": TEAL, "lw": 0.8},
)
ax.text(
    0.006,
    0.055,
    "insufficient guaranteed margin",
    color=ORANGE,
    fontsize=7.5,
)
ax.set(
    xlabel="exact finite-horizon MSE improvement",
    ylabel="certification probability",
    title="Independent one-sided certification",
    xlim=(-0.005, 0.25),
    ylim=(-0.03, 1.03),
)
ax.grid(True, color="#D8DEE3", lw=0.55, alpha=0.85)
ax.set_axisbelow(True)
ax.legend(frameon=False, loc="lower right")

out = Path("stage7_outputs/certification")
fig.savefig(out / "certification_power.pdf")
fig.savefig(out / "certification_power.png", dpi=300)
plt.close(fig)
