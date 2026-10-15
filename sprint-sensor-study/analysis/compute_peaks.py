#!/usr/bin/env python3
"""
compute_peaks.py - find the sprint peaks in each session file.

For every CSV in data/raw/ (or the files you pass in), this script:
  1. computes acceleration magnitude |a| = sqrt(x^2 + y^2 + z^2)
  2. smooths it with a short centered moving average (default 30 ms)
  3. finds the N largest peaks that are at least MIN_GAP seconds apart
     (default: 5 peaks, 60 s apart = the 5 sprints with 3-4 min rest)
  4. reports data-quality checks (sample rate, dropped samples, clipping)
  5. saves two plots: the whole session (figures/<file>_resultant.png) and a
     close-up of each sprint (figures/<file>_sprints.png)

All results go to data/processed/peaks_summary.csv.

Usage:
    python analysis/compute_peaks.py                     # every file in data/raw/
    python analysis/compute_peaks.py data/raw/2026-11-03_s07.csv
    python analysis/compute_peaks.py --n-sprints 5 --min-gap 60 --min-peak 15

Always look at the plots: if the marked peaks don't line up with the sprints,
note it in the session log rather than trusting the number.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parent.parent
RAW_DIR = REPO / "data" / "raw"
OUT_CSV = REPO / "data" / "processed" / "peaks_summary.csv"
FIG_DIR = REPO / "figures"

# BNO085 accelerometer full scale is +/-8 g. Per-axis readings at or above
# this are probably clipped.
CLIP_THRESHOLD = 0.97 * 8 * 9.80665  # ~76 m/s^2

# Chart styling (light theme)
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
SERIES = "#2a78d6"   # magnitude trace
ACCENT = "#eb6834"   # detected peaks


def load_run(path: Path) -> pd.DataFrame:
    """Read one logger CSV, dropping any partial or malformed rows."""
    df = pd.read_csv(path, on_bad_lines="skip")
    df.columns = [c.strip().lower() for c in df.columns]
    missing = {"time_ms", "x", "y", "z"} - set(df.columns)
    if missing:
        raise ValueError(f"missing columns {sorted(missing)}")
    for col in ["time_ms", "x", "y", "z"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["time_ms", "x", "y", "z"]).reset_index(drop=True)
    # keep only rows where time moves forward (guards against stray lines)
    keep = df["time_ms"].diff().fillna(1) > 0
    return df[keep].reset_index(drop=True)


def find_peaks(t_s, values, n_peaks, min_gap_s, min_peak):
    """Greedy peak picking: take the largest value, blank out +/- min_gap_s
    around it, repeat. Returns indices sorted by time."""
    remaining = values.astype(float).copy()
    picked = []
    while len(picked) < n_peaks:
        i = int(np.argmax(remaining))
        v = remaining[i]
        if not np.isfinite(v) or v < min_peak:
            break
        picked.append(i)
        remaining[np.abs(t_s - t_s[i]) < min_gap_s] = -np.inf
    return sorted(picked, key=lambda k: t_s[k])


def analyze(df, smooth_ms, n_sprints, min_gap_s, min_peak):
    t_ms = df["time_ms"].to_numpy(dtype=float)
    t_s = (t_ms - t_ms[0]) / 1000.0
    xyz = df[["x", "y", "z"]].to_numpy(dtype=float)
    mag = np.sqrt((xyz ** 2).sum(axis=1))

    dt_ms = float(np.median(np.diff(t_ms))) if len(t_ms) > 1 else 10.0
    window = max(1, int(round(smooth_ms / dt_ms)))
    smooth = (
        pd.Series(mag).rolling(window, center=True, min_periods=1).mean().to_numpy()
    )

    near_clip = (np.abs(xyz) >= CLIP_THRESHOLD).any(axis=1)
    idx = find_peaks(t_s, smooth, n_sprints, min_gap_s, min_peak)
    peak_vals = [float(smooth[i]) for i in idx]
    top3 = sorted(peak_vals, reverse=True)[:3]

    return {
        "t_s": t_s,
        "smooth": smooth,
        "peak_idx": idx,
        "duration_s": round(float(t_s[-1]), 1),
        "sample_rate_hz": round(1000.0 / dt_ms, 1),
        "dropped_gaps": int((np.diff(t_ms) > 3 * dt_ms).sum()),
        "clipped_samples": int(near_clip.sum()),
        "near_clip": near_clip,
        "peaks": peak_vals,
        "top3_mean": round(float(np.mean(top3)), 2) if len(top3) == 3 else np.nan,
        "max_peak": round(max(peak_vals), 2) if peak_vals else np.nan,
    }


def plot_session(name, res, out_path):
    t, s, idx = res["t_s"], res["smooth"], res["peak_idx"]
    fig, ax = plt.subplots(figsize=(10, 4), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    ax.plot(t, s, color=SERIES, linewidth=1.2, label="|a|, smoothed")
    if idx:
        ax.plot(t[idx], s[idx], "o", markersize=8, color=ACCENT,
                markeredgecolor=SURFACE, markeredgewidth=2,
                label="detected sprint peak", zorder=3)
        for n, i in enumerate(idx, start=1):
            ax.annotate(f"#{n}  {s[i]:.1f}", (t[i], s[i]),
                        textcoords="offset points", xytext=(6, 6),
                        fontsize=8, color=INK)

    ax.set_title(f"{name} — resultant acceleration", loc="left",
                 fontsize=11, color=INK)
    ax.set_xlabel("Time since power-on (s)", color=INK_2, fontsize=9)
    ax.set_ylabel("|a| (m/s²)", color=INK_2, fontsize=9)
    ax.set_ylim(0, max(float(np.nanmax(s)), 1.0) * 1.15)  # headroom for labels
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.tick_params(colors=INK_2, labelsize=8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    # legend sits in the title row, clear of the data
    ax.legend(frameon=False, fontsize=8, loc="lower right", bbox_to_anchor=(1, 1),
              ncol=2, labelcolor=INK_2, borderaxespad=0.2)

    fig.tight_layout()
    fig.savefig(out_path, facecolor=SURFACE)
    plt.close(fig)


def plot_sprints(name, res, out_path, before_s=4.0, after_s=6.0):
    """One panel per detected sprint, zoomed in so individual foot strikes
    are visible. Moments where any axis is near the sensor's 8 g limit are
    marked with an x along the top edge."""
    t, s, idx, clip = res["t_s"], res["smooth"], res["peak_idx"], res["near_clip"]
    if not idx:
        return
    n = len(idx)
    fig, axes = plt.subplots(1, n, figsize=(2.6 * n, 3.4), dpi=150, sharey=True,
                             squeeze=False)
    fig.patch.set_facecolor(SURFACE)
    eight_g = 8 * 9.80665
    ymax = max(float(np.nanmax(s[idx])), eight_g) * 1.12
    for k, (ax, i) in enumerate(zip(axes[0], idx), start=1):
        m = (t >= t[i] - before_s) & (t <= t[i] + after_s)
        tt = t[m] - t[i]
        ax.set_facecolor(SURFACE)
        ax.plot(tt, s[m], color=SERIES, linewidth=1.0)
        ax.axhline(eight_g, color=INK_2, linewidth=0.8, linestyle=(0, (4, 3)))
        cm = clip[m]
        if cm.any():  # mark the moments along the top edge of the panel
            ax.plot(tt[cm], np.full(cm.sum(), ymax * 0.96), "x", color=INK,
                    markersize=5, markeredgewidth=1.2, clip_on=False)
        ax.plot(0, s[i], "o", markersize=8, color=ACCENT,
                markeredgecolor=SURFACE, markeredgewidth=2, zorder=3)
        ax.set_title(f"Sprint {k}  ·  peak {s[i]:.1f}", loc="left",
                     fontsize=9, color=INK)
        ax.set_ylim(0, ymax)
        ax.set_xlim(-before_s, after_s)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.tick_params(colors=INK_2, labelsize=7)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(GRID)
        ax.set_xlabel("s from peak", fontsize=8, color=INK_2)
    axes[0][0].set_ylabel("|a| (m/s²)", fontsize=8, color=INK_2)
    axes[0][-1].text(after_s, eight_g, "8 g ", ha="right", va="bottom",
                     fontsize=7, color=INK_2)
    fig.suptitle(f"{name} — each sprint up close  (× at top = a moment when an axis reached the sensor's 8 g limit)",
                 x=0.01, ha="left", fontsize=10, color=INK)
    fig.tight_layout()
    fig.savefig(out_path, facecolor=SURFACE)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="*", type=Path,
                   help="CSV files to process (default: every file in data/raw/)")
    p.add_argument("--n-sprints", type=int, default=5,
                   help="sprints per session (default 5)")
    p.add_argument("--min-gap", type=float, default=60.0,
                   help="minimum seconds between sprint peaks (default 60)")
    p.add_argument("--min-peak", type=float, default=15.0,
                   help="ignore peaks below this many m/s^2 (default 15)")
    p.add_argument("--smooth-ms", type=float, default=30.0,
                   help="moving-average window in ms (default 30)")
    p.add_argument("--no-plots", action="store_true", help="skip saving figures")
    args = p.parse_args()

    files = args.files or sorted(RAW_DIR.glob("*.csv"))
    if not files:
        print(f"No CSV files found in {RAW_DIR}. Copy session files there first.")
        sys.exit(1)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    for path in files:
        try:
            df = load_run(path)
        except Exception as e:  # keep going if one file is broken
            print(f"[skip] {path.name}: {e}")
            continue
        if len(df) < 10:
            print(f"[skip] {path.name}: only {len(df)} valid rows")
            continue

        res = analyze(df, args.smooth_ms, args.n_sprints, args.min_gap, args.min_peak)

        row = {
            "file": path.name,
            "samples": len(df),
            "duration_s": res["duration_s"],
            "sample_rate_hz": res["sample_rate_hz"],
            "dropped_gaps": res["dropped_gaps"],
            "clipped_samples": res["clipped_samples"],
            "peaks_found": len(res["peaks"]),
        }
        for k in range(args.n_sprints):
            row[f"peak_{k + 1}"] = round(res["peaks"][k], 2) if k < len(res["peaks"]) else np.nan
        row["top3_mean"] = res["top3_mean"]
        row["max_peak"] = res["max_peak"]
        rows.append(row)

        flags = []
        if res["peaks"] and len(res["peaks"]) < args.n_sprints:
            flags.append(f"only {len(res['peaks'])}/{args.n_sprints} peaks")
        if not res["peaks"]:
            flags.append("no peaks above threshold")
        if res["dropped_gaps"]:
            flags.append(f"{res['dropped_gaps']} gaps in data")
        if res["clipped_samples"]:
            flags.append(f"{res['clipped_samples']} samples near ±8 g limit")
        note = f"  ⚠ {'; '.join(flags)}" if flags else ""
        print(f"{path.name}: {res['duration_s']} s @ {res['sample_rate_hz']} Hz, "
              f"peaks {[round(v, 1) for v in res['peaks']]}, "
              f"top-3 mean {res['top3_mean']}{note}")

        if not args.no_plots:
            plot_session(path.stem, res, FIG_DIR / f"{path.stem}_resultant.png")
            plot_sprints(path.stem, res, FIG_DIR / f"{path.stem}_sprints.png")

    if not rows:
        print("Nothing processed.")
        sys.exit(1)

    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)
    print(f"\nWrote {OUT_CSV.relative_to(REPO)} ({len(rows)} file(s))")
    if not args.no_plots:
        print(f"Plots in {FIG_DIR.relative_to(REPO)}/")


if __name__ == "__main__":
    main()
