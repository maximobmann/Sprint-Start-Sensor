/*
  Sensor Stream Test (v13)
  --------------------------------------------------------------------------
  Bring-up test for the BNO085 on the Feather RP2040. Does not use the SD card.

  Once per second it prints:
    v13 | samples/sec: N | resets: R | X: .. Y: .. Z: ..

  Pass criteria: samples/sec stays near 100, resets stays at 0 (or recovers
  immediately), and X/Y/Z sit near 0 at rest and spike when the sensor is shaken.
  Run it for at least 15 minutes.
*/

#include <Wire.h>
#include <Adafruit_BNO08x.h>

Adafruit_BNO08x bno08x;
sh2_SensorValue_t sensorValue;

unsigned long sampleCount = 0, resetCount = 0, lastPrint = 0;
float lastX = 0, lastY = 0, lastZ = 0;

void setReports() {
  if (!bno08x.enableReport(SH2_LINEAR_ACCELERATION, 10000)) {
    Serial.println("!! could not enable report");
  }
}

void setup() {
  Serial.begin(115200);
  delay(2000);
  Serial.println("===== FEATHER RP2040 v13 =====");

  if (bno08x.begin_I2C(0x4A, &Wire)) {
    Serial.println("found at 0x4A");
  } else if (bno08x.begin_I2C(0x4B, &Wire)) {
    Serial.println("found at 0x4B");
  } else {
    Serial.println("not found");
    while (1) delay(10);
  }
  setReports();
}

void loop() {
  if (bno08x.wasReset()) {
    resetCount++;
    setReports();
  }
  if (bno08x.getSensorEvent(&sensorValue)) {
    if (sensorValue.sensorId == SH2_LINEAR_ACCELERATION) {
      sampleCount++;
      lastX = sensorValue.un.linearAcceleration.x;
      lastY = sensorValue.un.linearAcceleration.y;
      lastZ = sensorValue.un.linearAcceleration.z;
    }
  }
  if (millis() - lastPrint >= 1000) {
    Serial.print("v13 | samples/sec: ");
    Serial.print(sampleCount);
    Serial.print(" | resets: ");
    Serial.print(resetCount);
    Serial.print(" | X: "); Serial.print(lastX);
    Serial.print(" Y: "); Serial.print(lastY);
    Serial.print(" Z: "); Serial.println(lastZ);
    sampleCount = 0;
    lastPrint = millis();
  }
}
