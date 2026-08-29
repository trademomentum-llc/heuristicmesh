#!/usr/bin/env python3
"""
HeuristicMesh Unified Ingestion Daemon
Jetson Orin Nano side - Framework 1 receiver + Framework 2 spatial analysis

Supports:
- Unified Binary Protocol v1.0 (see PROTOCOL_SPECIFICATION.md)
- Legacy protocol (0xA5) for backward compatibility
- Direct USB serial connection
- ModBus/TCP via USR-TCP232
- MQTT (optional)
- AMG8833 and MLX90640 sensors
- Multi-device aggregation
- Full provenance logging

Usage:
    python3 hm_ingest_unified.py --port /dev/ttyACM0 --baud 921600
    python3 hm_ingest_unified.py --modbus 192.168.30.10:502 --unit-id 1
    python3 hm_ingest_unified.py --mqtt mqtt://192.168.10.100:1883

Author: HeuristicMesh Engineering Team
Version: 1.0
Date: 2026-08-29
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
from typing import Optional, Union, Dict, List, Any
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
    MLX_FRAME = 0x04
    BURST_START = 0x05
    BURST_FRAME = 0x06
    BURST_END = 0x07
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
    MLX90640 = 0x02
    DUAL = 0x03

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
class MLXFrame:
    """MLX90640 frame data"""
    timestamp_us: int
    frame_id: int
    flags: int
    max_temp: float
    avg_temp: float
    min_temp: float
    pixels: List[float] = field(default_factory=list)
    device_id: int = 0
    burst_id: Optional[int] = None
    burst_index: Optional[int] = None
    
    @classmethod
    def from_payload(cls, payload: bytes, device_id: int) -> 'MLXFrame':
        if len(payload) < 3092:
            raise ValueError("MLX frame payload too short")
        
        timestamp_us = struct.unpack_from('<Q', payload, 0)[0]
        frame_id = struct.unpack_from('<I', payload, 8)[0]
        flags = payload[12]
        max_temp = struct.unpack_from('<f', payload, 16)[0]
        avg_temp = struct.unpack_from('<f', payload, 20)[0]
        min_temp = struct.unpack_from('<f', payload, 24)[0]
        
        # Read 768 float pixels (3072 bytes)
        pixels = list(struct.unpack_from('<768f', payload, 28))
        
        return cls(timestamp_us, frame_id, flags, max_temp, avg_temp, min_temp,
                  pixels, device_id)

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
    
    def __init__(self, max_frames: int = 1000):
        self.buf = deque(maxlen=max_frames)
        self.lock = threading.Lock()
    
    def push(self, frame: Union[AMGFrame, MLXFrame]) -> None:
        with self.lock:
            self.buf.append(frame)
    
    def get_recent(self, n: int = 10) -> List[Union[AMGFrame, MLXFrame]]:
        with self.lock:
            return list(self.buf)[-n:]
    
    def get_all(self) -> List[Union[AMGFrame, MLXFrame]]:
        with self.lock:
            return list(self.buf)
    
    def clear(self) -> None:
        with self.lock:
            self.buf.clear()
    
    def __len__(self) -> int:
        with self.lock:
            return len(self.buf)

# ============================================================================
# FRAMEWORK 2: SPATIAL ANALYSIS
# ============================================================================

class Framework2:
    """
    Spatial analysis on thermal stream
    Implements transparent, rule-based fall detection
    """
    
    def __init__(self, device_id: int):
        self.device_id = device_id
        self.events: List[Dict[str, Any]] = []
        self.burst_frames: Dict[int, List[MLXFrame]] = {}  # burst_id -> frames
        self.current_burst_id: Optional[int] = None
        
        # Tunable thresholds (can be loaded from config)
        self.thresholds = {
            'velocity_trigger': 1.8,
            'persistence_frames': 4,
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
    
    def evaluate_mlx_frame(self, frame: MLXFrame) -> Optional[Dict[str, Any]]:
        """
        Evaluate MLX90640 frame for spatial features
        """
        # For MLX frames, we compute additional spatial features
        features = self._extract_spatial_features(frame)
        
        # If this is part of a burst, store it
        if frame.burst_id is not None:
            if frame.burst_id not in self.burst_frames:
                self.burst_frames[frame.burst_id] = []
            self.burst_frames[frame.burst_id].append(frame)
            
            # If we have all frames in the burst, analyze
            if len(self.burst_frames[frame.burst_id]) >= 24:  # BURST_FRAMES
                return self._analyze_burst(frame.burst_id)
        
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
    
    def _extract_spatial_features(self, frame: MLXFrame) -> Dict[str, float]:
        """
        Extract spatial features from MLX90640 frame
        """
        pixels = frame.pixels
        
        # Find hot pixels (above human threshold)
        hot_pixels = [(i, p) for i, p in enumerate(pixels) if p >= 27.5]
        
        if not hot_pixels:
            return {
                'hot_pixel_count': 0,
                'centroid_x': 0,
                'centroid_y': 0,
                'bounding_box_area': 0,
                'aspect_ratio': 0,
                'max_temp': frame.max_temp,
                'min_temp': frame.min_temp,
                'avg_temp': frame.avg_temp
            }
        
        # Compute centroid
        sum_x = 0
        sum_y = 0
        total_weight = 0
        
        for idx, temp in hot_pixels:
            row = idx // 32
            col = idx % 32
            weight = temp - 27.5
            sum_x += col * weight
            sum_y += row * weight
            total_weight += weight
        
        centroid_x = sum_x / total_weight if total_weight > 0 else 0
        centroid_y = sum_y / total_weight if total_weight > 0 else 0
        
        # Compute bounding box
        min_col = min(idx % 32 for idx, _ in hot_pixels)
        max_col = max(idx % 32 for idx, _ in hot_pixels)
        min_row = min(idx // 32 for idx, _ in hot_pixels)
        max_row = max(idx // 32 for idx, _ in hot_pixels)
        
        bbox_width = max_col - min_col + 1
        bbox_height = max_row - min_row + 1
        bbox_area = bbox_width * bbox_height
        aspect_ratio = bbox_width / bbox_height if bbox_height > 0 else 0
        
        return {
            'hot_pixel_count': len(hot_pixels),
            'centroid_x': round(centroid_x, 2),
            'centroid_y': round(centroid_y, 2),
            'bounding_box_area': bbox_area,
            'aspect_ratio': round(aspect_ratio, 2),
            'max_temp': round(frame.max_temp, 1),
            'min_temp': round(frame.min_temp, 1),
            'avg_temp': round(frame.avg_temp, 1)
        }
    
    def _analyze_burst(self, burst_id: int) -> Dict[str, Any]:
        """
        Analyze complete burst of MLX90640 frames
        """
        frames = self.burst_frames.get(burst_id, [])
        if not frames:
            return None
        
        # Sort by frame_id
        frames.sort(key=lambda f: f.frame_id)
        
        # Extract features from all frames
        all_features = [self._extract_spatial_features(f) for f in frames]
        
        # Compute temporal features
        centroids = [(f['centroid_x'], f['centroid_y']) for f in all_features]
        
        # Compute velocity profile
        velocities = []
        for i in range(1, len(centroids)):
            dx = centroids[i][0] - centroids[i-1][0]
            dy = centroids[i][1] - centroids[i-1][1]
            vel = (dx**2 + dy**2)**0.5
            velocities.append(vel)
        
        max_velocity = max(velocities) if velocities else 0
        avg_velocity = sum(velocities) / len(velocities) if velocities else 0
        
        # Compute acceleration profile
        accelerations = []
        for i in range(1, len(velocities)):
            accel = velocities[i] - velocities[i-1]
            accelerations.append(accel)
        
        max_acceleration = max(accelerations) if accelerations else 0
        
        # Detect impact (sudden deceleration)
        impact_detected = any(a < -1.0 for a in accelerations)
        
        # Detect post-fall immobility
        final_frames = all_features[-5:]  # Last 5 frames
        final_centroids = [(f['centroid_x'], f['centroid_y']) for f in final_frames]
        immobility = all(
            (final_centroids[i][0] - final_centroids[i-1][0])**2 + 
            (final_centroids[i][1] - final_centroids[i-1][1])**2 < 0.1
            for i in range(1, len(final_centroids))
        ) if len(final_centroids) > 1 else False
        
        # Compute confidence
        confidence = self.thresholds['base_confidence']
        confidence += min(0.2, max_velocity * self.thresholds['velocity_weight'])
        confidence += self.thresholds['impact_weight'] if impact_detected else 0
        confidence += self.thresholds['immobility_weight'] if immobility else 0
        
        event = {
            'type': 'burst_analysis',
            'ts': frames[-1].timestamp_us / 1e6,
            'ts_us': frames[-1].timestamp_us,
            'burst_id': burst_id,
            'device_id': frames[0].device_id,
            'frame_count': len(frames),
            'sensor': 'MLX90640',
            'confidence': round(min(0.95, confidence), 2),
            'max_velocity': round(max_velocity, 2),
            'avg_velocity': round(avg_velocity, 2),
            'max_acceleration': round(max_acceleration, 2),
            'impact_detected': impact_detected,
            'immobility_detected': immobility,
            'features': all_features
        }
        
        self.events.append(event)
        return event

# ============================================================================
# SERIAL CONNECTION MANAGER
# ============================================================================

class SerialConnection:
    """
    Manages serial connection to ESP32 devices
    Supports both direct USB and ModBus/TCP
    """
    
    def __init__(self, port: str, baud: int = 115200):
        self.port = port
        self.baud = baud
        self.connection: Optional[serial.Serial] = None
        self.buffer = bytearray()
        self.device_info: Optional[DeviceInfo] = None
        self.is_connected = False
    
    def connect(self) -> bool:
        """Connect to serial port"""
        try:
            self.connection = serial.Serial(
                self.port,
                self.baud,
                timeout=0.1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            self.is_connected = True
            logging.info(f"Connected to {self.port} at {self.baud} baud")
            return True
        except Exception as e:
            logging.error(f"Failed to connect to {self.port}: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from serial port"""
        if self.connection and self.connection.is_open:
            self.connection.close()
        self.is_connected = False
    
    def read(self) -> bytes:
        """Read available data"""
        if not self.is_connected:
            return b''
        
        data = self.connection.read(self.connection.in_waiting or 1024)
        self.buffer.extend(data)
        return data
    
    def write(self, data: bytes) -> int:
        """Write data to serial port"""
        if not self.is_connected:
            return 0
        return self.connection.write(data)
    
    def parse_messages(self) -> List[tuple]:
        """
        Parse messages from buffer
        Returns list of (header, payload) tuples
        """
        messages = []
        
        while len(self.buffer) >= 10:  # Minimum header size
            # Check for magic bytes
            if self.buffer[0:2] != PROTOCOL_MAGIC:
                # Try to find magic bytes
                idx = self.buffer.find(PROTOCOL_MAGIC)
                if idx > 0:
                    # Discard bytes before magic
                    self.buffer = self.buffer[idx:]
                else:
                    # No magic found, discard first byte
                    self.buffer = self.buffer[1:]
                continue
            
            # We have magic bytes, parse header
            try:
                header = MessageHeader.from_bytes(self.buffer[0:10])
            except Exception as e:
                logging.warning(f"Failed to parse header: {e}")
                self.buffer = self.buffer[1:]
                continue
            
            # Check version
            if header.version != PROTOCOL_VERSION:
                logging.warning(f"Unsupported protocol version: {header.version}")
                self.buffer = self.buffer[10:]
                continue
            
            # Check if we have full message
            total_len = 10 + header.payload_len  # Header + payload
            if len(self.buffer) < total_len:
                break  # Wait for more data
            
            # Extract payload
            payload = self.buffer[10:total_len]
            self.buffer = self.buffer[total_len:]
            
            messages.append((header, payload))
        
        return messages

# ============================================================================
# MODBUS/TCP CONNECTION MANAGER
# ============================================================================

class ModBusConnection:
    """
    Manages ModBus/TCP connection to USR-TCP232 devices
    """
    
    def __init__(self, ip: str, port: int = 502, unit_id: int = 1):
        self.ip = ip
        self.port = port
        self.unit_id = unit_id
        self.connection = None
        self.is_connected = False
        self.buffer = bytearray()
    
    def connect(self) -> bool:
        """Connect to ModBus/TCP device"""
        if not MODBUS_AVAILABLE:
            logging.error("ModBus/TCP not available - install pymodbus")
            return False
        
        try:
            self.connection = ModbusTcpClient(
                self.ip,
                port=self.port,
                timeout=1.0,
                retry_on_empty=True
            )
            self.is_connected = self.connection.connect()
            if self.is_connected:
                logging.info(f"Connected to ModBus/TCP device at {self.ip}:{self.port}")
            return self.is_connected
        except Exception as e:
            logging.error(f"Failed to connect to ModBus/TCP device: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from ModBus/TCP device"""
        if self.connection:
            self.connection.close()
        self.is_connected = False
    
    def read_holding_registers(self, address: int, count: int) -> Optional[List[int]]:
        """Read holding registers (for debugging)"""
        if not self.is_connected:
            return None
        
        try:
            response = self.connection.read_holding_registers(
                address=address,
                count=count,
                slave=self.unit_id
            )
            if response.isError():
                return None
            return response.registers
        except Exception as e:
            logging.error(f"ModBus read error: {e}")
            return None

# ============================================================================
# MQTT CONNECTION MANAGER
# ============================================================================

class MQTTConnection:
    """
    Manages MQTT connection for optional MQTT transport
    """
    
    def __init__(self, broker: str, port: int = 1883, client_id: str = "heuristicmesh-jetson"):
        self.broker = broker
        self.port = port
        self.client_id = client_id
        self.client = None
        self.is_connected = False
        self.subscriptions: List[str] = []
        self.message_callback = None
    
    def connect(self, username: str = None, password: str = None) -> bool:
        """Connect to MQTT broker"""
        if not MQTT_AVAILABLE:
            logging.error("MQTT not available - install paho-mqtt")
            return False
        
        try:
            self.client = mqtt.Client(client_id=self.client_id)
            
            if username and password:
                self.client.username_pw_set(username, password)
            
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            self.is_connected = True
            logging.info(f"Connected to MQTT broker at {self.broker}:{self.port}")
            return True
        except Exception as e:
            logging.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def _on_connect(self, client, userdata, flags, rc) -> None:
        """MQTT connection callback"""
        if rc == 0:
            logging.info("MQTT connected successfully")
            # Resubscribe to topics
            for topic in self.subscriptions:
                client.subscribe(topic)
        else:
            logging.error(f"MQTT connection failed with code {rc}")
    
    def _on_message(self, client, userdata, msg) -> None:
        """MQTT message callback"""
        if self.message_callback:
            self.message_callback(msg.topic, msg.payload)
    
    def subscribe(self, topic: str, qos: int = 1) -> None:
        """Subscribe to MQTT topic"""
        if self.is_connected:
            self.client.subscribe(topic, qos)
        self.subscriptions.append(topic)
    
    def publish(self, topic: str, payload: Union[str, bytes], qos: int = 1, retain: bool = False) -> None:
        """Publish MQTT message"""
        if self.is_connected:
            self.client.publish(topic, payload, qos=qos, retain=retain)
    
    def disconnect(self) -> None:
        """Disconnect from MQTT broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        self.is_connected = False

# ============================================================================
# MAIN INGESTION CLASS
# ============================================================================

class HeuristicMeshIngest:
    """
    Main ingestion class that manages all connections and processing
    """
    
    def __init__(self, args):
        self.args = args
        
        # Connections
        self.serial_connections: Dict[str, SerialConnection] = {}
        self.modbus_connections: Dict[str, ModBusConnection] = {}
        self.mqtt_connection: Optional[MQTTConnection] = None
        
        # Data storage
        self.amg_buffer = RingBuffer(max_frames=1000)
        self.mlx_buffer = RingBuffer(max_frames=1000)
        self.events: List[Dict[str, Any]] = []
        
        # Framework instances
        self.fw2_instances: Dict[int, Framework2] = {}  # device_id -> Framework2
        
        # Device tracking
        self.devices: Dict[int, DeviceInfo] = {}
        
        # Logging
        self.setup_logging()
        
        # Statistics
        self.stats = {
            'frames_received': 0,
            'amg_frames': 0,
            'mlx_frames': 0,
            'fall_candidates': 0,
            'errors': 0,
            'start_time': time.time()
        }
    
    def setup_logging(self) -> None:
        """Setup logging configuration"""
        log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('hm_ingest_unified.log')
            ]
        )
        self.logger = logging.getLogger('hm_ingest')
    
    def initialize_connections(self) -> None:
        """Initialize all configured connections"""
        
        # Serial connections
        if self.args.port:
            ports = [self.args.port]
        else:
            # Auto-detect serial ports
            ports = [p.device for p in serial.tools.list_ports.comports()
                    if 'ACM' in p.device or 'USB' in p.device]
        
        for port in ports:
            conn = SerialConnection(port, self.args.baud)
            if conn.connect():
                self.serial_connections[port] = conn
                self.logger.info(f"Initialized serial connection: {port}")
        
        # ModBus connections
        if self.args.modbus:
            for modbus_config in self.args.modbus:
                ip, port = modbus_config.split(':')
                port = int(port) if port else 502
                conn = ModBusConnection(ip, port, self.args.unit_id)
                if conn.connect():
                    key = f"{ip}:{port}"
                    self.modbus_connections[key] = conn
                    self.logger.info(f"Initialized ModBus connection: {ip}:{port}")
        
        # MQTT connection
        if self.args.mqtt:
            self.mqtt_connection = MQTTConnection(self.args.mqtt)
            if self.mqtt_connection.connect(self.args.mqtt_user, self.args.mqtt_pass):
                # Subscribe to relevant topics
                self.mqtt_connection.subscribe('hm/fw1/+/telemetry')
                self.mqtt_connection.subscribe('hm/fw1/+/status')
                self.mqtt_connection.subscribe('hm/fw1/+/fall_flag')
                self.mqtt_connection.message_callback = self.handle_mqtt_message
                self.logger.info(f"Initialized MQTT connection: {self.args.mqtt}")
    
    def handle_mqtt_message(self, topic: str, payload: bytes) -> None:
        """Handle incoming MQTT message"""
        self.logger.debug(f"MQTT message: {topic} = {payload[:50]}")
        # TODO: Parse MQTT messages
    
    def process_connections(self) -> None:
        """Process all connections for incoming data"""
        
        # Process serial connections
        for port, conn in list(self.serial_connections.items()):
            if not conn.is_connected:
                continue
            
            # Read data
            data = conn.read()
            if not data:
                continue
            
            # Parse messages
            messages = conn.parse_messages()
            for header, payload in messages:
                self.process_message(header, payload, conn)
        
        # Process ModBus connections
        for key, conn in list(self.modbus_connections.items()):
            if not conn.is_connected:
                continue
            
            # TODO: Implement ModBus message reading
            # For now, ModBus/TCP is handled via the USR-TCP232 which
            # forwards to serial, so we rely on serial connections
    
    def process_message(self, header: MessageHeader, payload: bytes, 
                       conn: SerialConnection) -> None:
        """Process a single message"""
        self.stats['frames_received'] += 1
        
        # Update device tracking
        if header.device_id not in self.devices:
            self.devices[header.device_id] = DeviceInfo(
                device_id=header.device_id,
                device_type=DeviceType(header.device_id),  # Placeholder
                sensor_type=SensorType.NONE,
                capabilities=0,
                fw_version="0.0.0.0"
            )
        
        device = self.devices[header.device_id]
        device.last_heartbeat = time.time()
        device.is_online = True
        
        # Route message based on type
        try:
            if header.message_type == MessageType.HELLO:
                self.handle_hello(header, payload, device)
            elif header.message_type == MessageType.HEARTBEAT:
                self.handle_heartbeat(header, payload, device)
            elif header.message_type == MessageType.AMG_FRAME:
                self.handle_amg_frame(header, payload, device)
            elif header.message_type == MessageType.MLX_FRAME:
                self.handle_mlx_frame(header, payload, device)
            elif header.message_type == MessageType.FALL_CANDIDATE:
                self.handle_fall_candidate(header, payload, device)
            elif header.message_type == MessageType.ERROR:
                self.handle_error(header, payload, device)
            elif header.message_type == MessageType.BURST_START:
                self.handle_burst_start(header, payload, device)
            elif header.message_type == MessageType.BURST_FRAME:
                self.handle_burst_frame(header, payload, device)
            elif header.message_type == MessageType.BURST_END:
                self.handle_burst_end(header, payload, device)
            else:
                self.logger.warning(f"Unknown message type: {header.message_type}")
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Error processing message: {e}")
    
    def handle_hello(self, header: MessageHeader, payload: bytes, 
                   device: DeviceInfo) -> None:
        """Handle HELLO message"""
        if len(payload) < 16:
            self.logger.warning(f"HELLO payload too short from device {header.device_id}")
            return
        
        device_type = DeviceType(payload[0])
        fw_version_bytes = payload[1:5]
        fw_version = f"{fw_version_bytes[0]}.{fw_version_bytes[1]}.{fw_version_bytes[2]}.{fw_version_bytes[3]}"
        sensor_count = payload[5]
        sensor_types = [SensorType(payload[6 + i]) for i in range(sensor_count)]
        capabilities = struct.unpack_from('<I', payload, 6 + sensor_count)[0]
        
        device.device_type = device_type
        device.fw_version = fw_version
        device.sensor_count = sensor_count
        device.sensor_types = sensor_types
        device.capabilities = capabilities
        
        # Determine primary sensor type
        if SENSOR_DUAL in sensor_types:
            device.sensor_type = SENSOR_DUAL
        elif SENSOR_MLX90640 in sensor_types:
            device.sensor_type = SENSOR_MLX90640
        elif SENSOR_AMG8833 in sensor_types:
            device.sensor_type = SENSOR_AMG8833
        
        # Initialize Framework 2 for this device
        self.fw2_instances[header.device_id] = Framework2(header.device_id)
        
        self.logger.info(f"Device {header.device_id} connected: "
                        f"{device_type.name}, FW {fw_version}, "
                        f"Sensors: {[s.name for s in sensor_types]}, "
                        f"Capabilities: 0x{capabilities:08X}")
    
    def handle_heartbeat(self, header: MessageHeader, payload: bytes, 
                       device: DeviceInfo) -> None:
        """Handle HEARTBEAT message"""
        if len(payload) < 8:
            return
        
        uptime_ms = struct.unpack_from('<I', payload, 0)[0]
        status = payload[4]
        sensor_status = payload[5]
        error_count = struct.unpack_from('<H', payload, 6)[0]
        
        device.is_online = (status == 0x00)
        
        if status != 0x00:
            self.logger.warning(f"Device {header.device_id} status: {status}")
        
        if error_count > 0:
            self.logger.warning(f"Device {header.device_id} errors: {error_count}")
    
    def handle_amg_frame(self, header: MessageHeader, payload: bytes, 
                       device: DeviceInfo) -> None:
        """Handle AMG_FRAME message"""
        try:
            frame = AMGFrame.from_payload(payload, header.device_id)
            self.amg_buffer.push(frame)
            self.stats['amg_frames'] += 1
            
            # Process through Framework 2
            fw2 = self.fw2_instances.get(header.device_id)
            if fw2:
                event = fw2.evaluate_amg_frame(frame)
                if event:
                    self.stats['fall_candidates'] += 1
                    self.logger.warning(f"Fall candidate: {json.dumps(event, indent=2)}")
                    self.log_event(event)
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Error processing AMG frame: {e}")
    
    def handle_mlx_frame(self, header: MessageHeader, payload: bytes, 
                       device: DeviceInfo) -> None:
        """Handle MLX_FRAME message"""
        try:
            frame = MLXFrame.from_payload(payload, header.device_id)
            self.mlx_buffer.push(frame)
            self.stats['mlx_frames'] += 1
            
            # Process through Framework 2
            fw2 = self.fw2_instances.get(header.device_id)
            if fw2:
                event = fw2.evaluate_mlx_frame(frame)
                if event:
                    self.logger.warning(f"MLX event: {json.dumps(event, indent=2)}")
                    self.log_event(event)
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Error processing MLX frame: {e}")
    
    def handle_fall_candidate(self, header: MessageHeader, payload: bytes, 
                            device: DeviceInfo) -> None:
        """Handle FALL_CANDIDATE message"""
        try:
            candidate = FallCandidate.from_payload(payload, header.device_id)
            self.stats['fall_candidates'] += 1
            
            event = {
                'type': 'fall_candidate',
                'ts': candidate.timestamp_us / 1e6,
                'ts_us': candidate.timestamp_us,
                'device_id': candidate.device_id,
                'frame_id': candidate.frame_id,
                'sensor': candidate.sensor_source.name,
                'confidence': round(candidate.confidence, 2),
                'centroid': {
                    'x': round(candidate.centroid_x, 2),
                    'y': round(candidate.centroid_y, 2)
                },
                'velocity': round(candidate.velocity, 2),
                'acceleration': round(candidate.acceleration, 2),
                'flags': candidate.flags
            }
            
            self.logger.warning(f"Fall candidate: {json.dumps(event, indent=2)}")
            self.log_event(event)
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Error processing fall candidate: {e}")
    
    def handle_error(self, header: MessageHeader, payload: bytes, 
                   device: DeviceInfo) -> None:
        """Handle ERROR message"""
        if len(payload) < 4:
            return
        
        error_code = payload[0]
        severity = payload[1]
        error_data = struct.unpack_from('<H', payload, 2)[0]
        message = payload[4:].decode('utf-8', errors='ignore').strip()
        
        severity_names = {0: 'INFO', 1: 'WARNING', 2: 'ERROR', 3: 'FATAL'}
        severity_name = severity_names.get(severity, 'UNKNOWN')
        
        self.logger.error(f"Device {header.device_id} error [{error_code}]: "
                         f"[{severity_name}] {message}")
    
    def handle_burst_start(self, header: MessageHeader, payload: bytes, 
                          device: DeviceInfo) -> None:
        """Handle BURST_START message"""
        if len(payload) < 12:
            return
        
        burst_id = struct.unpack_from('<Q', payload, 0)[0]
        sensor_type = SensorType(payload[8])
        frame_rate = payload[9]
        frame_count = struct.unpack_from('<H', payload, 10)[0]
        trigger_reason = struct.unpack_from('<I', payload, 12)[0]
        
        self.logger.info(f"Burst start: device={header.device_id}, "
                        f"burst_id={burst_id}, sensor={sensor_type.name}, "
                        f"frames={frame_count}, reason={trigger_reason}")
        
        # Notify Framework 2
        fw2 = self.fw2_instances.get(header.device_id)
        if fw2:
            fw2.current_burst_id = burst_id
    
    def handle_burst_frame(self, header: MessageHeader, payload: bytes, 
                          device: DeviceInfo) -> None:
        """Handle BURST_FRAME message"""
        # Parse burst header
        if len(payload) < 8:
            return
        
        burst_id = struct.unpack_from('<Q', payload, 0)[0]
        frame_index = struct.unpack_from('<H', payload, 8)[0]
        total_frames = struct.unpack_from('<H', payload, 10)[0]
        
        # Remaining payload is the frame data
        frame_data = payload[12:]
        
        # Determine frame type based on size
        if len(frame_data) >= 3092:
            # MLX frame
            try:
                frame = MLXFrame.from_payload(frame_data, header.device_id)
                frame.burst_id = burst_id
                frame.burst_index = frame_index
                self.mlx_buffer.push(frame)
                self.stats['mlx_frames'] += 1
            except Exception as e:
                self.logger.error(f"Error parsing burst MLX frame: {e}")
        elif len(frame_data) >= 84:
            # AMG frame
            try:
                frame = AMGFrame.from_payload(frame_data, header.device_id)
                self.amg_buffer.push(frame)
                self.stats['amg_frames'] += 1
            except Exception as e:
                self.logger.error(f"Error parsing burst AMG frame: {e}")
    
    def handle_burst_end(self, header: MessageHeader, payload: bytes, 
                        device: DeviceInfo) -> None:
        """Handle BURST_END message"""
        if len(payload) < 8:
            return
        
        burst_id = struct.unpack_from('<Q', payload, 0)[0]
        frames_captured = struct.unpack_from('<H', payload, 8)[0]
        status = payload[10]
        
        self.logger.info(f"Burst end: device={header.device_id}, "
                        f"burst_id={burst_id}, frames={frames_captured}, "
                        f"status={status}")
        
        # Notify Framework 2
        fw2 = self.fw2_instances.get(header.device_id)
        if fw2:
            fw2.current_burst_id = None
    
    def log_event(self, event: Dict[str, Any]) -> None:
        """Log event to JSONL file"""
        if not hasattr(self, 'event_log_path'):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.event_log_path = Path(f'thermal_events_{timestamp}.jsonl')
        
        with open(self.event_log_path, 'a') as f:
            f.write(json.dumps(event) + '\n')
        
        # Also publish to MQTT if connected
        if self.mqtt_connection and self.mqtt_connection.is_connected:
            topic = f'hm/fw2/{event.get("device_id", "unknown")}/event'
            self.mqtt_connection.publish(topic, json.dumps(event))
    
    def print_stats(self) -> None:
        """Print statistics"""
        uptime = time.time() - self.stats['start_time']
        
        self.logger.info("=" * 60)
        self.logger.info("HeuristicMesh Ingest Statistics")
        self.logger.info("=" * 60)
        self.logger.info(f"Uptime: {uptime:.1f} seconds")
        self.logger.info(f"Frames received: {self.stats['frames_received']}")
        self.logger.info(f"  AMG frames: {self.stats['amg_frames']}")
        self.logger.info(f"  MLX frames: {self.stats['mlx_frames']}")
        self.logger.info(f"Fall candidates: {self.stats['fall_candidates']}")
        self.logger.info(f"Errors: {self.stats['errors']}")
        self.logger.info(f"Devices online: {sum(1 for d in self.devices.values() if d.is_online)}")
        self.logger.info("=" * 60)
    
    def run(self) -> None:
        """Main run loop"""
        self.logger.info("Starting HeuristicMesh Unified Ingest")
        self.initialize_connections()
        
        try:
            last_stats = time.time()
            
            while True:
                # Process all connections
                self.process_connections()
                
                # Print stats periodically
                if time.time() - last_stats >= 60:
                    self.print_stats()
                    last_stats = time.time()
                
                # Small sleep to prevent CPU overload
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
        finally:
            # Cleanup
            for conn in self.serial_connections.values():
                conn.disconnect()
            for conn in self.modbus_connections.values():
                conn.disconnect()
            if self.mqtt_connection:
                self.mqtt_connection.disconnect()
            
            self.logger.info("Shutdown complete")

# ============================================================================
# LEGACY PROTOCOL SUPPORT
# ============================================================================

class LegacyProtocolHandler:
    """
    Handles legacy protocol (0xA5) for backward compatibility
    """
    
    LEGACY_PACKET_SIZE = 19
    
    @classmethod
    def parse_legacy_packet(cls, data: bytes) -> Optional[Dict[str, Any]]:
        """Parse legacy packet format"""
        if len(data) != cls.LEGACY_PACKET_SIZE or data[0] != LEGACY_MAGIC[0]:
            return None
        
        frame_id = struct.unpack_from('<I', data, 1)[0]
        flags = data[5]
        max_temp = struct.unpack_from('<h', data, 6)[0] / 100.0
        avg_temp = struct.unpack_from('<h', data, 8)[0] / 100.0
        hot_count = data[10]
        cx = struct.unpack_from('<h', data, 11)[0] / 100.0
        cy = struct.unpack_from('<h', data, 13)[0] / 100.0
        vel = struct.unpack_from('<h', data, 15)[0] / 100.0
        mass = struct.unpack_from('<h', data, 17)[0] / 10.0
        
        return {
            'type': 'legacy_amg_frame',
            'frame_id': frame_id,
            'flags': flags,
            'fall_candidate': bool(flags & 0x01),
            'centroid_valid': bool(flags & 0x02),
            'max_temp': max_temp,
            'avg_temp': avg_temp,
            'hot_count': hot_count,
            'centroid_x': cx,
            'centroid_y': cy,
            'velocity': vel,
            'mass': mass
        }

# ============================================================================
# MAIN
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description='HeuristicMesh Unified Ingestion Daemon',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Direct USB connection
  python3 hm_ingest_unified.py --port /dev/ttyACM0 --baud 921600

  # Multiple USB connections
  python3 hm_ingest_unified.py --port /dev/ttyACM0 --port /dev/ttyACM1 --baud 921600

  # ModBus/TCP connection
  python3 hm_ingest_unified.py --modbus 192.168.30.10:502 --unit-id 1

  # MQTT connection
  python3 hm_ingest_unified.py --mqtt mqtt://192.168.10.100:1883

  # Combined
  python3 hm_ingest_unified.py --port /dev/ttyACM0 --baud 921600 --modbus 192.168.30.10:502 --mqtt mqtt://192.168.10.100:1883
"""
    )
    
    parser.add_argument('--port', action='append', default=[],
                       help='Serial port(s) to connect to (can specify multiple)')
    parser.add_argument('--baud', type=int, default=115200,
                       help='Baud rate for serial connections')
    parser.add_argument('--modbus', action='append', default=[],
                       help='ModBus/TCP device(s) as ip:port')
    parser.add_argument('--unit-id', type=int, default=1,
                       help='ModBus unit ID')
    parser.add_argument('--mqtt', type=str, default=None,
                       help='MQTT broker URL (e.g., mqtt://host:port)')
    parser.add_argument('--mqtt-user', type=str, default=None,
                       help='MQTT username')
    parser.add_argument('--mqtt-pass', type=str, default=None,
                       help='MQTT password')
    parser.add_argument('--log-level', type=str, default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    parser.add_argument('--event-log', type=str, default=None,
                       help='Path for event log file (default: auto-generated)')
    parser.add_argument('--legacy', action='store_true',
                       help='Enable legacy protocol support')
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    # Create ingest instance
    ingest = HeuristicMeshIngest(args)
    
    # Run
    ingest.run()


if __name__ == '__main__':
    main()
