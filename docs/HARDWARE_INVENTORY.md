# Hardware Inventory
**Snapshot Date:** 2026-08-11 conversation snapshot  
**Status Note:** This inventory records what was in hand or on order as of the 2026-08-11 discussion. It is not a statement of current 2026-09-10 possession.

## Sensor Inventory

| Sensor | Resolution | Framework Role | I2C Address | 2026-08-11 Status | Notes |
|---|---|---|---|---|---|
| AMG8833 | 8x8 = 64 pixels | Framework 1 thermal trigger | `0x68` or `0x69` | In hand as a bare chip needing soldering | Fast, low-power trigger path |
| MLX90640 | 32x24 = 768 pixels | Framework 2 spatial analysis | `0x33` typical | On order, expected 2026-08-12 | Higher-resolution analysis path |

## Shared-Bus Architecture

The AMG8833 and MLX90640 are intended to run simultaneously on the same I2C bus, with either the ESP32-S3 or the Jetson acting as the bus master.

- AMG8833 remains the fast, low-power trigger sensor and must not be blocked by MLX activity.
- MLX90640 provides the higher-resolution thermal frames used for spatial analysis after a trigger event.

## Dual-Sensor Pipeline

1. AMG8833 watches continuously for a thermal anomaly or abnormal movement.
2. AMG8833 trigger opens the alert window.
3. MLX90640 capture starts during that alert window.
4. Jetson runs inference on the MLX frames.
5. System raises an alert if the confidence threshold is met.

## Integration Requirements

- I2C address configuration must be verified so both sensors coexist cleanly on the shared bus.
- MLX90640 needs a frame buffer during the alert window.
- Each sensor should run in a dedicated thread so AMG polling stays responsive.
- Latency must be balanced against EMS response speed; the trigger path should stay fast even if the analysis path is heavier.
