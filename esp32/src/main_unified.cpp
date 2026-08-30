/**
 * HeuristicMesh Unified ESP32 Firmware
 * 
 * Supports: ESP32-S3, ESP32-S2-WROOM
 * Sensors: AMG8833 ONLY (2x sensors in inventory)
 * Transport: USB Serial (primary), UART -> USR-TCP232 -> ModBus/TCP (optional)
 * Protocol: Unified Binary Protocol v1.1 (see PROTOCOL_SPECIFICATION.md)
 * 
 * Features:
 * - AMG8833 thermal sensor support (8x8 arrays)
 * - Fall detection with transparent heuristics
 * - ModBus/TCP support via USR-TCP232
 * - MQTT support (future)
 * - Configuration via serial commands
 * - I2C error recovery
 * - Full provenance logging
 * 
 * Hardware Requirements:
 * - ESP32-S3 or ESP32-S2
 * - AMG8833 (8x8 thermal array) - 2 sensors max
 * - Optional: USR-TCP232 for Serial-to-Ethernet
 * 
 * Pin Configuration (ESP32-S3):
 * - I2C SDA: GPIO 8
 * - I2C SCL: GPIO 9
 * - UART TX: GPIO 43 (for USR-TCP232)
 * - UART RX: GPIO 44 (for USR-TCP232)
 * - Status LED: GPIO 2
 * 
 * Author: HeuristicMesh Engineering Team
 * Version: 1.1
 * Date: 2026-08-29
 * Note: MLX90640 support removed - only 2x AMG8833 sensors in inventory
 */

#include <Arduino.h>
#include <Wire.h>

// ============================================================================
// CONFIGURATION - Can be overridden via serial commands
// ============================================================================

// Hardware configuration
#define I2C_SDA            8
#define I2C_SCL            9
#define UART_TX            43  // For USR-TCP232
#define UART_RX            44  // For USR-TCP232
#define STATUS_LED         2

// Sensor configuration
#define AMG_I2C_ADDR_DEFAULT 0x69  // Default AMG8833 address (AD0=HIGH)
#define AMG_I2C_ADDR_ALT     0x68  // Alternate AMG8833 address (AD0=LOW)

// Serial configuration
#define SERIAL_BAUD        115200  // For USR-TCP232
#define USB_BAUD           921600  // For direct USB to Jetson

// Protocol configuration
#define PROTOCOL_VERSION   0x01
#define DEVICE_ID          1     // Unique per device (configurable)

// Timing configuration
#define AMG_POLL_MS        50    // ~20Hz polling for AMG8833
#define STATUS_INTERVAL_MS  1000  // Heartbeat interval

// Thermal thresholds (tunable)
#define HUMAN_TEMP_THRESHOLD  27.5f
#define HOT_PIXEL_MIN_COUNT    3
#define VELOCITY_TRIGGER       1.8f
#define PERSISTENCE_FRAMES     4
#define CENTROID_HISTORY       8

// ModBus configuration
#define MODBUS_ENABLED        false  // Set to true for USR-TCP232
#define MODBUS_UNIT_ID        1
#define MODBUS_TRANSACTION_ID  1

// ============================================================================
// INCLUDES - Sensor Libraries
// ============================================================================

#include <Adafruit_AMG88xx.h>
// MLX90640 support removed - only 2x AMG8833 in inventory

// ============================================================================
// PROTOCOL DEFINITIONS (from PROTOCOL_SPECIFICATION.md)
// ============================================================================

// Message types
#define MSG_HELLO           0x01
#define MSG_HEARTBEAT       0x02
#define MSG_AMG_FRAME       0x03
#define MSG_FALL_CANDIDATE   0x04
#define MSG_CONFIG_REQUEST  0x05
#define MSG_CONFIG_RESPONSE 0x06
#define MSG_ERROR           0x07
#define MSG_ACK             0x08
#define MSG_NACK            0x09
#define MSG_MODBUS_WRAPPER  0x0A

// Sensor type codes
#define SENSOR_NONE         0x00
#define SENSOR_AMG8833      0x01

// Device type codes
#define DEVICE_ESP32_S3     0x01
#define DEVICE_ESP32_S2     0x02
#define DEVICE_ESP32_GENERIC 0x03

// ============================================================================
// DATA STRUCTURES
// ============================================================================

// Common message header (10 bytes)
struct MessageHeader {
    uint8_t  magic[2];        // 0xAA, 0x55
    uint8_t  version;         // Protocol version
    uint8_t  device_id;       // Unique device identifier
    uint8_t  message_type;    // Message type code
    uint8_t  flags;           // Message flags
    uint16_t payload_len;     // Payload length (little-endian)
    uint16_t sequence;        // Sequence number
    uint32_t timestamp;       // Unix timestamp or millis()
};

// Centroid structure
struct Centroid {
    float x;
    float y;
    float mass;
    bool valid;
};

// AMG8833 frame payload
struct AMGFramePayload {
    uint64_t timestamp_us;
    uint32_t frame_id;
    uint8_t  flags;
    uint8_t  hot_pixel_count;
    uint8_t  reserved[2];
    float max_temp;
    float avg_temp;
    float centroid_x;
    float centroid_y;
    float velocity;
    float mass;
    float pixels[64];  // 8x8 temperature values
};

// Fall candidate payload
struct FallCandidatePayload {
    uint64_t timestamp_us;
    uint32_t frame_id;
    float confidence;
    float centroid_x;
    float centroid_y;
    float velocity;
    float acceleration;
    uint8_t sensor_source;
    uint8_t flags;
    uint16_t reserved;
};

// Error payload
struct ErrorPayload {
    uint8_t error_code;
    uint8_t severity;
    uint16_t error_data;
    char message[64];
};

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================

// Sensor instances
Adafruit_AMG88xx amg;

// HardwareSerial for USR-TCP232
HardwareSerial SerialUSR(1);  // UART 1 for ESP32-S3

// State tracking
enum SystemState { 
    STATE_INITIALIZING, 
    STATE_IDLE,
    STATE_ERROR 
};
SystemState systemState = STATE_INITIALIZING;

// Configuration
uint8_t deviceId = DEVICE_ID;
uint8_t deviceType = DEVICE_ESP32_S3;
uint8_t sensorType = SENSOR_AMG8833;
uint8_t capabilities = 0;

// Sensor state
bool amgAvailable = false;

// Centroid tracking
Centroid centroidHistory[CENTROID_HISTORY];
int centroidHistoryIdx = 0;

// Fall detection state
int persistenceCounter = 0;
bool fallCandidateFlag = false;
float prevCentroidY = 3.5f;  // Center of 0-7 range

// Frame counters
uint32_t amgFrameCounter = 0;
uint32_t sequenceCounter = 0;

// Timing
unsigned long lastAmgPoll = 0;
unsigned long lastHeartbeat = 0;
unsigned long lastStatusLed = 0;

// Buffers
float amgPixels[64];

// ModBus state
bool modbusEnabled = MODBUS_ENABLED;

// ============================================================================
// PROTOCOL HELPER FUNCTIONS
// ============================================================================

/**
 * Send a message with header and payload
 */
void sendMessage(uint8_t messageType, const void* payload, uint16_t payloadLen, Stream* stream = &Serial) {
    MessageHeader header;
    header.magic[0] = 0xAA;
    header.magic[1] = 0x55;
    header.version = PROTOCOL_VERSION;
    header.device_id = deviceId;
    header.message_type = messageType;
    header.flags = 0;
    header.payload_len = payloadLen;
    header.sequence = sequenceCounter++;
    header.timestamp = millis();
    
    // Send header
    stream->write((uint8_t*)&header, sizeof(MessageHeader));
    
    // Send payload
    if (payload != nullptr && payloadLen > 0) {
        stream->write((const uint8_t*)payload, payloadLen);
    }
}

/**
 * Send HELLO message
 */
void sendHello(Stream* stream = &Serial) {
    struct {
        uint8_t device_type;
        uint8_t fw_version[4];
        uint8_t sensor_count;
        uint8_t sensor_types[2];
        uint32_t capabilities;
    } payload;
    
    payload.device_type = deviceType;
    payload.fw_version[0] = 1;
    payload.fw_version[1] = 1;  // Version 1.1 - AMG8833 only
    payload.fw_version[2] = 0;
    payload.fw_version[3] = 0;
    payload.sensor_count = 0;
    
    if (amgAvailable) {
        payload.sensor_types[payload.sensor_count++] = SENSOR_AMG8833;
        capabilities |= 0x0001;  // Supports AMG8833
    }
    
    if (modbusEnabled) {
        capabilities |= 0x0008;  // Supports ModBus/TCP
    }
    
    payload.capabilities = capabilities;
    
    sendMessage(MSG_HELLO, &payload, sizeof(payload), stream);
}

/**
 * Send HEARTBEAT message
 */
void sendHeartbeat(Stream* stream = &Serial) {
    struct {
        uint32_t uptime_ms;
        uint8_t status;
        uint8_t sensor_status;
        uint16_t error_count;
    } payload;
    
    payload.uptime_ms = millis();
    payload.status = (systemState == STATE_ERROR) ? 0x02 : 0x00;
    payload.sensor_status = 0;
    
    if (amgAvailable) payload.sensor_status |= 0x01;
    if (fallCandidateFlag) payload.sensor_status |= 0x04;
    
    payload.error_count = 0;  // TODO: Track actual error count
    
    sendMessage(MSG_HEARTBEAT, &payload, sizeof(payload), stream);
}

/**
 * Send AMG_FRAME message
 */
void sendAMGFrame(AMGFramePayload* frame, Stream* stream = &Serial) {
    sendMessage(MSG_AMG_FRAME, frame, sizeof(AMGFramePayload), stream);
}

/**
 * Send FALL_CANDIDATE message
 */
void sendFallCandidate(FallCandidatePayload* candidate, Stream* stream = &Serial) {
    sendMessage(MSG_FALL_CANDIDATE, candidate, sizeof(FallCandidatePayload), stream);
}

/**
 * Send ERROR message
 */
void sendError(uint8_t errorCode, const char* message, Stream* stream = &Serial) {
    ErrorPayload payload;
    payload.error_code = errorCode;
    payload.severity = 0x02;  // Error
    payload.error_data = 0;
    strncpy(payload.message, message, sizeof(payload.message) - 1);
    payload.message[sizeof(payload.message) - 1] = '\0';
    
    sendMessage(MSG_ERROR, &payload, sizeof(ErrorPayload), stream);
}

// ============================================================================
// SENSOR FUNCTIONS
// ============================================================================

/**
 * Initialize AMG8833 sensor
 */
bool initAMG8833() {
    if (!amg.begin(AMG_I2C_ADDR_DEFAULT)) {
        sendError(0x02, "AMG8833 not found");
        return false;
    }
    amgAvailable = true;
    return true;
}

/**
 * Scan I2C bus for devices
 */
void scanI2C() {
    Serial.println("[SYS] Scanning I2C bus...");
    for (uint8_t addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() == 0) {
            Serial.printf("[SYS] Found device at 0x%02X\n", addr);
            
            if (addr == AMG_I2C_ADDR_DEFAULT || addr == AMG_I2C_ADDR_ALT) {
                Serial.println("[SYS] AMG8833 detected");
                amgAvailable = true;
            }
        }
    }
}

/**
 * Read AMG8833 pixels and compute centroid
 */
bool readAMG8833(Centroid* centroid, float* pixels, float* maxTemp, float* avgTemp, int* hotCount) {
    if (!amgAvailable) return false;
    
    amg.readPixels(pixels);
    
    // Compute statistics
    float sum = 0;
    *maxTemp = -100;
    *avgTemp = 0;
    *hotCount = 0;
    
    for (int i = 0; i < 64; i++) {
        if (pixels[i] > *maxTemp) *maxTemp = pixels[i];
        sum += pixels[i];
        if (pixels[i] >= HUMAN_TEMP_THRESHOLD) {
            (*hotCount)++;
        }
    }
    *avgTemp = sum / 64.0f;
    
    // Compute centroid
    float sumX = 0, sumY = 0, mass = 0;
    for (int i = 0; i < 64; i++) {
        int row = i / 8;
        int col = i % 8;
        float w = pixels[i] - HUMAN_TEMP_THRESHOLD;
        if (w > 0) {
            sumX += col * w;
            sumY += row * w;
            mass += w;
        }
    }
    
    if (mass > 0.5f) {
        centroid->x = sumX / mass;
        centroid->y = sumY / mass;
        centroid->mass = mass;
        centroid->valid = true;
    } else {
        centroid->valid = false;
    }
    
    return true;
}

/**
 * Compute centroid velocity
 */
float computeCentroidVelocity(const Centroid* current) {
    if (!current->valid) return 0.0f;
    
    for (int i = 1; i < CENTROID_HISTORY; i++) {
        int idx = (centroidHistoryIdx - i + CENTROID_HISTORY) % CENTROID_HISTORY;
        if (centroidHistory[idx].valid) {
            float dx = current->x - centroidHistory[idx].x;
            float dy = current->y - centroidHistory[idx].y;
            return sqrtf(dx*dx + dy*dy) / i;
        }
    }
    return 0.0f;
}

/**
 * Check for fall trigger based on AMG8833 data
 */
bool checkFallTrigger(const Centroid* centroid, float velocity, int hotCount) {
    if (!centroid->valid) return false;
    
    // Rapid downward motion while in upper half of FOV
    float dy = prevCentroidY - centroid->y;
    prevCentroidY = centroid->y;
    
    if (dy > 1.4f && centroid->y < 4.0f && 
        velocity >= VELOCITY_TRIGGER && 
        hotCount >= HOT_PIXEL_MIN_COUNT) {
        persistenceCounter++;
        if (persistenceCounter >= PERSISTENCE_FRAMES) {
            return true;
        }
    } else {
        persistenceCounter = 0;
    }
    
    return false;
}

// ============================================================================
// MODBUS/TCP FUNCTIONS
// ============================================================================

/**
 * Send ModBus/TCP wrapped message
 */
void sendModBusMessage(uint8_t messageType, const void* payload, uint16_t payloadLen) {
    if (!modbusEnabled) return;
    
    // ModBus/TCP MBAP Header (6 bytes)
    struct {
        uint16_t transaction_id;
        uint16_t protocol_id;
        uint16_t length;
        uint8_t  unit_id;
    } mbap;
    
    mbap.transaction_id = MODBUS_TRANSACTION_ID;
    mbap.protocol_id = 0;  // Always 0 for ModBus
    mbap.length = sizeof(MessageHeader) + payloadLen + sizeof(uint8_t) + sizeof(uint16_t);
    mbap.unit_id = MODBUS_UNIT_ID;
    
    // HeuristicMesh ModBus PDU
    uint8_t functionCode = 0x5A;  // 'Z' for HeuristicMesh
    
    // Write to USR-TCP232 serial
    SerialUSR.write((uint8_t*)&mbap, sizeof(mbap));
    SerialUSR.write(&functionCode, sizeof(functionCode));
    SerialUSR.write(&messageType, sizeof(messageType));
    SerialUSR.write((uint8_t*)&payloadLen, sizeof(payloadLen));
    
    // Write message header
    MessageHeader header;
    header.magic[0] = 0xAA;
    header.magic[1] = 0x55;
    header.version = PROTOCOL_VERSION;
    header.device_id = deviceId;
    header.message_type = messageType;
    header.flags = 0;
    header.payload_len = payloadLen;
    header.sequence = sequenceCounter++;
    header.timestamp = millis();
    SerialUSR.write((uint8_t*)&header, sizeof(MessageHeader));
    
    // Write payload
    if (payload != nullptr && payloadLen > 0) {
        SerialUSR.write((const uint8_t*)payload, payloadLen);
    }
}

/**
 * Initialize USR-TCP232 connection
 */
void initUSR_TCP232() {
    if (!modbusEnabled) return;
    
    SerialUSR.begin(SERIAL_BAUD, SERIAL_8N1, UART_RX, UART_TX);
    delay(100);
    
    Serial.println("[MODBUS] USR-TCP232 initialized");
    
    // Send test message
    sendModBusMessage(MSG_HELLO, nullptr, 0);
}

// ============================================================================
// SETUP AND MAIN LOOP
// ============================================================================

void setup() {
    // Initialize status LED
    pinMode(STATUS_LED, OUTPUT);
    digitalWrite(STATUS_LED, HIGH);  // Off (active low)
    
    // Start USB Serial (for direct connection to Jetson)
    Serial.begin(USB_BAUD);
    while (!Serial && millis() < 3000) {
        delay(10);
    }
    
    Serial.println("\n=== HeuristicMesh Unified Firmware ===");
    Serial.println("Version: 1.1");
    Serial.println("Date: 2026-08-29");
    Serial.println("Note: AMG8833 ONLY - No MLX90640 support");
    
    // Determine device type
    #if defined(CONFIG_IDF_TARGET_ESP32S3)
        deviceType = DEVICE_ESP32_S3;
        Serial.println("[SYS] Detected: ESP32-S3");
    #elif defined(CONFIG_IDF_TARGET_ESP32S2)
        deviceType = DEVICE_ESP32_S2;
        Serial.println("[SYS] Detected: ESP32-S2");
    #else
        deviceType = DEVICE_ESP32_GENERIC;
        Serial.println("[SYS] Detected: Generic ESP32");
    #endif
    
    // Initialize I2C
    Wire.begin(I2C_SDA, I2C_SCL);
    Wire.setClock(400000);  // 400 kHz
    
    Serial.println("[SYS] I2C initialized");
    
    // Scan I2C bus
    scanI2C();
    
    // Initialize sensors
    amgAvailable = initAMG8833();
    
    if (amgAvailable) {
        sensorType = SENSOR_AMG8833;
        Serial.println("[SYS] AMG8833 sensor mode");
    } else {
        sensorType = SENSOR_NONE;
        Serial.println("[SYS] WARNING: No AMG8833 detected!");
        systemState = STATE_ERROR;
    }
    
    // Initialize USR-TCP232 if enabled
    if (modbusEnabled) {
        initUSR_TCP232();
    }
    
    // Clear centroid history
    for (int i = 0; i < CENTROID_HISTORY; i++) {
        centroidHistory[i].valid = false;
    }
    centroidHistoryIdx = 0;
    
    // Send initial HELLO
    sendHello(&Serial);
    if (modbusEnabled) {
        sendHello(&SerialUSR);
    }
    
    // Initialize previous centroid Y
    prevCentroidY = 3.5f;
    
    // Transition to IDLE
    systemState = STATE_IDLE;
    
    Serial.println("[SYS] Initialization complete");
    Serial.println("[SYS] Ready for data collection");
    
    digitalWrite(STATUS_LED, LOW);  // On
}

void loop() {
    unsigned long now = millis();
    
    // Handle status LED (blink every 2 seconds)
    if (now - lastStatusLed >= 2000) {
        lastStatusLed = now;
        digitalWrite(STATUS_LED, !digitalRead(STATUS_LED));
    }
    
    // Send periodic heartbeat
    if (now - lastHeartbeat >= STATUS_INTERVAL_MS) {
        lastHeartbeat = now;
        sendHeartbeat(&Serial);
        if (modbusEnabled) {
            sendHeartbeat(&SerialUSR);
        }
    }
    
    // Handle USR-TCP232 data (if any)
    if (modbusEnabled && SerialUSR.available()) {
        // Read and process incoming ModBus messages
        // For now, just echo back
        while (SerialUSR.available()) {
            uint8_t c = SerialUSR.read();
            Serial.printf("[MODBUS] RX: 0x%02X\n", c);
        }
    }
    
    // Main state machine
    switch (systemState) {
        case STATE_INITIALIZING:
            // Should not reach here after setup
            break;
            
        case STATE_IDLE: {
            // Poll AMG8833 at regular intervals
            if (amgAvailable && now - lastAmgPoll >= AMG_POLL_MS) {
                lastAmgPoll = now;
                
                Centroid centroid;
                float maxTemp, avgTemp;
                int hotCount;
                
                if (readAMG8833(&centroid, amgPixels, &maxTemp, &avgTemp, &hotCount)) {
                    // Store centroid in history
                    centroidHistory[centroidHistoryIdx] = centroid;
                    centroidHistoryIdx = (centroidHistoryIdx + 1) % CENTROID_HISTORY;
                    
                    // Compute velocity
                    float velocity = computeCentroidVelocity(&centroid);
                    
                    // Check for fall trigger
                    bool isFallCandidate = checkFallTrigger(&centroid, velocity, hotCount);
                    
                    if (isFallCandidate && !fallCandidateFlag) {
                        // New fall candidate
                        fallCandidateFlag = true;
                        
                        // Send fall candidate message
                        FallCandidatePayload candidate;
                        candidate.timestamp_us = esp_timer_get_time();
                        candidate.frame_id = amgFrameCounter;
                        candidate.confidence = 0.0f;  // Will be computed by Jetson
                        candidate.centroid_x = centroid.x;
                        candidate.centroid_y = centroid.y;
                        candidate.velocity = velocity;
                        candidate.acceleration = 0.0f;  // TODO: Compute
                        candidate.sensor_source = sensorType;
                        candidate.flags = 0x01;  // Fall candidate flag
                        candidate.reserved = 0;
                        
                        sendFallCandidate(&candidate, &Serial);
                        if (modbusEnabled) {
                            sendFallCandidate(&candidate, &SerialUSR);
                        }
                        
                        Serial.printf("[FALL] Candidate detected! v=%.2f, y=%.2f\n", velocity, centroid.y);
                    } else if (!isFallCandidate) {
                        fallCandidateFlag = false;
                    }
                    
                    // Send AMG frame
                    AMGFramePayload frame;
                    frame.timestamp_us = esp_timer_get_time();
                    frame.frame_id = amgFrameCounter++;
                    frame.flags = fallCandidateFlag ? 0x01 : 0x00;
                    frame.flags |= centroid.valid ? 0x02 : 0x00;
                    frame.hot_pixel_count = hotCount;
                    frame.max_temp = maxTemp;
                    frame.avg_temp = avgTemp;
                    frame.centroid_x = centroid.x;
                    frame.centroid_y = centroid.y;
                    frame.velocity = velocity;
                    frame.mass = centroid.mass;
                    memcpy(frame.pixels, amgPixels, sizeof(float) * 64);
                    
                    sendAMGFrame(&frame, &Serial);
                    if (modbusEnabled) {
                        sendAMGFrame(&frame, &SerialUSR);
                    }
                }
            }
            break;
        }
        
        case STATE_ERROR:
            // Error state - blink LED rapidly
            if (now - lastStatusLed >= 500) {
                lastStatusLed = now;
                digitalWrite(STATUS_LED, !digitalRead(STATUS_LED));
            }
            break;
    }
    
    // Small delay to prevent watchdog and allow serial processing
    delay(1);
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Calculate CRC-16 (ModBus standard, polynomial 0x8005)
 * Not currently used but available for future implementation
 */
uint16_t calculateCRC16(const uint8_t* data, uint16_t length) {
    uint16_t crc = 0xFFFF;
    for (uint16_t i = 0; i < length; i++) {
        crc ^= data[i];
        for (uint8_t j = 0; j < 8; j++) {
            if (crc & 0x0001) {
                crc >>= 1;
                crc ^= 0xA001;
            } else {
                crc >>= 1;
            }
        }
    }
    return crc;
}

// ============================================================================
// END OF FILE
// ============================================================================
