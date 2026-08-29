#!/usr/bin/env python3
"""
HeuristicMesh Dataset Generation Script

Converts raw session data into structured training/validation/test datasets:
- Extracts features from thermal frames
- Applies ground truth labels from body cam sync
- Splits into training/validation/test sets
- Saves in standardized format

Usage:
    python3 generate_dataset.py --session-dir heuristicmesh-data/sessions/2026-08-29_001/ \
        --output-dir heuristicmesh-data/datasets/ \
        --train-ratio 0.7 --val-ratio 0.15 --test-ratio 0.15

Author: HeuristicMesh Engineering Team
Version: 1.0
Date: 2026-08-29
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

# Feature definitions
AMG_FEATURES = [
    'centroid_x', 'centroid_y', 'velocity', 'acceleration',
    'thermal_mass', 'hot_pixel_count', 'max_temp', 'avg_temp', 'min_temp'
]

MLX_FEATURES = [
    'centroid_x', 'centroid_y', 'bounding_box_area', 'aspect_ratio',
    'hot_pixel_count', 'max_temp', 'avg_temp', 'min_temp'
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
    sensor: str  # 'AMG8833' or 'MLX90640'
    features: Dict[str, float]
    label: Optional[str] = None
    confidence: Optional[float] = None
    scenario_id: Optional[str] = None
    trial: Optional[int] = None
    burst_id: Optional[int] = None
    burst_index: Optional[int] = None
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
    """
    
    def __init__(self, session_dir: Path, output_dir: Path, 
                 train_ratio: float = 0.7, val_ratio: float = 0.15, 
                 test_ratio: float = 0.15, random_seed: int = 42):
        self.session_dir = session_dir
        self.output_dir = output_dir
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.random_seed = random_seed
        
        # Validate ratios
        total = train_ratio + val_ratio + test_ratio
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Ratios must sum to 1.0, got {total}")
        
        # Setup output directories
        self.setup_output()
        
        # Data storage
        self.all_frames: List[ThermalFrame] = []
        self.labels: Dict[str, Any] = {}
        self.scenario_map: Dict[str, List[ThermalFrame]] = defaultdict(list)
    
    def setup_output(self) -> None:
        """Create output directory structure"""
        self.dataset_dir = self.output_dir / "datasets"
        
        # Create splits
        (self.dataset_dir / "training").mkdir(parents=True, exist_ok=True)
        (self.dataset_dir / "validation").mkdir(parents=True, exist_ok=True)
        (self.dataset_dir / "test").mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for each split
        for split in ["training", "validation", "test"]:
            split_dir = self.dataset_dir / split
            (split_dir / "thermal").mkdir(exist_ok=True)
            (split_dir / "features").mkdir(exist_ok=True)
            (split_dir / "labels").mkdir(exist_ok=True)
        
        logger.info(f"Output directory created: {self.dataset_dir}")
    
    def load_session_data(self) -> None:
        """Load all data from session directory"""
        logger.info(f"Loading session data from: {self.session_dir}")
        
        # Load thermal frames
        self.load_thermal_frames()
        
        # Load labels
        self.load_labels()
        
        # Load metadata
        self.load_metadata()
        
        logger.info(f"Loaded {len(self.all_frames)} frames and {len(self.labels)} labels")
    
    def load_thermal_frames(self) -> None:
        """Load thermal frames from session directory"""
        # Look for AMG frames
        for amg_dir in (self.session_dir / "esp32_*").glob("amg_frames"):
            device_id = amg_dir.parent.name
            logger.info(f"Loading AMG frames from: {amg_dir}")
            
            for frame_file in sorted(amg_dir.glob("*.json")):
                try:
                    with open(frame_file, 'r') as f:
                        data = json.load(f)
                    
                    frame = self.parse_amg_frame(data, device_id)
                    if frame:
                        self.all_frames.append(frame)
                        if frame.scenario_id:
                            self.scenario_map[frame.scenario_id].append(frame)
                except Exception as e:
                    logger.warning(f"Error loading {frame_file}: {e}")
        
        # Look for MLX frames
        for mlx_dir in (self.session_dir / "esp32_*").glob("mlx_frames"):
            device_id = mlx_dir.parent.name
            logger.info(f"Loading MLX frames from: {mlx_dir}")
            
            for frame_file in sorted(mlx_dir.glob("*.json")):
                try:
                    with open(frame_file, 'r') as f:
                        data = json.load(f)
                    
                    frame = self.parse_mlx_frame(data, device_id)
                    if frame:
                        self.all_frames.append(frame)
                        if frame.scenario_id:
                            self.scenario_map[frame.scenario_id].append(frame)
                except Exception as e:
                    logger.warning(f"Error loading {frame_file}: {e}")
        
        # Also check Jetson output for processed frames
        jetson_dir = self.session_dir / "jetson"
        if jetson_dir.exists():
            self.load_jetson_data(jetson_dir)
    
    def parse_amg_frame(self, data: Dict[str, Any], device_id: str) -> Optional[ThermalFrame]:
        """Parse AMG8833 frame data"""
        try:
            features = {
                'centroid_x': float(data.get('centroid', {}).get('x', 0)),
                'centroid_y': float(data.get('centroid', {}).get('y', 0)),
                'velocity': float(data.get('velocity', 0)),
                'acceleration': float(data.get('acceleration', 0)),
                'thermal_mass': float(data.get('mass', 0)),
                'hot_pixel_count': int(data.get('hot_pixel_count', 0)),
                'max_temp': float(data.get('max_temp', 0)),
                'avg_temp': float(data.get('avg_temp', 0)),
                'min_temp': float(data.get('min_temp', 0))
            }
            
            frame = ThermalFrame(
                frame_id=int(data.get('frame_id', 0)),
                timestamp_us=int(data.get('timestamp_us', 0)),
                device_id=device_id,
                sensor='AMG8833',
                features=features,
                raw_data=data
            )
            
            # Try to extract scenario info from metadata
            metadata = data.get('metadata', {})
            if 'scenario_id' in metadata:
                frame.scenario_id = metadata['scenario_id']
            if 'trial' in metadata:
                frame.trial = metadata['trial']
            
            return frame
        except Exception as e:
            logger.warning(f"Error parsing AMG frame: {e}")
            return None
    
    def parse_mlx_frame(self, data: Dict[str, Any], device_id: str) -> Optional[ThermalFrame]:
        """Parse MLX90640 frame data"""
        try:
            # Extract spatial features if available
            features = {
                'centroid_x': float(data.get('features', {}).get('centroid_x', 0)),
                'centroid_y': float(data.get('features', {}).get('centroid_y', 0)),
                'bounding_box_area': float(data.get('features', {}).get('bounding_box_area', 0)),
                'aspect_ratio': float(data.get('features', {}).get('aspect_ratio', 0)),
                'hot_pixel_count': int(data.get('features', {}).get('hot_pixel_count', 0)),
                'max_temp': float(data.get('max_temp', 0)),
                'avg_temp': float(data.get('avg_temp', 0)),
                'min_temp': float(data.get('min_temp', 0))
            }
            
            frame = ThermalFrame(
                frame_id=int(data.get('frame_id', 0)),
                timestamp_us=int(data.get('timestamp_us', 0)),
                device_id=device_id,
                sensor='MLX90640',
                features=features,
                burst_id=data.get('burst_id'),
                burst_index=data.get('burst_index'),
                raw_data=data
            )
            
            # Try to extract scenario info
            if 'scenario_id' in data:
                frame.scenario_id = data['scenario_id']
            if 'trial' in data:
                frame.trial = data['trial']
            
            return frame
        except Exception as e:
            logger.warning(f"Error parsing MLX frame: {e}")
            return None
    
    def load_jetson_data(self, jetson_dir: Path) -> None:
        """Load processed data from Jetson"""
        # Load Framework 2 events
        fw2_file = jetson_dir / "fw2_events.jsonl"
        if fw2_file.exists():
            logger.info(f"Loading Framework 2 events from: {fw2_file}")
            with open(fw2_file, 'r') as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        # Link event to frames
                        self.link_event_to_frames(event)
                    except Exception as e:
                        logger.warning(f"Error parsing FW2 event: {e}")
        
        # Load Framework 3 classifications
        fw3_file = jetson_dir / "fw3_classifications.jsonl"
        if fw3_file.exists():
            logger.info(f"Loading Framework 3 classifications from: {fw3_file}")
            with open(fw3_file, 'r') as f:
                for line in f:
                    try:
                        classification = json.loads(line)
                        # Apply classification to frames
                        self.apply_classification(classification)
                    except Exception as e:
                        logger.warning(f"Error parsing FW3 classification: {e}")
    
    def link_event_to_frames(self, event: Dict[str, Any]) -> None:
        """Link FW2 event to corresponding frames"""
        # Find frames around the event timestamp
        event_ts = event.get('ts_us', 0)
        
        for frame in self.all_frames:
            if abs(frame.timestamp_us - event_ts) < 100000:  # Within 100ms
                frame.scenario_id = event.get('scenario_id')
                frame.trial = event.get('trial')
                if 'confidence' in event:
                    frame.confidence = event['confidence']
    
    def apply_classification(self, classification: Dict[str, Any]) -> None:
        """Apply FW3 classification to frames"""
        # This would link classifications to specific frames
        # Implementation depends on classification format
        pass
    
    def load_labels(self) -> None:
        """Load ground truth labels from body cam sync"""
        labels_file = self.session_dir / "labels.csv"
        
        if labels_file.exists():
            logger.info(f"Loading labels from: {labels_file}")
            with open(labels_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    frame_id = int(row.get('frame_id', 0))
                    self.labels[frame_id] = {
                        'label': row.get('label', 'UNKNOWN'),
                        'confidence': float(row.get('confidence', 0)),
                        'scenario_id': row.get('scenario_id'),
                        'trial': int(row.get('trial', 0)) if row.get('trial') else None,
                        'annotator': row.get('annotator', 'bodycam_sync'),
                        'timestamp_annotation': row.get('timestamp_annotation')
                    }
        else:
            logger.warning(f"Labels file not found: {labels_file}")
    
    def load_metadata(self) -> None:
        """Load session metadata"""
        metadata_file = self.session_dir / "metadata" / "session_metadata.json"
        
        if metadata_file.exists():
            logger.info(f"Loading metadata from: {metadata_file}")
            with open(metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}
    
    def apply_labels(self) -> None:
        """Apply ground truth labels to frames"""
        logger.info("Applying ground truth labels...")
        
        labeled_count = 0
        for frame in self.all_frames:
            if frame.frame_id in self.labels:
                label_data = self.labels[frame.frame_id]
                frame.label = label_data['label']
                frame.confidence = label_data.get('confidence')
                frame.scenario_id = label_data.get('scenario_id')
                frame.trial = label_data.get('trial')
                labeled_count += 1
        
        logger.info(f"Applied labels to {labeled_count}/{len(self.all_frames)} frames")
    
    def extract_additional_features(self) -> None:
        """Extract additional features from raw data"""
        logger.info("Extracting additional features...")
        
        for frame in self.all_frames:
            if frame.raw_data and 'pixels' in frame.raw_data:
                pixels = frame.raw_data['pixels']
                
                if frame.sensor == 'AMG8833':
                    # Compute additional statistics for AMG
                    frame.features['temp_std'] = float(np.std(pixels))
                    frame.features['temp_range'] = float(np.max(pixels) - np.min(pixels))
                    
                elif frame.sensor == 'MLX90640':
                    # Compute additional statistics for MLX
                    frame.features['temp_std'] = float(np.std(pixels))
                    frame.features['temp_range'] = float(np.max(pixels) - np.min(pixels))
                    frame.features['temp_median'] = float(np.median(pixels))
    
    def split_dataset(self) -> Tuple[DatasetSplit, DatasetSplit, DatasetSplit]:
        """
        Split dataset into training/validation/test sets
        Stratified by scenario to maintain distribution
        """
        logger.info("Splitting dataset...")
        
        # Group frames by scenario
        scenario_groups = defaultdict(list)
        for frame in self.all_frames:
            if frame.scenario_id:
                scenario_groups[frame.scenario_id].append(frame)
            else:
                # Frames without scenario go to training
                scenario_groups['UNKNOWN'].append(frame)
        
        # Split each scenario group
        train_split = DatasetSplit('training')
        val_split = DatasetSplit('validation')
        test_split = DatasetSplit('test')
        
        # Set random seed for reproducibility
        random.seed(self.random_seed)
        np.random.seed(self.random_seed)
        
        for scenario_id, frames in scenario_groups.items():
            # Shuffle frames within scenario
            random.shuffle(frames)
            
            # Calculate split sizes
            n = len(frames)
            n_train = int(n * self.train_ratio)
            n_val = int(n * self.val_ratio)
            n_test = n - n_train - n_val
            
            # Split
            train_split.frames.extend(frames[:n_train])
            val_split.frames.extend(frames[n_train:n_train + n_val])
            test_split.frames.extend(frames[n_train + n_val:])
        
        # Shuffle each split
        random.shuffle(train_split.frames)
        random.shuffle(val_split.frames)
        random.shuffle(test_split.frames)
        
        logger.info(f"Split complete:")
        logger.info(f"  Training: {len(train_split.frames)} frames")
        logger.info(f"  Validation: {len(val_split.frames)} frames")
        logger.info(f"  Test: {len(test_split.frames)} frames")
        
        return train_split, val_split, test_split
    
    def save_split(self, split: DatasetSplit) -> None:
        """Save a dataset split to disk"""
        split_dir = self.dataset_dir / split.name
        logger.info(f"Saving {split.name} split to: {split_dir}")
        
        # Save thermal frames
        thermal_dir = split_dir / "thermal"
        for i, frame in enumerate(split.frames):
            frame_file = thermal_dir / f"{i:06d}.json"
            frame_dict = asdict(frame)
            # Remove raw_data to save space
            frame_dict.pop('raw_data', None)
            
            with open(frame_file, 'w') as f:
                json.dump(frame_dict, f, indent=2)
        
        # Save features as CSV
        features_file = split_dir / "features" / "features.csv"
        self.save_features_csv(split.frames, features_file)
        
        # Save labels as CSV
        labels_file = split_dir / "labels" / "labels.csv"
        self.save_labels_csv(split.frames, labels_file)
        
        # Save metadata
        metadata = {
            'split': split.name,
            'frame_count': len(split.frames),
            'generated': datetime.now().isoformat(),
            'scenario_distribution': self.get_scenario_distribution(split.frames)
        }
        metadata_file = split_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def save_features_csv(self, frames: List[ThermalFrame], path: Path) -> None:
        """Save features to CSV file"""
        if not frames:
            return
        
        # Determine feature columns based on sensor type
        feature_columns = set()
        for frame in frames:
            feature_columns.update(frame.features.keys())
        feature_columns = sorted(feature_columns)
        
        # Write CSV
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            header = ['frame_id', 'timestamp_us', 'device_id', 'sensor', 'label', 'scenario_id', 'trial']
            header.extend(feature_columns)
            writer.writerow(header)
            
            # Data rows
            for frame in frames:
                row = [
                    frame.frame_id,
                    frame.timestamp_us,
                    frame.device_id,
                    frame.sensor,
                    frame.label or '',
                    frame.scenario_id or '',
                    frame.trial if frame.trial is not None else ''
                ]
                row.extend(frame.features.get(col, '') for col in feature_columns)
                writer.writerow(row)
        
        logger.info(f"Saved features to: {path}")
    
    def save_labels_csv(self, frames: List[ThermalFrame], path: Path) -> None:
        """Save labels to CSV file"""
        if not frames:
            return
        
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(['frame_id', 'label', 'confidence', 'scenario_id', 'trial'])
            
            # Data rows
            for frame in frames:
                writer.writerow([
                    frame.frame_id,
                    frame.label or '',
                    frame.confidence if frame.confidence is not None else '',
                    frame.scenario_id or '',
                    frame.trial if frame.trial is not None else ''
                ])
        
        logger.info(f"Saved labels to: {path}")
    
    def get_scenario_distribution(self, frames: List[ThermalFrame]) -> Dict[str, int]:
        """Get distribution of scenarios in frames"""
        distribution = defaultdict(int)
        for frame in frames:
            scenario = frame.scenario_id or 'UNKNOWN'
            distribution[scenario] += 1
        return dict(distribution)
    
    def generate(self) -> None:
        """Generate complete dataset"""
        logger.info(f"\n{'#'*60}")
        logger.info(f"# Generating Dataset from: {self.session_dir.name}")
        logger.info(f"{'#'*60}\n")
        
        # Load data
        self.load_session_data()
        
        # Apply labels
        self.apply_labels()
        
        # Extract additional features
        self.extract_additional_features()
        
        # Split dataset
        train_split, val_split, test_split = self.split_dataset()
        
        # Save splits
        self.save_split(train_split)
        self.save_split(val_split)
        self.save_split(test_split)
        
        # Save dataset metadata
        self.save_dataset_metadata(train_split, val_split, test_split)
        
        logger.info(f"\nDataset generation complete!")
        logger.info(f"Output directory: {self.dataset_dir}")
    
    def save_dataset_metadata(self, train: DatasetSplit, val: DatasetSplit, test: DatasetSplit) -> None:
        """Save overall dataset metadata"""
        metadata = {
            'session_id': self.session_dir.name,
            'generated': datetime.now().isoformat(),
            'splits': {
                'training': {
                    'frame_count': len(train.frames),
                    'scenarios': self.get_scenario_distribution(train.frames)
                },
                'validation': {
                    'frame_count': len(val.frames),
                    'scenarios': self.get_scenario_distribution(val.frames)
                },
                'test': {
                    'frame_count': len(test.frames),
                    'scenarios': self.get_scenario_distribution(test.frames)
                }
            },
            'total_frames': len(self.all_frames),
            'labeled_frames': sum(1 for f in self.all_frames if f.label),
            'label_distribution': self.get_label_distribution(),
            'feature_statistics': self.compute_feature_statistics()
        }
        
        metadata_file = self.dataset_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Saved dataset metadata to: {metadata_file}")
    
    def get_label_distribution(self) -> Dict[str, int]:
        """Get distribution of labels"""
        distribution = defaultdict(int)
        for frame in self.all_frames:
            label = frame.label or 'UNLABELED'
            distribution[label] += 1
        return dict(distribution)
    
    def compute_feature_statistics(self) -> Dict[str, Dict[str, float]]:
        """Compute statistics for each feature"""
        statistics = {}
        
        # Collect all feature values
        feature_values = defaultdict(list)
        for frame in self.all_frames:
            for feature, value in frame.features.items():
                feature_values[feature].append(value)
        
        # Compute statistics
        for feature, values in feature_values.items():
            if values:
                statistics[feature] = {
                    'mean': float(np.mean(values)),
                    'median': float(np.median(values)),
                    'std': float(np.std(values)),
                    'min': float(np.min(values)),
                    'max': float(np.max(values)),
                    'count': len(values)
                }
        
        return statistics

# ============================================================================
# MAIN
# ============================================================================

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('generate_dataset.log')
    ]
)
logger = logging.getLogger('generate_dataset')


def parse_args():
    parser = argparse.ArgumentParser(
        description='HeuristicMesh Dataset Generation Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate dataset from session
  python3 generate_dataset.py --session-dir heuristicmesh-data/sessions/2026-08-29_001/

  # With custom split ratios
  python3 generate_dataset.py --session-dir heuristicmesh-data/sessions/2026-08-29_001/ \
      --train-ratio 0.7 --val-ratio 0.15 --test-ratio 0.15

  # With custom output directory
  python3 generate_dataset.py --session-dir heuristicmesh-data/sessions/2026-08-29_001/ \
      --output-dir /custom/output/
"""
    )
    
    parser.add_argument('--session-dir', type=Path, required=True,
                       help='Path to session directory')
    parser.add_argument('--output-dir', type=Path, default=Path('heuristicmesh-data'),
                       help='Output directory for datasets')
    parser.add_argument('--train-ratio', type=float, default=0.7,
                       help='Training set ratio')
    parser.add_argument('--val-ratio', type=float, default=0.15,
                       help='Validation set ratio')
    parser.add_argument('--test-ratio', type=float, default=0.15,
                       help='Test set ratio')
    parser.add_argument('--random-seed', type=int, default=42,
                       help='Random seed for reproducibility')
    parser.add_argument('--log-level', type=str, default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    # Create generator
    generator = DatasetGenerator(
        session_dir=args.session_dir,
        output_dir=args.output_dir,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        random_seed=args.random_seed
    )
    
    # Generate dataset
    generator.generate()


if __name__ == '__main__':
    main()
