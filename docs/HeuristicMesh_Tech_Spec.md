# Technical Specifications
## HeuristicMesh Fall Detection System – Hardware & Software Stack
**Document Version:** 1.0  
**Date:** 2026-08-11  

### 1. Compute Nodes
| Role                    | Hardware                  | OS / Runtime                          | Primary Function                          |
|-------------------------|---------------------------|---------------------------------------|-------------------------------------------|
| Control Plane / Orchestrator | ASUS NUC (x86_64)        | Ubuntu 24.04 LTS + Docker + k3s      | HeuristicMesh mesh controller, logging, OTA, alert routing, Jasterish toolchain host |
| Inference Node A        | Jetson Orin Nano 8 GB    | JetPack 6.x + TensorRT 10 + CUDA 12  | Primary thermal vision encoder + Framework 2/3 execution |
| Inference Node B        | Jetson Orin Nano 8 GB    | JetPack 6.x + TensorRT 10 + CUDA 12  | Hot-standby + secondary spatial analysis / load balancing |

### 2. Sensors
- AMG8833 (8×8, I2C 0x68 or 0x69) – continuous 10 Hz polling, anomaly trigger  
-  (32×24, I2C 0x33) – on-demand 4–16 Hz capture window of 3–5 s after trigger  
- Interconnect: ESP32-S3 (or direct Jetson I2C) acting as sensor concentrator; dual-address I2C bus with 4.7 kΩ pull-ups.

### 3. Network Fabric (Zyxel)
- USG Flex 100H – Layer-3 firewall / router, policy-based routing, VPN endpoint for remote admin, DPI for outbound alert destinations only.  
- GS1200 (web-managed) – 1 GbE access ports, VLAN isolation (Sensor VLAN, Inference VLAN, Management VLAN, Alert VLAN).  
- NWA90BE-class AP – Wi-Fi 6 for any mobile configuration tablets or caregiver devices; 5 GHz only for system traffic if wireless bridge required.

### 4. Software Stack
- Sensor firmware: ESP-IDF or MicroPython (I2C master, ring-buffer, trigger GPIO/MQTT).  
- Vision encoder: TensorRT-optimized lightweight model (YOLOv8n-pose thermal-adapted or custom MobileNet-V3 + pose head) quantized to int8.  
- HeuristicMesh runtime: Python 3.12 / Rust service on NUC; gRPC or ZeroMQ for inter-framework messaging; each framework is an independent process/container.  
- Logging: structured JSON + SQLite + optional encrypted append-only log on NUC.  
- Alert path: local MQTT → NUC router → Twilio / SIP / direct 911 API (configurable).  

### 5. Performance Targets
- AMG8833 → trigger decision: ≤ 50 ms  
-  frame acquisition + transfer: ≤ 200 ms  
- Jetson inference (single frame + temporal buffer): ≤ 80 ms (int8)  
- Mesh arbitration + alert dispatch: ≤ 100 ms  
- Total budget: ≤ 1 800 ms