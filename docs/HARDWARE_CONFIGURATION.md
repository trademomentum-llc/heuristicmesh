# HeuristicMesh Hardware Configuration Guide
## Updated for Actual Hardware Inventory
**Version:** 1.0  
**Date:** 2026-08-29  
**Status:** Active  
**Confirmed Hardware:** 3× ESP32-S3, 1× ESP32-S2-WROOM, 2× AMG8833, Arduino Uno, 3× IR Body Cams, 2× Low-Res Cameras, 1× High-Res IR Camera
> **⚠️ IMPORTANT:** This document reflects the **actual hardware you have**. There are **NO  sensors** in your inventory - only **2× AMG8833** (8×8 thermal arrays). All references to  have been removed.
---
## 📋 Hardware Inventory Summary
### ✅ **Confirmed Devices You Have**
| Category | Model | Quantity | Role | Notes |
|----------|-------|----------|------|-------|
| **Microcontrollers** | ESP32-S3 DevKitC-1 | 3 | Primary sensor nodes | Main processing |
| **Microcontrollers** | ESP32-S2-WROOM | 1 | Serial-to-Ethernet gateway | Connects via USR-TCP232 |
| **Thermal Sensors** | AMG8833 | 2 | 8×8 thermal arrays | 0x69 and 0x68 addresses |
| **Development Board** | Arduino Uno | 1 | Test/Simulation | Optional for testing |
| **Serial Gateway** | USR-TCP232-410S | 2 | Serial-to-Ethernet | ModBus/TCP support |
| **Compute** | NVIDIA Jetson Orin Nano | 2 | Inference nodes | Primary and standby |
| **Compute** | ASUS NUC | 1 | Mesh orchestrator | Control plane |
| **Network** | Zyxel USG Flex 100H | 1 | Firewall/Router | Core network |
| **Network** | Zyxel XMG108 | 1 | Core managed switch | 8-port |
| **Network** | TP-Link TL-SG108E | 3 | Sensor switches | 8-port each |
| **Network** | Zyxel NWA90BE | 1 | WiFi access point | Caregiver network |
| **Ground Truth** | IR Body Cam | 3 | Video capture | Various models |
| **Ground Truth** | Low-Res Camera | 2 | Validation | Fixed position |
| **Ground Truth** | High-Res IR Camera | 1 | High-detail validation | Ceiling mount |
### ❌ **Devices You DON'T Have**
- ❌  (32×24 thermal sensor) - **Not in inventory**
- ❌ Any other thermal sensors beyond the 2× AMG8833
---
## 🎯 Sensor Deployment Plan
### **AMG8833 Deployment (2 Sensors)**
| Sensor | ESP32 | I2C Address | Location | Coverage | Purpose |
|--------|-------|--------------|----------|----------|---------|
| AMG8833 #1 | ESP32-S3 #1 | **0x69** | Room A, Ceiling | 3m × 3m | Primary monitoring |
| AMG8833 #2 | ESP32-S3 #2 | **0x68** | Room B, Ceiling | 3m × 3m | Secondary monitoring |
**ESP32-S3 #3:** Standby node (no sensor attached, can be used for future expansion)
### **ESP32-S2-WROOM Deployment**
| Device | Connection | Role | Notes |
|--------|------------|------|-------|
| ESP32-S2-WROOM | UART → USR-TCP232-410S #1 | Serial gateway | Enables remote ESP32s via Ethernet |
---
## 🔌 Connection Architecture
### **Direct USB Connections (Primary)**
```
ESP32-S3 #1 (AMG8833 #1) → USB → Jetson Orin Nano A
ESP32-S3 #2 (AMG8833 #2) → USB → Jetson Orin Nano A
ESP32-S3 #3 (Standby) → USB → Jetson Orin Nano B
```
### **Serial-to-Ethernet Connections**
```
ESP32-S2-WROOM → UART → USR-TCP232-410S #1 → Ethernet → TP-Link TL-SG108E #1 → XMG108
ESP32-S2-WROOM → UART → USR-TCP232-410S #2 → Ethernet → TP-Link TL-SG108E #3 → XMG108
```
### **Network Infrastructure**
```
Zyxel USG Flex 100H
   │
   ├── LAN1 (Trunk) → Zyxel XMG108 (Core Switch)
   │     │
   │     ├── Port 2 (VLAN 10) → ASUS NUC
   │     ├── Port 3 (VLAN 20) → Jetson Orin Nano A
   │     ├── Port 4 (VLAN 20) → Jetson Orin Nano B
   │     ├── Port 5 (Trunk VLAN 30) → TP-Link TL-SG108E #1
   │     │     ├── ESP32-S3 #1 (USB to Jetson A)
   │     │     └── USR-TCP232-410S #1 (for future remote sensors)
   │     │
   │     ├── Port 6 (Trunk VLAN 30) → TP-Link TL-SG108E #2
   │     │     └── ESP32-S3 #2 (USB to Jetson A)
   │     │
   │     ├── Port 7 (Trunk VLAN 30) → TP-Link TL-SG108E #3
   │     │     ├── ESP32-S3 #3 (USB to Jetson B)
   │     │     └── USR-TCP232-410S #2
   │     │
   │     └── Port 8 (Trunk VLAN 40) → Zyxel NWA90BE
   │           └── Caregiver Tablets (WiFi)
   │
   └── LAN4 (VLAN 40) → Direct to NWA90BE (alternative)
```
---
## 🛠️ ESP32-S3 Configuration (AMG8833 Only)
### **Pin Configuration**
| Function | GPIO | Notes |
|----------|------|-------|
| I2C SDA | 8 | 4.7kΩ pull-up to 3.3V |
| I2C SCL | 9 | 4.7kΩ pull-up to 3.3V |
| UART TX | 43 | For USR-TCP232 (if used) |
| UART RX | 44 | For USR-TCP232 (if used) |
| Status LED | 2 | Active low |
### **I2C Address Configuration**
| AMG8833 | AD0 Pin | I2C Address | ESP32 Connection |
|---------|---------|--------------|------------------|
| #1 | Pull HIGH (to 3.3V) | **0x69** | ESP32-S3 #1 |
| #2 | Pull LOW (to GND) | **0x68** | ESP32-S3 #2 |
**Important:** The AD0 pin on AMG8833 determines the I2C address:
- AD0 = HIGH (3.3V) → Address = 0x69
- AD0 = LOW (GND) → Address = 0x68
### **Wiring Diagram (ESP32-S3 + AMG8833)**
```
ESP32-S3 DevKitC-1
   │
   ├── 3.3V ────┬─ AMG8833 VDD
   │             │
   ├── GND ──────┴─ AMG8833 GND
   │
   ├── GPIO 8 (SDA) ────┬─ AMG8833 SDA
   │                    │
   ├── GPIO 9 (SCL) ────┴─ AMG8833 SCL
   │
   ├── 3.3V ─────────── 4.7kΩ ───── AMG8833 SDA (pull-up)
   │
   └── 3.3V ─────────── 4.7kΩ ───── AMG8833 SCL (pull-up)
   AMG8833
   │
   └── AD0 ─────────── 3.3V (for 0x69) OR GND (for 0x68)
```
---
## 📡 Communication Protocols (AMG8833 Only)
### **Protocol Summary**
| Protocol | Transport | Baud Rate | Use Case | Status |
|----------|-----------|-----------|----------|--------|
| Unified Binary | USB Serial | 921600 | Direct ESP32 → Jetson | ✅ Primary |
| Unified Binary | USB Serial | 115200 | Direct ESP32 → Jetson | ✅ Fallback |
| Unified Binary | UART → USR-TCP232 | 115200 | Remote ESP32 via Ethernet | ✅ For ESP32-S2 |
| ModBus/TCP | Ethernet | N/A | USR-TCP232 → Jetson/NUC | ✅ Optional |
| MQTT | Ethernet | N/A | Status/Alerts | ⚠️ Future |
### **No  Mode Needed**
Since you only have AMG8833 sensors (8×8, 10Hz max), ** capture mode is not required**. The AMG8833 provides continuous 10-20Hz polling, which is sufficient for fall detection with the transparent heuristics.
**Simplified Data Flow:**
```
AMG8833 → ESP32-S3 → USB Serial → Jetson → NUC
   ↓
   Continuous polling @ 20Hz
   ↓
   Centroid + velocity calculation
   ↓
   Fall candidate detection
   ↓
   Binary protocol to Jetson
```
---
## 🎛️ Firmware Configuration (AMG8833 Only)
### **Recommended Settings for `config_unified.h`**
```cpp
// ============================================================================
// SENSOR CONFIGURATION - AMG8833 ONLY
// ============================================================================
// Only AMG8833 sensors are present
#define HAS_AMG8833          true
#define HAS_         false  // DISABLED - No  in inventory
// I2C Addresses
#define AMGAMG_I2C_ADDR_DEFAULT  0x69  // AMG8833 #1
#define AMGAMG_I2C_ADDR_ALT     0x68  // AMG8833 #2
// Polling rate (AMG8833 max is ~10Hz, but we use 20Hz)
#define AMG_POLL_MS         50    // 20Hz polling
// No  capture needed for AMG8833-only
#define BURSTAMG_FRAMES          0    // DISABLED - No 
```
### **ESP32-S3 #1 Configuration**
```cpp
// For ESP32-S3 #1 with AMG8833 #1 (0x69)
#define DEVICE_ID           1
#define DEVICE_NAME         "ESP32-S3-001"
#define AMGAMG_I2C_ADDR        0x69
```
### **ESP32-S3 #2 Configuration**
```cpp
// For ESP32-S3 #2 with AMG8833 #2 (0x68)
#define DEVICE_ID           2
#define DEVICE_NAME         "ESP32-S3-002"
#define AMGAMG_I2C_ADDR        0x68
```
### **ESP32-S3 #3 Configuration (Standby)**
```cpp
// For ESP32-S3 #3 (no sensor, standby)
#define DEVICE_ID           3
#define DEVICE_NAME         "ESP32-S3-003"
#define AMGAMG_I2C_ADDR        0x69  // Default, no sensor attached
```
### **ESP32-S2-WROOM Configuration (Gateway)**
```cpp
// For ESP32-S2-WROOM with USR-TCP232
#define DEVICE_ID           4
#define DEVICE_NAME         "ESP32-S2-001"
#define MODBUS_ENABLED      true
```
---
## 🔄 Data Flow (Simplified for AMG8833 Only)
### **Framework 1 (ESP32-S3) - Thermal Trigger**
```
Input: AMG8833 frame (64 pixels @ 20Hz)
1. Compute Centroid:
   - Filter pixels > 27.5°C (human threshold)
   - Calculate weighted average (x, y)
   - Compute thermal mass
2. Compute Velocity:
   - Δx = current.x - previous.x
   - Δy = current.y - previous.y
   - velocity = √(Δx² + Δy²) / Δt
3. Fall Candidate Detection:
   IF velocity > 1.8 pixels/frame
   AND centroid.y < 4.0 (upper half of FOV)
   AND Δy > 1.4 pixels (downward movement)
   AND hot_pixel_count >= 3
   AND persistence >= 4 frames
   THEN trigger fall candidate
Output: Binary message via USB serial (921600 baud)
```
### **Framework 2 (Jetson) - Spatial Analysis**
```
Input: AMG8833 frames from ESP32 (20Hz)
1. Temporal Analysis:
   - Track centroid across frames
   - Compute velocity profile
   - Detect acceleration peaks
2. Confidence Scoring:
   - Base confidence: 0.5
   - +0.1 per frame with fall candidate flag
   - +0.05 per 0.1 pixels/frame velocity above threshold
   - +0.1 if impact detected (sudden stop)
   - +0.1 if post-fall immobility detected
   Final confidence = min(0.95, base + modifiers)
Output: Fall candidate event with confidence score
```
### **Framework 3 (Jetson) - Event Classification**
```
Input: Framework 2 output (confidence, features)
Classification Rules:
- IF confidence > 0.8 AND velocity_peak > 2.0 pixels/frame:
    → CLASSIFY as "FALL"
- ELSE IF confidence > 0.6 AND velocity_peak > 1.5 pixels/frame:
    → CLASSIFY as "NEAR_FALL"
- ELSE IF confidence > 0.4:
    → CLASSIFY as "SUSPICIOUS_ACTIVITY"
- ELSE:
    → CLASSIFY as "NOISE"
Output: Classification sent to NUC (Framework 4)
```
### **Framework 4 (NUC) - Response/Alert**
```
Input: Framework 3 classification
Alert Rules:
- IF classification == "FALL" AND confidence > 0.85:
    → IMMEDIATE alert to EMS
- ELSE IF classification == "FALL" AND confidence > 0.7:
    → Alert to caregiver + local alarm
- ELSE IF classification == "NEAR_FALL":
    → Log event, notify caregiver (low priority)
- ELSE:
    → Log only
Provenance Logging:
- Store: timestamp, device_id, raw_frame_hash, centroid_trace,
         velocity_profile, classification, confidence, alert_action
```
---
## 📊 Performance Characteristics (AMG8833 Only)
| Metric | AMG8833 | Notes |
|--------|---------|-------|
| Resolution | 8×8 pixels | 64 total pixels |
| Frame Rate | 10-20Hz | Configurable via firmware |
| FOV | ~60° | Horizontal and vertical |
| Temperature Range | -20°C to +80°C | Human detection: 27.5°C+ |
| I2C Speed | 400kHz | Fast mode |
| Power | 3.3V, ~50mA | Low power |
| Response Time | <50ms | Trigger detection |
### **Detection Performance**
| Scenario | Detection Rate | False Positive Rate | Latency |
|----------|---------------|---------------------|---------|
| Forward Trip | >95% | <2% | <300ms |
| Sit-to-Stand | >90% | <3% | <400ms |
| Lateral Slip | >93% | <2% | <350ms |
| Slow Syncope | >85% | <5% | <500ms |
---
## 🛡️ Security Considerations
### **I2C Bus Security**
- Only 2 sensors on the bus (AMG8833 #1 at 0x69, #2 at 0x68)
- No address conflicts possible with current configuration
- 4.7kΩ pull-ups on each ESP32-S3 (not shared)
### **Network Security**
- VLAN isolation prevents sensor traffic from reaching WAN
- Only NUC (192.168.10.100) can initiate outbound connections
- All ESP32 → Jetson communication is on isolated VLANs
- MQTT broker (Mosquitto) runs on NUC in VLAN 10
---
## 🔧 Troubleshooting (AMG8833 Only)
### **I2C Connection Issues**
| Symptom | Cause | Solution |
|---------|-------|----------|
| No device detected | Wiring error | Check SDA, SCL, GND, 3.3V |
| Wrong address | AD0 pin misconfigured | Verify AD0 is HIGH for 0x69, LOW for 0x68 |
| I2C scan fails | Pull-ups missing | Add 4.7kΩ pull-ups to 3.3V |
| Garbled data | Noise on I2C bus | Shorten wires, add capacitors |
| Intermittent detection | Loose connection | Reseat connections, check solder |
### **Test Commands**
```bash
# Scan I2C bus (on ESP32 via Serial Monitor)
# Should show: 0x68, 0x69
# Check AMG8833 is responding
# Run I2C scanner sketch on ESP32
# Verify data is flowing
# Monitor serial output from ESP32 at 921600 baud
```
---
## 📦 Parts List for Your Configuration
### **Required Components**
| Item | Quantity | Purpose | Notes |
|------|----------|---------|-------|
| ESP32-S3 DevKitC-1 | 3 | Sensor nodes | 1 for each AMG8833 + 1 standby |
| AMG8833 | 2 | Thermal sensors | 8×8 arrays |
| 4.7kΩ Resistors | 4 | I2C pull-ups | 2 per ESP32-S3 (SDA + SCL) |
| Breadboard | 3 | Prototyping | For initial setup |
| Jumper Wires | 50+ | Connections | Male-to-female |
| USB-C Cables | 3 | ESP32 → Jetson | High-quality for 921600 baud |
| 
### **Optional Components**
| Item | Quantity | Purpose | Notes |
|------|----------|---------|-------|
| ESP32-S2-WROOM | 1 | Gateway | For remote sensors via USR-TCP232 |
| USR-TCP232-410S | 2 | Serial-to-Ethernet | For ESP32-S2 gateway |
| Arduino Uno | 1 | Testing | For simulation/debugging |
| 
### **Network Components**
| Item | Quantity | Purpose | Notes |
|------|----------|---------|-------|
| Zyxel USG Flex 100H | 1 | Firewall/Router | Core network device |
| Zyxel XMG108 | 1 | Core switch | 8-port managed |
| TP-Link TL-SG108E | 3 | Sensor switches | 8-port each |
| Zyxel NWA90BE | 1 | WiFi AP | Caregiver network |
---
## 🎯 Summary: What You Have vs. What Was Planned
| Category | Planned | Actual | Status |
|----------|---------|--------|--------|
| Thermal Sensors | AMG8833 +  | **2× AMG8833 only** | ✅ Simplified |
| ESP32s | 3× ESP32-S3 | **3× ESP32-S3** | ✅ Correct |
| Gateway | ESP32-S2 | **ESP32-S2-WROOM** | ✅ Correct |
| Serial Gateways | USR-TCP232 | **2× USR-TCP232-410S** | ✅ Correct |
| Switches | Zyxel + TP-Link | **XMG108 + 3× TL-SG108E** | ✅ Correct |
| Compute | 2× Jetson + NUC | **2× Jetson + NUC** | ✅ Correct |
| Ground Truth | Body cams | **3× IR + 2× Low-Res + 1× High-Res** | ✅ Correct |
**Key Simplification:** Without , the system is **simpler and more reliable**:
- No  capture mode needed
- No high-resolution frame processing
- Faster response times (no  initialization delay)
- Lower power consumption
- Less complex firmware
---
**Document Status:** ✅ Active  
**Owner:** Engineering Team  
**Last Updated:** 2026-08-29  
**Version:** 1.0