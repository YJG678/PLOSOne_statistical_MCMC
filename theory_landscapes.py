#!/usr/bin/env python3
"""Publication figure for the exact finite-sample theory landscapes."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D


OUT = Path("stage8_outputs")
OUT.mkdir(parents=True, exist_ok=True)

NAVY = "#174A73"
TEAL = "#16827A"
ORANGE = "#D2693C"
GOLD = "#D5A72C"
SLATE = "#59636E"
LIGHT = "#EAF1F5"

mpl.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["DejaVu Serif"],
        "mathtext.fontset": "dejavuserif",
        "font.size": 8.5,
        "axes.titlesize": 9.5,
        "axes.titleweight": "semibold",
        "axes.labelsize": 8.5,
        "legend.fontsize": 7.4,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.7,
        "lines.linewidth": 1.8,
        "savefig.bbox": "tight",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)

fig, axes = plt.subplots(1, 3, figsize=(11.8, 3.65), layout="constrained")

# Panel (a): exact false-precision probability.
n = 200
L = 16
x = np.logspace(-2, 2, 260)  # x = n epsilon
p = np.logspace(-3, math.log10(0.5), 220)
xx, pp = np.meshgrid(x, p)
eps = xx / n
false_precision = np.power(1.0 - eps * pp, L * n)
cmap = LinearSegmentedColormap.from_list(
    "false_precision", ["#F7FBFF", "#A8D5E5", "#3F8FB8", NAVY]
)
im = axes[0].pcolormesh(
    xx, pp, false_precision, shading="auto", cmap=cmap, vmin=0.0, vmax=1.0,
    rasterized=True
)
cs = axes[0].contour(
    xx,
    pp,
    false_precision,
    levels=[0.05, 0.50, 0.95],
    colors=[SLATE, "white", "white"],
    linewidths=[0.9, 1.0, 1.0],
)
axes[0].clabel(cs, fmt={0.05: ".05", 0.50: ".50", 0.95: ".95"}, fontsize=6.8)
axes[0].set(
    xscale="log",
    yscale="log",
    xlabel=r"transition scale $n\varepsilon$",
    ylabel=r"target event mass $p$",
    title=r"(a) False precision: $(1-\varepsilon p)^{Ln}$",
)
cbar = fig.colorbar(im, ax=axes[0], fraction=0.052, pad=0.02)
cbar.set_label("all-zero probability", fontsize=7.5)
cbar.ax.tick_params(labelsize=7)

# Panel (b): proxy failure along w = p^3.
p_line = np.logspace(-4, math.log10(0.3), 320)
w_line = p_line**3
acceptance_defect = p_line - w_line
reverse_kl = (1.0 - w_line) * np.log((1.0 - w_line) / (1.0 - p_line))
reverse_kl += w_line * np.log(w_line / p_line)
relative_lrv = 2.0 * p_line / w_line - 1.0
axes[1].loglog(
    p_line, acceptance_defect, color=NAVY, label=r"$1-\mathrm{Acc}(p,p^3)$"
)
axes[1].loglog(
    p_line, reverse_kl, color=TEAL, ls="--", label=r"$D_{\mathrm{KL}}(q_{p^3}\Vert\pi_p)$"
)
axes[1].loglog(
    p_line,
    relative_lrv,
    color=ORANGE,
    ls="-.",
    label=r"$\sigma^2(\mathbf{1}_B)/\{p(1-p)\}$",
)
axes[1].annotate(
    "global proxies improve",
    xy=(2.0e-3, 2.0e-3),
    xytext=(1.0e-2, 1.5e-1),
    color=TEAL,
    fontsize=7,
    arrowprops={"arrowstyle": "->", "color": TEAL, "lw": 0.8},
)
axes[1].annotate(
    "event inefficiency diverges",
    xy=(8.0e-4, 3.0e6),
    xytext=(5.0e-3, 2.5e5),
    color=ORANGE,
    fontsize=7,
    arrowprops={"arrowstyle": "->", "color": ORANGE, "lw": 0.8},
)
axes[1].set(
    xlabel=r"minority mass $p$ with $w=p^3$",
    ylabel="exact diagnostic scale",
    title="(b) Rare-mode proxy separation",
    ylim=(2e-5, 5e8),
)
axes[1].legend(frameon=False, loc="lower left")

# Panel (c): distribution-free certification cost and observed power.
delta_cert = 0.015
beta = 0.20
coefficient = 2.0 * (
    math.sqrt(math.log(1.0 / delta_cert)) + math.sqrt(math.log(1.0 / beta))
) ** 2
g = np.linspace(0.04, 0.30, 400)
m_required = coefficient / g**2
axes[2].semilogy(g, m_required, color=NAVY)
axes[2].fill_between(g, m_required, 2.0e4, color=LIGHT, alpha=0.65)
axes[2].axhline(551, color=SLATE, lw=1.0, ls=":")
axes[2].axvline(0.20, color=SLATE, lw=1.0, ls=":")
axes[2].plot([0.20], [551], marker="s", color=NAVY, ms=5)
axes[2].annotate(
    r"$g=.20,\ m=551$",
    xy=(0.20, 551),
    xytext=(0.205, 950),
    fontsize=7,
    color=NAVY,
    arrowprops={"arrowstyle": "->", "color": NAVY, "lw": 0.8},
)

certification_rows = list(
    csv.DictReader(open("stage7_outputs/certification/certification_power.csv"))
)
positive_rows = sorted(
    (row for row in certification_rows if float(row["true_improvement"]) > 0.0),
    key=lambda row: float(row["true_improvement"]),
)
effects = np.array([float(row["true_improvement"]) for row in positive_rows])
powers = np.array([float(row["certification_power"]) for row in positive_rows])
power_colors = [SLATE if q == 0 else GOLD if q < 1 else TEAL for q in powers]
power_markers = ["o" if q == 0 else "D" if q < 1 else "^" for q in powers]
for effect, power, color, marker in zip(effects, powers, power_colors, power_markers):
    axes[2].scatter(
        [effect], [551], s=32, marker=marker, facecolor=color, edgecolor="white",
        linewidth=0.6, zorder=5
    )

axes[2].text(
    0.045,
    1.25e4,
    "shaded: theorem guarantees\npower at least 80%",
    fontsize=7,
    color=NAVY,
    va="top",
)
axes[2].text(
    0.292,
    260,
    "null: 0/2000\nfalse certifications",
    fontsize=7,
    color=SLATE,
    ha="right",
    va="bottom",
)
legend_handles = [
    Line2D([0], [0], marker="o", color="none", markerfacecolor=SLATE,
           markeredgecolor="white", label="observed power 0"),
    Line2D([0], [0], marker="D", color="none", markerfacecolor=GOLD,
           markeredgecolor="white", label="observed power .743"),
    Line2D([0], [0], marker="^", color="none", markerfacecolor=TEAL,
           markeredgecolor="white", label="observed power 1"),
]
axes[2].legend(handles=legend_handles, frameon=False, loc="upper right")
axes[2].set(
    xlabel=r"guaranteed mean improvement $g$",
    ylabel=r"required certification units $m_{\mathrm{cert}}$",
    title="(c) Certification cost and power",
    xlim=(0.04, 0.30),
    ylim=(2.0e2, 1.6e4),
)

for ax in axes:
    ax.grid(True, which="major", color="#D8DEE3", lw=0.55, alpha=0.8)
    ax.grid(True, which="minor", color="#EDF0F2", lw=0.35, alpha=0.7)
    ax.set_axisbelow(True)

fig.savefig(OUT / "theory_landscapes.pdf", dpi=300)
fig.savefig(OUT / "theory_landscapes.png", dpi=300)
plt.close(fig)

summary = {
    "status": "PASS",
    "false_precision": {
        "n": n,
        "L": L,
        "n_epsilon_range": [float(x.min()), float(x.max())],
        "p_range": [float(p.min()), float(p.max())],
        "contours": [0.05, 0.50, 0.95],
    },
    "proxy_path": {
        "relation": "w=p^3",
        "p_range": [float(p_line.min()), float(p_line.max())],
    },
    "certification": {
        "delta_cert": delta_cert,
        "beta": beta,
        "coefficient": coefficient,
        "m_at_g_0.20": int(math.ceil(coefficient / 0.20**2)),
        "effects": effects.tolist(),
        "observed_powers": powers.tolist(),
        "null_false_certifications": 0,
        "null_repetitions": 2000,
    },
}
(OUT / "theory_landscapes.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
