# MQTT Topic Schema (HeuristicMesh)

Base: `hm/`

## Framework 1 (ESP32 / thermal node)
- `hm/fw1/{device_id}/telemetry`     – binary or JSON thermal frames
- `hm/fw1/{device_id}/status`        – online / offline / error
- `hm/fw1/{device_id}/fall_flag`     – immediate fall-candidate boolean

## Framework 2 (Jetson spatial)
- `hm/fw2/{location}/event`          – confirmed spatial fall candidate
- `hm/fw2/{location}/debug`          – centroid traces (optional)

## Framework 3 (Classification)
- `hm/fw3/{location}/classified`     – fall / near-fall / sit / noise

## System
- `hm/sys/{device_id}/heartbeat`
- `hm/sys/{device_id}/config`
