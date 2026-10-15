# Analysis

Two scripts, run in order from the repository root.

## Setup

Install Python 3.10+ from [python.org](https://www.python.org/downloads/) (on Windows, tick **"Add python.exe to PATH"** in the installer), then:

```bash
pip install -r analysis/requirements.txt
```

## 1. `compute_peaks.py` — find the sprints

```bash
python analysis/compute_peaks.py
```

For every CSV in `data/raw/`:

1. Computes resultant acceleration `|a| = √(x² + y² + z²)` (the magnitude of the 3-axis vector).
2. Smooths it with a 30 ms centered moving average (3 samples at 100 Hz).
3. Picks the 5 largest peaks that are at least 60 s apart, one per sprint.
4. Checks data quality: effective sample rate, gaps in the data, samples near the sensor's ±8 g limit.
5. Saves a plot to `figures/<file>_resultant.png` with each detected peak marked.

Output: `data/processed/peaks_summary.csv` with one row per file: `peak_1`…`peak_5` in time order, `top3_mean` (primary outcome), and `max_peak`.

Options:

| Flag | Default | Meaning |
|---|---|---|
| `--n-sprints` | 5 | Sprints per session |
| `--min-gap` | 60 | Minimum seconds between sprint peaks |
| `--min-peak` | 15 | Ignore peaks below this (m/s²) so walking isn't counted as a sprint |
| `--smooth-ms` | 30 | Moving-average window |
| `--no-plots` | off | Skip figures |

**Check every plot.** If a marked peak isn't on a sprint (for example, the device got bumped), record it in the session log's `notes` and adjust.

## 2. `correlate_sleep.py` — relate sleep to performance

```bash
cp data/session_log_template.csv data/session_log.csv   # once, then fill it in
python analysis/correlate_sleep.py
```

Joins the session log with the peak summary and, for each of the five WHOOP metrics, reports:

- **n** — sessions with data for that metric
- **Pearson r** with a 95% confidence interval and p-value
- **Spearman ρ** with p-value (less sensitive to outliers)

Output: `data/processed/correlations.csv`, `figures/sleep_vs_peak.png`, `figures/peak_over_time.png`.

Use `--outcome max_peak` to run the secondary outcome.

## Reading the results honestly

- With 12–24 sessions, the confidence intervals will be wide. Report them, not just r.
- Five metrics are tested, so one p < 0.05 could easily be chance. Treat it as a lead, not a finding.
- Check `peak_over_time.png` first. If performance trends up across the study (training effect), that trend can create or hide a sleep correlation.
