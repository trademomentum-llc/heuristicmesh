#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_AMG88xx.h>
#include <SparkFun_MLX90640.h>

// --- Hardware Defines ---
#define I2C_SDA 8
#define I2C_SCL 9
#define AMG_ADDR 0x69       // AD0 pin pulled HIGH
#define MLX_ADDR 0x33

// --- State Machine ---
enum SystemState { IDLE, BURST_CAPTURE, STREAMING_OUT };
SystemState state = IDLE;

// --- Sensor Instances ---
Adafruit_AMG88xx amg;
MLX90640 mlx;

// --- Buffers ---
float amg_pixels[AMG88xx_PIXEL_ARRAY_SIZE];
float mlx_frame[768];
float burst_buffer[24][768];  // 24 frames @ 8Hz = 3 seconds
uint8_t frame_count = 0;
bool burst_ready = false;

// --- Trigger Heuristics ---
float prev_centroid_y = 2.0;   // Normalized 0-7
unsigned long trigger_timer = 0;

// --- I2C Scanning Helper (for boot diagnostics) ---
void scanI2C() {
    Serial.println("[SYS] Scanning I2C bus...");
    for (uint8_t addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() == 0) {
            Serial.printf("[SYS] Device found at 0x%02X\n", addr);
        }
    }
}

// --- AMG Polling & Trigger Logic ---
bool checkFallTrigger() {
    amg.readPixels(amg_pixels);
    
    // Compute centroid (simple weighted average across 8x8 grid)
    float total_temp = 0;
    float weighted_y = 0;
    for (int i = 0; i < AMG88xx_PIXEL_ARRAY_SIZE; i++) {
        int row = i / 8;
        if (amg_pixels[i] > 26.0) { // Only consider warm objects (human body)
            total_temp += amg_pixels[i];
            weighted_y += amg_pixels[i] * row;
        }
    }
    if (total_temp == 0) return false;
    float centroid_y = weighted_y / total_temp; // 0-7 range
    
    // Velocity check: rapid downward movement (falling)
    float delta_y = prev_centroid_y - centroid_y; // Positive = moving down
    prev_centroid_y = centroid_y;

    // Trigger threshold: Downward velocity > 1.5 rows per 100ms AND centroid in upper half
    if (delta_y > 1.5 && centroid_y < 4.0) {
        return true;
    }
    return false;
}

// --- MLX90640 Burst Capture ---
void startBurst() {
    Serial.println("[BURST] Trigger accepted. Starting MLX capture...");
    state = BURST_CAPTURE;
    frame_count = 0;
    burst_ready = false;
    
    // Set MLX to 8Hz Chessboard mode (interleaved)
    mlx.setMode(MLX90640_CHESS);
    mlx.setRefreshRate(MLX90640_8_HZ);
    delay(100); // Settling time
}

void captureBurst() {
    if (state != BURST_CAPTURE) return;
    
    if (mlx.isFrameReady() && frame_count < 24) {
        // Capture the raw float data (already temperature compensated by library)
        mlx.getFrame(mlx_frame);
        
        // Copy to burst buffer with timestamp offset
        memcpy(burst_buffer[frame_count], mlx_frame, sizeof(float) * 768);
        frame_count++;
        
        if (frame_count >= 24) {
            burst_ready = true;
            state = STREAMING_OUT;
            // Return MLX to standby to save power
            mlx.setRefreshRate(MLX90640_1_HZ);
            mlx.setMode(MLX90640_CHESS);
            Serial.println("[BURST] Capture complete. Ready to stream.");
        }
    }
}

// --- Binary Serial Protocol ---
// Packet structure: 
// HEADER (0xAA 0xBB) | FRAME_COUNT (uint8) | TIMESTAMP_US (uint64) | FRAME DATA (768 x float)
void streamBurst() {
    if (!burst_ready) return;
    
    // We'll stream frame-by-frame to avoid blocking the serial bus for too long.
    static uint8_t stream_index = 0;
    
    if (stream_index < 24) {
        // Send header + metadata
        uint8_t header[2] = {0xAA, 0xBB};
        Serial.write(header, 2);
        Serial.write(stream_index);
        
        // Timestamp (ESP32 hardware tick, microseconds)
        uint64_t ts = esp_timer_get_time();
        Serial.write((uint8_t*)&ts, sizeof(ts));
        
        // Send the 768 floats (4 bytes each) directly in little-endian
        Serial.write((uint8_t*)burst_buffer[stream_index], sizeof(float) * 768);
        
        stream_index++;
    } else {
        // All frames sent. Reset.
        stream_index = 0;
        burst_ready = false;
        state = IDLE;
        Serial.println("[BURST] Stream complete. Returning to IDLE.");
    }
}

// --- Setup ---
void setup() {
    Serial.begin(921600);
    Wire.begin(I2C_SDA, I2C_SCL);
    Wire.setClock(400000); // Fast mode for MLX

    scanI2C();

    // Init AMG8833
    if (!amg.begin(AMG_ADDR)) {
        Serial.println("[ERR] AMG8833 not found! Check wiring.");
    } else {
        Serial.println("[OK] AMG8833 initialized.");
    }

    // Init MLX90640
    mlx.begin(MLX_ADDR, Wire);
    mlx.setMode(MLX90640_CHESS);
    mlx.setRefreshRate(MLX90640_1_HZ); // Standby until trigger
    delay(50);
    
    // Get MLX EEPROM parameters (required for accurate math)
    int paramError = mlx.getParameters();
    if (paramError != 0) {
        Serial.printf("[ERR] MLX90640 EEPROM read failed: %d\n", paramError);
    } else {
        Serial.println("[OK] MLX90640 initialized.");
    }

    prev_centroid_y = 2.0; // Initial calibration assumption
    Serial.println("[SYS] HeuristicMesh ESP32 Sensor Concentrator ready.");
}

// --- Main Loop ---
void loop() {
    switch (state) {
        case IDLE:
            // Poll AMG at ~10 Hz (non-blocking)
            static unsigned long last_poll = 0;
            if (millis() - last_poll > 100) {
                last_poll = millis();
                if (checkFallTrigger()) {
                    startBurst();
                }
            }
            break;

        case BURST_CAPTURE:
            captureBurst();
            break;

        case STREAMING_OUT:
            streamBurst();
            break;
    }

    // Small yield to prevent watchdog
    delay(1);
}