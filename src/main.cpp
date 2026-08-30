#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_AMG88xx.h>

// --- Hardware Defines ---
#define I2C_SDA 8
#define I2C_SCL 9
#define AMG_ADDR_DEFAULT 0x69       // AD0 pin pulled HIGH
#define AMG_ADDR_ALT     0x68       // AD0 pin pulled LOW

// --- State Machine ---
enum SystemState { IDLE, STREAMING_OUT };
SystemState state = IDLE;

// --- Sensor Instances ---
Adafruit_AMG88xx amg;

// --- Buffers ---
float amg_pixels[AMG88xx_PIXEL_ARRAY_SIZE];

// --- Trigger Heuristics ---
float prev_centroid_y = 3.5;   // Center of 0-7 range
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
        int col = i % 8;
        
        if (amg_pixels[i] > 27.0f) {  // Human temperature threshold
            total_temp += amg_pixels[i];
            weighted_y += amg_pixels[i] * row;
        }
    }
    
    if (total_temp < 1.0f) return false;
    
    float cy = weighted_y / total_temp;
    float dy = prev_centroid_y - cy;  // positive = downward
    prev_centroid_y = cy;
    
    // Rapid downward motion while still in upper half of FOV
    return (dy > 1.4f && cy < 4.0f);
}

void setup() {
    Serial.begin(921600);
    while (!Serial && millis() < 3000) delay(10);
    
    Wire.begin(I2C_SDA, I2C_SCL);
    Wire.setClock(400000);  // Fast Mode
    
    Serial.println("[SYS] HeuristicMesh Sensor Node v1.1");

    
    scanI2C();
    
    if (!amg.begin(AMG_ADDR_DEFAULT)) {
        Serial.println("[ERR] AMG8833 not found at 0x69");
        if (!amg.begin(AMG_ADDR_ALT)) {
            Serial.println("[ERR] AMG8833 not found at 0x68");
            while (1) delay(1000);
        } else {
            Serial.println("[OK] AMG8833 found at 0x68");
        }
    } else {
        Serial.println("[OK] AMG8833 found at 0x69");
    }
    
    state = IDLE;
    Serial.println("[SYS] Ready - waiting for fall triggers");
}

void loop() {
    static unsigned long last_poll = 0;
    
    // Poll AMG8833 at ~20Hz (50ms interval)
    if (millis() - last_poll >= 50) {
        last_poll = millis();
        
        if (checkFallTrigger()) {
            state = STREAMING_OUT;
            trigger_timer = millis();
            Serial.println("[FALL] Trigger detected!");
        }
    }
    
    // In streaming state, send frames continuously
    if (state == STREAMING_OUT) {
        // Send AMG frame data
        // Format: 0xAA 0xBB | frame_type | timestamp | pixels...
        const uint8_t hdr[2] = {0xAA, 0xBB};
        uint8_t frame_type = 0x01;  // AMG frame
        uint64_t ts = micros();
        
        Serial.write(hdr, 2);
        Serial.write(frame_type);
        Serial.write((uint8_t*)&ts, sizeof(ts));
        Serial.write((uint8_t*)amg_pixels, sizeof(float) * AMG88xx_PIXEL_ARRAY_SIZE);
        
        // Return to idle (optional)
        if (millis() - trigger_timer > 500) {
            state = IDLE;
            Serial.println("[FALL] Stream complete");
        }
    }
    
    delay(1);
}
