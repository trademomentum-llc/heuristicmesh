# Design Specifications
## HeuristicMesh Fall Detection System – Architecture & Interconnection
**Document Version:** 1.0  
**Date:** 2026-08-11  

### 1. HeuristicMesh Layer Model
┌──────────────────────────────────────────────────────────────┐
│                    Mesh Orchestrator (NUC)                   │
│  State bus • Confidence arbitration • Provenance logger      │
└────────────┬───────────────────────────────┬─────────────────┘
             │                               │
   ┌─────────▼─────────┐           ┌─────────▼─────────┐
   │ Framework 1       │           │ Framework 4       │
   │ Thermal Trigger   │           │ Response / Alert  │
   │ (AMG8833)         │           │                   │
   └─────────┬─────────┘           └─────────▲─────────┘
             │                               │
   ┌─────────▼─────────┐           ┌─────────┴───────────┐
   │ Framework 2       │           │ Framework 3         │
   │ Spatial Analysis  │──────────►│ Event Classification│
   │ (MLX90640 + pose) │           │ (rules + confidence)│
   └───────────────────┘           └─────────────────────┘


### 2. Physical / Logical Interconnection (Production Topology)

                    ┌──────────────────────┐
                    │   Internet / ISP     │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Zyxel USG Flex 100H │  ← Firewall, NAT, VPN, policy
                    │  (WAN + LAN ports)   │
                    └──────────┬───────────┘
                               │ 1 GbE trunk
                    ┌──────────▼───────────┐
                    │  Zyxel GS1200 Switch │  ← VLAN-aware, web-managed
                    │  (managed L2)        │
                    └─┬─────┬─────┬─────┬──┘
                      │     │     │     │
         ┌────────────┘     │     │     └────────────┐
         │                  │     │                  │
┌────────▼────────┐ ┌───────▼─────▼──────┐ ┌─────────▼────────┐
│ ASUS NUC        │ │ Jetson Orin Nano A │ │ Jetson Orin Nano B│
│ (Control Plane) │ │ (Primary Inference)│ │ (Standby / Load)  │
│ Mgmt + Mesh     │ │ TensorRT + F2/F3   │ │ Hot-spare         │
└────────┬────────┘ └─────────┬──────────┘ └─────────┬─────────┘
         │                    │                      │
         │                    └──────────┬───────────┘
         │                               │ I2C / MQTT / gRPC
         │                    ┌──────────▼───────────┐
         │                    │  Sensor Concentrator │
         │                    │  (ESP32-S3 or direct)│
         │                    └──────────┬───────────┘
         │                               │
         │                    ┌──────────▼───────────┐
         │                    │ AMG8833  +  MLX90640 │
         │                    │ (shared I2C bus)     │
         │                    └──────────────────────┘
         │
┌────────▼────────┐
│ Zyxel NWA90BE   │  ← Wi-Fi 6 AP for caregiver tablets / config
│ Access Point    │
└─────────────────┘


### 3. VLAN & Security Design
- VLAN 10 – Management (NUC, switch, firewall admin)  
- VLAN 20 – Inference (both Jetsons)  
- VLAN 30 – Sensors (ESP32 / I2C bridges)  
- VLAN 40 – Alert / Caregiver (AP + outbound only)  
USG Flex 100H enforces inter-VLAN ACLs; only NUC may initiate outbound alert connections.

### 4. Data Flow (Happy Path)
1. AMG8833 continuous poll detects thermal anomaly → GPIO/MQTT trigger.  
2. Sensor concentrator starts MLX90640 high-rate capture (3–5 s buffer).  
3. Frames streamed to Jetson A (primary) via MQTT or ZeroMQ.  
4. Jetson A runs vision encoder → pose / shape features → Framework 2 & 3.  
5. Confidence + feature vector returned to NUC Mesh Orchestrator.  
6. Mesh arbitrates; if threshold met, Framework 4 fires alert.  
7. Full provenance record written; optional secondary confirmation from Jetson B.

### 5. Failure Modes & Degradation
- Jetson A failure → automatic failover to Jetson B within 2 s.  
- MLX90640 offline → system continues on AMG8833 + simplified heuristics (reduced confidence).  
- Network partition → local Jetson can still raise local GPIO/audible alert; NUC reconciles on reconnection.  
- All decisions remain fully reconstructible from local logs.

### 6. Future Extension Points
- Jasterish native mesh definition language (Phase 2)  
- Additional Framework 5 (multi-room correlation)  
- Signed OTA heuristic packages from NUC  
- Provisional patent filing on the mesh arbitration method