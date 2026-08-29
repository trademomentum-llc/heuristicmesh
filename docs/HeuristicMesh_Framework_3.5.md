# HeuristicMesh Framework 3.5 — MQTT Topic Schema & Integration Spec
**Version:** 1.0  
**Date:** 2026-08-11  
**Broker:** Mosquitto on ASUS NUC (VLAN 10 / Management)  
**Gateway:** USR-TCP232-410S (VLAN 30 → MQTT over TLS)

## 1. Topic Namespace

All topics follow the hierarchical pattern:


hm/fw35/{location}/{sensor_type}/{metric}


| Topic | Payload Type | Example Payload | QoS | Retain | Description |
|-------|--------------|-----------------|-----|--------|-------------|
| `hm/fw35/room1/bed_pressure/status` | string | `"occupied"` / `"vacant"` | 1 | true | Bed or floor mat occupancy |
| `hm/fw35/room1/bed_pressure/force` | float | `42.7` | 0 | false | Optional force reading (kg or raw ADC) |
| `hm/fw35/room1/door/status` | string | `"open"` / `"closed"` | 1 | true | Door/window contact |
| `hm/fw35/room1/env/temperature` | float | `22.4` | 0 | false | Ambient temperature °C |
| `hm/fw35/room1/env/humidity` | float | `48.1` | 0 | false | Relative humidity % |
| `hm/fw35/room1/env/co2` | int | `612` | 0 | false | CO₂ concentration ppm |
| `hm/fw35/room1/medical/spo2` | float | `97.2` | 1 | false | Pulse-oximeter SpO₂ (if present) |
| `hm/fw35/room1/medical/hr` | int | `78` | 1 | false | Heart rate bpm |
| `hm/fw35/system/gateway/status` | string | `"online"` / `"offline"` | 1 | true | USR gateway health |

## 2. Payload Conventions

- All numeric values are JSON numbers (no units in the payload; units are defined by topic).
- Status strings are lowercase, single-token.
- Every published message **must** include an ISO-8601 timestamp in the JSON envelope when possible:

```json
{
  "ts": "2026-08-11T20:15:33.412Z",
  "value": 22.4
}
```

If the USR gateway cannot embed a timestamp, the NUC subscriber will stamp the message with `time.time_ns()` on receipt.

## 3. Integration Rules (Framework 3.5)

- Framework 3 (Event Classification) subscribes to all `hm/fw35/#` topics.
- Environmental context is used only as a **soft prior**:
  - Bed occupied + rapid thermal descent → higher fall confidence.
  - Door open + thermal activity near threshold → possible exit rather than fall.
- No environmental sensor is allowed to trigger an alert by itself. It may only modulate confidence scores inside the mesh arbitration layer.
- All messages are logged into the same provenance store as the thermal and visual frameworks for full auditability.

## 4. USR-TCP232-410S Configuration Notes

- Protocol: MQTT (TLS enabled, port 8883 recommended).
- Client ID: `usr-tcp-410s-hm-01`
- Publish interval: 1–5 s for continuous sensors; on-change for binary contacts.
- Keep-alive: 30 s.
- Last Will: `hm/fw35/system/gateway/status` → `"offline"` (QoS 1, retain).
