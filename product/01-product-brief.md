# HeuristicMesh Home Fall Sensor
## Consumer Product Brief – Manufacturing Target

### Goal
A small, wall- or ceiling-mountable thermal fall-detection node that can be manufactured at consumer-accessible cost and installed in ordinary homes.

### Design Constraints
- Form factor: ≤ 90 × 90 × 30 mm (roughly a large smoke-detector footprint)
- Power: USB-C 5 V (wall adapter) or optional PoE later
- Wireless: Wi-Fi for connectivity to home hub / phone app (ESP32 native)
- Sensor: single AMG8833 (8×8 thermal)
- Target manufacturing cost (electronics + enclosure, qty 1k): under $28–35
- Retail target: $79–99

### What it does
- Continuously monitors a room for human thermal presence and rapid downward motion
- Emits local fall-candidate events over Wi-Fi (MQTT or HTTPS)
- Designed to work with a central hub (Jetson / NUC / cloud) for confirmation and alerting
- No camera – privacy-first thermal only

### Non-goals (v1)
- High-resolution thermal imaging
- On-device neural network inference
- Battery operation (wall power only for reliability)
