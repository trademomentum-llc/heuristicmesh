# HeuristicMesh Baseline Data Capture Guide

**Version:** 1.0  
**Date:** 2026-08-29  
**Status:** Active  
**Purpose:** Step-by-step guide for capturing baseline thermal data to tune heuristic fall detection thresholds

---

## 🎯 Overview

This guide provides a **complete workflow** for capturing baseline thermal data using your hardware:
- **3× ESP32-S3** with **2× AMG8833** sensors
- **ESP32-S2-WROOM** as gateway
- **IR Body Cams** (2× consumer + 1× law enforcement) for ground truth
- **IR Cameras** (2× low-res + 1× high-res) for validation

The captured data will be used to:
1. **Tune heuristic thresholds** (velocity, centroid movement, persistence)
2. **Create training datasets** for Framework 2/3
3. **Validate detection accuracy**
4. **Generate evaluation sets** for testing

---

## 📋 Prerequisites

### Hardware Setup
✅ **ESP32-S3 #1** with AMG8833 #1 (0x69) - Room A  
✅ **ESP32-S3 #2** with AMG8833 #2 (0x68) - Room B  
✅ **ESP32-S3 #3** - Standby or  (if available)  
✅ **ESP32-S2-WROOM** with USR-TCP232 - Gateway  
✅ **Jetson Orin Nano A** - Primary inference  
✅ **Jetson Orin Nano B** - Standby/validation  
✅ **ASUS NUC** - Orchestrator  
✅ **Zyxel Network** - VLANs configured  
✅ **IR Body Cams** - Charged, SD cards formatted  
✅ **IR Cameras** - Powered, network connected  

### Software Setup
✅ ESP32 firmware flashed (`esp32/src/main_unified.cpp`)  
✅ Jetson ingest running (`jetson/hm_ingest_unified.py`)  
✅ Mosquitto MQTT broker running on NUC  
✅ USR-TCP232 configured (if using ModBus/TCP)  

### Environment Setup
✅ Quiet indoor room (4m × 4m minimum)  
✅ Stable temperature (20-24°C)  
✅ No direct sunlight on sensors  
✅ No strong HVAC drafts across FOV  
✅ Flooring: mix of hard surface and low-pile rug  

---

## 📁 File Structure

```
heuristicmesh-data/
├── README.md                    # Dataset description
├── config/                      # Configuration files
│   ├── session_config.yaml      # Current session config
│   └── thresholds.yaml          # Tuned thresholds
│
├── sessions/                    # All capture sessions
│   ├── 2026-08-29_001/          # Session ID: YYYY-MM-DD_XXX
│   │   ├── metadata.json        # Session metadata
│   │   ├── esp32_001/           # ESP32-S3 #1 data
│   │   │   ├── amg_frames/      # AMG8833 frames (JSONL)
│   │   │   │   ├── 000000.json
│   │   │   │   ├── 000001.json
│   │   │   │   └── ...
│   │   │   └── fall_candidates.jsonl  # Fall candidate events
│   │   │
│   │   ├── esp32_002/           # ESP32-S3 #2 data
│   │   │   └── amg_frames/
│   │   │
│   │   ├── jetson/              # Jetson processed data
│   │   │   ├── fw2_events.jsonl # Framework 2 events
│   │   │   └── fw3_classifications.jsonl
│   │   │
│   │   └── bodycams/            # Body camera footage
│   │       ├── bodycam_001.avi
│   │       ├── bodycam_002.avi
│   │       └── bodycam_003.avi
│   │
│   └── 2026-08-29_002/          # Next session
│       └── ...
│
├── datasets/                    # Processed datasets
│   ├── training/                # Training set (70%)
│   │   ├── thermal/            # Thermal frames
│   │   ├── features/           # Extracted features
│   │   └── labels/             # Ground truth labels
│   │
│   ├── validation/              # Validation set (15%)
│   │   └── ...
│   │
│   └── test/                   # Test set (15%)
│       └── ...
│
├── baseline/                   # Baseline analysis
│   ├── statistics.json         # Statistical analysis
│   ├── histograms/             # Distribution plots
│   └── thresholds_recommended.yaml
│
└── scripts/                    # Helper scripts
    ├── capture_session.py       # Session capture script
    ├── process_data.py          # Data processing script
    ├── sync_bodycams.py         # Body cam sync utility
    ├── generate_dataset.py      # Dataset generation
    ├── analyze_baseline.py      # Baseline analysis
    └── validate_thresholds.py    # Threshold validation
```

---

## 🚀 Step-by-Step Workflow

### Step 1: Prepare Configuration

Create `config/session_config.yaml`:

```yaml
# Session Configuration
session:
  id: "2026-08-29_001"
  date: "2026-08-29"
  start_time: "14:00:00"
  location: "Room A"
  operator: "Engineer"
  notes: "First baseline capture session"

# Hardware Configuration
devices:
  esp32_001:
    model: esp32-s3
    sensor: amg8833
    i2c_address: 0x69
    port: /dev/ttyACM0
    baud: 921600
    location: roomA
    mount_height: 2.5
    mount_angle: 30
    
  esp32_002:
    model: esp32-s3
    sensor: amg8833
    i2c_address: 0x68
    port: /dev/ttyACM1
    baud: 921600
    location: roomB
    mount_height: 2.5
    mount_angle: 30

# Sensor Thresholds (initial values - will be tuned)
thresholds:
  human_temp_c: 27.5
  hot_pixel_min: 3
  velocity_trigger: 1.8
  persistence_frames: 4
  centroid_upper_half: 4.0
  centroid_downward_delta: 1.4

# Body Camera Configuration
bodycams:
  enabled: true
  sync_utility: "hm_bodycam_sync.py"
  clock_offsets:  # Measure these before session
    bodycam_001: 0
    bodycam_002: 0
    bodycam_003: 0
```

---

### Step 2: Set Up Hardware

#### Sensor Mounting

```
Room A (ESP32-S3 #1 + AMG8833 #1):
  ┌─────────────────────┐
  │     Ceiling          │ 2.5m
  │       ▲              │
  │       │ 30°          │
  │       │              │
  │   ┌───────┐          │
  │   │AMG8833│          │
  │   │ 0x69  │          │
  │   └───────┘          │
  │                     │
  └─────────────────────┘
       3m × 3m coverage
       (floor area)

Room B (ESP32-S3 #2 + AMG8833 #2):
  Same as Room A, but with AMG8833 at 0x68
```

**Mounting Checklist:**
- [ ] Sensor at 2.5m height
- [ ] 30-45° downward angle
- [ ] Clear FOV (no obstructions)
- [ ] Away from heat sources
- [ ] I2C pull-ups installed (4.7kΩ)
- [ ] Stable power supply

#### Body Camera Setup

**Before Session:**
1. Format SD cards (FAT32)
2. Set camera clocks to UTC (or note offset)
3. Test recording on all cameras
4. Verify battery levels (>80%)
5. Position cameras:
   - **Body Cam #1**: Chest mount
   - **Body Cam #2**: Upper back/shoulder mount
   - **Law Enforcement Cam**: Waist or chest (secondary angle)

**Camera Settings:**
- Resolution: 1080p or highest available
- Frame rate: 30fps or 60fps
- IR mode: Enabled (if available)
- Timestamp: Embedded in video

---

### Step 3: Start Data Collection

#### Option A: Using Capture Script

```bash
# Navigate to scripts directory
cd heuristicmesh-data/scripts

# Start capture session
python3 capture_session.py \
    --session-id 2026-08-29_001 \
    --config ../config/session_config.yaml \
    --output ../sessions/2026-08-29_001 \
    --bodycams bodycam_001,bodycam_002,bodycam_003
```

#### Option B: Manual Startup

**Terminal 1 - NUC (MQTT Broker):**
```bash
cd /workspace/github__trademomentum-llc__heuristicmesh
sudo systemctl start mosquitto
sudo systemctl status mosquitto
```

**Terminal 2 - Jetson A (Primary):**
```bash
cd /workspace/github__trademomentum-llc__heuristicmesh/jetson
python3 hm_ingest_unified.py \
    --port /dev/ttyACM0 \
    --baud 921600 \
    --port /dev/ttyACM1 \
    --baud 921600 \
    --mqtt mqtt://192.168.10.100:1883
```

**Terminal 3 - Jetson B (Standby):**
```bash
cd /workspace/github__trademomentum-llc__heuristicmesh/jetson
python3 hm_ingest_unified.py \
    --port /dev/ttyACM2 \
    --baud 921600
```

**Terminal 4 - Body Cam Sync (After Session):**
```bash
cd /workspace/github__trademomentum-llc__heuristicmesh
python3 scripts/hm_bodycam_sync.py \
    --video-dir /path/to/bodycam_footage/ \
    --event-log /path/to/thermal_events.jsonl \
    --output heuristicmesh-data/sessions/2026-08-29_001/labels.csv
```

---

### Step 4: Execute Fall Scenarios

Use **mannequins or instrumented surrogates** (human testing requires safety gate approval).

#### Scenario Execution Protocol

```
For EACH scenario:
1. Announce scenario ID and name (for audio track)
2. Position surrogate in starting posture
3. Ensure all sensors are online and logging
4. Start body cameras recording (if not already)
5. Countdown: "Three... two... one... execute!"
6. Execute scenario (surrogate performs fall)
7. Surrogate remains still for 4-6 seconds after impact
8. Announce: "Hold... recover"
9. Log exact timestamp of "execute" command
10. Log exact timestamp of floor contact (from body cams)
11. Allow 30-60 seconds recovery/repositioning
12. Verify body camera recording status
```

#### Recommended Scenario Order

**Session 1 (Common Falls):**
| Order | Scenario | Trials | Notes |
|-------|----------|--------|-------|
| 1 | S01 Forward Trip | 6 | Use rolled towel as obstacle |
| 2 | S02 Sit-to-Stand Failure | 6 | Standard chair, feet flat |
| 3 | S03 Lateral Slip | 6 | Smooth surface, sock-on-tile |
| 4 | S05 Rotation + Fall | 4 | 90-180° turn, lose balance |

**Session 2 (Elusive Falls):**
| Order | Scenario | Trials | Notes |
|-------|----------|--------|-------|
| 1 | S06 Slow Syncope | 8 | **Highest priority** - gradual collapse |
| 2 | S07 Fall from Bed | 6 | Low platform or actual bed |
| 3 | S08 Near-Fall + Collapse | 6 | Catch on furniture, then fall |
| 4 | S10 Controlled Descent | 6 | **Negative class** - slow to floor |

**Session 3 (Mixed):**
| Order | Scenario | Trials | Notes |
|-------|----------|--------|-------|
| 1 | S04 Forward Fall (Head-Risk) | 4 | Use landing mat |
| 2 | S09 Fall with Object | 5 | Carry empty box/bag |
| 3 | Free-form | 4 | "Worst-case" directed by operator |

---

### Step 5: Data Collection Details

#### What Gets Logged

**ESP32 → Jetson (Continuous):**
- AMG8833 frames @ 20Hz (50ms interval)
- Centroid position (x, y)
- Velocity estimate
- Thermal mass
- Hot pixel count
- Fall candidate flags

**ESP32 → Jetson (On Trigger):**
-   (24 frames @ 8Hz = 3 seconds)
- Full 32×24 thermal array per frame
- Timestamp per frame

**Jetson → NUC:**
- Framework 2 spatial analysis results
- Framework 3 classification
- Confidence scores
- Full provenance data

**Body Cams:**
- Continuous video @ 30-60fps
- Embedded timestamps
- Audio track (for "execute" commands)

**NUC:**
- All events logged to JSONL
- MQTT messages (optional)
- Provenance database

#### File Naming Convention

```
Thermal frames:
  esp32_{device_id}/amg_frames/{frame_id:06d}.json
  esp32_{device_id}/_frames/{_id}_{frame_index:03d}.json

Body cam videos:
  bodycams/{camera_id}_{scenario_id}_{trial:03d}.avi

Event logs:
  thermal_events_{session_id}.jsonl
  fw2_events_{session_id}.jsonl
  fw3_classifications_{session_id}.jsonl

Labels:
  labels_{session_id}.csv
  labels_{session_id}_{scenario_id}.csv
```

---

## 📊 Data Processing

### Step 6: Sync Body Cams with Thermal Data

After each session, run the sync utility:

```bash
python3 scripts/sync_bodycams.py \
    --video-dir heuristicmesh-data/sessions/2026-08-29_001/bodycams/ \
    --event-log heuristicmesh-data/sessions/2026-08-29_001/jetson/fw2_events.jsonl \
    --output heuristicmesh-data/sessions/2026-08-29_001/labels.csv
```

**Sync Utility Workflow:**
1. Extract timestamps from body cam videos (file modification time or embedded metadata)
2. Match with thermal event timestamps from NUC log
3. Create labeled CSV with frame-by-frame annotations
4. Generate ground truth labels for training

### Step 7: Generate Training/Evaluation Sets

```bash
python3 scripts/generate_dataset.py \
    --session-dir heuristicmesh-data/sessions/2026-08-29_001/ \
    --output-dir heuristicmesh-data/datasets/ \
    --train-ratio 0.7 \
    --val-ratio 0.15 \
    --test-ratio 0.15
```

**Dataset Generation:**
1. Load all thermal frames from session
2. Load ground truth labels from sync utility
3. Split into training/validation/test sets
4. Extract features for each frame:
   - Centroid x, y
   - Velocity
   - Acceleration
   - Thermal mass
   - Hot pixel count
   - Bounding box (for )
   - Aspect ratio
   - Temperature statistics
5. Save in standardized format

### Step 8: Feature Extraction

**AMG8833 Features (per frame):**
```json
{
  "frame_id": 12345,
  "timestamp_us": 1723402533412000,
  "device_id": "esp32_001",
  "sensor": "AMG8833",
  "features": {
    "centroid_x": 3.2,
    "centroid_y": 2.8,
    "velocity": 1.85,
    "acceleration": 2.1,
    "thermal_mass": 45.2,
    "hot_pixel_count": 5,
    "max_temp": 27.8,
    "avg_temp": 23.5,
    "min_temp": 21.2
  },
  "label": "FALL",
  "confidence": 0.92,
  "scenario_id": "S01",
  "trial": 1
}
```

** Features (per frame):**
```json
{
  "frame_id": 12345,
  "timestamp_us": 1723402533412000,
  "device_id": "esp32_001",
  "sensor": "",
  "_id": 42,
  "_index": 5,
  "features": {
    "centroid_x": 15.8,
    "centroid_y": 12.3,
    "bounding_box_area": 120,
    "aspect_ratio": 0.85,
    "hot_pixel_count": 45,
    "max_temp": 28.2,
    "avg_temp": 24.1,
    "min_temp": 21.8
  },
  "label": "FALL",
  "confidence": 0.95,
  "scenario_id": "S01",
  "trial": 1
}
```

---

## 🎯 Baseline Analysis

### Step 9: Analyze Collected Data

```bash
python3 scripts/analyze_baseline.py \
    --dataset heuristicmesh-data/datasets/training/ \
    --output heuristicmesh-data/baseline/
```

**Analysis Performed:**

1. **Statistical Analysis**
   - Mean, median, std deviation for each feature
   - Per-scenario statistics
   - Per-device statistics

2. **Distribution Analysis**
   - Histograms of velocity, centroid movement, temperature
   - Outlier detection

3. **Correlation Analysis**
   - Feature correlations with fall labels
   - Identify most predictive features

4. **Threshold Recommendations**
   - Optimal velocity threshold
   - Optimal persistence frames
   - Optimal centroid movement thresholds

**Example Output (`baseline/statistics.json`):**
```json
{
  "statistics": {
    "velocity": {
      "mean": 1.23,
      "median": 0.98,
      "std": 0.87,
      "min": 0.0,
      "max": 4.56,
      "fall_mean": 2.34,
      "non_fall_mean": 0.45
    },
    "centroid_downward_delta": {
      "mean": 0.87,
      "median": 0.65,
      "std": 0.54,
      "fall_mean": 1.89,
      "non_fall_mean": 0.32
    },
    "hot_pixel_count": {
      "mean": 8.2,
      "median": 7,
      "std": 5.1,
      "fall_mean": 12.5,
      "non_fall_mean": 4.8
    }
  },
  "recommendations": {
    "velocity_trigger": 1.5,
    "persistence_frames": 3,
    "centroid_downward_delta": 1.2,
    "hot_pixel_min": 4
  },
  "confusion_matrix": {
    "true_positives": 48,
    "true_negatives": 120,
    "false_positives": 3,
    "false_negatives": 2
  },
  "accuracy": 0.972
}
```

### Step 10: Validate Thresholds

```bash
python3 scripts/validate_thresholds.py \
    --dataset heuristicmesh-data/datasets/validation/ \
    --thresholds heuristicmesh-data/baseline/thresholds_recommended.yaml \
    --output heuristicmesh-data/baseline/validation_results.json
```

**Validation Metrics:**
- Precision, Recall, F1-score
- Confusion matrix
- ROC curve (if applicable)
- False positive rate
- False negative rate
- End-to-end latency

---

## 🔧 Configuration Tuning

### Update Thresholds

Based on baseline analysis, update `config/thresholds.yaml`:

```yaml
# Tuned thresholds from baseline analysis
thermal:
  human_temp_c: 27.5        # Adjusted based on ambient temp
  hot_pixel_min: 4         # Increased from 3 to reduce false positives
  velocity_trigger: 1.5     # Decreased from 1.8 for better sensitivity
  persistence_frames: 3     # Decreased from 4 for faster response
  
  centroid_upper_half: 4.0
  centroid_downward_delta: 1.2  # Decreased from 1.4
  
  # Confidence scoring
  base_confidence: 0.5
  velocity_weight: 0.05
  persistence_weight: 0.1
  impact_weight: 0.15       # Increased for impact detection
  immobility_weight: 0.1

# Alert thresholds
fall_confidence_threshold: 0.82  # Adjusted based on validation
near_fall_threshold: 0.6
```

### Update ESP32 Firmware

Recompile and flash with updated thresholds:

```bash
cd /workspace/github__trademomentum-llc__heuristicmesh/esp32

# Edit config_unified.h with new thresholds
nano include/config_unified.h

# Build and flash
pio run -t upload -e esp32-s3-devkitc-1
pio run -t upload -e esp32-s3-devkitc-1  # For second device
```

---

## 📈 Expected Results

### After 3 Sessions (65 Trials)

| Metric | Target | Expected After Tuning |
|--------|--------|----------------------|
| True Positive Rate | >95% | 97-99% |
| False Positive Rate | <3% | 1-2% |
| False Negative Rate | <5% | 2-3% |
| Detection Latency | <500ms | 200-400ms |
| Confidence (Falls) | >0.8 | 0.85-0.95 |

### Data Volume

| Data Type | Per Session | After 3 Sessions |
|-----------|-------------|------------------|
| AMG Frames | ~12,000 | ~36,000 |
|  s | ~200 | ~600 |
|  Frames | ~4,800 | ~14,400 |
| Body Cam Video | ~20 GB | ~60 GB |
| Event Logs | ~1 MB | ~3 MB |

---

## 🎓 Best Practices

### Do's
✅ **Always use mannequins/surrogates** until safety gate is passed  
✅ **Verify I2C connections** before each session  
✅ **Check sensor FOV** is clear and unobstructed  
✅ **Sync clocks** on all devices before session  
✅ **Label data immediately** after session while memory is fresh  
✅ **Backup data** to multiple locations  
✅ **Document deviations** from protocol in session notes  

### Don'ts
❌ **Don't use human subjects** without safety gate approval  
❌ **Don't change hardware** during a session  
❌ **Don't move sensors** after calibration  
❌ **Don't delete raw data** - always keep originals  
❌ **Don't mix scenarios** in one session without clear separation  

---

## 🚨 Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| No frames received | Serial connection failed | Check port, baud rate, permissions |
| I2C errors | Wiring issue | Check pull-ups, connections, addresses |
| Low confidence scores | Thresholds too high | Decrease velocity_trigger, persistence_frames |
| High false positives | Thresholds too low | Increase velocity_trigger, hot_pixel_min |
|  not responding | Address conflict | Check AD0 pin, use 0x33 or 0x34 |
| USR-TCP232 not connecting | IP/config issue | Verify USR-TCP232 settings |
| Body cam sync fails | Clock drift | Measure offset, use embedded timestamps |

### Debug Commands

```bash
# Check serial ports
ls /dev/tty*

# Monitor serial data
screen /dev/ttyACM0 115200

# Test I2C
sudo apt install i2c-tools
sudo i2cdetect -y 1

# Check network
ping 192.168.30.10

# Monitor MQTT
mosquitto_sub -h 192.168.10.100 -t 'hm/#' -v

# View logs
tail -f /var/log/heuristicmesh/*.log
```

---

## 📚 References

- [Deployment Architecture](DEPLOYMENT_ARCHITECTURE.md)
- [Protocol Specification](PROTOCOL_SPECIFICATION.md)
- [Gap Analysis](GAP_ANALYSIS.md)
- [Fall Simulation Protocol](HeuristicMesh_Fall_Simulation_Production_Package.md)
- [Human Testing Safety Gate](Human_Testing_Safety_Gate.md)

---

**Document Status:** ✅ Active  
**Owner:** Engineering Team  
**Last Updated:** 2026-08-29  
**Version:** 1.0
