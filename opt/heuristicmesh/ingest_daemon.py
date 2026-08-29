#!/usr/bin/env python3
import serial
import serial.tools.list_ports
import struct
import time
import threading
import numpy as np
from multiprocessing import shared_memory

# Config
EXPECTED_VID = 0x303A  # Espressif USB VID
BAUD = 921600
FRAME_PIXELS = 768

def find_esp32_ports():
    return [p.device for p in serial.tools.list_ports.comports() if p.vid == EXPECTED_VID]

def handle_esp32(port):
    print(f"[INGEST] Spawning thread for {port}")
    ser = serial.Serial(port, BAUD, timeout=0.5)
    while True:
        # Parse exact binary protocol from the firmware
        if ser.read(2) != b'\xAA\xBB':
            continue
        frame_idx = ser.read(1)[0]
        ts_esp = struct.unpack('<Q', ser.read(8))[0]
        raw = ser.read(FRAME_PIXELS * 4)
        if len(raw) != FRAME_PIXELS * 4:
            continue
        data = np.frombuffer(raw, dtype=np.float32)
        # TODO: Push to shared memory or local ring buffer
        print(f"[{port}] Frame {frame_idx} received, Temp max: {data.max():.1f}°C")

if __name__ == "__main__":
    ports = find_esp32_ports()
    if not ports:
        print("[ERR] No ESP32s found. Check USB cables.")
        exit(1)
    threads = []
    for p in ports:
        t = threading.Thread(target=handle_esp32, args=(p,))
        t.daemon = True
        t.start()
        threads.append(t)
    for t in threads:
        t.join()