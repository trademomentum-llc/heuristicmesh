#!/usr/bin/env python3
"""
HeuristicMesh Dataset Generation Script (AMG8833 Only)

Converts raw session data into structured training/validation/test datasets:
- Extracts features from AMG8833 thermal frames
- Applies ground truth labels from body cam sync
- Splits into training/validation/test sets
- Saves in standardized format

Usage:
    python3 generate_dataset.py --session-dir heuristicmesh-data/sessions/2026-08-29_001/ \
        --output-dir heuristicmesh-data/datasets/ \
        --train-ratio 0.7 --val-ratio 0.15 --test-ratio 0.15

Author: HeuristicMesh Engineering Team
Version: 1.1
Date: 2026-08-29
Note: MLX90640 support removed - only 2x AMG8833 sensors in inventory
"""

import argparse
import csv
import json
import logging
import os
import random
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import numpy as np

# ============================================================================
# CONFIGURATION
# ============================================================================

# Feature definitions (AMG8833 only)
AMG_FEATURES = [
    'centroid_x', 'centroid_y', 'velocity', 'acceleration',
    'thermal_mass', 'hot_pixel_count', 'max_temp', 'avg_temp'
]

# Label mapping
LABEL_MAP = {
    'FALL': 0,
    'NEAR_FALL': 1,
    'SUSPICIOUS_ACTIVITY': 2,
    'NOISE': 3,
    'NEGATIVE': 3,  # Same as NOISE for now
    'CONTROLLED_DESCENT': 3
}

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ThermalFrame:
    """Represents a thermal frame with features and label"""
    frame_id: int
    timestamp_us: int
    device_id: str
    sensor: str  # 'AMG8833' only
    features: Dict[str, float]
    label: Optional[str] = None
    confidence: Optional[float] = None
    scenario_id: Optional[str] = None
    trial: Optional[int] = None
    raw_data: Optional[Dict[str, Any]] = None

@dataclass
class DatasetSplit:
    """Represents a dataset split (train/val/test)"""
    name: str
    frames: List[ThermalFrame] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'frame_count': len(self.frames),
            'features': [asdict(f) for f in self.frames]
        }

# ============================================================================
# DATASET GENERATOR
# ============================================================================

class DatasetGenerator:
    """
    Generates structured datasets from raw session data
    AMG8833 only version - no MLX90640 or burst mode support
    """
    
    def __init__(self, session_dir: Path, output_dir: Path, 
                 train_ratio: float = 0.7, val_ratio: float = 0.15, test_ratio: float = 0.15):
        self.session_dir = Path(session_dir)
        self.output_dir = Path(output_dir)
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'training').mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'validation').mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'test').mkdir(parents=True, exist_ok=True)
        
        # Logger
        self.logger = logging.getLogger('DatasetGenerator')
        self.logger.setLevel(logging.INFO)
    
    def load_session(self) -> List[ThermalFrame]:
        """Load all thermal frames from session directory"""
        frames = []
        
        # Look for AMG frames
        for amg_dir in (self.session_dir / "esp32_*").glob("amg_frames"):
            device_id = amg_dir.parent.name
            self.logger.info(f"Loading AMG frames from: {amg_dir}")
            
            for frame_file in sorted(amg_dir.glob("*.json")):
                try:
                    with open(frame_file, 'r') as f:
                        data = json.load(f)
                    
                    frame = self.parse_amg_frame(data, device_id)
                    if frame:
                        frames.append(frame)
                except Exception as e:
                    self.logger.warning(f"Error loading {frame_file}: {e}")
        
        self.logger.info(f"Loaded {len(frames)} total frames")
        return frames
    
    def parse_amg_frame(self, data: Dict[str, Any], device_id: str) -> Optional[ThermalFrame]:
        """Parse AMG8833 frame data"""
        try:
            features = {}
            
            # Extract features
            if 'metadata' in data:
                meta = data['metadata']
                features['centroid_x'] = meta.get('centroid', {}).get('x', 0)
                features['centroid_y'] = meta.get('centroid', {}).get('y', 0)
                features['velocity'] = meta.get('velocity', 0)
                features['acceleration'] = meta.get('acceleration', 0)
                features['thermal_mass'] = meta.get('mass', 0)
                features['hot_pixel_count'] = meta.get('hot_pixel_count', 0)
                features['max_temp'] = meta.get('max_temp', 0)
                features['avg_temp'] = meta.get('avg_temp', 0)
            
            return ThermalFrame(
                frame_id=data.get('frame_id', 0),
                timestamp_us=data.get('timestamp_us', 0),
                device_id=device_id,
                sensor='AMG8833',
                features=features,
                raw_data=data
            )
        except Exception as e:
            self.logger.warning(f"Error parsing AMG frame: {e}")
            return None
    
    def apply_labels(self, frames: List[ThermalFrame]) -> List[ThermalFrame]:
        """Apply ground truth labels from body cam sync data"""
        # Load label file if it exists
        label_file = self.session_dir / "labels.csv"
        if not label_file.exists():
            self.logger.warning(f"No label file found: {label_file}")
            return frames
        
        # Load labels
        labels = {}
        with open(label_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                frame_id = int(row.get('frame_id', 0))
                labels[frame_id] = {
                    'label': row.get('label', 'UNKNOWN'),
                    'confidence': float(row.get('confidence', 0.0)),
                    'scenario_id': row.get('scenario_id', ''),
                    'trial': int(row.get('trial', 0))
                }
        
        # Apply labels to frames
        labeled_frames = []
        for frame in frames:
            if frame.frame_id in labels:
                label_data = labels[frame.frame_id]
                frame.label = label_data['label']
                frame.confidence = label_data['confidence']
                frame.scenario_id = label_data['scenario_id']
                frame.trial = label_data['trial']
            labeled_frames.append(frame)
        
        self.logger.info(f"Applied labels to {len(labeled_frames)} frames")
        return labeled_frames
    
    def split_dataset(self, frames: List[ThermalFrame]) -> Tuple[DatasetSplit, DatasetSplit, DatasetSplit]:
        """Split dataset into training, validation, and test sets"""
        # Shuffle frames
        random.shuffle(frames)
        
        # Calculate split sizes
        n = len(frames)
        n_train = int(n * self.train_ratio)
        n_val = int(n * self.val_ratio)
        n_test = n - n_train - n_val
        
        # Split
        train = DatasetSplit('training', frames[:n_train])
        val = DatasetSplit('validation', frames[n_train:n_train+n_val])
        test = DatasetSplit('test', frames[n_train+n_val:])
        
        self.logger.info(f"Dataset split: train={len(train.frames)}, val={len(val.frames)}, test={len(test.frames)}")
        return train, val, test
    
    def save_split(self, split: DatasetSplit, split_dir: Path) -> None:
        """Save a dataset split to disk"""
        split_dir.mkdir(parents=True, exist_ok=True)
        
        # Save metadata
        metadata = {
            'split': split.name,
            'frame_count': len(split.frames),
            'features': AMG_FEATURES,
            'label_map': LABEL_MAP
        }
        with open(split_dir / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save frames as JSON
        frames_file = split_dir / 'frames.json'
        frames_data = [asdict(f) for f in split.frames]
        with open(frames_file, 'w') as f:
            json.dump(frames_data, f, indent=2)
        
        # Save as CSV
        csv_file = split_dir / 'frames.csv'
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['frame_id', 'timestamp_us', 'device_id', 'sensor'] + 
                                                   AMG_FEATURES + ['label', 'confidence', 'scenario_id', 'trial'])
            writer.writeheader()
            for frame in split.frames:
                row = {
                    'frame_id': frame.frame_id,
                    'timestamp_us': frame.timestamp_us,
                    'device_id': frame.device_id,
                    'sensor': frame.sensor
                }
                row.update(frame.features)
                row['label'] = frame.label or ''
                row['confidence'] = frame.confidence or 0.0
                row['scenario_id'] = frame.scenario_id or ''
                row['trial'] = frame.trial or 0
                writer.writerow(row)
        
        self.logger.info(f"Saved {split.name} split to {split_dir}")
    
    def generate(self) -> None:
        """Generate complete dataset from session"""
        self.logger.info(f"Generating dataset from: {self.session_dir}")
        
        # Load frames
        frames = self.load_session()
        
        # Apply labels
        frames = self.apply_labels(frames)
        
        # Split dataset
        train, val, test = self.split_dataset(frames)
        
        # Save splits
        self.save_split(train, self.output_dir / 'training')
        self.save_split(val, self.output_dir / 'validation')
        self.save_split(test, self.output_dir / 'test')
        
        # Save overall metadata
        overall_meta = {
            'session': self.session_dir.name,
            'total_frames': len(frames),
            'train_frames': len(train.frames),
            'val_frames': len(val.frames),
            'test_frames': len(test.frames),
            'features': AMG_FEATURES,
            'label_map': LABEL_MAP
        }
        with open(self.output_dir / 'metadata.json', 'w') as f:
            json.dump(overall_meta, f, indent=2)
        
        self.logger.info(f"Dataset generation complete: {self.output_dir}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='HeuristicMesh Dataset Generator (AMG8833 Only)')
    parser.add_argument('--session-dir', type=str, required=True,
                        help='Path to session directory')
    parser.add_argument('--output-dir', type=str, required=True,
                        help='Path to output directory')
    parser.add_argument('--train-ratio', type=float, default=0.7,
                        help='Training set ratio (default: 0.7)')
    parser.add_argument('--val-ratio', type=float, default=0.15,
                        help='Validation set ratio (default: 0.15)')
    parser.add_argument('--test-ratio', type=float, default=0.15,
                        help='Test set ratio (default: 0.15)')
    parser.add_argument('--log-level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=getattr(logging, args.log_level))
    
    # Create generator and run
    generator = DatasetGenerator(
        session_dir=Path(args.session_dir),
        output_dir=Path(args.output_dir),
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio
    )
    
    generator.generate()

if __name__ == '__main__':
    main()
