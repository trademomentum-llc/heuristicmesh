#!/bin/bash
PORT=${1:-/dev/ttyUSB0}
cd "$(dirname "$0")/../jetson"
python3 hm_ingest.py --port "$PORT"
