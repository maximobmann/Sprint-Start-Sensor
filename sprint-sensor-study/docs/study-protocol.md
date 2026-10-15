# Study protocol

**Title:** Nightly sleep metrics and peak sprint acceleration in a trained high school sprinter: an n-of-1 pilot study

**Version:** 1.0 · written before formal data collection began
**Status:** Pilot session completed (August 1, 2026); data collection paused for injury recovery

This protocol is fixed in advance so that the analysis can't be shaped by the results. Any change made after data collection starts will be recorded in the [change log](#change-log) at the bottom with the date and reason.

---

## 1. Research question

Do sleep metrics from the night before a training session predict peak sprint acceleration in that session?

**Hypothesis:** better sleep (longer duration, higher sleep performance, higher recovery score, higher HRV, lower resting heart rate) is associated with higher session peak acceleration.

**Alternative I take seriously:** with one participant and day-to-day variability from training, weather and soreness, any sleep effect may be too small to detect. A null result will be reported as such.

## 2. Design

- Prospective, observational, **n-of-1** (single participant: the author).
- Sleep is **not manipulated**. Natural night-to-night variation is the predictor.
- **Target:** 3 sessions per week for 8 weeks (24 sessions).
- **Minimum for analysis:** 12 sessions (4 weeks). Results from fewer sessions will be described only as feasibility data.

## 3. Participant

One male high school varsity sprinter, injury-free at the time of each session. Sessions are skipped, not modified, if the participant is injured or ill; skipped sessions are recorded in the session log.

## 4. Instrument

- Waist-worn logger described in [hardware.md](hardware.md): BNO085 IMU reporting linear acceleration at 100 Hz, logged to microSD.
- Taped to the front of the waistband of the same sprint shorts, in the same position and orientation every session (the pilot mount; see [hardware.md](hardware.md#mounting)).
- Sleep data: WHOOP strap, worn every night of the study.

## 5. Session procedure

1. **Same track, same lane** every session. Aim for the **same time of day** (±1 h).
2. **Same shoes** every session.
3. **Standardized warm-up**, identical each time (the same routine used in the pilot):
   - A skips
   - B skips
   - C skips
   - Bounds
   - Frankensteins
   <!-- TODO: add distances/reps for each drill (e.g. 2 × 20 m each) so it can be repeated exactly. -->
4. Connect the battery to start recording. Note the clock time.
5. Stand still for ~10 s before the first sprint (gives a clean baseline in the file).
6. **5 × 30 m maximal sprints** from the same start position every time *[standing or three-point: to be fixed before session 1]*.
7. **3–4 min rest** between sprints, walking back slowly.
8. After the last sprint, stand still ~10 s, then disconnect the battery.
9. Copy the CSV from the SD card the same day and rename it per [data/README.md](../data/README.md).
10. Fill in one row of the session log (WHOOP metrics + confounds).

## 6. Measures

### Outcome (from the sensor)

For each sprint:

- Resultant acceleration per sample: `|a| = √(x² + y² + z²)` (m/s²)
- Light smoothing: centered moving average over ~30 ms (3 samples at 100 Hz) to suppress single-sample spikes
- **Peak acceleration** = maximum smoothed resultant during that sprint

For each session:

> ⚠️ **Under review after the pilot.** The pilot showed sprint peaks reaching the sensor's 8 g limit (see the [README](../README.md#pilot-session-august-1-2026)). The outcome below may change before session 1; any change will be recorded in the change log.

- **Primary outcome: mean of the top 3 of the 5 sprint peaks.** This drops the two lowest reps (a slip, a mistimed start, fatigue) without letting one unusually high rep dominate.
- Secondary outcome: highest single peak of the session.

Sprints are identified automatically as the 5 largest peaks separated by at least 60 s (see `analysis/compute_peaks.py`). Every session's plot is checked by eye; if the detected peaks don't line up with the 5 sprints, this is noted and corrected in the session log rather than silently changed.

### Predictors (from WHOOP, for the night before the session)

1. Sleep duration (h)
2. Sleep performance (%)
3. Recovery score (%)
4. Heart rate variability, HRV (ms)
5. Resting heart rate (bpm)

### Confounds (recorded every session)

| Variable | How recorded |
|---|---|
| Time of day | Clock time of first sprint (24 h) |
| Temperature | °F from a weather app at session time |
| Wind | none / light / moderate / strong, plus head or tail if obvious |
| Surface | dry / damp / wet |
| Soreness before session | 1–10 self-rating |
| Prior 24 h training load | WHOOP day strain, plus rest / light / moderate / hard |
| Other | illness, caffeine, meal timing, anything unusual |

## 7. Analysis plan

1. For each WHOOP metric, compute the **Pearson** and **Spearman** correlation with the primary outcome across sessions, with 95% confidence intervals where possible.
2. Plot each predictor against the outcome (scatter with the session number labeled).
3. Plot the outcome over time to check for a training trend; if a clear trend exists, repeat step 1 on detrended values as a secondary analysis.
4. Describe confounds alongside the results; with this sample size they cannot all be statistically controlled.
5. All five predictors are reported regardless of outcome. Because five correlations are tested, any single "significant" result is treated as exploratory, not confirmed.

## 8. Limitations (known in advance)

- **n = 1.** Results describe one athlete and do not generalize.
- **Small number of sessions.** Statistical power is low; only large effects could be detected.
- **What the outcome measures.** Peak resultant acceleration at the waist includes the vertical impact spike at each foot contact, not only forward propulsion. It is best read as a measure of sprint movement intensity, not a direct measure of horizontal acceleration. Adding timed 30 m splits is planned as a validation measure.
- **Mounting.** The sensor is taped to the shorts waistband, which can move slightly relative to the body. Some of the measured peak may come from fabric movement rather than the body itself.
- **Sensor range.** The BNO085 accelerometer saturates at ±8 g (≈ 78 m/s²) per axis. The pilot confirmed that sprint foot strikes reach this limit, so recorded peaks can understate the true impact.
- **WHOOP accuracy.** Consumer wearable sleep staging and recovery scores are estimates, not polysomnography.
- **Uncontrolled factors.** Weather, training cycle, motivation, and the injury interruption all add variability.
- **Single investigator.** The participant also runs the sessions and the analysis; the pre-specified protocol and public raw data are the safeguards against bias.

## 9. Data sharing

All raw session files, the session log, and the analysis code are published in this repository, including sessions that turn out noisy or unusable (marked as such).

## Change log

| Date | Change | Reason |
|---|---|---|
| — | Protocol v1.0 | Initial version |
| 2026-08-01 | Pilot session completed (5 × 30 m) | Tested the device, mounting, and session procedure |
| 2026-08-01 | Outcome measure, sensor range, and mount placed under review | Pilot peaks reached the sensor's 8 g limit in sprints 2–5 |
| Fall 2026 | Data collection paused after the pilot session | Injury; will resume once cleared to sprint |
