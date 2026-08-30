# HeuristicMesh Unified Protocol Specification

**Version:** 1.1  
**Date:** 2026-08-29  
**Status:** Active  
**Author:** HeuristicMesh Engineering Team

---

## 📋 Overview

This document defines the **unified binary protocol** for communication between HeuristicMesh edge devices (ESP32 + sensors) and compute nodes (Jetson, NUC). The protocol is designed to:

- Support **AMG8833 (8×8) thermal sensors only**
- Work over **direct USB serial** or **Serial-to-Ethernet ModBus/TCP** (USR-TCP232)
- Enable **MQTT** as an optional transport (future)
- Be **backward compatible** with existing implementations
- Support **multi-device** deployments

**Note:** MLX90640 support has been **completely removed**. Only **2× AMG8833 sensors** are present in the inventory.

---

## 🚀 Transport Layers

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

## 📧 Message Types

### Message Type Codes (1 byte)
| Code | Hex | Name | Description |
|------|-----|------|-------------|
| 0x01 | 0x01 | `HELLO` | Device identification and capabilities |
| 0x02 | 0x02 | `HEARTBEAT` | Keep-alive message |
| 0x03 | 0x03 | `AMG_FRAME` | AMG8833 single frame |
| 0x04 | 0x04 | `FALL_CANDIDATE` | Fall detection candidate |
| 0x05 | 0x05 | `CONFIG_REQUEST` | Request configuration |
| 0x06 | 0x06 | `CONFIG_RESPONSE` | Configuration data |
| 0x07 | 0x07 | `ERROR` | Error report |
| 0x08 | 0x08 | `ACK` | Acknowledgment |
| 0x09 | 0x09 | `NACK` | Negative acknowledgment |
| 0x0A | 0x0A | `MODBUS_WRAPPER` | ModBus/TCP wrapped message |

---

## 📜 Common Message Header

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
- Bits 3-7: Reserved

---

## 📥 Message Definitions

### 1. HELLO Message (0x01)
Sent on device startup or connection establishment.

**Payload (16 bytes):**
```c
struct HelloPayload {
    uint8_t  device_type;    // 0x01=ESP32-S3, 0x02=ESP32-S2, 0x03=ESP32-Generic
    uint8_t  fw_version[4];  // Firmware version (e.g., "1.1.0.0")
    uint8_t  sensor_count;   // Number of sensors attached (1 for AMG8833)
    uint8_t  sensor_types[2]; // Array of sensor type codes
    uint32_t capabilities;   // Bitmask of capabilities
};
```

**Sensor Type Codes:**
- `0x01` - AMG8833

**Capabilities Bitmask:**
- `0x0001` - Supports AMG8833
- `0x0008` - Supports ModBus/TCP
- `0x0010` - Supports MQTT
- `0x0020` - Supports OTA updates

---

### 2. HEARTBEAT Message (0x02)
Periodic keep-alive message (sent every 1 second).

**Payload (8 bytes):**
```c
struct HeartbeatPayload {
    uint32_t uptime_ms;      // Device uptime in milliseconds
    uint8_t  status;         // 0x00=OK, 0x01=Warning, 0x02=Error
    uint8_t  sensor_status;  // Bitmask: 0x01=AMG8833 OK, 0x02=Fall flag active
    uint16_t error_count;    // Number of errors since last heartbeat
};
```

---

### 3. AMG_FRAME Message (0x03)
Single frame from AMG8833 sensor (8×8 thermal array).

**Payload (84 bytes):**
```c
struct AMGFramePayload {
    // Frame metadata (20 bytes)
    uint64_t timestamp_us;    // Microsecond timestamp
    uint32_t frame_id;        // Sequential frame counter
    uint8_t  flags;           // Frame flags
    uint8_t  hot_pixel_count; // Number of pixels above human threshold
    uint8_t  reserved[2];     // Alignment
    float    max_temp;        // Maximum temperature in frame (°C)
    float    avg_temp;        // Average temperature in frame (°C)
    float    centroid_x;      // Centroid X coordinate (0-7)
    float    centroid_y;      // Centroid Y coordinate (0-7)
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

### 4. FALL_CANDIDATE Message (0x04)
Fall detection candidate event from ESP32.

**Payload (32 bytes):**
```c
struct FallCandidatePayload {
    uint64_t timestamp_us;    // Microsecond timestamp
    uint32_t frame_id;        // Frame ID that triggered candidate
    float    confidence;       // Initial confidence score (0.0-1.0)
    float    centroid_x;      // Centroid X position
    float    centroid_y;      // Centroid Y position
    float    velocity;        // Velocity at detection (pixels/frame)
    float    acceleration;    // Acceleration estimate
    uint8_t  sensor_source;   // Source sensor type (0x01=AMG8833)
    uint8_t  flags;           // Detection flags
    uint16_t reserved;        // Alignment
};
```

---

### 5. CONFIG_REQUEST Message (0x05)
Request configuration from device.

**Payload:** Variable length, configuration parameters requested

---

### 6. CONFIG_RESPONSE Message (0x06)
Configuration data response.

**Payload:** Variable length, configuration key-value pairs

---

### 7. ERROR Message (0x07)
Error report from device.

**Payload:** Variable length, error details string

---

### 8. ACK Message (0x08)
Acknowledgment of received message.

**Payload:** 0 bytes (header only)

---

### 9. NACK Message (0x09)
Negative acknowledgment.

**Payload:** 0 bytes (header only)

---

### 10. MODBUS_WRAPPER Message (0x0A)
ModBus/TCP wrapped message for USR-TCP232 transport.

**Payload:** Variable length, wrapped HeuristicMesh message

---

## 🔄 Protocol Examples

### Example 1: Normal AMG Frame Transmission
```
ESP32 --> Jetson:
  Header: AA 55 01 01 03 00 54 00 00 00 00 00 00
  (Magic: AA 55, Version: 01, Device: 01, Type: AMG_FRAME, 
   Flags: 00, Payload: 84 bytes, Sequence: 00 00)
  
  Payload: [84 bytes of AMGFramePayload]
```

### Example 2: Fall Candidate Detection
```
ESP32 --> Jetson:
  Header: AA 55 01 01 04 00 20 00 00 00 00 00 00
  (Magic: AA 55, Version: 01, Device: 01, Type: FALL_CANDIDATE,
   Flags: 00, Payload: 32 bytes, Sequence: 00 00)
  
  Payload: [32 bytes of FallCandidatePayload]
```

### Example 3: Heartbeat
```
ESP32 --> Jetson:
  Header: AA 55 01 01 02 00 08 00 00 00 00 00 00
  (Magic: AA 55, Version: 01, Device: 01, Type: HEARTBEAT,
   Flags: 00, Payload: 8 bytes, Sequence: 00 00)
  
  Payload: [8 bytes of HeartbeatPayload]
```

---

## 📊 Payload Size Summary

| Message Type | Payload Size | Total Message Size |
|--------------|--------------|-------------------|
| HELLO | 16 bytes | 26 bytes |
| HEARTBEAT | 8 bytes | 18 bytes |
| AMG_FRAME | 84 bytes | 94 bytes |
| FALL_CANDIDATE | 32 bytes | 42 bytes |
| CONFIG_REQUEST | Variable | Variable |
| CONFIG_RESPONSE | Variable | Variable |
| ERROR | Variable | Variable |
| ACK | 0 bytes | 10 bytes |
| NACK | 0 bytes | 10 bytes |
| MODBUS_WRAPPER | Variable | Variable |

---

## 🛡️ Error Handling

All errors are reported via ERROR message (0x07) with error codes:

| Code | Hex | Description |
|------|-----|-------------|
| 0x01 | 0x01 | I2C bus error |
| 0x02 | 0x02 | Sensor not detected |
| 0x03 | 0x03 | Sensor read error |
| 0x04 | 0x04 | Serial overflow |
| 0x05 | 0x05 | Memory error |
| 0x06 | 0x06 | Configuration error |
| 0x07 | 0x07 | Watchdog timeout |
| 0x08 | 0x08 | ModBus error |

---

## 🎯 Implementation Notes

### ESP32 Side
- Use `Serial.write()` for binary protocol
- Always send complete messages (header + payload)
- Increment sequence number for each message
- Use `millis()` for timestamp
- Flush serial after each message for reliability

### Jetson Side
- Read serial in binary mode
- Parse header first, then payload
- Handle partial messages gracefully
- Validate magic bytes
- Check payload length matches header

### Endianness
- All multi-byte fields are **little-endian**
- This matches ESP32 (XTensa) and x86/x64 architecture

---

## 📝 Changelog

### v1.1 (2026-08-29)
- **REMOVED** MLX90640 and burst mode support completely
- Only AMG8833 sensors (2×) are now supported
- Simplified message types (removed MLX_FRAME, BURST_* messages)
- Updated sensor type codes and capabilities

### v1.0 (2026-08-28)
- Initial version

---

**Document Status:** ✅ Active  
**Owner:** Engineering Team  
**Last Updated:** 2026-08-29  
**Version:** 1.1
