#!/usr/bin/env python3
"""
HeuristicMesh AMG8833-Only Ingestion Daemon
Jetson Orin Nano side - Framework 1 receiver + Framework 2 spatial analysis
Supports:
- Unified Binary Protocol v1.0 (see PROTOCOL_SPECIFICATION.md)
- Legacy protocol (0xA5) for backward compatibility
- Direct USB serial connection
- ModBus/TCP via USR-TCP232
- MQTT (optional)
- AMG8833 sensors ONLY (2x sensors, no )
- Multi-device aggregation
- Full provenance logging
Usage:
    python3 hm_ingest_amg_only.py --port /dev/ttyACM0 --baud 921600
    python3 hm_ingest_amg_only.py --modbus 192.168.30.10:502 --unit-id 1
    python3 hm_ingest_amg_only.py --mqtt mqtt://192.168.10.100:1883
Author: HeuristicMesh Engineering Team
Version: 1.1
Date: 2026-08-29
Note:  support removed - only 2x AMG8833 sensors in inventory
"""
import argparse
import json
import logging
import struct
import time
import threading
from collections import deque, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Optional, Dict, List, Any
import serial
import serial.tools.list_ports
# Optional imports (install as needed)
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logging.warning("MQTT not available - install paho-mqtt")
try:
    from pymodbus.client import ModbusTcpClient
    MODBUS_AVAILABLE = True
except ImportError:
    MODBUS_AVAILABLE = False
    logging.warning("ModBus/TCP not available - install pymodbus")
# ============================================================================
# CONSTANTS
# ============================================================================
# Protocol constants
PROTOCOL_MAGIC = b'\xAA\x55'
LEGACY_MAGIC = b'\xA5'
PROTOCOL_VERSION = 0x01
# Message types
class MessageType(Enum):
    HELLO = 0x01
    HEARTBEAT = 0x02
    AMG_FRAME = 0x03
    FALL_CANDIDATE = 0x08
    CONFIG_REQUEST = 0x09
    CONFIG_RESPONSE = 0x0A
    ERROR = 0x0B
    ACK = 0x0C
    NACK = 0x0D
    MODBUS_WRAPPER = 0x80
# Sensor types
class SensorType(Enum):
    NONE = 0x00
    AMG8833 = 0x01
# Device types
class DeviceType(Enum):
    ESP32_S3 = 0x01
    ESP32_S2 = 0x02
    ESP32_GENERIC = 0x03
# ============================================================================
# DATA CLASSES
# ============================================================================
@dataclass
class MessageHeader:
    """Unified protocol message header"""
    magic: bytes
    version: int
    device_id: int
    message_type: MessageType
    flags: int
    payload_len: int
    sequence: int
    timestamp: int
    @classmethod
    def from_bytes(cls, data: bytes) -> 'MessageHeader':
        if len(data) < 10:
            raise ValueError("Header too short")
        magic = data[0:2]
        version = data[2]
        device_id = data[3]
        message_type = MessageType(data[4])
        flags = data[5]
        payload_len = struct.unpack_from('<H', data, 6)[0]
        sequence = struct.unpack_from('<H', data, 8)[0]
        timestamp = struct.unpack_from('<I', data, 10)[0]
        return cls(magic, version, device_id, message_type, flags, payload_len, sequence, timestamp)
@dataclass
class AMGFrame:
    """AMG8833 frame data"""
    timestamp_us: int
    frame_id: int
    flags: int
    hot_pixel_count: int
    max_temp: float
    avg_temp: float
    centroid_x: float
    centroid_y: float
    velocity: float
    mass: float
    pixels: List[float] = field(default_factory=list)
    device_id: int = 0
    @classmethod
    def from_payload(cls, payload: bytes, device_id: int) -> 'AMGFrame':
        if len(payload) < 84:
            raise ValueError("AMG frame payload too short")
        timestamp_us = struct.unpack_from('<Q', payload, 0)[0]
        frame_id = struct.unpack_from('<I', payload, 8)[0]
        flags = payload[12]
        hot_pixel_count = payload[13]
        max_temp = struct.unpack_from('<f', payload, 16)[0]
        avg_temp = struct.unpack_from('<f', payload, 20)[0]
        centroid_x = struct.unpack_from('<f', payload, 24)[0]
        centroid_y = struct.unpack_from('<f', payload, 28)[0]
        velocity = struct.unpack_from('<f', payload, 32)[0]
        mass = struct.unpack_from('<f', payload, 36)[0]
        # Read 64 float pixels (256 bytes)
        pixels = list(struct.unpack_from('<64f', payload, 40))
        return cls(timestamp_us, frame_id, flags, hot_pixel_count, max_temp, avg_temp,
                  centroid_x, centroid_y, velocity, mass, pixels, device_id)
@dataclass
class FallCandidate:
    """Fall candidate detection"""
    timestamp_us: int
    frame_id: int
    confidence: float
    centroid_x: float
    centroid_y: float
    velocity: float
    acceleration: float
    sensor_source: SensorType
    flags: int
    device_id: int = 0
    @classmethod
    def from_payload(cls, payload: bytes, device_id: int) -> 'FallCandidate':
        if len(payload) < 32:
            raise ValueError("Fall candidate payload too short")
        timestamp_us = struct.unpack_from('<Q', payload, 0)[0]
        frame_id = struct.unpack_from('<I', payload, 8)[0]
        confidence = struct.unpack_from('<f', payload, 12)[0]
        centroid_x = struct.unpack_from('<f', payload, 16)[0]
        centroid_y = struct.unpack_from('<f', payload, 20)[0]
        velocity = struct.unpack_from('<f', payload, 24)[0]
        acceleration = struct.unpack_from('<f', payload, 28)[0]
        sensor_source = SensorType(payload[32])
        flags = payload[33]
        return cls(timestamp_us, frame_id, confidence, centroid_x, centroid_y,
                  velocity, acceleration, sensor_source, flags, device_id)
@dataclass
class DeviceInfo:
    """Device information"""
    device_id: int
    device_type: DeviceType
    sensor_type: SensorType
    capabilities: int
    fw_version: str
    last_heartbeat: float = 0.0
    is_online: bool = False
    sensor_count: int = 0
    sensor_types: List[SensorType] = field(default_factory=list)
# ============================================================================
# RING BUFFER FOR FRAME STORAGE
# ============================================================================
class RingBuffer:
    """Thread-safe ring buffer for frame storage"""
    def __init__(self, maxAMG_FRAMES: int = 1000):
        self.buf = deque(maxlen=maxAMG_FRAMES)
        self.lock = threading.Lock()
    def push(self, frame: AMGFrame) -> None:
        with self.lock:
            self.buf.append(frame)
    def get_recent(self, n: int = 10) -> List[AMGFrame]:
        with self.lock:
            return list(self.buf)[-n:]
    def get_all(self) -> List[AMGFrame]:
        with self.lock:
            return list(self.buf)
    def clear(self) -> None:
        with self.lock:
            self.buf.clear()
    def __len__(self) -> int:
        with self.lock:
            return len(self.buf)
# ============================================================================
# FRAMEWORK 2: SPATIAL ANALYSIS (AMG8833 ONLY)
# ============================================================================
class Framework2:
    """
    Spatial analysis on AMG8833 thermal stream
    Implements transparent, rule-based fall detection
    """
    def __init__(self, device_id: int):
        self.device_id = device_id
        self.events: List[Dict[str, Any]] = []
        # Tunable thresholds (can be loaded from config)
        self.thresholds = {
            'velocity_trigger': 1.8,
            'persistenceAMG_FRAMES': 4,
            'centroid_upper_half': 4.0,
            'centroid_downward_delta': 1.4,
            'base_confidence': 0.5,
            'velocity_weight': 0.05,
            'persistence_weight': 0.1,
            'impact_weight': 0.1,
            'immobility_weight': 0.1,
            'fall_confidence_threshold': 0.85
        }
    def evaluate_amg_frame(self, frame: AMGFrame) -> Optional[Dict[str, Any]]:
        """
        Evaluate AMG8833 frame for fall candidate
        Returns event dict if fall candidate detected, else None
        """
        # Check if this is a fall candidate from ESP32
        is_fall_candidate = bool(frame.flags & 0x01)
        centroid_valid = bool(frame.flags & 0x02)
        if not is_fall_candidate or not centroid_valid:
            return None
        # Compute confidence based on transparent rules
        confidence = self._compute_confidence(frame)
        if confidence >= self.thresholds['fall_confidence_threshold']:
            event = {
                'type': 'fall_candidate',
                'ts': frame.timestamp_us / 1e6,  # Convert to seconds
                'ts_us': frame.timestamp_us,
                'device_id': frame.device_id,
                'frame_id': frame.frame_id,
                'sensor': 'AMG8833',
                'confidence': round(confidence, 2),
                'centroid': {'x': round(frame.centroid_x, 2), 'y': round(frame.centroid_y, 2)},
                'velocity': round(frame.velocity, 2),
                'mass': round(frame.mass, 2),
                'hot_pixels': frame.hot_pixel_count,
                'max_temp': round(frame.max_temp, 1),
                'avg_temp': round(frame.avg_temp, 1),
                'flags': frame.flags
            }
            self.events.append(event)
            return event
        return None
    def _compute_confidence(self, frame: AMGFrame) -> float:
        """
        Compute confidence score using transparent rules
        """
        confidence = self.thresholds['base_confidence']
        # Velocity contribution
        if frame.velocity > self.thresholds['velocity_trigger']:
            excess_vel = frame.velocity - self.thresholds['velocity_trigger']
            confidence += excess_vel * 10 * self.thresholds['velocity_weight']
        # Hot pixel count contribution
        if frame.hot_pixel_count >= 3:
            confidence += (frame.hot_pixel_count - 2) * 0.05
        # Centroid position contribution (lower is better for fall)
        if frame.centroid_y < self.thresholds['centroid_upper_half']:
            confidence += (self.thresholds['centroid_upper_half'] - frame.centroid_y) * 0.05
        # Mass contribution
        if frame.mass > 10:
            confidence += min(0.1, (frame.mass - 10) * 0.005)
        return min(0.95, confidence)
# ============================================================================
# FRAMEWORK 3: EVENT CLASSIFICATION
# ============================================================================
class Framework3:
    """
    Event classification using transparent rules
    No ML/black-box models - purely rule-based
    """
    def __init__(self):
        self.classifications: List[Dict[str, Any]] = []
        self.event_history: List[Dict[str, Any]] = []
        # Classification thresholds
        self.thresholds = {
            'fall_velocity': 2.0,
            'fall_confidence': 0.8,
            'near_fall_velocity': 1.5,
            'near_fall_confidence': 0.6,
            'suspicious_confidence': 0.4
        }
    def classify_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a Framework 2 event using transparent rules
        """
        velocity = event.get('velocity', 0)
        confidence = event.get('confidence', 0)
        # Transparent classification rules
        if confidence > self.thresholds['fall_confidence'] and velocity > self.thresholds['fall_velocity']:
            classification = 'FALL'
            priority = 'HIGH'
        elif confidence > self.thresholds['near_fall_confidence'] and velocity > self.thresholds['near_fall_velocity']:
            classification = 'NEAR_FALL'
            priority = 'MEDIUM'
        elif confidence > self.thresholds['suspicious_confidence']:
            classification = 'SUSPICIOUS_ACTIVITY'
            priority = 'LOW'
        else:
            classification = 'NOISE'
            priority = 'NONE'
        result = {
            'event_id': len(self.classifications),
            'classification': classification,
            'priority': priority,
            'confidence': confidence,
            'velocity': velocity,
            'timestamp': event.get('ts', 0),
            'device_id': event.get('device_id', 0),
            'frame_id': event.get('frame_id', 0),
            'sensor': event.get('sensor', 'UNKNOWN')
        }
        self.classifications.append(result)
        self.event_history.append(result)
        return result
# ============================================================================
# INGESTION ENGINE
# ============================================================================
class IngestionEngine:
    """
    Main ingestion engine for HeuristicMesh
    Handles serial connections, protocol parsing, and data distribution
    """
    def __init__(self):
        self.devices: Dict[int, DeviceInfo] = {}
        self.fw2_engines: Dict[int, Framework2] = {}
        self.fw3_engine = Framework3()
        self.buffers: Dict[int, RingBuffer] = {}
        # Statistics
        self.stats = {
            'amgAMG_FRAMES': 0,
            'fall_candidates': 0,
            'classifications': 0,
            'errors': 0,
            'bytes_received': 0,
            'messages_received': 0
        }
        # Logger
        self.logger = logging.getLogger('IngestionEngine')
    def register_device(self, header: MessageHeader, payload: bytes) -> None:
        """Register a new device from HELLO message"""
        if len(payload) < 12:
            self.logger.warning(f"Short HELLO payload from device {header.device_id}")
            return
        device_type = DeviceType(payload[0])
        fw_version = f"{payload[1]}.{payload[2]}.{payload[3]}.{payload[4]}"
        sensor_count = payload[5]
        sensor_types = []
        for i in range(sensor_count):
            if i + 6 < len(payload):
                sensor_types.append(SensorType(payload[6 + i]))
        capabilities = struct.unpack_from('<I', payload, 8)[0] if len(payload) >= 12 else 0
        device = DeviceInfo(
            device_id=header.device_id,
            device_type=device_type,
            sensor_type=sensor_types[0] if sensor_types else SensorType.NONE,
            capabilities=capabilities,
            fw_version=fw_version,
            sensor_count=sensor_count,
            sensor_types=sensor_types
        )
        self.devices[header.device_id] = device
        self.fw2_engines[header.device_id] = Framework2(header.device_id)
        self.buffers[header.device_id] = RingBuffer(maxAMG_FRAMES=1000)
        self.logger.info(f"Device {header.device_id} registered: {device_type.name}, "
                        f"FW {fw_version}, Sensors: {[s.name for s in sensor_types]}")
    def handle_amg_frame(self, header: MessageHeader, payload: bytes, device: DeviceInfo) -> None:
        """Handle AMG_FRAME message"""
        try:
            frame = AMGFrame.from_payload(payload, header.device_id)
            # Store in buffer
            self.buffers[header.device_id].push(frame)
            self.stats['amgAMG_FRAMES'] += 1
            self.stats['bytes_received'] += len(payload)
            # Process through Framework 2
            fw2 = self.fw2_engines.get(header.device_id)
            if fw2:
                event = fw2.evaluate_amg_frame(frame)
                if event:
                    self.stats['fall_candidates'] += 1
                    self.logger.warning(f"Fall candidate: device={header.device_id}, "
                                       f"confidence={event['confidence']:.2f}, "
                                       f"velocity={event['velocity']:.2f}")
                    # Pass to Framework 3 for classification
                    classification = self.fw3_engine.classify_event(event)
                    self.stats['classifications'] += 1
                    self.logger.warning(f"Classification: {classification['classification']} "
                                       f"(priority: {classification['priority']})")
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Error processing AMG frame from device {header.device_id}: {e}")
    def handle_fall_candidate(self, header: MessageHeader, payload: bytes, device: DeviceInfo) -> None:
        """Handle FALL_CANDIDATE message"""
        try:
            candidate = FallCandidate.from_payload(payload, header.device_id)
            self.stats['fall_candidates'] += 1
            self.logger.warning(f"Fall candidate from device {header.device_id}: "
                               f"confidence={candidate.confidence:.2f}, "
                               f"velocity={candidate.velocity:.2f}")
            # Classify using Framework 3
            classification = self.fw3_engine.classify_event({
                'ts': candidate.timestamp_us / 1e6,
                'confidence': candidate.confidence,
                'velocity': candidate.velocity,
                'device_id': candidate.device_id,
                'frame_id': candidate.frame_id,
                'sensor': candidate.sensor_source.name
            })
            self.stats['classifications'] += 1
            self.logger.warning(f"Classification: {classification['classification']}")
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Error processing fall candidate from device {header.device_id}: {e}")
    def handle_heartbeat(self, header: MessageHeader, payload: bytes, device: DeviceInfo) -> None:
        """Handle HEARTBEAT message"""
        if device:
            device.last_heartbeat = time.time()
            device.is_online = True
    def handle_message(self, header: MessageHeader, payload: bytes) -> None:
        """Route message to appropriate handler"""
        self.stats['messages_received'] += 1
        # Get or create device info
        device = self.devices.get(header.device_id)
        if not device and header.message_type != MessageType.HELLO:
            self.logger.warning(f"Message from unknown device {header.device_id}")
        # Route based on message type
        if header.message_type == MessageType.HELLO:
            self.register_device(header, payload)
        elif header.message_type == MessageType.HEARTBEAT:
            self.handle_heartbeat(header, payload, device)
        elif header.message_type == MessageType.AMG_FRAME:
            self.handle_amg_frame(header, payload, device)
        elif header.message_type == MessageType.FALL_CANDIDATE:
            self.handle_fall_candidate(header, payload, device)
        elif header.message_type == MessageType.ERROR:
            self.logger.error(f"Error from device {header.device_id}: {payload}")
        else:
            self.logger.debug(f"Unhandled message type {header.message_type} from device {header.device_id}")
# ============================================================================
# SERIAL CONNECTION MANAGER
# ============================================================================
class SerialConnection:
    """Manages a single serial connection"""
    def __init__(self, port: str, baudrate: int, engine: IngestionEngine):
        self.port = port
        self.baudrate = baudrate
        self.engine = engine
        self.serial = None
        self.running = False
        self.thread = None
        self.logger = logging.getLogger(f'SerialConnection[{port}]')
    def start(self) -> None:
        """Start the serial connection"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=0.1,
                rtscts=False,
                dsrdtr=False
            )
            self.running = True
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
            self.logger.info(f"Started serial connection on {self.port} at {self.baudrate} baud")
        except Exception as e:
            self.logger.error(f"Failed to start serial connection: {e}")
            raise
    def stop(self) -> None:
        """Stop the serial connection"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        if self.serial:
            self.serial.close()
            self.serial = None
        self.logger.info("Stopped serial connection")
    def _read_loop(self) -> None:
        """Read loop for serial connection"""
        buffer = bytearray()
        while self.running and self.serial:
            try:
                # Read available bytes
                data = self.serial.read(self.serial.in_waiting or 1024)
                if not data:
                    time.sleep(0.01)
                    continue
                buffer.extend(data)
                # Process complete messages
                while len(buffer) >= 10:  # Minimum header size
                    # Check for protocol magic
                    if buffer[0:2] == PROTOCOL_MAGIC:
                        # Parse header
                        if len(buffer) >= 10:
                            payload_len = struct.unpack_from('<H', buffer, 6)[0]
                            total_len = 10 + payload_len
                            if len(buffer) >= total_len:
                                # Extract message
                                header_data = bytes(buffer[0:10])
                                payload_data = bytes(buffer[10:total_len])
                                try:
                                    header = MessageHeader.from_bytes(header_data)
                                    self.engine.handle_message(header, payload_data)
                                except Exception as e:
                                    self.logger.error(f"Error parsing message: {e}")
                                # Remove processed bytes
                                del buffer[0:total_len]
                            else:
                                break  # Wait for more data
                        else:
                            break
                    elif buffer[0:1] == LEGACY_MAGIC:
                        # Legacy protocol - skip for now
                        self.logger.debug("Legacy protocol message detected")
                        del buffer[0:1]
                    else:
                        # Unknown data - skip byte by byte
                        self.logger.debug(f"Unknown byte: 0x{buffer[0]:02X}")
                        del buffer[0:1]
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error in read loop: {e}")
                    time.sleep(0.1)
        self.logger.info("Read loop exited")
# ============================================================================
# MODBUS/TCP CONNECTION MANAGER
# ============================================================================
class ModBusConnection:
    """Manages ModBus/TCP connection via USR-TCP232"""
    def __init__(self, host: str, port: int, unit_id: int, engine: IngestionEngine):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.engine = engine
        self.client = None
        self.running = False
        self.thread = None
        self.logger = logging.getLogger(f'ModBusConnection[{host}:{port}]')
    def start(self) -> None:
        """Start the ModBus connection"""
        if not MODBUS_AVAILABLE:
            self.logger.error("ModBus/TCP not available - pymodbus not installed")
            return
        try:
            self.client = ModbusTcpClient(self.host, port=self.port, unit_id=self.unit_id)
            if not self.client.connect():
                self.logger.error(f"Failed to connect to ModBus at {self.host}:{self.port}")
                return
            self.running = True
            self.thread = threading.Thread(target=self._poll_loop, daemon=True)
            self.thread.start()
            self.logger.info(f"Started ModBus connection to {self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Failed to start ModBus connection: {e}")
            raise
    def stop(self) -> None:
        """Stop the ModBus connection"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        if self.client:
            self.client.close()
            self.client = None
        self.logger.info("Stopped ModBus connection")
    def _poll_loop(self) -> None:
        """Poll loop for ModBus connection"""
        while self.running and self.client:
            try:
                # Read holding registers or use custom protocol
                # For HeuristicMesh, we use a custom wrapper protocol
                result = self.client.read_holding_registers(0x0000, 10)
                if result.isError():
                    self.logger.debug(f"ModBus read error: {result}")
                else:
                    # Parse custom protocol
                    # This is a placeholder - implement based on your ModBus wrapper
                    pass
                time.sleep(0.1)
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error in ModBus poll loop: {e}")
                    time.sleep(1.0)
# ============================================================================
# MAIN APPLICATION
# ============================================================================
class HeuristicMeshIngest:
    """Main application class"""
    def __init__(self):
        self.engine = IngestionEngine()
        self.serial_connections: List[SerialConnection] = []
        self.modbus_connections: List[ModBusConnection] = []
        self.mqtt_client = None
        self.running = False
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('HeuristicMeshIngest')
    def add_serial_connection(self, port: str, baudrate: int = 921600) -> None:
        """Add a serial connection"""
        conn = SerialConnection(port, baudrate, self.engine)
        self.serial_connections.append(conn)
    def add_modbus_connection(self, host: str, port: int = 502, unit_id: int = 1) -> None:
        """Add a ModBus/TCP connection"""
        conn = ModBusConnection(host, port, unit_id, self.engine)
        self.modbus_connections.append(conn)
    def start(self) -> None:
        """Start all connections"""
        self.running = True
        # Start serial connections
        for conn in self.serial_connections:
            try:
                conn.start()
            except Exception as e:
                self.logger.error(f"Failed to start serial connection {conn.port}: {e}")
        # Start ModBus connections
        for conn in self.modbus_connections:
            try:
                conn.start()
            except Exception as e:
                self.logger.error(f"Failed to start ModBus connection {conn.host}: {e}")
        self.logger.info("HeuristicMesh Ingestion started")
    def stop(self) -> None:
        """Stop all connections"""
        self.running = False
        for conn in self.serial_connections:
            conn.stop()
        for conn in self.modbus_connections:
            conn.stop()
        self.logger.info("HeuristicMesh Ingestion stopped")
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        return {
            **self.engine.stats,
            'devices': len(self.engine.devices),
            'buffers': {did: len(buf) for did, buf in self.engine.buffers.items()}
        }
    def print_stats(self) -> None:
        """Print current statistics"""
        stats = self.get_stats()
        self.logger.info("=== Statistics ===")
        for key, value in stats.items():
            if isinstance(value, dict):
                self.logger.info(f"  {key}: {value}")
            else:
                self.logger.info(f"  {key}: {value}")
# ============================================================================
# MAIN
# ============================================================================
def main():
    parser = argparse.ArgumentParser(description='HeuristicMesh AMG8833-Only Ingestion Daemon')
    parser.add_argument('--port', type=str, nargs='+', 
                        help='Serial port(s) to connect to (e.g., /dev/ttyACM0 /dev/ttyACM1)')
    parser.add_argument('--baud', type=int, default=921600,
                        help='Baud rate for serial connections (default: 921600)')
    parser.add_argument('--modbus', type=str, nargs='+',
                        help='ModBus/TCP connection(s) in host:port format')
    parser.add_argument('--unit-id', type=int, default=1,
                        help='ModBus unit ID (default: 1)')
    parser.add_argument('--list-ports', action='store_true',
                        help='List available serial ports and exit')
    parser.add_argument('--stats-interval', type=int, default=60,
                        help='Statistics print interval in seconds (default: 60)')
    parser.add_argument('--log-level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging level (default: INFO)')
    args = parser.parse_args()
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    # List ports if requested
    if args.list_ports:
        ports = serial.tools.list_ports.comports()
        print("Available serial ports:")
        for port in ports:
            print(f"  {port.device}: {port.description}")
        return
    # Create application
    app = HeuristicMeshIngest()
    # Add serial connections
    if args.port:
        for port in args.port:
            app.add_serial_connection(port, args.baud)
    # Add ModBus connections
    if args.modbus:
        for conn in args.modbus:
            host, port = conn.split(':')
            app.add_modbus_connection(host, int(port), args.unit_id)
    # Start application
    app.start()
    # Print stats periodically
    try:
        while app.running:
            time.sleep(args.stats_interval)
            app.print_stats()
    except KeyboardInterrupt:
        print("\nShutting down...")
        app.stop()
if __name__ == '__main__':
    main()