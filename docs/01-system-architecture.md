# HeuristicMesh – Full System Architecture

## Nodes
- **Thermal Node**: ESP32-S3 + AMG8833 + MLX90640 on the same I2C bus (wall/ceiling)
- **Edge Compute**: 1–2 × Jetson Orin Nano
- **Archive / Orchestration**: ASUS NUC
- **Ground Truth**: Body cameras (portable)
- **Network**: Optional Zyxel (not required for field capture)

## Data Flow
AMG8833 trigger → Thermal Node (ESP32-S3 captures MLX90640 on the shared I2C bus) → Jetson inference → JSONL / MQTT → NUC / Hub

## Frameworks
1. **Framework 1 – Thermal Trigger**: AMG8833 (8x8 = 64 px) provides the always-on low-power trigger path.
2. **Framework 2 – Spatial Analysis**: MLX90640 (32x24 = 768 px) provides higher-resolution thermal frames for posture and orientation analysis.
3. **Framework 3 – Event Classification**: computer-vision rules or models classify rapid descent, horizontal posture, and immobility while suppressing false positives such as sitting down or bending over.
4. **Framework 4 – Response / Alert**: mesh logic decides whether confidence is high enough to escalate to an alert.

## Inference Constraint
The discussed DeepSeek, Qwen, and Llama candidates are text-only or primarily text models running int8 on Jetson. They are not the thermal vision model. Raw thermal pixels should stay in the vision pipeline; if Jasterish or other mesh reasoning is added later, it should consume structured features rather than raw MLX frames.

## Related Documentation
- `docs/HeuristicMesh_Architecture_Philosophy.md`
- `docs/HARDWARE_INVENTORY.md`
- `docs/INFERENCE_STACK.md`
- `docs/IP_AND_REGULATORY_STRATEGY.md`

## Collection Modes
1. Body-cam only (volume + actor diversity)
2. Multi-modal fixed (thermal + body-cam) when hardware is co-located
