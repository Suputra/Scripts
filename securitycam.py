#!/usr/bin/env python3
import cv2
import os
import time
from datetime import datetime
from pathlib import Path
import logging
import signal
import sys
import json
from typing import Dict, List
import threading
import numpy as np

class VideoWriter:
    def __init__(self, filename: str, fps: int, frame_size: tuple):
        """Wrapper for cv2.VideoWriter with proper codec selection"""
        # On macOS, try to use mp4v codec first, fallback to MJPG if needed
        self.writer = cv2.VideoWriter(
            filename,
            cv2.VideoWriter_fourcc(*'mp4v'),
            fps,
            frame_size
        )
        
        # Test if the writer was initialized successfully
        if not self.writer.isOpened():
            self.writer = cv2.VideoWriter(
                filename,
                cv2.VideoWriter_fourcc(*'MJPG'),
                fps,
                frame_size
            )
    
    def write(self, frame):
        self.writer.write(frame)
    
    def release(self):
        self.writer.release()

class CameraProcess:
    def __init__(self, camera_id: str, device_id: int, storage_dir: Path, 
                 max_storage_gb: int, chunk_duration_mins: int = 60):
        self.camera_id = camera_id
        self.device_id = device_id
        self.storage_dir = storage_dir / camera_id
        self.max_storage_bytes = max_storage_gb * 1024 * 1024 * 1024
        self.chunk_duration_mins = chunk_duration_mins
        self.cap = None
        self.writer = None
        self.current_file = None
        self.chunk_start_time = None
        self.running = False
        
        # Create camera-specific directory
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def cleanup_old_files(self):
        """Delete oldest files when storage limit is exceeded"""
        try:
            video_files = sorted(
                [f for f in self.storage_dir.glob("*.mp4")],
                key=lambda x: x.stat().st_mtime
            )
            
            total_size = sum(f.stat().st_size for f in video_files)
            
            while total_size > self.max_storage_bytes and video_files:
                oldest_file = video_files.pop(0)
                total_size -= oldest_file.stat().st_size
                logging.info(f"Camera {self.camera_id}: Removing old file: {oldest_file}")
                oldest_file.unlink()
                
        except Exception as e:
            logging.error(f"Camera {self.camera_id}: Error during cleanup: {e}")
    
    def start_new_chunk(self):
        """Start a new video chunk"""
        if self.writer:
            self.writer.release()
        
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.current_file = self.storage_dir / f"{timestamp}.mp4"
        
        # Get frame size from capture device
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        
        self.writer = VideoWriter(str(self.current_file), fps, (width, height))
        self.chunk_start_time = time.time()
    
    def record(self):
        """Main recording loop for a single camera"""
        try:
            self.cap = cv2.VideoCapture(self.device_id)
            if not self.cap.isOpened():
                raise Exception(f"Failed to open camera {self.device_id}")
            
            self.start_new_chunk()
            
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    raise Exception("Failed to read frame")
                
                self.writer.write(frame)
                
                # Check if it's time for a new chunk
                if time.time() - self.chunk_start_time > (self.chunk_duration_mins * 60):
                    self.start_new_chunk()
                    self.cleanup_old_files()
                
        except Exception as e:
            logging.error(f"Camera {self.camera_id}: Recording error: {e}")
        finally:
            if self.writer:
                self.writer.release()
            if self.cap:
                self.cap.release()
    
    def stop(self):
        """Stop recording"""
        self.running = False

class MultiCameraSystem:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.cameras: Dict[str, CameraProcess] = {}
        self.running = False
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("security-cam.log"),
                logging.StreamHandler()
            ]
        )
        
        self.load_config()
    
    def load_config(self):
        """Load camera configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
            base_dir = Path(config.get('base_storage_dir', 
                Path.home() / "Library/Application Support/SecurityCam"))
            
            for cam_config in config['cameras']:
                camera_id = cam_config['id']
                self.cameras[camera_id] = CameraProcess(
                    camera_id=camera_id,
                    device_id=cam_config['device_id'],
                    storage_dir=base_dir,
                    max_storage_gb=cam_config.get('max_storage_gb', 50),
                    chunk_duration_mins=cam_config.get('chunk_duration_mins', 60)
                )
                
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            sys.exit(1)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logging.info("Received shutdown signal")
        self.running = False
        for camera in self.cameras.values():
            camera.stop()
        sys.exit(0)
    
    def run(self):
        """Main loop for the multi-camera system"""
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        self.running = True
        threads = []
        
        # Start recording threads for each camera
        for camera in self.cameras.values():
            camera.running = True
            thread = threading.Thread(target=camera.record)
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Wait for all threads
        while self.running:
            time.sleep(1)
        
        for thread in threads:
            thread.join()

def list_available_cameras():
    """Utility function to list available camera devices"""
    available_cameras = []
    index = 0
    while True:
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            break
        ret, _ = cap.read()
        if ret:
            available_cameras.append(index)
        cap.release()
        index += 1
    return available_cameras

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Camera Security System")
    parser.add_argument("--config", default="~/security-cam-config.json",
                      help="Path to camera configuration file")
    parser.add_argument("--list-cameras", action="store_true",
                      help="List available camera devices and exit")
    
    args = parser.parse_args()
    
    if args.list_cameras:
        cameras = list_available_cameras()
        print("Available cameras:")
        for idx in cameras:
            print(f"Camera ID: {idx}")
        sys.exit(0)
    
    system = MultiCameraSystem(os.path.expanduser(args.config))
    system.run()