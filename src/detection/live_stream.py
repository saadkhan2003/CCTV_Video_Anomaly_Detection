"""
Live Stream Module for Real-time Anomaly Detection
===================================================
Supports: Webcam, USB cameras, iPhone (via apps), IP cameras (RTSP)
"""

import cv2
import numpy as np
import time
import threading
from typing import Optional, Dict, Any, Generator, Callable
from collections import deque
import logging

logger = logging.getLogger(__name__)


class LiveStreamDetector:
    """
    Real-time video stream processing with YOLO detection
    
    Supports:
    - Local webcam: source=0, 1, 2...
    - RTSP stream: source="rtsp://..."
    - HTTP stream: source="http://..."
    """
    
    def __init__(
        self,
        source: any = 0,
        crowd_threshold: int = 3,
        confidence: float = 0.5
    ):
        """
        Initialize live stream detector
        
        Args:
            source: Camera index (0, 1, 2) or RTSP/HTTP URL
            crowd_threshold: People count to trigger alert
            confidence: Detection confidence threshold
        """
        self.source = source
        self.crowd_threshold = crowd_threshold
        self.confidence = confidence
        
        self.cap = None
        self.detector = None
        self.is_running = False
        self.current_frame = None
        self.current_results = {}
        self.alert_callback: Optional[Callable] = None
        
        # Alert cooldown (don't spam alerts)
        self.last_alert_time = 0
        self.alert_cooldown = 30  # seconds
        
        # FPS tracking
        self.fps_buffer = deque(maxlen=30)
        self.last_frame_time = time.time()
        
    def start(self) -> bool:
        """Start the video stream"""
        try:
            # Open video source with timeout settings
            if isinstance(self.source, int):
                self.cap = cv2.VideoCapture(self.source)
            else:
                # For network streams, set timeout
                import os
                os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;5000000"  # 5 second timeout
                self.cap = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)
                # Set buffer size for faster response
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            if not self.cap.isOpened():
                logger.error(f"Cannot open source: {self.source}")
                return False
            
            # Test if we can read a frame (with quick timeout)
            self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)  # 5 sec open timeout
            self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)  # 5 sec read timeout
            
            # Load YOLO detector
            from detection.yolo_detector import YOLOAnomalyDetector
            self.detector = YOLOAnomalyDetector(
                model_size="n",
                crowd_threshold=self.crowd_threshold,
                confidence_threshold=self.confidence
            )
            
            self.is_running = True
            logger.info(f"Stream started: {self.source}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting stream: {e}")
            return False
    
    def stop(self):
        """Stop the video stream"""
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        logger.info("Stream stopped")
    
    def get_frame(self) -> Optional[tuple]:
        """
        Get the next processed frame
        
        Returns:
            Tuple of (jpeg_bytes, results_dict) or None if no frame
        """
        if not self.cap or not self.is_running:
            return None
        
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        # Calculate FPS
        current_time = time.time()
        fps = 1.0 / (current_time - self.last_frame_time)
        self.fps_buffer.append(fps)
        self.last_frame_time = current_time
        avg_fps = sum(self.fps_buffer) / len(self.fps_buffer)
        
        # Process with YOLO
        if self.detector:
            annotated_frame, results = self.detector.process_frame(frame)
            results["fps"] = round(avg_fps, 1)
            
            # Check for alert
            if results.get("is_anomaly") and self.alert_callback:
                if current_time - self.last_alert_time > self.alert_cooldown:
                    self.alert_callback(results)
                    self.last_alert_time = current_time
            
            self.current_results = results
            frame = annotated_frame
        
        # Add FPS overlay
        cv2.putText(frame, f"FPS: {avg_fps:.1f}", (10, frame.shape[0] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Encode to JPEG
        _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        
        return jpeg.tobytes(), self.current_results
    
    def generate_frames(self) -> Generator[bytes, None, None]:
        """
        Generator for streaming frames (MJPEG format)
        
        Yields:
            MJPEG frame bytes
        """
        while self.is_running:
            result = self.get_frame()
            if result is None:
                time.sleep(0.1)
                continue
            
            frame_bytes, _ = result
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    def get_status(self) -> Dict[str, Any]:
        """Get current stream status"""
        return {
            "is_running": self.is_running,
            "source": str(self.source),
            "fps": round(sum(self.fps_buffer) / max(len(self.fps_buffer), 1), 1),
            "is_anomaly": self.current_results.get("is_anomaly", False),
            "person_count": self.current_results.get("person_count", 0),
            "vehicle_count": self.current_results.get("vehicle_count", 0),
            "anomaly_types": self.current_results.get("anomaly_types", [])
        }


# Global stream instances
_streams: Dict[str, LiveStreamDetector] = {}


def get_stream(stream_id: str) -> Optional[LiveStreamDetector]:
    """Get stream by ID"""
    return _streams.get(stream_id)


def create_stream(
    stream_id: str,
    source: any,
    crowd_threshold: int = 3,
    confidence: float = 0.5
) -> LiveStreamDetector:
    """Create and start a new stream"""
    # Stop existing stream if any
    if stream_id in _streams:
        _streams[stream_id].stop()
    
    stream = LiveStreamDetector(
        source=source,
        crowd_threshold=crowd_threshold,
        confidence=confidence
    )
    
    _streams[stream_id] = stream
    return stream


def stop_stream(stream_id: str) -> bool:
    """Stop and remove a stream"""
    if stream_id in _streams:
        _streams[stream_id].stop()
        del _streams[stream_id]
        return True
    return False


def list_streams() -> Dict[str, Dict]:
    """List all active streams"""
    return {
        stream_id: stream.get_status()
        for stream_id, stream in _streams.items()
    }


def detect_cameras() -> list:
    """Detect available cameras"""
    available = []
    
    # Check USB cameras (0-9)
    for i in range(10):
        try:
            cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
            if cap.isOpened():
                # Try to read a frame to confirm it works
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                ret, _ = cap.read()
                if ret:
                    available.append({
                        "index": i,
                        "name": f"Camera {i}",
                        "type": "usb"
                    })
                cap.release()
        except:
            pass
    
    return available
