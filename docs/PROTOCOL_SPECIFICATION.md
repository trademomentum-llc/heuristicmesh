# HeuristicMesh Unified Protocol Specification

**Version:** 1.0  
**Date:** 2026-08-29  
**Status:** Draft  
**Author:** HeuristicMesh Engineering Team

---

## 📋 Overview

This document defines the **unified binary protocol** for communication between HeuristicMesh edge devices (ESP32 + sensors) and compute nodes (Jetson, NUC). The protocol is designed to:

- Support **both AMG8833 (8×8) and MLX90640 (32×24)** thermal sensors
- Work over **direct USB serial** or **Serial-to-Ethernet ModBus/TCP** (USR-TCP232)
- Enable **MQTT** as an optional transport (future)
- Be **backward compatible** with existing implementations
- Support **multi-device** deployments

---

## 🔌 Transport Layers

### Layer 1: Physical
| Transport | Connection | Baud Rate | Protocol |
|-----------|------------|-----------|----------|
| USB Serial | ESP32 → Jetson USB | 921600 or 115200 | Binary |
| UART Serial | ESP32 → USR-TCP232 | 115200 | Binary |
| Ethernet | USR-TCP232 → Jetson/NUC | 100Mbps | ModBus/TCP or Raw TCP |
| WiFi | ESP32 → Network | N/A | MQTT (future) |

### Layer 2: Protocol
```
+------------------+------------------+------------------+
| Transport Layer  |  TCP/UDP/MQTT    |  Serial/UART     |
+------------------+------------------+------------------+
|                  | ModBus/TCP       |                  |
+------------------+------------------+------------------+
| Application Layer| HeuristicMesh    | HeuristicMesh    |
|                  | Binary Protocol  | Binary Protocol  |
+------------------+------------------+------------------+
```

---

## 📦 Message Types

### Message Type Codes (1 byte)
| Code | Hex | Name | Description |
|------|-----|------|-------------|
| 0x01 | 0x01 | `HELLO` | Device identification and capabilities |
| 0x02 | 0x02 | `HEARTBEAT` | Keep-alive message |
| 0x03 | 0x03 | `AMG_FRAME` | AMG8833 single frame |
| 0x04 | 0x04 | `MLX_FRAME` | MLX90640 single frame |
| 0x05 | 0x05 | `BURST_START` | Burst capture start notification |
| 0x06 | 0x06 | `BURST_FRAME` | Burst frame (part of sequence) |
| 0x07 | 0x07 | `BURST_END` | Burst capture end |
| 0x08 | 0x08 | `FALL_CANDIDATE` | Fall detection candidate |
| 0x09 | 0x09 | `CONFIG_REQUEST` | Request configuration |
| 0x0A | 0x0A | `CONFIG_RESPONSE` | Configuration data |
| 0x0B | 0x0B | `ERROR` | Error report |
| 0x0C | 0x0C | `ACK` | Acknowledgment |
| 0x0D | 0x0D | `NACK` | Negative acknowledgment |
| 0x80 | 0x80 | `MODBUS_WRAPPER` | ModBus/TCP wrapped message |

---

## 📐 Common Message Header

All messages start with a **10-byte header**:

```c
// Common Header (10 bytes)
struct MessageHeader {
    uint8_t  magic[2];      // 0xAA, 0x55 (big-endian for easy detection)
    uint8_t  version;       // Protocol version (currently 0x01)
    uint8_t  device_id;     // Unique device identifier (0-255)
    uint8_t  message_type;  // From Message Type Codes table
    uint8_t  flags;         // Message flags
    uint16_t payload_len;   // Payload length (little-endian)
    uint16_t sequence;      // Sequence number for ordering
    uint32_t timestamp;     // Unix timestamp or millis() since boot
};
```

**Magic Bytes:** `0xAA 0x55` - Chosen for easy detection in serial streams  
**Version:** `0x01` - Current protocol version  
**Flags:**
- Bit 0: `0x01` - Compressed payload
- Bit 1: `0x02` - Encrypted payload (future)
- Bit 2: `0x04` - Requires acknowledgment
- Bit 3: `0x08` - Part of burst sequence
- Bits 4-7: Reserved

---

## 📡 Message Definitions

### 1. HELLO Message (0x01)
Sent on device startup or connection establishment.

**Payload (16 bytes):**
```c
struct HelloPayload {
    uint8_t  device_type;    // 0x01=ESP32-AMG, 0x02=ESP32-MLX, 0x03=ESP32-Dual
    uint8_t  fw_version[4];  // Firmware version (e.g., "1.0.0.0")
    uint8_t  sensor_count;   // Number of sensors attached
    uint8_t  sensor_types[2]; // Array of sensor type codes
    uint32_t capabilities;   // Bitmask of capabilities
};
```

**Sensor Type Codes:**
- `0x01` - AMG8833
- `0x02` - MLX90640
- `0x03` - Both (Dual mode)

**Capabilities Bitmask:**
- `0x0001` - Supports AMG8833
- `0x0002` - Supports MLX90640
- `0x0004` - Supports burst mode
- `0x0008` - Supports ModBus/TCP
- `0x0010` - Supports MQTT
- `0x0020` - Supports OTA updates

---

### 2. HEARTBEAT Message (0x02)
Periodic keep-alive message.

**Payload (8 bytes):**
```c
struct HeartbeatPayload {
    uint32_t uptime_ms;      // Device uptime in milliseconds
    uint8_t  status;         // 0x00=OK, 0x01=Warning, 0x02=Error
    uint8_t  sensor_status;  // Bitmask of sensor health
    uint16_t error_count;    // Number of errors since last heartbeat
};
```

---

### 3. AMG_FRAME Message (0x03)
Single frame from AMG8833 sensor.

**Payload (64 + 20 = 84 bytes):**
```c
struct AMGFramePayload {
    // Frame metadata (20 bytes)
    uint64_t timestamp_us;    // Microsecond timestamp
    uint32_t frame_id;        // Sequential frame counter
    uint8_t  flags;           // Frame flags
    uint8_t  hot_pixel_count; // Number of pixels above threshold
    uint8_t  reserved[2];     // Alignment
    float    max_temp;        // Maximum temperature in frame
    float    avg_temp;        // Average temperature in frame
    float    centroid_x;      // Centroid X (0-7)
    float    centroid_y;      // Centroid Y (0-7)
    float    velocity;        // Centroid velocity (pixels/frame)
    float    mass;            // Thermal mass estimate
    
    // Pixel data (64 floats = 256 bytes)
    float    pixels[64];      // 8x8 temperature values
};
```

**Frame Flags:**
- `0x01` - Fall candidate detected
- `0x02` - Centroid valid
- `0x04` - Hot pixels above threshold
- `0x08` - Motion detected

---

### 4. MLX_FRAME Message (0x04)
Single frame from MLX90640 sensor.

**Payload (768 * 4 + 20 = 3092 bytes):**
```c
struct MLXFramePayload {
    // Frame metadata (20 bytes)
    uint64_t timestamp_us;    // Microsecond timestamp
    uint32_t frame_id;        // Sequential frame counter
    uint8_t  flags;           // Frame flags
    uint8_t  reserved[3];     // Alignment
    float    max_temp;        // Maximum temperature in frame
    float    avg_temp;        // Average temperature in frame
    float    min_temp;        // Minimum temperature in frame
    
    // Pixel data (768 floats = 3072 bytes)
    float    pixels[768];     // 32x24 temperature values
};
```

---

### 5. BURST_START Message (0x05)
Notification that burst capture is starting.

**Payload (12 bytes):**
```c
struct BurstStartPayload {
    uint64_t burst_id;        // Unique burst identifier
    uint8_t  sensor_type;     // 0x01=AMG8833, 0x02=MLX90640
    uint8_t  frame_rate;      // Frames per second (e.g., 8 for MLX90640)
    uint16_t frame_count;     // Number of frames in burst
    uint32_t trigger_reason;  // Reason for burst trigger
};
```

**Trigger Reasons:**
- `0x0001` - Fall candidate from AMG8833
- `0x0002` - Manual trigger
- `0x0003` - External GPIO trigger
- `0x0004` - MIDI trigger
- `0x0005` - Scheduled capture

---

### 6. BURST_FRAME Message (0x06)
Single frame within a burst sequence.

**Payload (varies by sensor):**
- For AMG8833: Same as AMG_FRAME payload (84 bytes)
- For MLX90640: Same as MLX_FRAME payload (3092 bytes)

**Additional Header Fields:**
```c
struct BurstFrameHeader {
    uint64_t burst_id;        // Burst identifier (matches BURST_START)
    uint16_t frame_index;     // Index within burst (0 to N-1)
    uint16_t total_frames;    // Total frames in burst
};
```

---

### 7. BURST_END Message (0x07)
Notification that burst capture is complete.

**Payload (8 bytes):**
```c
struct BurstEndPayload {
    uint64_t burst_id;        // Burst identifier
    uint16_t frames_captured; // Actual number of frames captured
    uint8_t  status;          // 0x00=Success, 0x01=Partial, 0x02=Failed
    uint8_t  reserved;        // Alignment
};
```

---

### 8. FALL_CANDIDATE Message (0x08)
Notification of a potential fall detection.

**Payload (32 bytes):**
```c
struct FallCandidatePayload {
    uint64_t timestamp_us;    // Timestamp of detection
    uint32_t frame_id;        // Frame ID where fall was detected
    float    confidence;      // Detection confidence (0.0 to 1.0)
    float    centroid_x;      // Centroid X at detection
    float    centroid_y;      // Centroid Y at detection
    float    velocity;        // Velocity at detection
    float    acceleration;    // Acceleration estimate
    uint8_t  sensor_source;   // 0x01=AMG8833, 0x02=MLX90640, 0x03=Both
    uint8_t  flags;           // Detection flags
    uint16_t reserved;        // Alignment
};
```

**Detection Flags:**
- `0x01` - Rapid downward motion
- `0x02` - Sustained hot mass
- `0x04` - Impact detected
- `0x08` - Post-fall immobility

---

### 9. CONFIG_REQUEST Message (0x09)
Request current configuration.

**Payload (4 bytes):**
```c
struct ConfigRequestPayload {
    uint32_t config_mask;     // Bitmask of requested config items
};
```

**Config Mask Bits:**
- `0x0001` - Sensor thresholds
- `0x0002` - Network settings
- `0x0004` - Serial settings
- `0x0008` - Device identification
- `0x0010` - All settings

---

### 10. CONFIG_RESPONSE Message (0x0A)
Response to configuration request.

**Payload (variable, JSON format):**
```json
{
    "device_id": "ESP32-001",
    "sensors": {
        "amg8833": {
            "enabled": true,
            "address": 0x69,
            "threshold_c": 27.5,
            "poll_interval_ms": 50
        },
        "mlx90640": {
            "enabled": true,
            "address": 0x33,
            "refresh_rate": 8,
            "burst_frames": 24
        }
    },
    "serial": {
        "baud": 115200,
        "protocol": "binary"
    },
    "network": {
        "modbus_enabled": true,
        "modbus_address": 1,
        "mqtt_enabled": false
    }
}
```

---

### 11. ERROR Message (0x0B)
Error report from device.

**Payload (variable):**
```c
struct ErrorPayload {
    uint8_t  error_code;      // Error code
    uint8_t  severity;        // 0x00=Info, 0x01=Warning, 0x02=Error, 0x03=Fatal
    uint16_t error_data;      // Error-specific data
    char     message[64];    // Human-readable error message (null-terminated)
};
```

**Error Codes:**
| Code | Hex | Description |
|------|-----|-------------|
| 0x01 | 0x01 | I2C bus error |
| 0x02 | 0x02 | Sensor not found |
| 0x03 | 0x03 | Sensor read error |
| 0x04 | 0x04 | Serial overflow |
| 0x05 | 0x05 | Memory error |
| 0x06 | 0x06 | Configuration error |
| 0x07 | 0x07 | Watchdog timeout |
| 0x08 | 0x08 | ModBus error |

---

### 12. ACK/NACK Messages (0x0C, 0x0D)
Acknowledgment messages.

**Payload (4 bytes):**
```c
struct AckPayload {
    uint16_t ack_sequence;   // Sequence number being acknowledged
    uint8_t  ack_type;        // 0x00=Generic, 0x01=Message received, 0x02=Processed
    uint8_t  reserved;        // Alignment
};
```

---

## 🔄 ModBus/TCP Wrapper

For Serial-to-Ethernet via USR-TCP232, messages are wrapped in a ModBus/TCP header.

### ModBus/TCP Frame Format
```
+------------------+------------------+------------------+
| MBAP Header      | HeuristicMesh    | CRC (optional)   |
| (6 bytes)         | Message          | (2 bytes)        |
+------------------+------------------+------------------+
```

**MBAP Header:**
```c
struct MBAPHeader {
    uint16_t transaction_id;  // Transaction identifier
    uint16_t protocol_id;     // Always 0 for ModBus
    uint16_t length;          // Length of following data (PDU + HM message)
    uint8_t  unit_id;         // Device/unit identifier
};
```

**HeuristicMesh ModBus PDU:**
```c
struct HMModBusPDU {
    uint8_t  function_code;   // 0x5A ('Z') for HeuristicMesh custom function
    uint8_t  message_type;   // From Message Type Codes table
    uint16_t payload_len;    // Length of HeuristicMesh message
    // HeuristicMesh message follows (header + payload)
};
```

### ModBus/TCP Configuration
| Parameter | Value | Description |
|-----------|-------|-------------|
| IP Address | Device-specific | USR-TCP232 IP on VLAN 30 |
| Port | 502 | Standard ModBus/TCP port |
| Unit ID | 1-247 | Configurable per device |
| Function Code | 0x5A | HeuristicMesh custom function |

---

## 📊 Message Size Summary

| Message Type | Header | Payload | Total |
|--------------|--------|---------|-------|
| HELLO | 10 | 16 | 26 bytes |
| HEARTBEAT | 10 | 8 | 18 bytes |
| AMG_FRAME | 10 | 84 | 94 bytes |
| MLX_FRAME | 10 | 3092 | 3102 bytes |
| BURST_START | 10 | 12 | 22 bytes |
| BURST_FRAME (AMG) | 10 | 84 + 8 | 102 bytes |
| BURST_FRAME (MLX) | 10 | 3092 + 8 | 3110 bytes |
| BURST_END | 10 | 8 | 18 bytes |
| FALL_CANDIDATE | 10 | 32 | 42 bytes |
| CONFIG_REQUEST | 10 | 4 | 14 bytes |
| CONFIG_RESPONSE | 10 | Variable (JSON) | Variable |
| ERROR | 10 | Variable | Variable |
| ACK/NACK | 10 | 4 | 14 bytes |

---

## 🎯 Implementation Guidelines

### ESP32 Side
1. **Buffer Management**: Use ring buffers for outgoing messages
2. **Message Construction**: Build complete message before sending
3. **Error Handling**: Send ERROR message on critical failures
4. **Flow Control**: Respect ACK/NACK for critical messages
5. **Timeout**: Implement message timeout and retry

### Jetson/NUC Side
1. **Message Parsing**: Parse header first, then payload
2. **Validation**: Check magic bytes, version, and checksum
3. **Buffer Management**: Handle partial messages (TCP stream)
4. **Multi-Device**: Track devices by device_id
5. **Error Recovery**: Request retransmission on error

---

## 🔍 Backward Compatibility

### Legacy Protocol v1 (0xA5)
The existing `0xA5` protocol from `esp32/src/main.cpp` can be supported as a **legacy mode**:

```c
// Legacy packet format (19 bytes)
struct LegacyPacket {
    uint8_t  magic;          // 0xA5
    uint32_t frame_id;       // Frame counter
    uint8_t  flags;          // Fall candidate + centroid valid
    int16_t  max_temp_x100;  // max temp * 100
    int16_t  avg_temp_x100;  // avg temp * 100
    uint8_t  hot_count;      // Hot pixel count
    int16_t  cx_x100;        // Centroid X * 100
    int16_t  cy_x100;        // Centroid Y * 100
    int16_t  vel_x100;       // Velocity * 100
    int16_t  mass_x10;       // Mass * 10
};
```

**Migration Path:**
1. New devices use unified protocol (version 0x01)
2. Legacy devices continue to work with existing `hm_ingest.py`
3. Jetson ingest detects protocol version and handles accordingly

---

## 📝 Checksum and Validation

### CRC-16 (Optional)
For critical applications, add a CRC-16 checksum at the end of each message:

```c
uint16_t crc = crc16(message_header + message_payload, header.payload_len + sizeof(MessageHeader));
```

**CRC-16 Polynomial:** `0x8005` (ModBus standard)

### Validation Steps
1. Check magic bytes (`0xAA 0x55`)
2. Check version (`0x01`)
3. Check payload length matches actual data
4. Verify CRC-16 (if enabled)
5. Parse message based on message_type

---

## 🧪 Testing

### Test Vectors
| Test | Description | Expected Result |
|------|-------------|-----------------|
| TV-01 | Valid HELLO message | Parsed correctly, device registered |
| TV-02 | Valid AMG_FRAME message | Frame data extracted, centroid computed |
| TV-03 | Valid MLX_FRAME message | Frame data extracted |
| TV-04 | Invalid magic bytes | Message discarded, error logged |
| TV-05 | Invalid version | Message discarded, ERROR sent |
| TV-06 | Payload length mismatch | Message discarded, ERROR sent |
| TV-07 | CRC failure | Message discarded, ERROR sent |
| TV-08 | Burst sequence (START + N×FRAME + END) | All frames received in order |

---

## 📚 References

- [ModBus/TCP Specification](http://www.modbus.org/specs.php)
- [HeuristicMesh Design Spec](01-system-architecture.md)
- [HeuristicMesh Tech Spec](HeuristicMesh_Tech_Spec.md)
- [ESP32 Serial Documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/uart.html)

---

**Document Status:** ✅ Draft  
**Owner:** Engineering Team  
**Last Updated:** 2026-08-29  
**Version:** 1.0
