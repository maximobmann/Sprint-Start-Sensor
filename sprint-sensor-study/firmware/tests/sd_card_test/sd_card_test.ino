/*
  SD Card Test
  --------------------------------------------------------------------------
  Bring-up test for the Adalogger FeatherWing's microSD socket on the
  Feather RP2040. Checks that the card is detected and writes test.txt.

  Expected output:
    ===== SD TEST =====
    SD card detected!
    Wrote test.txt successfully

  If the card isn't detected: check it is fully inserted, 32 GB or smaller,
  and formatted FAT32.
*/

#include <SPI.h>
#include <SD.h>

#define SD_CS 10  // Adalogger's SD chip-select pin

void setup() {
  Serial.begin(115200);
  delay(2000);
  Serial.println("===== SD TEST =====");

  if (!SD.begin(SD_CS)) {
    Serial.println("SD card NOT detected -- check card is inserted, formatted FAT32, and <=32GB");
    while (1) delay(10);
  }
  Serial.println("SD card detected!");

  // Try to create a test file
  File f = SD.open("test.txt", FILE_WRITE);
  if (f) {
    f.println("hello from feather");
    f.close();
    Serial.println("Wrote test.txt successfully");
  } else {
    Serial.println("Failed to open test.txt for writing");
  }
}

void loop() {}
