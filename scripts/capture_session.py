#!/usr/bin/env python3
"""
HeuristicMesh Session Capture Script

Automates the data capture workflow for baseline collection:
- Starts ESP32 logging
- Starts Jetson ingest
- Manages session metadata
- Coordinates body camera start/stop
- Logs all events with timestamps

Usage:
    python3 capture_session.py --session-id 2026-08-29_001 --config config/session_config.yaml

Author: HeuristicMesh Engineering Team
Version: 1.0
Date: 2026-08-29
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml

# ============================================================================
# CONFIGURATION
# ============================================================================

# Default paths
DEFAULT_CONFIG = Path(__file__).parent.parent / "config" / "session_config.yaml"
DEFAULT_SESSIONS = Path(__file__).parent.parent / "heuristicmesh-data" / "sessions"
DEFAULT_SCRIPTS = Path(__file__).parent

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('capture_session.log')
    ]
)
logger = logging.getLogger('capture_session')

# ============================================================================
# SESSION MANAGER
# ============================================================================

class SessionManager:
    """
    Manages a complete data capture session
    """
    
    def __init__(self, session_id: str, config_path: Path, output_dir: Path):
        self.session_id = session_id
        self.config_path = config_path
        self.output_dir = output_dir
        
        # Load configuration
        self.config = self.load_config()
        
        # Create output directory structure
        self.setup_output_directory()
        
        # Process tracking
        self.processes: Dict[str, subprocess.Popen] = {}
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
        # State
        self.is_running = False
        self.current_scenario: Optional[str] = None
        self.current_trial: int = 0
    
    def load_config(self) -> Dict[str, Any]:
        """Load session configuration from YAML file"""
        if not self.config_path.exists():
            logger.error(f"Config file not found: {self.config_path}")
            sys.exit(1)
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Set defaults
        if 'thresholds' not in config:
            config['thresholds'] = {}
        if 'bodycams' not in config:
            config['bodycams'] = {'enabled': False}
        
        return config
    
    def setup_output_directory(self) -> None:
        """Create output directory structure"""
        # Create main session directory
        self.session_dir = self.output_dir / self.session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.session_dir / "metadata").mkdir(exist_ok=True)
        (self.session_dir / "esp32_001" / "amg_frames").mkdir(parents=True, exist_ok=True)
        (self.session_dir / "esp32_002" / "amg_frames").mkdir(parents=True, exist_ok=True)
        (self.session_dir / "esp32_003" / "amg_frames").mkdir(parents=True, exist_ok=True)
        (self.session_dir / "jetson").mkdir(exist_ok=True)
        (self.session_dir / "bodycams").mkdir(exist_ok=True)
        (self.session_dir / "logs").mkdir(exist_ok=True)
        
        logger.info(f"Output directory created: {self.session_dir}")
    
    def save_metadata(self) -> None:
        """Save session metadata"""
        metadata = {
            'session_id': self.session_id,
            'start_time': datetime.now().isoformat() if self.start_time else None,
            'config': self.config,
            'system_info': self.get_system_info()
        }
        
        metadata_path = self.session_dir / "metadata" / "session_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Metadata saved to: {metadata_path}")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        import platform
        import psutil
        
        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_gb': round(psutil.virtual_memory().total / (1024**3), 2)
        }
    
    def start_services(self) -> None:
        """Start all required services"""
        logger.info("Starting services...")
        
        # Start Mosquitto (if not running)
        self.start_mosquitto()
        
        # Start Jetson ingest
        self.start_jetson_ingest()
        
        # Start ESP32 monitoring (if not using direct serial)
        # For direct serial, the Jetson ingest handles it
        
        self.is_running = True
        self.start_time = time.time()
        
        logger.info("All services started")
    
    def start_mosquitto(self) -> None:
        """Start Mosquitto MQTT broker"""
        try:
            # Check if Mosquitto is running
            result = subprocess.run(['systemctl', 'is-active', 'mosquitto'],
                                  capture_output=True, text=True)
            if result.stdout.strip() != 'active':
                logger.info("Starting Mosquitto...")
                subprocess.Popen(['sudo', 'systemctl', 'start', 'mosquitto'])
                time.sleep(2)
            else:
                logger.info("Mosquitto already running")
        except Exception as e:
            logger.warning(f"Could not start Mosquitto: {e}")
    
    def start_jetson_ingest(self) -> None:
        """Start Jetson ingest daemon"""
        jetson_script = DEFAULT_SCRIPTS / "run_jetson_ingest_unified.sh"
        
        if not jetson_script.exists():
            logger.warning(f"Jetson ingest script not found: {jetson_script}")
            return
        
        # Build command
        cmd = [str(jetson_script)]
        
        # Add ports from config
        if 'devices' in self.config:
            for device_id, device_config in self.config['devices'].items():
                if 'port' in device_config:
                    cmd.extend(['--port', device_config['port']])
                    if 'baud' in device_config:
                        cmd.extend(['--baud', str(device_config['baud'])])
        
        # Add MQTT if configured
        if self.config.get('mqtt', {}).get('enabled', False):
            mqtt_broker = self.config['mqtt'].get('broker', '192.168.10.100')
            mqtt_port = self.config['mqtt'].get('port', 1883)
            cmd.extend(['--mqtt', f'mqtt://{mqtt_broker}:{mqtt_port}'])
        
        logger.info(f"Starting Jetson ingest: {' '.join(cmd)}")
        
        # Start process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.processes['jetson_ingest'] = process
        
        # Log output in background
        def log_process_output(process, name):
            for line in process.stdout:
                logger.debug(f"[{name}] {line.strip()}")
            for line in process.stderr:
                logger.error(f"[{name}] {line.strip()}")
        
        threading.Thread(target=log_process_output, 
                        args=(process, 'jetson_ingest'),
                        daemon=True).start()
    
    def start_body_cams(self) -> None:
        """Start body cameras (placeholder - manual for now)"""
        if not self.config.get('bodycams', {}).get('enabled', False):
            logger.info("Body cameras not enabled in config")
            return
        
        logger.info("Starting body cameras...")
        logger.warning("Body camera start is manual - please start recording on all cameras")
        logger.warning("Press Enter when all body cameras are recording...")
        input()
        
        # Record start time
        bodycam_start = datetime.now()
        logger.info(f"Body cameras started at: {bodycam_start.isoformat()}")
    
    def start_scenario(self, scenario_id: str) -> None:
        """Start a new scenario"""
        self.current_scenario = scenario_id
        self.current_trial = 0
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting Scenario: {scenario_id}")
        logger.info(f"{'='*60}")
        
        # Log scenario start
        scenario_log = {
            'timestamp': datetime.now().isoformat(),
            'scenario_id': scenario_id,
            'action': 'start'
        }
        self.log_event(scenario_log)
    
    def start_trial(self, trial_num: int) -> None:
        """Start a new trial"""
        self.current_trial = trial_num
        
        logger.info(f"\n--- Trial {trial_num} ---")
        logger.info(f"Announce: 'Trial {trial_num}, Scenario {self.current_scenario}'")
        logger.info("Countdown: 'Three... two... one... execute!'")
        
        # Log trial start
        trial_log = {
            'timestamp': datetime.now().isoformat(),
            'scenario_id': self.current_scenario,
            'trial': trial_num,
            'action': 'execute'
        }
        self.log_event(trial_log)
    
    def end_trial(self, notes: str = "") -> None:
        """End current trial"""
        logger.info(f"Announce: 'Hold... recover'")
        logger.info(f"Trial {self.current_trial} complete")
        
        # Log trial end
        trial_log = {
            'timestamp': datetime.now().isoformat(),
            'scenario_id': self.current_scenario,
            'trial': self.current_trial,
            'action': 'recover',
            'notes': notes
        }
        self.log_event(trial_log)
    
    def end_scenario(self) -> None:
        """End current scenario"""
        logger.info(f"\nScenario {self.current_scenario} complete")
        logger.info(f"{'='*60}\n")
        
        # Log scenario end
        scenario_log = {
            'timestamp': datetime.now().isoformat(),
            'scenario_id': self.current_scenario,
            'action': 'end'
        }
        self.log_event(scenario_log)
        
        self.current_scenario = None
    
    def log_event(self, event: Dict[str, Any]) -> None:
        """Log event to session log"""
        log_path = self.session_dir / "logs" / "session_events.jsonl"
        
        with open(log_path, 'a') as f:
            f.write(json.dumps(event) + '\n')
        
        logger.debug(f"Event logged: {event}")
    
    def stop_services(self) -> None:
        """Stop all services"""
        logger.info("Stopping services...")
        
        # Stop all processes
        for name, process in self.processes.items():
            if process.poll() is None:  # Process is still running
                logger.info(f"Stopping {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        
        self.is_running = False
        self.end_time = time.time()
        
        # Save final metadata
        self.save_metadata()
        
        logger.info("All services stopped")
    
    def stop_body_cams(self) -> None:
        """Stop body cameras (placeholder - manual for now)"""
        if not self.config.get('bodycams', {}).get('enabled', False):
            return
        
        logger.info("\nStopping body cameras...")
        logger.warning("Body camera stop is manual - please stop recording on all cameras")
        logger.warning("Press Enter when all body cameras are stopped...")
        input()
        
        bodycam_end = datetime.now()
        logger.info(f"Body cameras stopped at: {bodycam_end.isoformat()}")
    
    def copy_body_cam_data(self) -> None:
        """Copy body cam data to session directory"""
        if not self.config.get('bodycams', {}).get('enabled', False):
            return
        
        logger.info("Copying body cam data...")
        logger.warning("Please copy body cam videos to:")
        logger.warning(f"  {self.session_dir / 'bodycams'}")
        logger.warning("Press Enter when copy is complete...")
        input()
        
        # Verify files
        bodycam_files = list((self.session_dir / "bodycams").glob("*.avi"))
        if bodycam_files:
            logger.info(f"Copied {len(bodycam_files)} body cam files")
        else:
            logger.warning("No body cam files found")
    
    def run_session(self) -> None:
        """Run complete session"""
        logger.info(f"\n{'#'*60}")
        logger.info(f"# Starting HeuristicMesh Session: {self.session_id}")
        logger.info(f"{'#'*60}\n")
        
        try:
            # Start services
            self.start_services()
            
            # Start body cameras
            self.start_body_cams()
            
            # Save initial metadata
            self.save_metadata()
            
            # Run scenarios
            self.run_scenarios()
            
            # Stop body cameras
            self.stop_body_cams()
            
            # Copy body cam data
            self.copy_body_cam_data()
            
        except KeyboardInterrupt:
            logger.info("\nSession interrupted by user")
        except Exception as e:
            logger.error(f"Session error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Stop services
            self.stop_services()
            
            # Print summary
            self.print_summary()
    
    def run_scenarios(self) -> None:
        """Run all configured scenarios"""
        # Get scenarios from config or use defaults
        scenarios = self.config.get('scenarios', [
            {'id': 'S01', 'name': 'Forward Trip', 'trials': 6, 'type': 'common'},
            {'id': 'S02', 'name': 'Sit-to-Stand Failure', 'trials': 6, 'type': 'common'},
            {'id': 'S03', 'name': 'Lateral Slip', 'trials': 6, 'type': 'common'},
            {'id': 'S06', 'name': 'Slow Syncope', 'trials': 8, 'type': 'elusive'},
            {'id': 'S07', 'name': 'Fall from Bed', 'trials': 6, 'type': 'elusive'},
            {'id': 'S08', 'name': 'Near-Fall + Collapse', 'trials': 6, 'type': 'elusive'},
            {'id': 'S10', 'name': 'Controlled Descent', 'trials': 6, 'type': 'negative'}
        ])
        
        for scenario in scenarios:
            scenario_id = scenario['id']
            trials = scenario['trials']
            
            self.start_scenario(scenario_id)
            
            for trial in range(1, trials + 1):
                self.start_trial(trial)
                
                # Wait for user to execute scenario
                logger.info(f"Execute Scenario {scenario_id}, Trial {trial}")
                logger.info("Press Enter when scenario is complete...")
                input()
                
                # Get notes from user
                notes = input("Enter notes (or press Enter): ").strip()
                self.end_trial(notes)
                
                # Brief pause between trials
                if trial < trials:
                    logger.info(f"Waiting 30 seconds before next trial...")
                    time.sleep(30)
            
            self.end_scenario()
            
            # Longer pause between scenarios
            if scenario != scenarios[-1]:
                logger.info(f"Waiting 60 seconds before next scenario...")
                time.sleep(60)
    
    def print_summary(self) -> None:
        """Print session summary"""
        duration = self.end_time - self.start_time if self.start_time and self.end_time else 0
        
        logger.info(f"\n{'#'*60}")
        logger.info(f"# Session Summary: {self.session_id}")
        logger.info(f"{'#'*60}")
        logger.info(f"Start Time: {datetime.fromtimestamp(self.start_time).isoformat() if self.start_time else 'N/A'}")
        logger.info(f"End Time: {datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else 'N/A'}")
        logger.info(f"Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        logger.info(f"Output Directory: {self.session_dir}")
        logger.info(f"{'#'*60}\n")

# ============================================================================
# MAIN
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description='HeuristicMesh Session Capture Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start a new session
  python3 capture_session.py --session-id 2026-08-29_001

  # With custom config
  python3 capture_session.py --session-id 2026-08-29_001 --config my_config.yaml

  # With custom output directory
  python3 capture_session.py --session-id 2026-08-29_001 --output /data/sessions/
"""
    )
    
    parser.add_argument('--session-id', type=str, required=True,
                       help='Unique session identifier (e.g., 2026-08-29_001)')
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG,
                       help='Path to session configuration file')
    parser.add_argument('--output', type=Path, default=DEFAULT_SESSIONS,
                       help='Output directory for session data')
    parser.add_argument('--log-level', type=str, default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    parser.add_argument('--dry-run', action='store_true',
                       help='Test configuration without running session')
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    # Create session manager
    manager = SessionManager(args.session_id, args.config, args.output)
    
    if args.dry_run:
        logger.info("Dry run mode - configuration check only")
        logger.info(f"Session ID: {args.session_id}")
        logger.info(f"Config: {args.config}")
        logger.info(f"Output: {args.output}")
        logger.info(f"Config loaded successfully: {list(manager.config.keys())}")
        return
    
    # Run session
    manager.run_session()


if __name__ == '__main__':
    import threading
    main()
