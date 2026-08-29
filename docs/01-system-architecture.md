# HeuristicMesh – Full System Architecture

## Nodes
- **Thermal Node**: ESP32 + AMG8833 (wall/ceiling)
- **Edge Compute**: 1–2 × Jetson Orin Nano
- **Archive / Orchestration**: ASUS NUC
- **Ground Truth**: Body cameras (portable)
- **Network**: Optional Zyxel (not required for field capture)

## Data Flow
AMG8833 → ESP32 (Framework 1) → USB Serial → Jetson (Framework 2) → JSONL / MQTT → NUC / Hub

## Collection Modes
1. Body-cam only (volume + actor diversity)
2. Multi-modal fixed (thermal + body-cam) when hardware is co-located
