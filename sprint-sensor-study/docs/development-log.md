# Development log

How the device got from "sensor not found" to a reliable 100 Hz logger. I'm keeping this because the debugging taught me more than the parts that worked on the first try.

**Summary:** three hardware configurations over about a month. The first two used a classic ESP32 and failed in the same way: the sensor was detected but stopped streaming. After ruling out soldering, wiring, connectors, and the sensor board, the remaining explanation was a known incompatibility between the classic ESP32's I²C peripheral and the BNO08x's use of clock stretching. Version 3 replaced the microcontroller with an RP2040 and worked immediately.

---

## Version 1 — ESP32 + clone BNO08x breakout (breadboard)

**Hardware:** ESP32 dev board (ESP-WROOM-32), GY-BNO08X clone breakout with headers I hand-soldered, breadboard, jumper wires. I²C on GPIO 21 (SDA) and 22 (SCL).

**What happened**

1. **Not detected at all.** An I²C scanner sketch found no devices. After inspecting the joints and rebuilding the wiring, the sensor appeared at address `0x4B`.
2. **Streamed, then stopped.** The Adafruit BNO08x example printed linear acceleration for 10–20 seconds and then went silent.
3. **Made it worse by changing two things at once.** I raised the I²C clock from 100 kHz to 400 kHz *and* the report rate from 100 Hz to 200 Hz in the same edit. Output dropped to 0 samples/s, and I couldn't tell which change caused it.
4. **Added reset recovery.** The BNO08x forgets its report settings if it resets. I added a `wasReset()` check that re-enables the report, plus counters for samples/s and resets.
5. **"Found" but couldn't start.** A plain I²C scan kept finding `0x4B`, but `begin_I2C()` failed. A scan is one tiny transaction; starting the sensor and streaming need long ones. Short transactions worked, long ones didn't.
6. **Tried SPI mode.** The BNO08x also speaks SPI, which avoids the I²C problem. I pulled PS0/PS1 high and rewired 10 connections. Result: not found over SPI, and an I²C scan on the same pins reported a phantom device at `0x02`, a sign of floating, half-connected lines.

**What I noticed about the setup:** the ESP32 was hanging in the air, held only by jumper wires pushed onto its pins. Every connection was friction-fit and moved whenever I touched anything.

## Version 1.5 — ESP32 on an expansion dock

**Change:** moved the ESP32 into a pin-header expansion board so it sat flat with dedicated 3.3 V and GND pins.

**What happened**

- The dock's printed pin labels **did not line up** with the ESP32's own labels, and the offset wasn't uniform along the board. I switched to wiring by tracing each pin straight out from the label printed on the ESP32 itself.
- With solid connections, a dedicated 3.3 V supply, and verified pin columns, I²C showed the **same signature as before**: sensor found, one reset, then 0 samples/s.
- A second clone board, which I soldered more carefully, behaved the same way.

**Conclusion at this point:** two sensor boards, two solder jobs, two wiring setups, one identical failure. The problem probably wasn't anything I had swapped.

## Version 2 — ESP32 + genuine Adafruit BNO085 (STEMMA QT)

**Change:** replaced the clone with Adafruit's BNO085 breakout, connected with a factory STEMMA QT cable. Four connections, nothing hand-soldered on the sensor side.

**What happened**

- A new laptop didn't recognize the ESP32 at all. Device Manager showed the USB chip (CP2102N) with "drivers not installed (Code 28)". The fix was Silicon Labs' universal CP210x driver; the older driver package didn't support the CP2102N.
- The sensor streamed at a steady **100 samples/s and then decayed to zero** (100 → 78 → 0). I reproduced this on two different days.
- When I connected the sensor's **RST pin to GPIO 26** and let the library control it, streaming held at 100 samples/s and the reset counter showed it recovering on its own. Removing that wire brought the stall back.
- My RST connection was a temporary, unsoldered pin wedged in the hole. It was unreliable: it sometimes blocked uploads and at one point the sensor stopped being detected entirely.

**Diagnosis:** with a known-good sensor and factory connectors, the same failure remained. It matched a documented problem: the BNO08x uses I²C *clock stretching* (holding the clock line low while it prepares data), and the classic ESP32's I²C hardware handles this poorly. Resetting the sensor through RST was a workaround, not a fix.

**Decision:** instead of soldering more workarounds onto a known-bad pairing, change the microcontroller.

## Version 3 — Feather RP2040 + Adafruit BNO085 (final)

**Change:** Adafruit Feather RP2040, which has its own STEMMA QT jack. One cable, clicked in at both ends.

**What happened**

- First upload required BOOTSEL mode (the board appears as a USB drive called RPI-RP2). After that, it showed up as a normal serial port. No driver needed.
- The first sketch reported "not found." The fix was using the `Wire` I²C bus for this board's STEMMA QT port and making sure the new upload actually landed (see lesson 2 below).
- **Result: 100 samples/s for 30 minutes straight with no stalls**, including while I wiggled the cable and shook the sensor.

### Getting data off the device

- **Tethered:** changed the output to CSV, logged the serial stream to a file with PuTTY, and plotted it in Google Sheets. A shake test showed a flat baseline near 0 and clear spikes of roughly ±60 m/s².
- **Startup timing:** sometimes the board booted faster than the sensor and reported "not found" until I pressed RESET. A 3-second startup delay fixed it.
- **Untethered:** stacked an Adalogger FeatherWing (microSD) on the Feather. Adafruit's short male headers didn't seat securely in the short female sockets, so I used standard-height male headers instead. An SD test sketch confirmed the card, and the final logger writes `runNNN.csv` files directly.

### Pilot

One pilot field session was recorded on **August 1, 2026** with the full portable setup, the device taped to the front of my shorts waistband. It logged 13 minutes at 100 Hz and captured all five 30 m sprints cleanly, with individual foot strikes visible.

It also exposed a measurement problem I hadn't seen on the bench: the foot-strike spikes reach the BNO085's ±8 g per-axis limit, so the highest peaks are capped by the sensor. That's exactly what a pilot is for. The outcome measure, sensor range, and mount are now under review before formal data collection (see the [README](../README.md#pilot-session-august-1-2026)).

Shortly after the pilot, an injury paused the study; data collection will resume once I'm cleared to sprint.

---

## Lessons

1. **Change one variable at a time.** The one time I changed two settings together, I lost a day figuring out which one mattered.
2. **Confirm what code is actually running.** Several "fixes" never reached the board because the upload failed, and the board kept running the old sketch. I started printing a version banner (`v12`, `v13`, …) at the top of every sketch so the serial output always says which code produced it.
3. **Detected is not the same as working.** An I²C scan only proves the device answers one short message. Test the real workload (sustained streaming) before trusting a connection.
4. **Mechanical problems look like electrical problems.** A dangling board, friction-fit jumpers, and a wedged pin all produced intermittent faults that were hard to tell apart from software bugs.
5. **Check that parts work together, not just individually.** The ESP32 and the BNO08x are both good parts. On I²C, they're a documented bad pairing. A few minutes on forums before buying would have saved weeks.
6. **Trust the chip's own labels, not the board around it.** The expansion dock's silkscreen was offset from the actual pins.
7. **Dry-fit before soldering.** Header orientation and fit are much easier to fix before the solder goes on.
8. **Bench tests don't show everything.** My hand-shake test topped out around 6 g. Real sprinting passed the sensor's 8 g limit on the first field test.
