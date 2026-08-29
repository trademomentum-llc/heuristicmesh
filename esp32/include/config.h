#pragma once

// I2C pins for classic ESP32 DevKitC
#define I2C_SDA 21
#define I2C_SCL 22

// AMG8833
#define AMG_I2C_ADDR 0x69

// Thermal thresholds (°C)
#define HUMAN_TEMP_THRESHOLD 27.5f
#define HOT_PIXEL_MIN_COUNT  3

// Timing
#define FRAME_INTERVAL_MS    50      // 20 Hz
#define STATUS_INTERVAL_MS   500

// Serial protocol
#define SERIAL_BAUD          115200
#define PROTOCOL_MAGIC       0xA5

// Fall candidate logic
#define CENTROID_HISTORY     8
#define VELOCITY_TRIGGER     1.8f    // grid cells per frame (tuned later)
#define PERSISTENCE_FRAMES   4
