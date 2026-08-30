/**
 * HeuristicMesh Unified Configuration
 * 
 * Central configuration header for ESP32 firmware
 * All tunable parameters in one place
 * 
 * Author: HeuristicMesh Engineering Team
 * Version: 1.1
 * Date: 2026-08-29
 * Note: MLX90640 support removed - only 2x AMG8833 sensors in inventory
 */

#pragma once

// ============================================================================
// HARDWARE CONFIGURATION
// ============================================================================

// ESP32-S3 Pin Definitions
#define I2C_SDA            8      // Default I2C SDA pin
#define I2C_SCL            9      // Default I2C SCL pin
#define UART_TX           43      // UART TX for USR-TCP232
#define UART_RX           44      // UART RX for USR-TCP232
#define STATUS_LED         2      // Status LED (active low)
#define BOOT_BUTTON        0      // Boot mode button

// Alternative pin definitions for different boards
#ifdef ESP32_S2
    #undef I2C_SDA
    #undef I2C_SCL
    #define I2C_SDA        21     // ESP32-S2 default I2C
    #define I2C_SCL        22
#endif

// ============================================================================
// SENSOR CONFIGURATION
// ============================================================================

// I2C Addresses
#define AMG_I2C_ADDR_DEFAULT  0x69  // AD0 pulled HIGH
#define AMG_I2C_ADDR_ALT     0x68  // AD0 pulled LOW

// Sensor capabilities
#define HAS_AMG8833          true
#define HAS_MLX90640         false  // DISABLED - No MLX90640 in inventory

// ============================================================================
// SERIAL COMMUNICATION CONFIGURATION
// ============================================================================

// Baud rates
#define USB_BAUD            921600  // For direct USB to Jetson
#define UART_BAUD           115200  // For USR-TCP232 connection
#define DEBUG_BAUD          115200  // For debug output

// Protocol settings
#define PROTOCOL_VERSION    0x01    // Current protocol version
#define PROTOCOL_MAGIC_0    0xAA    // First magic byte
#define PROTOCOL_MAGIC_1    0x55    // Second magic byte

// ============================================================================
// DEVICE CONFIGURATION
// ============================================================================

// Device identification
#define DEVICE_ID           1       // Unique per device (1-255)
#define DEVICE_NAME         "ESP32-S3-001"  // Human-readable name

// Device type codes
#define DEVICE_ESP32_S3     0x01
#define DEVICE_ESP32_S2     0x02
#define DEVICE_ESP32_GENERIC 0x03

// Sensor type codes
#define SENSOR_NONE         0x00
#define SENSOR_AMG8833      0x01

// ============================================================================
// TIMING CONFIGURATION
// ============================================================================

// AMG8833 polling
#define AMG_POLL_MS         50      // ~20Hz polling rate
#define AMG_POLL_MIN_MS     10      // Minimum polling interval

// Status and heartbeat
#define STATUS_INTERVAL_MS   1000    // Heartbeat interval
#define WATCHDOG_TIMEOUT_MS   5000    // Watchdog timeout

// ============================================================================
// THERMAL THRESHOLDS (Tunable via baseline capture)
// ============================================================================

// Human detection
#define HUMAN_TEMP_THRESHOLD  27.5f   // Minimum temp for human (degrees C)
#define HOT_PIXEL_MIN_COUNT    3       // Minimum hot pixels for valid detection

// Centroid tracking
#define CENTROID_HISTORY      8       // Number of historical centroids to track
#define CENTROID_UPPER_HALF   4.0f    // y < 4.0 for fall candidate (0-7 range)

// Fall detection
#define VELOCITY_TRIGGER      1.8f    // Velocity threshold (pixels/frame)
#define PERSISTENCE_FRAMES     4       // Consecutive frames above threshold
#define CENTROID_DOWNWARD_DELTA 1.4f   // Minimum downward movement

// Confidence scoring (computed on Jetson)
#define BASE_CONFIDENCE        0.5f
#define VELOCITY_WEIGHT        0.05f   // Per 0.1 pixels/frame above threshold
#define PERSISTENCE_WEIGHT     0.1f    // Per frame
#define IMPACT_WEIGHT          0.1f    // If sudden stop detected
#define IMMOBILITY_WEIGHT      0.1f    // If post-fall stillness

// Alert thresholds
#define FALL_CONFIDENCE_THRESHOLD  0.85f  // Minimum for alert
#define NEAR_FALL_THRESHOLD        0.6f   // Minimum for near-fall

// ============================================================================
// MODBUS/TCP CONFIGURATION
// ============================================================================

// ModBus settings
#define MODBUS_ENABLED        false   // Set to true for USR-TCP232
#define MODBUS_UNIT_ID        1       // ModBus unit ID (1-247)
#define MODBUS_TRANSACTION_ID  1       // Transaction ID
#define MODBUS_PORT            502     // Standard ModBus/TCP port

// USR-TCP232 configuration
#define USR_TCP232_IP         "192.168.30.10"  // IP on VLAN 30
#define USR_TCP232_GATEWAY    "192.168.30.1"
#define USR_TCP232_NETMASK    "255.255.255.0"

// ============================================================================
// MQTT CONFIGURATION (Future)
// ============================================================================

#define MQTT_ENABLED          false   // Set to true to enable MQTT
#define MQTT_BROKER_IP        "192.168.10.100"  // NUC IP (VLAN 10)
#define MQTT_PORT             1883    // MQTT port
#define MQTT_TLS_PORT         8883    // MQTT TLS port
#define MQTT_CLIENT_ID        "ESP32-S3-001"
#define MQTT_KEEPALIVE        30      // Keepalive in seconds

// ============================================================================
// BUFFER SIZE CONFIGURATION
// ============================================================================

// Message buffers
#define MAX_MESSAGE_SIZE      3200    // Maximum message size (AMG frame + header)
#define RX_BUFFER_SIZE        1024    // Receive buffer size
#define TX_BUFFER_SIZE        1024    // Transmit buffer size

// Frame buffers
#define AMG_FRAME_BUFFER_SIZE  64      // AMG8833 pixels

// ============================================================================
// ERROR CODES
// ============================================================================

#define ERR_NONE              0x00    // No error
#define ERR_I2C_BUS           0x01    // I2C bus error
#define ERR_SENSOR_NOT_FOUND  0x02    // Sensor not detected
#define ERR_SENSOR_READ       0x03    // Sensor read error
#define ERR_SERIAL_OVERFLOW    0x04    // Serial buffer overflow
#define ERR_MEMORY            0x05    // Memory allocation error
#define ERR_CONFIG            0x06    // Configuration error
#define ERR_WATCHDOG          0x07    // Watchdog timeout
#define ERR_MODBUS            0x08    // ModBus error
#define ERR_MQTT              0x09    // MQTT error

// ============================================================================
// DEBUG CONFIGURATION
// ============================================================================

// Debug levels
#define DEBUG_NONE            0       // No debug output
#define DEBUG_ERROR           1       // Errors only
#define DEBUG_WARNING         2       // Errors and warnings
#define DEBUG_INFO            3       // Informational messages
#define DEBUG_VERBOSE         4       // Verbose output
#define DEBUG_ALL             5       // All debug messages

#define DEBUG_LEVEL           DEBUG_INFO  // Current debug level

// Debug output macros
#if DEBUG_LEVEL >= DEBUG_ERROR
    #define DEBUG_ERROR(x)    Serial.println(x)
#else
    #define DEBUG_ERROR(x)
#endif

#if DEBUG_LEVEL >= DEBUG_WARNING
    #define DEBUG_WARNING(x)  Serial.println(x)
#else
    #define DEBUG_WARNING(x)
#endif

#if DEBUG_LEVEL >= DEBUG_INFO
    #define DEBUG_INFO(x)     Serial.println(x)
#else
    #define DEBUG_INFO(x)
#endif

#if DEBUG_LEVEL >= DEBUG_VERBOSE
    #define DEBUG_VERBOSE(x)  Serial.println(x)
#else
    #define DEBUG_VERBOSE(x)
#endif
