"""
YOLOv8 Object Detection with Rule-Based Anomaly Detection
=========================================================

Uses YOLOv8 for accurate object detection (people, vehicles, etc.) and
applies configurable rules to detect anomalies in CCTV footage.
"""

import cv2
import numpy as np
import imageio
from ultralytics import YOLO
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
import time
import os


class VideoWriter:
    """Cross-platform video writer using imageio"""

    def __init__(self, output_path: str, fps: float, width: int, height: int):
        self.output_path = output_path
        self.fps = fps
        self.width = width
        self.height = height
        self.writer = imageio.get_writer(
            output_path, fps=fps, codec="libx264", pixelformat="yuv420p"
        )
        self.frame_count = 0

    def write(self, frame):
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.writer.append_data(frame_rgb)
        self.frame_count += 1

    def release(self):
        self.writer.close()


class YOLOAnomalyDetector:
    """
    Object detection-based anomaly detector using YOLOv8

    Anomaly Rules:
    1. Crowd Gathering - More than N people in frame
    2. Loitering - Person in same spot for > X seconds
    3. Running - Fast movement detected
    4. Vehicle in pedestrian area
    """

    # COCO class names for YOLOv8
    PERSON_CLASS = 0
    VEHICLE_CLASSES = [2, 3, 5, 7]  # car, motorcycle, bus, truck
    WEAPON_CLASSES = [
        43,
        34,
        76,
    ]  # knife, baseball bat, scissors (often detected as sharp object)

    def __init__(
        self,
        model_size: str = "s",  # n=nano, s=small, m=medium, l=large, x=xlarge
        confidence_threshold: float = 0.5,
        crowd_threshold: int = 5,
        loiter_threshold_seconds: float = 10.0,
        device: str = "cpu",
    ):
        """
        Initialize YOLO detector

        Args:
            model_size: YOLO model size (n, s, m, l, x)
            confidence_threshold: Minimum detection confidence
            crowd_threshold: Number of people to trigger crowd alert
            loiter_threshold_seconds: Time to trigger loitering alert
            device: 'cpu' or 'cuda'
        """
        self.confidence_threshold = confidence_threshold
        self.crowd_threshold = crowd_threshold
        self.loiter_threshold = loiter_threshold_seconds
        self.device = device

        # Load YOLO model
        model_name = f"yolo11{model_size}.pt"
        print(f"Loading YOLO model: {model_name}")
        self.model = YOLO(model_name)

        # Export to OpenVINO for CPU speedup (only if not already exported)
        if device == "cpu":
            try:
                openvino_path = f"yolo11{model_size}_openvino_model/"
                if not os.path.exists(openvino_path):
                    print(
                        "🚀 Exporting model to OpenVINO for 2-3x CPU speedup... (This takes ~1 min once)"
                    )
                    self.model.export(format="openvino")
                    print("✅ Export complete!")

                # Load the exported model for inference
                print(f"Loading OpenVINO model: {openvino_path}")
                self.model = YOLO(openvino_path, task="detect")
                print("✅ OpenVINO optimized model loaded!")
            except Exception as e:
                print(f"⚠️ OpenVINO export failed (using PyTorch fallback): {e}")
                self.model = YOLO(model_name)  # Fallback
        else:
            print("✅ YOLO model loaded!")

        # Tracking for loitering and velocity
        self.person_tracks: Dict[int, List[Tuple[float, float, float]]] = defaultdict(
            list
        )
        self.object_velocities: Dict[int, float] = {}  # Store last calculated velocity
        self.frame_count = 0
        self.frame_count = 0

    def detect_objects(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Detect objects in a single frame

        Returns:
            Dictionary with detections and anomaly flags
        """
        # Run YOLO tracking (ByteTrack is built-in and fast)
        # persist=True is required for tracking to work across frames
        results = self.model.track(
            frame,
            conf=self.confidence_threshold,
            persist=True,
            verbose=False,
            tracker="bytetrack.yaml",
        )

        detections = {
            "persons": [],
            "vehicles": [],
            "weapons": [],
            "other_objects": [],
            "all_boxes": [],
        }

        if len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes

            for i, box in enumerate(boxes):
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].cpu().numpy()
                id = int(box.id[0]) if box.id is not None else -1
                x1, y1, x2, y2 = map(int, xyxy)

                detection = {
                    "class_id": cls,
                    "class_name": self.model.names[cls],
                    "confidence": conf,
                    "bbox": [x1, y1, x2, y2],
                    "center": ((x1 + x2) // 2, (y1 + y2) // 2),
                    "id": id,
                }

                detections["all_boxes"].append(detection)

                if cls == self.PERSON_CLASS:
                    detections["persons"].append(detection)
                elif cls in self.VEHICLE_CLASSES:
                    detections["vehicles"].append(detection)
                elif cls in self.WEAPON_CLASSES:
                    detections["weapons"].append(detection)
                else:
                    detections["other_objects"].append(detection)

        return detections

    def check_anomalies(
        self, detections: Dict[str, Any], fps: float = 30.0
    ) -> Dict[str, Any]:
        """
        Check for anomalies based on detection results

        Returns:
            Dictionary with anomaly information
        """
        anomalies = {
            "is_anomaly": False,
            "anomaly_types": [],
            "anomaly_details": [],
            "risk_level": "normal",  # normal, low, medium, high
        }

        person_count = len(detections["persons"])
        vehicle_count = len(detections["vehicles"])

        # Rule 1: Crowd Gathering (2+ people triggers alert)
        if person_count >= self.crowd_threshold:
            anomalies["is_anomaly"] = True
            anomalies["anomaly_types"].append("CROWD_GATHERING")
            anomalies["anomaly_details"].append(
                f"Crowd detected: {person_count} people (threshold: {self.crowd_threshold})"
            )
            anomalies["risk_level"] = (
                "high" if person_count > self.crowd_threshold * 2 else "medium"
            )

        # Rule 2: FIGHT/CONFLICT DETECTION - People in close proximity
        if person_count >= 2:
            close_pairs = self._check_proximity(
                detections["persons"], proximity_threshold=150
            )
            if close_pairs > 0:
                anomalies["is_anomaly"] = True
                anomalies["anomaly_types"].append("POTENTIAL_CONFLICT")
                anomalies["anomaly_details"].append(
                    f"Warning: {close_pairs} people in close proximity - possible altercation"
                )
                anomalies["risk_level"] = "high"

        # Rule 3: Multiple vehicles (potential traffic issue)
        if vehicle_count >= 3:
            anomalies["is_anomaly"] = True
            anomalies["anomaly_types"].append("TRAFFIC_CONGESTION")
            anomalies["anomaly_details"].append(
                f"Multiple vehicles detected: {vehicle_count}"
            )
            if anomalies["risk_level"] == "normal":
                anomalies["risk_level"] = "low"

        # Rule 4: Weapon Detection (High Priority)
        if len(detections["weapons"]) > 0:
            anomalies["is_anomaly"] = True
            weapon_names = [w["class_name"] for w in detections["weapons"]]
            anomalies["anomaly_types"].append("WEAPON_DETECTED")
            anomalies["anomaly_details"].insert(
                0, f"⚠ WEAPON DETECTED: {', '.join(weapon_names)}"
            )  # Priority msg
            anomalies["risk_level"] = "critical"

        # Rule 4: Unusual object combinations (vehicle + people)
        if vehicle_count > 0 and person_count >= 2:
            anomalies["is_anomaly"] = True
            if "CROWD_GATHERING" not in anomalies["anomaly_types"]:
                anomalies["anomaly_types"].append("ACTIVITY_DETECTED")
                anomalies["anomaly_details"].append(
                    f"Activity: {person_count} people near {vehicle_count} vehicle(s)"
                )

        # Update frame count for tracking
        self.frame_count += 1

        return anomalies

    def _check_proximity(
        self, persons: List[Dict], proximity_threshold: int = 150
    ) -> int:
        """
        Check if people are in close proximity (potential fight/conflict)

        Args:
            persons: List of person detections
            proximity_threshold: Distance in pixels to consider "close"

        Returns:
            Number of people in close proximity pairs
        """
        close_count = 0

        for i, p1 in enumerate(persons):
            for j, p2 in enumerate(persons):
                if i >= j:
                    continue

                # Calculate distance between centers
                c1 = p1["center"]
                c2 = p2["center"]
                distance = np.sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2)

                if distance < proximity_threshold:
                    close_count += 1

        return close_count

    def _check_velocity(self, persons: List[Dict], fps: float) -> int:
        """
        Calculate velocity of tracked persons and detect running.
        Returns number of people running.
        """
        running_count = 0
        velocity_threshold = 150  # pixels per second (adjustable)

        current_ids = set()

        for person in persons:
            track_id = person.get("id", -1)
            if track_id == -1:
                continue

            current_ids.add(track_id)
            center = person["center"]

            # Update track history
            # Store (frame_time, x, y)
            # We use frame_count as efficient proxy for time if FPS is constant,
            # but here we'll just use simple position history with max length

            if track_id not in self.person_tracks:
                self.person_tracks[track_id] = []

            self.person_tracks[track_id].append(center)

            # Keep only last 10 frames history (approx 0.3-1.0 sec depending on skip)
            if len(self.person_tracks[track_id]) > 10:
                self.person_tracks[track_id].pop(0)

            # Calculate speed if we have enough history (e.g., at least 3 points)
            history = self.person_tracks[track_id]
            if len(history) >= 3:
                # Distance moved between first and last point in history
                start_pos = history[0]
                end_pos = history[-1]
                distance = np.sqrt(
                    (start_pos[0] - end_pos[0]) ** 2 + (start_pos[1] - end_pos[1]) ** 2
                )

                # Time elapsed (in seconds)
                # Since we process every Nth frame, we need to account for that
                # Assuming history points are added every time this function is called (which is every N frames)
                # This function is called every processed frame
                # So frames elapsed = (len(history) - 1) * SKIP_FACTOR?
                # Actually, fps passed to this function is the video FPS.
                # If we process every 3rd frame, the time between history points is 3/fps.
                # Let's simplify:

                # frames_elapsed = (len(history) - 1) * 3  # Assuming skip=3 (hardcoded for now, should be param)
                # time_elapsed = frames_elapsed / fps

                # To be robust, let's just use raw pixels per processed-step
                # If speed > 50 pixels per step, that's fast.

                speed_per_step = distance / (len(history) - 1)

                # With skip=3, 1 step = 0.1s (at 30fps).
                # 50px/0.1s = 500px/s.
                # Let's tune: "Running" typically covers significant screen distance quickly.

                if speed_per_step > 25:  # Tunable threshold for 640x480 video
                    running_count += 1
                    self.object_velocities[track_id] = speed_per_step

        # Cleanup old tracks
        for tid in list(self.person_tracks.keys()):
            if tid not in current_ids:
                del self.person_tracks[tid]
                if tid in self.object_velocities:
                    del self.object_velocities[tid]

        return running_count

    def process_frame(
        self, frame: np.ndarray, draw_detections: bool = True, fps: float = 30.0
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Process a single frame: detect objects and check anomalies

        Args:
            frame: BGR image
            draw_detections: Whether to draw bounding boxes
            fps: Video FPS for timing calculations

        Returns:
            Tuple of (annotated_frame, results_dict)
        """
        # Detect objects
        detections = self.detect_objects(frame)

        # Check for anomalies
        anomalies = self.check_anomalies(detections, fps)

        # Combine results
        results = {
            **detections,
            **anomalies,
            "person_count": len(detections["persons"]),
            "vehicle_count": len(detections["vehicles"]),
        }

        # Draw on frame
        if draw_detections:
            frame = self.draw_annotations(frame, detections, anomalies)

        return frame, results

    def draw_annotations(
        self, frame: np.ndarray, detections: Dict[str, Any], anomalies: Dict[str, Any]
    ) -> np.ndarray:
        """Draw bounding boxes and labels on frame with modern UI"""
        frame_copy = frame.copy()
        overlay = frame.copy()
        h, w = frame_copy.shape[:2]

        # 1. Draw bounding boxes (cleaner style)
        # Person boxes
        person_color = (0, 0, 255) if anomalies["is_anomaly"] else (0, 255, 0)
        for det in detections["persons"]:
            x1, y1, x2, y2 = det["bbox"]
            # Corner styling or thinner lines
            cv2.rectangle(frame_copy, (x1, y1), (x2, y2), person_color, 2)

            # Label with background
            label = f"Person {det['confidence']:.0%}"
            if "id" in det and det["id"] != -1:
                label += f" ID:{det['id']}"

            (t_w, t_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame_copy, (x1, y1 - 20), (x1 + t_w, y1), person_color, -1)
            cv2.putText(
                frame_copy,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )

        # Vehicle boxes
        for det in detections["vehicles"]:
            x1, y1, x2, y2 = det["bbox"]
            cv2.rectangle(
                frame_copy, (x1, y1), (x2, y2), (255, 165, 0), 2
            )  # Orange for vehicles
            label = f"{det['class_name']}"

            (t_w, t_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame_copy, (x1, y1 - 20), (x1 + t_w, y1), (255, 165, 0), -1)
            cv2.putText(
                frame_copy,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )

        # Weapon boxes (Red/Flashy)
        for det in detections.get("weapons", []):
            x1, y1, x2, y2 = det["bbox"]
            cv2.rectangle(frame_copy, (x1, y1), (x2, y2), (0, 0, 255), 3)
            label = f"⚠ {det['class_name']} {det['confidence']:.0%}"

            (t_w, t_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame_copy, (x1, y1 - 25), (x1 + t_w, y1), (0, 0, 255), -1)
            cv2.putText(
                frame_copy,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

        # 2. Modern Header (Semi-transparent)
        # Instead of full solid block, use a floating status pill or semi-transparent bar

        pad = 20
        bar_height = 50

        if anomalies["is_anomaly"]:
            status_color = (0, 0, 200)  # Dark Red
            status_text = "⚠ ANOMALY DETECTED"
            detail_text = ", ".join(anomalies["anomaly_types"])
        else:
            status_color = (0, 150, 0)  # Dark Green
            status_text = "● NORMAL"
            detail_text = "Monitoring..."

        # Draw semi-transparent header bar
        cv2.rectangle(overlay, (0, 0), (w, bar_height), (0, 0, 0), -1)
        camera_alpha = 0.6
        cv2.addWeighted(
            overlay, camera_alpha, frame_copy, 1 - camera_alpha, 0, frame_copy
        )

        # Status text - Left side
        cv2.putText(
            frame_copy,
            status_text,
            (pad, 28),
            cv2.FONT_HERSHEY_DUPLEX,
            0.7,
            status_color if not anomalies["is_anomaly"] else (0, 0, 255),
            1,
        )

        # Detail text - Below status
        cv2.putText(
            frame_copy,
            detail_text,
            (pad, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (220, 220, 220),
            1,
        )

        # Stats on right side - Below header
        stats_text = (
            f"P: {len(detections['persons'])} | V: {len(detections['vehicles'])}"
        )

        (tw, th), _ = cv2.getTextSize(stats_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.putText(
            frame_copy,
            stats_text,
            (w - tw - pad, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (200, 200, 200),
            1,
        )

        # 3. Bottom Alert for Anomaly Details (Only if anomaly)
        if anomalies["is_anomaly"] and anomalies["anomaly_details"]:
            # Semi-transparent bottom bar
            overlay_bottom = frame_copy.copy()
            cv2.rectangle(
                overlay_bottom, (0, h - 40), (w, h), (0, 0, 150), -1
            )  # Red tint
            cv2.addWeighted(overlay_bottom, 0.6, frame_copy, 0.4, 0, frame_copy)

            detail_msg = anomalies["anomaly_details"][0]
            cv2.putText(
                frame_copy,
                detail_msg,
                (pad, h - 12),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                1,
            )

        return frame_copy

    def process_video(
        self,
        input_path: str,
        output_path: str,
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Process entire video file

        Returns:
            Summary statistics
        """
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {input_path}")

        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Output video - Use imageio for better browser compatibility
        out = VideoWriter(output_path, fps, width, height)

        # Statistics
        stats = {
            "total_frames": 0,
            "anomaly_frames": 0,
            "max_people": 0,
            "max_vehicles": 0,
            "anomaly_types_count": defaultdict(int),
            "frame_results": [],
        }

        start_time = time.time()
        frame_num = 0

        while True:
            # Update progress
            if progress_callback and frame_num % 10 == 0:
                progress = int((frame_num / total_frames) * 100)
                progress_callback(progress)

            ret, frame = cap.read()
            if not ret:
                break

            # Process frame (skip frames for speed)
            if frame_num % 3 == 0:
                annotated_frame, results = self.process_frame(
                    frame, draw_detections=True, fps=fps
                )
                last_results = results
                last_annotated = annotated_frame
            else:
                # Use last results but update frame count in logic if needed
                # For visualization, just use the last annotated frame (or draw on current frame with last dets)
                # To keep it simple and fast, we'll reuse the last detection results
                if "last_results" in locals():
                    results = last_results
                    # Optional: Redraw on new frame if camera moves, but for speed we can just copy
                    # or better, draw last detections on current frame
                    annotated_frame = self.draw_annotations(frame, results, results)
                else:
                    # First frame fallback
                    annotated_frame, results = self.process_frame(
                        frame, draw_detections=True, fps=fps
                    )
                    last_results = results

            # Update stats
            stats["total_frames"] += 1
            if results["is_anomaly"]:
                stats["anomaly_frames"] += 1
                for atype in results["anomaly_types"]:
                    stats["anomaly_types_count"][atype] += 1

            stats["max_people"] = max(stats["max_people"], results["person_count"])
            stats["max_vehicles"] = max(stats["max_vehicles"], results["vehicle_count"])

            # Store simplified result for each frame
            stats["frame_results"].append(
                {
                    "frame": frame_num,
                    "is_anomaly": results["is_anomaly"],
                    "persons": results["person_count"],
                    "vehicles": results["vehicle_count"],
                }
            )

            # Write frame
            out.write(annotated_frame)
            frame_num += 1

        cap.release()
        out.release()

        stats["processing_time"] = time.time() - start_time
        stats["anomaly_rate"] = (
            stats["anomaly_frames"] / stats["total_frames"]
            if stats["total_frames"] > 0
            else 0
        )
        stats["anomaly_types_count"] = dict(stats["anomaly_types_count"])

        return stats


# Singleton instance for the app
_detector_instance = None


def get_yolo_detector(
    model_size: str = "s",
    device: str = "cpu",
    confidence_threshold: float = 0.5,
    crowd_threshold: int = 5,
    loiter_threshold_seconds: float = 10.0,
    confidence: float = 0.5,
) -> YOLOAnomalyDetector:
    """Get or create YOLO detector instance"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = YOLOAnomalyDetector(
            model_size=model_size,
            device=device,
            confidence_threshold=confidence_threshold,
            crowd_threshold=crowd_threshold,
            loiter_threshold_seconds=loiter_threshold_seconds,
        )
    return _detector_instance
