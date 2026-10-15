/*
  Sprint Logger (v17)
  --------------------------------------------------------------------------
  Logs linear acceleration from a BNO085 IMU at 100 Hz to a CSV file on a
  microSD card.

  Hardware:
    - Adafruit Feather RP2040
    - Adafruit BNO085 breakout, connected via STEMMA QT (I2C, address 0x4A)
    - Adafruit Adalogger FeatherWing (microSD on SPI, chip select = D10)

  Behavior:
    - On every power-up, creates the next unused file: run000.csv, run001.csv, ...
    - Header row: time_ms,x,y,z
    - time_ms = milliseconds since power-up; x, y, z in m/s^2 (gravity removed)
    - Flushes to the card once per second, so at most ~1 s is lost if power
      is cut. Recording runs until power is removed.
    - Also mirrors every row to the USB serial port (115200 baud) for checking.

  Libraries: Adafruit BNO08x (+ dependencies), SD (bundled with the RP2040 core)
  Board: "Adafruit Feather RP2040" (Earle Philhower arduino-pico core)
*/

#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <Adafruit_BNO08x.h>

#define SD_CS 10

Adafruit_BNO08x bno08x;
sh2_SensorValue_t sensorValue;
File dataFile;

void setReports() {
  bno08x.enableReport(SH2_LINEAR_ACCELERATION, 10000);  // 10,000 us = 100 Hz
}

void setup() {
  Serial.begin(115200);
  delay(3000);  // give the sensor time to boot before talking to it
  Serial.println("===== SPRINT LOGGER v17 =====");

  // Start sensor
  if (!bno08x.begin_I2C(0x4A, &Wire)) {
    if (!bno08x.begin_I2C(0x4B, &Wire)) {
      Serial.println("Sensor not found");
      while (1) delay(10);
    }
  }
  Serial.println("Sensor OK");
  setReports();

  // Start SD
  if (!SD.begin(SD_CS)) {
    Serial.println("SD not detected");
    while (1) delay(10);
  }
  Serial.println("SD OK");

  // Create a new file with a unique number so old runs aren't overwritten
  int fileNum = 0;
  char filename[16];
  while (true) {
    snprintf(filename, sizeof(filename), "run%03d.csv", fileNum);
    if (!SD.exists(filename)) break;
    fileNum++;
  }
  dataFile = SD.open(filename, FILE_WRITE);
  if (!dataFile) {
    Serial.println("Failed to open file");
    while (1) delay(10);
  }
  Serial.print("Logging to ");
  Serial.println(filename);
  dataFile.println("time_ms,x,y,z");
}

void loop() {
  // If the sensor reset itself, it forgets its report settings: re-enable them
  if (bno08x.wasReset()) setReports();

  if (bno08x.getSensorEvent(&sensorValue)) {
    if (sensorValue.sensorId == SH2_LINEAR_ACCELERATION) {
      unsigned long t = millis();
      float x = sensorValue.un.linearAcceleration.x;
      float y = sensorValue.un.linearAcceleration.y;
      float z = sensorValue.un.linearAcceleration.z;

      dataFile.print(t); dataFile.print(",");
      dataFile.print(x, 3); dataFile.print(",");
      dataFile.print(y, 3); dataFile.print(",");
      dataFile.println(z, 3);

      Serial.print(t); Serial.print(",");
      Serial.print(x, 3); Serial.print(",");
      Serial.print(y, 3); Serial.print(",");
      Serial.println(z, 3);
    }
  }

  // Flush to card every second so data actually gets written (not just buffered)
  static unsigned long lastFlush = 0;
  if (millis() - lastFlush >= 1000) {
    dataFile.flush();
    lastFlush = millis();
  }
}
