# Firmware

| Sketch | Purpose |
|---|---|
| [`sprint_logger/`](sprint_logger/sprint_logger.ino) | **Field logger.** 100 Hz linear acceleration → `runNNN.csv` on microSD. |
| [`tests/sensor_stream_test/`](tests/sensor_stream_test/sensor_stream_test.ino) | Checks the sensor alone: prints samples/s and reset count once per second. |
| [`tests/sd_card_test/`](tests/sd_card_test/sd_card_test.ino) | Checks the microSD card: detects it and writes `test.txt`. |

Every sketch prints a version banner on startup so the serial output always shows which code is actually on the board.

## Setup (one time)

1. Install **Arduino IDE 2.x**.
2. **File → Preferences → Additional boards manager URLs**, add:
   ```
   https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json
   ```
3. **Tools → Board → Boards Manager**, search `pico`, install **Raspberry Pi Pico/RP2040/RP2350** by Earle F. Philhower, III.
4. **Tools → Board → Raspberry Pi Pico/RP2040/RP2350 → Adafruit Feather RP2040**.
5. **Tools → Manage Libraries**, search `Adafruit BNO08x`, install it and choose **Install All** for its dependencies. The `SD` library comes with the board package.

## Uploading

1. Connect the Feather by USB-C (use a data cable; many USB-C cables are charge-only).
2. **First upload only:** hold the **BOOTSEL** button while plugging in, then release. The board appears as a drive named `RPI-RP2`. Ignore Windows' prompt about the drive.
3. Open the sketch and click **Upload**. After the first upload, the board appears as a normal COM port and BOOTSEL is no longer needed.
4. Open **Serial Monitor** at **115200 baud** and confirm the version banner.

## Using the logger

| Action | Result |
|---|---|
| Connect battery or USB | Waits 3 s, starts the sensor and SD card, opens the next `runNNN.csv`, starts logging |
| Disconnect power | Logging stops; everything up to the last ~1 s is saved |
| Copy data | Remove the microSD card, read it on a computer, rename per [`data/README.md`](../data/README.md) |

Serial messages at startup:

| Message | Meaning |
|---|---|
| `Sensor OK` / `SD OK` / `Logging to run003.csv` | Everything is working |
| `Sensor not found` | Check the STEMMA QT cable at both ends, then press RESET |
| `SD not detected` | Reseat the card; it must be FAT32 and ≤ 32 GB |
| `Failed to open file` | Card is full, write-protected, or corrupted; reformat as FAT32 |

## Known limitations

- **Timestamps are relative.** `time_ms` counts from power-up. Session date comes from the file name. (The Adalogger has a real-time clock; using it is on the roadmap.)
- **Records whenever powered**, including while charging. Each file contains everything from power-on to power-off.
- **±8 g sensor range.** Acceleration above about 78 m/s² is clipped by the sensor.
- **No start/stop button.** The analysis script finds the sprints inside each file.
