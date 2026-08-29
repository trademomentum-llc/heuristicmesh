# HeuristicMesh Sensor Concentrator — ESP32-S3 Firmware v1.0
## Production Bring-up Artifact (AMG8833 + MLX90640)
**Target Board:** ESP32-S3-DevKitC-1 (or equivalent with headers)  
**I2C Clock:** 400 kHz Fast Mode  
**MLX Mode:** Chessboard @ 8 Hz (locked)  
**Transport:** Binary USB-CDC @ 921600 baud (MQTT path stubbed for later)  
**Date:** 2026-08-11  

### 1. Hardware Pinout & Pull-up Directive (Mandatory)

| Signal     | ESP32-S3 GPIO | Notes                                      |
|------------|---------------|--------------------------------------------|
| SDA        | GPIO 8        | External 4.7 kΩ pull-up to 3.3 V           |
| SCL        | GPIO 9        | External 4.7 kΩ pull-up to 3.3 V           |
| VCC        | 3.3 V         | **Never** use 5 V — both sensors are 3.3 V |
| GND        | GND           | Common ground plane                        |

- Place the two 4.7 kΩ resistors **as close to the ESP32 headers as possible** to minimise bus capacitance.
- AMG8833 AD0 pin → pull HIGH → address 0x69 (avoids collision with MLX default 0x33).
- Confirm both devices appear on the I2C scan before proceeding to trigger tests.

### 2. platformio.ini

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
    adafruit/Adafruit MLX90640 @ ^1.0.2
    adafruit/Adafruit BusIO @ ^1.14.5
build_flags =
    -D CORE_DEBUG_LEVEL=0
```

### 3. src/main.cpp (Complete, Compilable Skeleton)

```
#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_AMG88xx.h>
#include <Adafruit_MLX90640.h>

// ---------- Pin & Address Map ----------
#define I2C_SDA          8
#define I2C_SCL          9
#define AMG_I2C_ADDR     0x69          // AD0 pulled HIGH
#define MLX_I2C_ADDR     0x33

// ---------- Timing & Buffer Constants ----------
#define AMG_POLL_MS      100           // ~10 Hz
#define BURST_FRAMES     24            // 3 s @ 8 Hz
#define FRAME_PIXELS     768

// ---------- State Machine ----------
enum class State : uint8_t { IDLE, BURST_CAPTURE, STREAMING };
State state = State::IDLE;

// ---------- Sensor Objects ----------
Adafruit_AMG88xx amg;
Adafruit_MLX90640 mlx;

// ---------- Buffers ----------
float amg_pixels[AMG88xx_PIXEL_ARRAY_SIZE];
float mlx_frame[FRAME_PIXELS];
float burst_buffer[BURST_FRAMES][FRAME_PIXELS];
uint8_t frame_idx = 0;
bool   burst_ready = false;
uint64_t burst_start_us = 0;           // hardware tick of first frame

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

void startBurst() {
    Serial.println(F("[BURST] Trigger accepted — starting 8 Hz Chess capture"));
    state = State::BURST_CAPTURE;
    frame_idx = 0;
    burst_ready = false;

    mlx.setMode(MLX90640_CHESS);
    mlx.setRefreshRate(MLX90640_8_HZ);
    delay(120);                                    // allow sensor to settle
    burst_start_us = esp_timer_get_time();
}

void captureBurst() {
    if (mlx.getFrame(mlx_frame) != 0) return;      // not ready yet

    memcpy(burst_buffer[frame_idx], mlx_frame, sizeof(float) * FRAME_PIXELS);
    frame_idx++;

    if (frame_idx >= BURST_FRAMES) {
        // Return to low-power standby
        mlx.setRefreshRate(MLX90640_1_HZ);
        burst_ready = true;
        state = State::STREAMING;
        Serial.println(F("[BURST] 24 frames captured — streaming"));
    }
}

void streamBurst() {
    static uint8_t out_idx = 0;
    if (!burst_ready) return;

    if (out_idx < BURST_FRAMES) {
        // Packet: 0xAA 0xBB | frame# (u8) | timestamp_us (u64) | 768 × float32 LE
        const uint8_t hdr[2] = {0xAA, 0xBB};
        Serial.write(hdr, 2);
        Serial.write(out_idx);

        uint64_t ts = (out_idx == 0) ? burst_start_us : burst_start_us + (out_idx * 125000ULL);
        Serial.write(reinterpret_cast<uint8_t*>(&ts), sizeof(ts));
        Serial.write(reinterpret_cast<uint8_t*>(burst_buffer[out_idx]), sizeof(float) * FRAME_PIXELS);

        out_idx++;
    } else {
        out_idx = 0;
        burst_ready = false;
        state = State::IDLE;
        Serial.println(F("[BURST] Stream complete — IDLE"));
    }
}

void setup() {
    Serial.begin(921600);
    while (!Serial && millis() < 3000) delay(10);

    Wire.begin(I2C_SDA, I2C_SCL);
    Wire.setClock(400000);                         // Fast Mode — required for 8 Hz

    scanI2C();

    if (!amg.begin(AMG_I2C_ADDR)) {
        Serial.println(F("[ERR] AMG8833 not found"));
        while (1) delay(1000);
    }
    Serial.println(F("[OK] AMG8833 ready"));

    if (!mlx.begin(MLX_I2C_ADDR, &Wire)) {
        Serial.println(F("[ERR] MLX90640 not found"));
        while (1) delay(1000);
    }
    mlx.setMode(MLX90640_CHESS);
    mlx.setResolution(MLX90640_ADC_18BIT);
    mlx.setRefreshRate(MLX90640_1_HZ);             // standby until trigger
    Serial.println(F("[OK] MLX90640 ready (Chess / 1 Hz standby)"));

    Serial.println(F("[SYS] HeuristicMesh Sensor Concentrator v1.0 online"));
}

void loop() {
    switch (state) {
        case State::IDLE: {
            static uint32_t last = 0;
            if (millis() - last >= AMG_POLL_MS) {
                last = millis();
                if (checkFallTrigger()) startBurst();
            }
            break;
        }
        case State::BURST_CAPTURE:
            captureBurst();
            break;
        case State::STREAMING:
            streamBurst();
            break;
    }
    delay(1);                                      // yield / watchdog
}
```
### 4. Bring-up Sequence (Today)

Solder the two 4.7 kΩ pull-ups on the breadboard (SDA/SCL to 3.3 V).
Connect AMG8833 only first; flash and confirm I2C scan + continuous “IDLE” behaviour.
Wave a warm hand across the array and force a rapid downward motion — observe [BURST] log.
Tomorrow (MLX90640 arrival): hot-plug, re-scan, confirm both addresses, then exercise full 24-frame binary stream.