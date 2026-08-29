#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_AMG88xx.h>
#include "config.h"

Adafruit_AMG88xx amg;

float pixels[AMG88xx_PIXEL_ARRAY_SIZE];

struct Centroid {
  float x;
  float y;
  float mass;
  bool  valid;
};

Centroid history[CENTROID_HISTORY];
int histIdx = 0;
int persistence = 0;
bool fallCandidate = false;

uint32_t lastFrame = 0;
uint32_t lastStatus = 0;
uint32_t frameCounter = 0;

Centroid computeCentroid() {
  Centroid c = {0, 0, 0, false};
  float sumX = 0, sumY = 0, mass = 0;

  for (int i = 0; i < 64; i++) {
    if (pixels[i] >= HUMAN_TEMP_THRESHOLD) {
      int row = i / 8;
      int col = i % 8;
      float w = pixels[i] - HUMAN_TEMP_THRESHOLD;
      sumX += col * w;
      sumY += row * w;
      mass += w;
    }
  }

  if (mass > 0.5f) {
    c.x = sumX / mass;
    c.y = sumY / mass;
    c.mass = mass;
    c.valid = true;
  }
  return c;
}

float centroidVelocity(const Centroid& current) {
  if (!current.valid) return 0.0f;

  // Look back a few frames for a previous valid centroid
  for (int i = 1; i < CENTROID_HISTORY; i++) {
    int idx = (histIdx - i + CENTROID_HISTORY) % CENTROID_HISTORY;
    if (history[idx].valid) {
      float dx = current.x - history[idx].x;
      float dy = current.y - history[idx].y;
      return sqrtf(dx*dx + dy*dy) / i;
    }
  }
  return 0.0f;
}

void emitBinaryFrame(const Centroid& c, float maxT, float avgT, int hotCount, float vel) {
  // Compact binary packet for Jetson
  // Magic (1) | frame (4) | flags (1) | maxT (2) | avgT (2) | hot (1) | cx (2) | cy (2) | vel (2) | mass (2)
  uint8_t buf[19];
  buf[0] = PROTOCOL_MAGIC;
  memcpy(&buf[1], &frameCounter, 4);

  uint8_t flags = 0;
  if (fallCandidate) flags |= 0x01;
  if (c.valid)       flags |= 0x02;
  buf[5] = flags;

  int16_t maxT_c = (int16_t)(maxT * 100);
  int16_t avgT_c = (int16_t)(avgT * 100);
  int16_t cx_c   = (int16_t)(c.x * 100);
  int16_t cy_c   = (int16_t)(c.y * 100);
  int16_t vel_c  = (int16_t)(vel * 100);
  int16_t mass_c = (int16_t)(c.mass * 10);

  memcpy(&buf[6],  &maxT_c, 2);
  memcpy(&buf[8],  &avgT_c, 2);
  buf[10] = (uint8_t)hotCount;
  memcpy(&buf[11], &cx_c, 2);
  memcpy(&buf[13], &cy_c, 2);
  memcpy(&buf[15], &vel_c, 2);
  memcpy(&buf[17], &mass_c, 2);

  Serial.write(buf, sizeof(buf));
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(1000);

  Wire.begin(I2C_SDA, I2C_SCL);
  Wire.setClock(400000);

  if (!amg.begin(AMG_I2C_ADDR)) {
    Serial.println("FATAL: AMG8833 not detected");
    while (1) delay(1000);
  }

  // Clear history
  for (int i = 0; i < CENTROID_HISTORY; i++) {
    history[i].valid = false;
  }

  Serial.println("HM-ESP32 ready");
}

void loop() {
  uint32_t now = millis();
  if (now - lastFrame < FRAME_INTERVAL_MS) return;
  lastFrame = now;
  frameCounter++;

  amg.readPixels(pixels);

  float maxT = -100, sum = 0;
  int hotCount = 0;
  for (int i = 0; i < 64; i++) {
    if (pixels[i] > maxT) maxT = pixels[i];
    sum += pixels[i];
    if (pixels[i] >= HUMAN_TEMP_THRESHOLD) hotCount++;
  }
  float avgT = sum / 64.0f;

  Centroid c = computeCentroid();
  history[histIdx] = c;
  histIdx = (histIdx + 1) % CENTROID_HISTORY;

  float vel = centroidVelocity(c);

  // Simple fall-candidate heuristic
  if (c.valid && vel >= VELOCITY_TRIGGER && hotCount >= HOT_PIXEL_MIN_COUNT) {
    persistence++;
    if (persistence >= PERSISTENCE_FRAMES) {
      fallCandidate = true;
    }
  } else {
    persistence = 0;
    fallCandidate = false;
  }

  // Always emit binary telemetry
  emitBinaryFrame(c, maxT, avgT, hotCount, vel);

  // Human-readable status at lower rate
  if (now - lastStatus >= STATUS_INTERVAL_MS) {
    lastStatus = now;
    Serial.print("F:");
    Serial.print(frameCounter);
    Serial.print(" Max:");
    Serial.print(maxT, 1);
    Serial.print(" Hot:");
    Serial.print(hotCount);
    Serial.print(" C:");
    if (c.valid) {
      Serial.print(c.x, 1);
      Serial.print(",");
      Serial.print(c.y, 1);
    } else {
      Serial.print("-");
    }
    Serial.print(" V:");
    Serial.print(vel, 2);
    if (fallCandidate) Serial.print(" FALL");
    Serial.println();
  }
}
