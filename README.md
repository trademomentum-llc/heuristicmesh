# HeuristicMesh Complete Package
## Architectural Philosophy + Fall-Detection Product Definition

### Structure
- `esp32/` – production firmware (centroid + velocity + binary protocol)
- `jetson/` – production ingestion + Framework 2 daemon
- `config/` – thresholds + MQTT topic schema
- `scripts/` – flash helper, Jetson runner, body-cam log template
- `docs/` – architecture, hardware, inference, IP, and fall scenarios
- Human testing is currently prohibited; see `docs/Human_Testing_Safety_Gate.md` and `plan.md` for the opt-in, qualified-oversight go/no-go controls.
- `product/` – consumer node brief, schematic, mechanical, BOM

HeuristicMesh is the architectural philosophy that organizes the system into explicit frameworks and mesh logic. The product is the thermal fall-detection system built on top of that philosophy.

### Documentation Index
- `docs/HeuristicMesh_Architecture_Philosophy.md` – what HeuristicMesh means as the underlying architecture
- `docs/01-system-architecture.md` – top-level node layout, data flow, frameworks, and collection modes
- `docs/HARDWARE_INVENTORY.md` – 2026-08-11 hardware snapshot for AMG8833 and MLX90640
- `docs/INFERENCE_STACK.md` – Jetson-side model constraints, vision path, and latency targets
- `docs/IP_AND_REGULATORY_STRATEGY.md` – public-disclosure-aware IP and regulatory positioning notes

This archive consolidates the operable thermal path, the HeuristicMesh architecture, and the manufacturable product definition.
