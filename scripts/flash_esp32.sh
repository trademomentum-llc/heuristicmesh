#!/bin/bash
set -e
cd "$(dirname "$0")/../esp32"
echo "Building and uploading ESP32 firmware..."
pio run -t upload
echo "Done. Starting monitor (Ctrl+C to exit)..."
pio device monitor -b 115200
