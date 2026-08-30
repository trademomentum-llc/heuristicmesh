# HeuristicMesh Fall Simulation Production Package
## AMG8833-Only Version

**Version:** 1.1  
**Date:** 2026-08-29  
**Status:** Active  
**Sensors:** 2× AMG8833 (8×8 thermal arrays)  
**Note:** MLX90640 support removed - only AMG8833 sensors in inventory

---

## 🎯 Overview

This document describes the **fall simulation production package** for HeuristicMesh, including:
- Sensor placement and mounting specifications
- Fall simulation protocols
- Data capture procedures
- Quality assurance checklists
- Production bring-up procedures

**Key Change:** This version is **AMG8833-only**. All references to MLX90640 and burst mode have been removed.

---

## 📐 Sensor Placement Specifications

### AMG8833 Thermal Sensors (2× Available)

| Sensor | Location | Mount Height | Angle | Coverage | I2C Address |
|--------|----------|--------------|-------|----------|--------------|
| AMG8833 #1 | Room A, Ceiling | 2.4-2.8m | 30-45° downward | 3m × 3m | 0x69 |
| AMG8833 #2 | Room B, Ceiling | 2.4-2.8m | 30-45° downward | 3m × 3m | 0x68 |

**Mounting Requirements:**
- **Height:** 2.4-2.8m above floor (optimal for 8×8 resolution)
- **Angle:** 30-45° downward tilt (covers primary activity zone)
- **FOV:** ~60° horizontal × ~60° vertical
- **Coverage:** ~3m × 3m floor area at 2.5m height
- **Clearance:** No obstructions within FOV

**Wiring:**
- I2C with 4.7kΩ pull-ups to 3.3V
- Separate pull-ups for each ESP32 (not shared)
- Shielded cable recommended for >1m runs

---

## 🎭 Fall Simulation Protocol

### Test Scenarios (10 Total)

| ID | Scenario | Type | Priority | Description |
|----|----------|------|----------|-------------|
| S01 | Forward Trip | Common | High | Trip while walking forward |
| S02 | Sit-to-Stand Failure | Common | High | Failed attempt to stand from seated |
| S03 | Lateral Slip | Common | High | Slip to the side |
| S04 | Forward Fall (Head-Risk) | High-Impact | High | Fall forward, head first |
| S05 | Rotation + Fall | High-Impact | High | Spin then fall |
| S06 | Slow Syncope | **Elusive** | **High** | Gradual faint/collapse |
| S07 | Fall from Bed | Elusive | Medium | Fall from bed edge |
| S08 | Near-Fall + Collapse | Elusive | Medium | Catch then collapse |
| S09 | Fall with Object | Elusive | Medium | Fall while carrying object |
| S10 | Controlled Descent | Negative | Low | Slow, controlled sit-down |

**Note:** S06 (Slow Syncope) is the **most elusive** case and requires extra attention.

### Scenario Distribution

| Category | Scenarios | Training | Validation | Test | Total |
|----------|-----------|----------|------------|------|-------|
| Common | S01, S02, S03 | 15 | 3 | 3 | 21 |
| High-Impact | S04, S05 | 7 | 2 | 1 | 10 |
| Elusive | S06, S07, S08, S09 | 21 | 5 | 3 | 29 |
| Negative | S10 | 5 | 1 | 1 | 7 |
| **Total** | **10** | **48** | **11** | **8** | **67** |

---

## 🎬 Production Setup Checklist

### Pre-Session Setup

- [ ] **Hardware Check**
  - [ ] 2× ESP32-S3 with AMG8833 sensors mounted
  - [ ] 1× ESP32-S3 standby node
  - [ ] 1× ESP32-S2-WROOM with USR-TCP232 (optional)
  - [ ] 2× Jetson Orin Nano powered on
  - [ ] 1× ASUS NUC with Mosquitto running
  - [ ] Zyxel XMG108 switch configured with VLANs
  - [ ] Zyxel USG Flex 100H firewall operational
  - [ ] 3× TP-Link TL-SG108E switches for sensor network
  - [ ] Zyxel NWA90BE AP for caregiver WiFi

- [ ] **Sensor Check**
  - [ ] AMG8833 #1 at 0x69 responding
  - [ ] AMG8833 #2 at 0x68 responding
  - [ ] I2C pull-ups installed (4.7kΩ)
  - [ ] Clear FOV for both sensors
  - [ ] Proper mounting height (2.4-2.8m)
  - [ ] Correct downward angle (30-45°)

- [ ] **Network Check**
  - [ ] VLAN 10 (Management): NUC connected
  - [ ] VLAN 20 (Inference): Jetson A & B connected
  - [ ] VLAN 30 (Sensors): ESP32s and USR-TCP232 connected
  - [ ] VLAN 40 (Alert): AP connected, tablets can connect
  - [ ] Firewall rules configured correctly
  - [ ] No IP conflicts

- [ ] **Software Check**
  - [ ] ESP32 firmware v1.1 flashed (AMG8833-only)
  - [ ] Jetson ingestion daemon running
  - [ ] NUC event logger running
  - [ ] Mosquitto MQTT broker running
  - [ ] All serial connections established

### Session Start Procedure

1. **Power on all devices**
   ```bash
   # On NUC:
   sudo systemctl start mosquitto
   cd /opt/heuristicmesh/nuc
   python3 event_logger.py
   
   # On Jetson A:
   cd /opt/heuristicmesh/jetson
   python3 hm_ingest_amg_only.py --port /dev/ttyACM0 --baud 921600
   
   # On Jetson B:
   cd /opt/heuristicmesh/jetson
   python3 hm_ingest_amg_only.py --port /dev/ttyACM2 --baud 921600
   ```

2. **Verify all sensors online**
   - Check serial output from each ESP32
   - Confirm HELLO messages received on Jetson
   - Verify AMG8833 frames streaming

3. **Start body cameras**
   - Ensure all 3 IR body cams are recording
   - Verify timestamps are synchronized
   - Check storage space available

4. **Begin session logging**
   ```bash
   cd /opt/heuristicmesh/scripts
   ./start_capture_session.sh roomA S01
   ```

---

## 🎯 Data Capture Workflow

### Single Scenario Capture

1. **Position subject/mannequin**
   - In sensor FOV (3m × 3m area)
   - Clear of obstructions
   - Proper lighting (thermal works in dark)

2. **Start recording**
   - Body cams: RECORD
   - Jetson: Verify frames incoming
   - NUC: Verify events logging

3. **Perform scenario**
   - Follow protocol for specific scenario
   - Ensure fall is within sensor FOV
   - Multiple takes if needed

4. **Stop recording**
   - Body cams: STOP
   - Verify all data saved
   - Check frame counts match

5. **Tag data**
   - Scenario ID (S01-S10)
   - Trial number
   - Timestamp
   - Notes/observations

### Quality Assurance Checklist

- [ ] **Frame Count**
  - [ ] ESP32 #1: Expected frames received
  - [ ] ESP32 #2: Expected frames received
  - [ ] No frame drops or gaps
  - [ ] Timestamps are sequential

- [ ] **Fall Detection**
  - [ ] Fall candidate triggered for actual falls
  - [ ] No false triggers for non-falls
  - [ ] Confidence scores reasonable
  - [ ] Classification correct

- [ ] **Data Integrity**
  - [ ] All files readable
  - [ ] No corruption in binary data
  - [ ] JSON files valid
  - [ ] CSV files complete

- [ ] **Ground Truth**
  - [ ] Body cam footage available
  - [ ] Timestamps synchronized
  - [ ] Labels assigned correctly
  - [ ] All falls captured on video

---

## 📦 Data Archiving

### Directory Structure

```
heuristicmesh-data/
├── sessions/
│   ├── 2026-08-29_001/          # Session 1
│   │   ├── metadata.json
│   │   ├── esp32-001/           # ESP32-S3 #1
│   │   │   └── amg_frames/     # AMG8833 frames
│   │   │       ├── frame_00000.json
│   │   │       ├── frame_00001.json
│   │   │       └── ...
│   │   ├── esp32-002/           # ESP32-S3 #2
│   │   │   └── amg_frames/
│   │   ├── bodycam_001/         # Body Cam 1
│   │   │   └── video.mp4
│   │   ├── bodycam_002/         # Body Cam 2
│   │   │   └── video.mp4
│   │   ├── bodycam_003/         # Body Cam 3
│   │   │   └── video.mp4
│   │   ├── labels.csv           # Ground truth labels
│   │   └── session_log.txt
│   └── 2026-08-29_002/          # Session 2
│       └── ...
└── datasets/
    ├── training/               # Training set
    │   ├── metadata.json
    │   ├── frames.json
    │   └── frames.csv
    ├── validation/             # Validation set
    │   ├── metadata.json
    │   ├── frames.json
    │   └── frames.csv
    └── test/                   # Test set
        ├── metadata.json
        ├── frames.json
        └── frames.csv
```

### Archive Procedure

1. **Copy raw data**
   ```bash
   cp -r /opt/heuristicmesh/data/sessions/ /mnt/backup/heuristicmesh-data/sessions/
   ```

2. **Generate datasets**
   ```bash
   cd /opt/heuristicmesh/scripts
   python3 generate_dataset.py --session-dir /mnt/backup/heuristicmesh-data/sessions/2026-08-29_001/ \
       --output-dir /mnt/backup/heuristicmesh-data/datasets/session_001/
   ```

3. **Verify integrity**
   ```bash
   cd /opt/heuristicmesh/scripts
   python3 verify_dataset.py --dataset-dir /mnt/backup/heuristicmesh-data/datasets/
   ```

4. **Create backup**
   ```bash
   tar -czvf heuristicmesh_data_$(date +%Y%m%d).tar.gz /mnt/backup/heuristicmesh-data/
   ```

---

## 📊 Performance Metrics

### Target Detection Rates

| Scenario | Target Rate | False Positive Rate | Latency |
|----------|-------------|---------------------|---------|
| S01 Forward Trip | >95% | <2% | <300ms |
| S02 Sit-to-Stand | >90% | <3% | <400ms |
| S03 Lateral Slip | >93% | <2% | <350ms |
| S04 Forward Fall | >97% | <1% | <250ms |
| S05 Rotation + Fall | >94% | <2% | <300ms |
| S06 Slow Syncope | >85% | <5% | <500ms |
| S07 Fall from Bed | >90% | <3% | <400ms |
| S08 Near-Fall | >88% | <4% | <450ms |
| S09 Fall with Object | >87% | <4% | <450ms |
| S10 Controlled Descent | <5% | N/A | N/A |

### Confidence Thresholds

| Classification | Confidence Range | Action |
|----------------|------------------|--------|
| FALL | >0.85 | Immediate EMS alert |
| FALL | 0.70-0.85 | Caregiver alert + local alarm |
| NEAR_FALL | >0.60 | Log + notify caregiver |
| SUSPICIOUS | >0.40 | Log only |
| NOISE | ≤0.40 | Discard |

---

## 🛠️ Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| No frames from ESP32 | USB connection issue | Check cable, port, driver |
| I2C errors | Wiring problem | Check pull-ups, connections, address |
| Low detection rate | Thresholds too high | Lower velocity_trigger in config |
| High false positives | Thresholds too low | Increase velocity_trigger or persistence_frames |
| Sensor not detected | Address conflict | Verify AD0 pin configuration |
| Timestamps misaligned | Clock drift | Sync NTP on all devices |

### Debug Commands

```bash
# Check ESP32 serial output
screen /dev/ttyACM0 921600

# Monitor MQTT traffic
mosquitto_sub -h localhost -t 'hm/#' -v

# Check network connectivity
ping 192.168.30.10

# View system logs
journalctl -u mosquitto -f
```

---

## 📝 Changelog

### v1.1 (2026-08-29)
- **REMOVED** all MLX90640 references
- **REMOVED** burst mode references
- Updated for AMG8833-only configuration (2 sensors)
- Simplified data capture workflow

### v1.0 (2026-08-28)
- Initial version

---

**Document Status:** ✅ Active  
**Owner:** Engineering Team  
**Last Updated:** 2026-08-29  
**Version:** 1.1
