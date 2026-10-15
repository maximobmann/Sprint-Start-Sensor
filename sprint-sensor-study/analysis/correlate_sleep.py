#!/usr/bin/env python3
"""
correlate_sleep.py - relate WHOOP sleep metrics to session peak acceleration.

Inputs:
  data/session_log.csv              (copy session_log_template.csv and fill it in)
  data/processed/peaks_summary.csv  (made by compute_peaks.py)

The two are joined on session_log.raw_file == peaks_summary.file. Sessions
with include = "no" are left out.

For each sleep metric it reports n, Pearson r with a 95% confidence interval
and p-value, and Spearman rho with p-value, against the primary outcome
(top3_mean: mean of the best 3 of 5 sprint peaks).

Outputs:
  data/processed/correlations.csv
  figures/sleep_vs_peak.png       scatter plot for each metric
  figures/peak_over_time.png      outcome by session (checks for a training trend)

Usage:
    python analysis/correlate_sleep.py
    python analysis/correlate_sleep.py --outcome max_peak
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parent.parent
LOG_CSV = REPO / "data" / "session_log.csv"
PEAKS_CSV = REPO / "data" / "processed" / "peaks_summary.csv"
OUT_CSV = REPO / "data" / "processed" / "correlations.csv"
FIG_DIR = REPO / "figures"

METRICS = {
    "sleep_duration_h": "Sleep duration (h)",
    "sleep_performance_pct": "Sleep performance (%)",
    "recovery_pct": "Recovery (%)",
    "hrv_ms": "HRV (ms)",
    "resting_hr_bpm": "Resting heart rate (bpm)",
}
MIN_SESSIONS = 12  # minimum from the study protocol

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
SERIES = "#2a78d6"


def pearson_ci(r, n, level=0.95):
    """Confidence interval for Pearson r via the Fisher z-transform."""
    if n <= 3 or not np.isfinite(r) or abs(r) >= 1:
        return np.nan, np.nan
    z = np.arctanh(r)
    se = 1 / np.sqrt(n - 3)
    crit = stats.norm.ppf(0.5 + level / 2)
    return float(np.tanh(z - crit * se)), float(np.tanh(z + crit * se))


def style(ax):
    ax.set_facecolor(SURFACE)
    ax.grid(color=GRID, linewidth=0.8)
    ax.tick_params(colors=INK_2, labelsize=8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--outcome", default="top3_mean", choices=["top3_mean", "max_peak"],
                   help="session outcome to correlate (default top3_mean)")
    args = p.parse_args()

    if not LOG_CSV.exists():
        print(f"Missing {LOG_CSV.relative_to(REPO)}. Copy data/session_log_template.csv "
              "to data/session_log.csv and fill in one row per session.")
        sys.exit(1)
    if not PEAKS_CSV.exists():
        print(f"Missing {PEAKS_CSV.relative_to(REPO)}. Run compute_peaks.py first.")
        sys.exit(1)

    log = pd.read_csv(LOG_CSV)
    peaks = pd.read_csv(PEAKS_CSV)
    df = log.merge(peaks, left_on="raw_file", right_on="file", how="inner")

    if "include" in df.columns:
        df = df[df["include"].astype(str).str.strip().str.lower() != "no"]
    df = df.sort_values("date").reset_index(drop=True)

    unmatched = set(log["raw_file"].dropna()) - set(peaks["file"])
    if unmatched:
        print(f"Note: no peaks found for {sorted(unmatched)} (check file names).")

    n_total = len(df)
    print(f"Sessions in analysis: {n_total}  (outcome: {args.outcome})")
    if n_total < MIN_SESSIONS:
        print(f"⚠ Fewer than {MIN_SESSIONS} sessions: treat results as feasibility data only.")
    if n_total < 3:
        print("Need at least 3 sessions to compute correlations.")
        sys.exit(1)

    results = []
    for col, label in METRICS.items():
        sub = df[[col, args.outcome]].apply(pd.to_numeric, errors="coerce").dropna()
        n = len(sub)
        row = {"metric": col, "n": n}
        if n >= 3 and sub[col].nunique() > 1 and sub[args.outcome].nunique() > 1:
            r, p_r = stats.pearsonr(sub[col], sub[args.outcome])
            lo, hi = pearson_ci(r, n)
            rho, p_rho = stats.spearmanr(sub[col], sub[args.outcome])
            row.update(pearson_r=round(r, 3), pearson_ci_low=round(lo, 3) if np.isfinite(lo) else np.nan,
                       pearson_ci_high=round(hi, 3) if np.isfinite(hi) else np.nan,
                       pearson_p=round(p_r, 4), spearman_rho=round(rho, 3),
                       spearman_p=round(p_rho, 4))
        results.append(row)

    out = pd.DataFrame(results)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print("\n" + out.to_string(index=False))
    print(f"\nWrote {OUT_CSV.relative_to(REPO)}")
    print("Five metrics are tested, so treat any single p < 0.05 as exploratory.")

    # --- Scatter: each metric vs outcome -------------------------------------
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 3, figsize=(12, 7), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    for ax, (col, label) in zip(axes.flat, METRICS.items()):
        style(ax)
        sub = df[[col, args.outcome]].apply(pd.to_numeric, errors="coerce").dropna()
        ax.plot(sub[col], sub[args.outcome], "o", markersize=8, color=SERIES,
                markeredgecolor=SURFACE, markeredgewidth=2)
        r = out.loc[out["metric"] == col, "pearson_r"]
        r_txt = f"r = {r.iloc[0]:.2f}, n = {len(sub)}" if len(r) and pd.notna(r.iloc[0]) else f"n = {len(sub)}"
        ax.set_title(label, loc="left", fontsize=10, color=INK)
        ax.set_title(r_txt, loc="right", fontsize=8, color=INK_2)
        ax.set_ylabel("Session peak (m/s²)", fontsize=8, color=INK_2)
    axes.flat[-1].axis("off")
    fig.suptitle(f"Sleep metrics vs. session peak acceleration ({args.outcome})",
                 x=0.01, ha="left", fontsize=12, color=INK)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "sleep_vs_peak.png", facecolor=SURFACE)
    plt.close(fig)

    # --- Outcome over time ---------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 4), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    style(ax)
    x = np.arange(1, n_total + 1)
    y = pd.to_numeric(df[args.outcome], errors="coerce")
    ax.plot(x, y, "-o", color=SERIES, linewidth=1.5, markersize=8,
            markeredgecolor=SURFACE, markeredgewidth=2)
    ax.set_title("Session peak acceleration over the study", loc="left",
                 fontsize=11, color=INK)
    ax.set_xlabel("Session", fontsize=9, color=INK_2)
    ax.set_ylabel("Session peak (m/s²)", fontsize=9, color=INK_2)
    ax.set_xticks(x)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "peak_over_time.png", facecolor=SURFACE)
    plt.close(fig)
    print(f"Plots in {FIG_DIR.relative_to(REPO)}/")


if __name__ == "__main__":
    main()
