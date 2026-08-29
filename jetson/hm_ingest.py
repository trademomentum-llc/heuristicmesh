#!/usr/bin/env python3
"""
HeuristicMesh Production Ingestion Daemon
Jetson Orin Nano side – Framework 1 receiver + Framework 2 spatial analysis
"""

import serial
import struct
import time
import json
import logging
from collections import deque
from dataclasses import dataclass, asdict
from pathlib import Path
import argparse

MAGIC = 0xA5
PACKET_SIZE = 19

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("hm_ingest.log")
    ]
)
log = logging.getLogger("hm")

@dataclass
class ThermalFrame:
    ts: float
    frame_id: int
    fall_candidate: bool
    centroid_valid: bool
    max_temp: float
    avg_temp: float
    hot_count: int
    cx: float
    cy: float
    velocity: float
    mass: float

class RingBuffer:
    def __init__(self, seconds=15, hz=20):
        self.buf = deque(maxlen=seconds * hz)

    def push(self, frame: ThermalFrame):
        self.buf.append(frame)

    def recent(self, n=30):
        return list(self.buf)[-n:]

def parse_packet(data: bytes) -> ThermalFrame | None:
    if len(data) != PACKET_SIZE or data[0] != MAGIC:
        return None
    frame_id = struct.unpack_from("<I", data, 1)[0]
    flags = data[5]
    max_t = struct.unpack_from("<h", data, 6)[0] / 100.0
    avg_t = struct.unpack_from("<h", data, 8)[0] / 100.0
    hot = data[10]
    cx = struct.unpack_from("<h", data, 11)[0] / 100.0
    cy = struct.unpack_from("<h", data, 13)[0] / 100.0
    vel = struct.unpack_from("<h", data, 15)[0] / 100.0
    mass = struct.unpack_from("<h", data, 17)[0] / 10.0

    return ThermalFrame(
        ts=time.time(),
        frame_id=frame_id,
        fall_candidate=bool(flags & 0x01),
        centroid_valid=bool(flags & 0x02),
        max_temp=max_t,
        avg_temp=avg_t,
        hot_count=hot,
        cx=cx, cy=cy,
        velocity=vel,
        mass=mass
    )

class Framework2:
    """Spatial analysis on the thermal stream"""
    def __init__(self):
        self.events = []

    def evaluate(self, ring: RingBuffer) -> dict | None:
        frames = ring.recent(40)
        if len(frames) < 10:
            return None

        # Look for rapid downward centroid movement + sustained hot mass
        candidates = [f for f in frames if f.fall_candidate]
        if len(candidates) < 3:
            return None

        # Simple velocity integral and y-direction preference
        dys = []
        for i in range(1, len(frames)):
            if frames[i].centroid_valid and frames[i-1].centroid_valid:
                dys.append(frames[i].cy - frames[i-1].cy)

        if not dys:
            return None

        net_dy = sum(dys)
        # In AMG image coordinates, increasing y is downward
        if net_dy > 1.2 and max(f.velocity for f in frames) > 1.5:
            event = {
                "type": "fall_candidate",
                "ts": frames[-1].ts,
                "confidence": min(0.95, 0.55 + len(candidates) * 0.08),
                "net_dy": round(net_dy, 2),
                "max_vel": round(max(f.velocity for f in frames), 2),
                "frames": len(candidates)
            }
            self.events.append(event)
            return event
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--log-json", default="thermal_events.jsonl")
    args = parser.parse_args()

    ring = RingBuffer()
    fw2 = Framework2()

    log.info(f"Opening {args.port} @ {args.baud}")
    ser = serial.Serial(args.port, args.baud, timeout=0.1)

    buf = bytearray()
    json_log = open(args.log_json, "a")

    try:
        while True:
            data = ser.read(64)
            if data:
                buf.extend(data)

            while len(buf) >= PACKET_SIZE:
                # Resync on magic
                if buf[0] != MAGIC:
                    buf.pop(0)
                    continue
                packet = bytes(buf[:PACKET_SIZE])
                del buf[:PACKET_SIZE]

                frame = parse_packet(packet)
                if frame is None:
                    continue

                ring.push(frame)

                if frame.fall_candidate:
                    log.info(f"ESP flag  frame={frame.frame_id}  vel={frame.velocity:.2f}  hot={frame.hot_count}")

                event = fw2.evaluate(ring)
                if event:
                    log.warning(f"FRAMEWORK2 EVENT: {event}")
                    json_log.write(json.dumps(event) + "\n")
                    json_log.flush()

    except KeyboardInterrupt:
        log.info("Shutdown")
    finally:
        json_log.close()
        ser.close()

if __name__ == "__main__":
    main()
