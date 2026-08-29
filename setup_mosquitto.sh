#!/bin/bash
# HeuristicMesh — NUC MQTT Broker Setup (Ubuntu 24.04)
# Run with: sudo ./setup_mosquitto.sh

set -e

echo "[MQTT] Installing Mosquitto..."
apt update && apt install -y mosquitto mosquitto-clients

echo "[MQTT] Creating TLS certificate directory..."
mkdir -p /etc/mosquitto/certs
cd /etc/mosquitto/certs

echo "[MQTT] Generating self-signed CA & server cert (valid 365 days)..."
# CA key & cert
openssl genrsa -out ca.key 2048
openssl req -new -x509 -days 365 -key ca.key -out ca.crt -subj "/CN=HeuristicMesh-CA/O=TradeMomentum"

# Server key & CSR
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/CN=nuc.heuristicmesh.local/O=TradeMomentum"

# Sign server cert with CA
openssl x509 -req -days 365 -in server.csr -CA ca.crt -CAkey ca.key -set_serial 01 -out server.crt

chown mosquitto:mosquitto *.key *.crt *.pem
chmod 600 *.key

echo "[MQTT] Writing mosquitto.conf..."
cat > /etc/mosquitto/conf.d/heuristicmesh.conf <<EOF
listener 1883 0.0.0.0
listener 8883 0.0.0.0
cafile /etc/mosquitto/certs/ca.crt
certfile /etc/mosquitto/certs/server.crt
keyfile /etc/mosquitto/certs/server.key
require_certificate false
allow_anonymous false
password_file /etc/mosquitto/passwd
EOF

# Set a dedicated user for the USR gateway
echo "[MQTT] Set password for 'usr_gateway' user (enter twice):"
mosquitto_passwd -c /etc/mosquitto/passwd usr_gateway

echo "[MQTT] Restarting Mosquitto..."
systemctl restart mosquitto
systemctl enable mosquitto

echo "[MQTT] Broker ready."
echo ""
echo "========== FIREWALL NOTE =========="
echo "On your Zyxel USG Flex 100H, create ACL rules to allow:"
echo "  - VLAN30 → VLAN10, port 1883 (TCP) for plain MQTT"
echo "  - VLAN30 → VLAN10, port 8883 (TCP) for TLS MQTT"
echo "==================================="
echo ""
echo "Test locally:"
echo "  mosquitto_sub -h localhost -t 'test' -u usr_gateway -P '<password>'"
echo "  mosquitto_pub -h localhost -t 'test' -m 'hello' -u usr_gateway -P '<password>'"