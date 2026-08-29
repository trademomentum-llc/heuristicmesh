# HeuristicMesh Body-Camera Ground-Truth Sync Utility
**Version:** 1.0  
**Purpose:** Align offline AVI footage from CQH / Ksadbossbo body cameras with system monotonic timestamps for labeled training data and audit trails.  
**Date:** 2026-08-11  

## 1. Operating Procedure

1. Before a data-collection session, set each body camera’s internal clock as close as possible to UTC (or note the offset).
2. Start recording on all body cameras **before** the first fall simulation.
3. On the NUC, log every system event with nanosecond precision:

```python
# Example event log line written by the orchestrator
{"event": "fall_candidate", "ts_ns": 1723402533412000000, "confidence": 0.87, "source": "fw3"}
```

4. After the session, copy the AVI files from the body-camera SD cards.
5. Run the sync utility below. It produces a CSV mapping each system event to the nearest video frame time.

## 2. Sync Utility (Python)

```python
#!/usr/bin/env python3
"""
hm_bodycam_sync.py
Aligns HeuristicMesh event log (nanosecond timestamps) with body-camera AVI files.
Produces a labeled CSV for training / audit.
"""

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import cv2   # only used for duration & frame-rate extraction

def get_video_meta(avi_path: str):
    cap = cv2.VideoCapture(avi_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_s = frame_count / fps if fps > 0 else 0
    cap.release()
    # File modification time as proxy for stop time (or use embedded metadata if available)
    mtime = os.path.getmtime(avi_path)
    start_ts = mtime - duration_s
    return {
        "path": avi_path,
        "fps": fps,
        "duration_s": duration_s,
        "start_unix": start_ts,
        "end_unix": mtime
    }

def load_events(event_log_path: str):
    events = []
    with open(event_log_path) as f:
        for line in f:
            events.append(json.loads(line))
    return events

def sync(events, videos, max_offset_s=2.0):
    """
    For each event, find the video whose time window covers it
    and compute the approximate frame number.
    """
    results = []
    for ev in events:
        ev_unix = ev["ts_ns"] / 1e9
        for vid in videos:
            if vid["start_unix"] - max_offset_s <= ev_unix <= vid["end_unix"] + max_offset_s:
                offset_s = ev_unix - vid["start_unix"]
                frame = int(offset_s * vid["fps"])
                results.append({
                    "event_ts_ns": ev["ts_ns"],
                    "event_type": ev.get("event", "unknown"),
                    "confidence": ev.get("confidence", ""),
                    "video_file": Path(vid["path"]).name,
                    "approx_frame": frame,
                    "offset_s": round(offset_s, 3)
                })
                break
    return results

if __name__ == "__main__":
    EVENT_LOG = "hm_events.jsonl"
    VIDEO_DIR = "bodycam_footage/"
    OUTPUT_CSV = "hm_groundtruth_labels.csv"

    videos = [get_video_meta(str(p)) for p in Path(VIDEO_DIR).glob("*.avi")]
    events = load_events(EVENT_LOG)
    matched = sync(events, videos)

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=matched[0].keys() if matched else [])
        writer.writeheader()
        writer.writerows(matched)

    print(f"Wrote {len(matched)} labeled events → {OUTPUT_CSV}")
```

## 3. Usage Notes

- Run the utility after every data-collection session.
- The resulting CSV becomes the authoritative ground-truth index for training Framework 2 / 3 and for regulatory audit packages.
- If the body cameras support embedded UTC timestamps in the AVI container, replace the `mtime`-based start calculation with a proper metadata parse for higher accuracy.

