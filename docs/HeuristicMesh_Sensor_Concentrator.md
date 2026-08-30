# HeuristicMesh Sensor Concentrator
## AMG8833-Only Version

**Target Board:** ESP32-S3-DevKitC-1 (or equivalent with headers)  
**I2C Clock:** 400 kHz Fast Mode  
**Mode:** Chessboard @ 8 Hz (locked)  
**Transport:** Binary USB-CDC @ 921600 baud (MQTT path stubbed for later)  
**Date:** 2026-08-29  
**Version:** 1.1

---

## 📋 Overview

This document provides the **production bring-up artifact** for the HeuristicMesh sensor concentrator running on ESP32-S3. This version supports **AMG8833 sensors only** - MLX90640 support has been completely removed.

**Key Changes:**
- Only AMG8833 (8×8 thermal array) is supported
- 
- Simplified to continuous 20Hz polling
- Single sensor per ESP32-S3

---

## 🔌 Hardware Pinout & Pull-up Directive (Mandatory)

| Signal | ESP32-S3 GPIO | Notes |
|--------|---------------|-------|
| SDA | GPIO 8 | External 4.7 kΩ pull-up to 3.3 V |
| SCL | GPIO 9 | External 4.7 kΩ pull-up to 3.3 V |
| VCC | 3.3 V | **Never** use 5 V - both sensors are 3.3 V |
| GND | GND | Common ground plane |

**Important Notes:**
- Place the two 4.7 kΩ resistors **as close to the ESP32 headers as possible** to minimize bus capacitance
- AMG8833 AD0 pin → pull HIGH → address 0x69 (avoids collision)
- AMG8833 AD0 pin → pull LOW → address 0x68
- Confirm both devices appear on the I2C scan before proceeding to trigger tests

---

## 📄 platformio.ini

```ini
[env:esp32-s3-devkitc-1]
platform = espressif32
board = esp32-s3-devkitc-1
framework = arduino
monitor_speed = 921600
board_build.flash_mode = qio
board_build.f_cpu = 240000000L
lib_deps =
    adafruit/Adafruit AMG88xx @ ^1.1.1
    ; MLX90640 libraries removed - only AMG8833 sensors in inventory
build_flags =
    -D CORE_DEBUG_LEVEL=0
```

---

## 💻 src/main.cpp (Complete, Compilable Skeleton)

```cpp
#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_AMG88xx.h>

// ---------- Pin & Address Map ----------
#define I2C_SDA          8
#define I2C_SCL          9
#define AMG_I2C_ADDR     0x69          // AD0 pulled HIGH

// ---------- Timing Constants ----------
#define AMG_POLL_MS      50           // ~20 Hz

// ---------- State Machine ----------
enum class State : uint8_t { IDLE, STREAMING };
State state = State::IDLE;

// ---------- Sensor Objects ----------
Adafruit_AMG88xx amg;

// ---------- Buffers ----------
float amg_pixels[AMG88xx_PIXEL_ARRAY_SIZE];

// ---------- Trigger Heuristics (Framework 1 seed) ----------
float prev_centroid_y = 3.5f;          // centre of 0-7 range

void scanI2C() {
    Serial.println(F("[SYS] I2C bus scan..."));
    for (uint8_t a = 1; a < 127; a++) {
        Wire.beginTransmission(a);
        if (Wire.endTransmission() == 0)
            Serial.printf("[SYS] Found 0x%02X\n", a);
    }
}

bool checkFallTrigger() {
    amg.readPixels(amg_pixels);

    float sum = 0.0f, weighted_y = 0.0f;
    for (int i = 0; i < AMG88xx_PIXEL_ARRAY_SIZE; i++) {
        if (amg_pixels[i] > 27.0f) {               // human-body threshold
            sum += amg_pixels[i];
            weighted_y += amg_pixels[i] * (i / 8);
        }
    }
    if (sum < 1.0f) return false;

    float cy = weighted_y / sum;
    float dy = prev_centroid_y - cy;               // positive = downward
    prev_centroid_y = cy;

    // Rapid downward motion while still in upper half of FOV
    return (dy > 1.4f && cy < 4.0f);
}

void startStreaming() {
    Serial.println(F("[TRIG] Fall trigger accepted - starting stream"));
    state = State::STREAMING;
}

void streamFrames() {
    static uint32_t frame_count = 0;
    
    // Send AMG frame in binary format
    // Packet: 0xAA 0xBB | frame_type | timestamp | pixels...
    const uint8_t hdr[2] = {0xAA, 0xBB};
    uint8_t frame_type = 0x01;  // AMG frame
    uint64_t ts = esp_timer_get_time();
    
    Serial.write(hdr, 2);
    Serial.write(frame_type);
    Serial.write((uint8_t*)&ts, sizeof(ts));
    Serial.write((uint8_t*)amg_pixels, sizeof(float) * AMG88xx_PIXEL_ARRAY_SIZE);
    
    frame_count++;
    
    // Optional: Return to idle after a timeout
    // Or continue streaming indefinitely
}

void setup() {
    Serial.begin(921600);
    while (!Serial && millis() < 3000) delay(10);

    Wire.begin(I2C_SDA, I2C_SCL);
    Wire.setClock(400000);                         // Fast Mode

    scanI2C();

    if (!amg.begin(AMG_I2C_ADDR)) {
        Serial.println(F("[ERR] AMG8833 not found"));
        while (1) delay(1000);
    }
    Serial.println(F("[OK] AMG8833 ready"));

    Serial.println(F("[SYS] HeuristicMesh Sensor Concentrator v1.1 online"));
    Serial.println(F("[SYS] HeuristicMesh Sensor Concentrator v1.1 online"));
}

void loop() {
    switch (state) {
        case State::IDLE: {
            static uint32_t last = 0;
            if (millis() - last >= AMG_POLL_MS) {
                last = millis();
                if (checkFallTrigger()) startStreaming();
            }
            break;
        }
        case State::STREAMING:
            amg.readPixels(amg_pixels);
            streamFrames();
            // Continue streaming while in this state
            // To stop: external signal or timeout
            break;
    }
}
```

---

## 🚀 Production Bring-up Procedure

### Step 1: Hardware Setup

1. Mount AMG8833 sensors at specified locations
2. Connect I2C with pull-ups
3. Power on ESP32-S3
4. Verify I2C scan shows sensor at correct address

### Step 2: Software Setup

1. Install PlatformIO
2. Copy code to project directory
3. Configure platformio.ini for your environment
4. Build and upload

```bash
# Build
pio run -e esp32-s3-devkitc-1

# Upload
pio run -e esp32-s3-devkitc-1 -t upload

# Monitor
pio device monitor -e esp32-s3-devkitc-1 -b 921600
```

### Step 3: Verification

1. Check serial output for successful initialization
2. Verify AMG8833 detected at correct I2C address
3. Confirm frames are streaming at ~20Hz
4. Test fall trigger with manual movement

---

## 📊 Performance Characteristics

| Metric | Value |
|--------|-------|
| Frame Rate | ~20Hz (50ms polling) |
| Resolution | 8×8 pixels |
| Temperature Range | -20°C to +80°C |
| Human Detection Threshold | 27°C |
| I2C Speed | 400 kHz |
| Serial Baud | 921600 |
| Frame Size | 256 bytes (64 floats) |

---

## 🛠️ Troubleshooting

### Common Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| No serial output | USB driver | Install CP210x/CH340 driver |
| I2C scan empty | Wiring error | Check SDA, SCL, GND, 3.3V |
| Wrong address | AD0 misconfigured | Verify AD0 pull-up/down |
| Garbled data | Noise on I2C | Shorten wires, add capacitors |
| No trigger | Thresholds too high | Lower detection thresholds |
| False triggers | Thresholds too low | Increase detection thresholds |

---

## 📝 Changelog

### v1.1 (2026-08-29)
- **REMOVED** all MLX90640 references
- **REMOVED** burst mode (was for MLX90640 high-res capture)
- Simplified to AMG8833-only continuous streaming
- Updated for 2× AMG8833 sensor configuration

### v1.0 (2026-08-11)
- Initial version

---

**Document Status:** ✅ Active  
**Owner:** Engineering Team  
**Last Updated:** 2026-08-29  
**Version:** 1.1
