#!/usr/bin/env python3

"""Publication figures for the exact and matched-work benchmarks."""

import csv
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


BASE = Path("stage5_outputs")

NAVY = "#174A73"
TEAL = "#16827A"
ORANGE = "#D2693C"
SLATE = "#59636E"
COLORS = [NAVY, ORANGE, TEAL]

mpl.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["DejaVu Serif"],
        "mathtext.fontset": "dejavuserif",
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.titleweight": "semibold",
        "axes.labelsize": 9,
        "legend.fontsize": 7.7,
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


def finish_axes(axes):
    for axis in axes:
        axis.grid(
            True,
            which="major",
            color="#D8DEE3",
            lw=0.55,
            alpha=0.85,
        )
        axis.grid(
            True,
            which="minor",
            color="#EDF0F2",
            lw=0.35,
            alpha=0.75,
        )
        axis.set_axisbelow(True)


# ---------------------------------------------------------------------
# Experiment A: exact curves with Monte Carlo verification.
# ---------------------------------------------------------------------

with open(
    BASE / "experiment_A/two_state_results.csv",
    newline="",
    encoding="utf-8",
) as f:
    A = list(csv.DictReader(f))

fig, ax = plt.subplots(
    1,
    2,
    figsize=(10.6, 3.85),
    layout="constrained",
)

p_values = [0.5, 0.1, 0.01]

for color, p in zip(COLORS, p_values):
    rows = [
        r
        for r in A
        if float(r["p"]) == p and int(r["L"]) == 16
    ]

    x = np.array([float(r["n_epsilon"]) for r in rows])

    exact = np.array(
        [float(r["theorem_all_zero_probability"]) for r in rows]
    )

    simulated = np.array(
        [float(r["mc_all_zero_probability"]) for r in rows]
    )

    unscreened_error = np.array(
        [float(r["naive_selection_error"]) for r in rows]
    )

    screened_error = np.array(
        [float(r["gated_selection_error"]) for r in rows]
    )

    ax[0].plot(
        x,
        exact,
        color=color,
        label=rf"$p={p:g}$",
    )

    ax[0].scatter(
        x,
        simulated,
        s=18,
        facecolor="white",
        edgecolor=color,
        linewidth=0.8,
        zorder=3,
    )

    ax[1].plot(
        x,
        unscreened_error,
        color=color,
    )

    ax[1].plot(
        x,
        screened_error,
        color=color,
        ls="--",
    )


ax[0].set(
    xscale="log",
    xlabel=r"transition scale $n\varepsilon$",
    ylabel="all-zero probability",
    ylim=(-0.03, 1.03),
    title="(a) Exact false-precision mechanism",
)

ax[0].legend(
    frameon=False,
    title="event mass",
    title_fontsize=7.7,
)

ax[0].text(
    0.02,
    0.035,
    "solid curves: exact; open circles: Monte Carlo",
    transform=ax[0].transAxes,
    fontsize=7.2,
    color=SLATE,
)


ax[1].set(
    xscale="log",
    xlabel=r"transition scale $n\varepsilon$",
    ylabel="selection-error frequency",
    ylim=(-0.03, 1.03),
    title="(b) Exploration-based screening",
)

mass_legend = ax[1].legend(
    handles=[
        Line2D(
            [0],
            [0],
            color=c,
            label=rf"$p={p:g}$",
        )
        for c, p in zip(COLORS, p_values)
    ],
    frameon=False,
    loc="upper right",
)

ax[1].add_artist(mass_legend)

ax[1].legend(
    handles=[
        Line2D(
            [0],
            [0],
            color=SLATE,
            label="unscreened",
        ),
        Line2D(
            [0],
            [0],
            color=SLATE,
            ls="--",
            label="screened",
        ),
    ],
    frameon=False,
    loc="center right",
)

finish_axes(ax)

fig.savefig(BASE / "experiment_A/two_state_mechanism.pdf")
fig.savefig(
    BASE / "experiment_A/two_state_mechanism.png",
    dpi=300,
)

plt.close(fig)


# ---------------------------------------------------------------------
# Experiment B: equal-work risk and event non-exploration.
# ---------------------------------------------------------------------

with open(
    BASE / "experiment_B/estimand_metrics.csv",
    newline="",
    encoding="utf-8",
) as f:
    B = list(csv.DictReader(f))

mode_rows = [
    r for r in B
    if r["estimand"] == "mode"
]

with open(
    BASE / "experiment_B/oracle_risk.csv",
    newline="",
    encoding="utf-8",
) as f:
    O = list(csv.DictReader(f))

fig, ax = plt.subplots(
    1,
    2,
    figsize=(10.6, 3.85),
    layout="constrained",
)

algorithms = [
    "local_RWM",
    "transport_independence",
    "parallel_tempering",
]

display = {
    "local_RWM": "Local RWM",
    "transport_independence": "Transport MH",
    "parallel_tempering": "Parallel tempering",
}

settings = sorted(
    {r["setting"] for r in mode_rows}
)

width = 0.24
xpos = np.arange(len(settings))

for j, (algorithm, color) in enumerate(
    zip(algorithms, COLORS)
):
    offset = (j - 1) * width

    risk = [
        next(
            float(r["combined_risk"])
            for r in O
            if r["setting"] == setting
            and r["algorithm"] == algorithm
        )
        for setting in settings
    ]

    error = [
        next(
            1.96 * float(r["mcse"])
            for r in O
            if r["setting"] == setting
            and r["algorithm"] == algorithm
        )
        for setting in settings
    ]

    ax[0].bar(
        xpos + offset,
        risk,
        width,
        label=display[algorithm],
        color=color,
        yerr=error,
        capsize=2.5,
        error_kw={
            "elinewidth": 0.8,
            "capthick": 0.8,
        },
    )

    zero_transition = [
        next(
            float(r["zero_transition_fraction"])
            for r in mode_rows
            if r["setting"] == setting
            and r["algorithm"] == algorithm
        )
        for setting in settings
    ]

    ax[1].bar(
        xpos + offset,
        zero_transition,
        width,
        label=display[algorithm],
        color=color,
    )


for axis in ax:
    axis.set_xticks(
        xpos,
        settings,
    )
    axis.set_xlabel(
        "mixture setting"
    )


ax[0].set(
    ylabel="mode-probability MSE",
    title="(a) Reference risk estimates",
)

ax[0].ticklabel_format(
    axis="y",
    style="sci",
    scilimits=(-3, -3),
)


ax[1].set(
    ylabel="zero-transition path fraction",
    title="(b) Event non-exploration",
    ylim=(0, 1.03),
)

ax[1].legend(
    frameon=False,
    loc="upper left",
)

finish_axes(ax)

fig.savefig(BASE / "experiment_B/mixture_results.pdf")
fig.savefig(
    BASE / "experiment_B/mixture_results.png",
    dpi=300,
)

plt.close(fig)
