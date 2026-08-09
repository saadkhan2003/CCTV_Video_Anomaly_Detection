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
from pathlib import Path


class AnalysisCancelled(Exception):
    """Raised when a user stops an in-progress uploaded-video analysis."""


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
    # A higher confirmation threshold avoids treating bags and clothing in
    # crowded scenes as weapons while retaining clear weapon detections.
    WEAPON_CONFIDENCE_THRESHOLD = 0.60
    WEAPON_CHECK_INTERVAL_FRAMES = 3
    VEHICLE_CONFIDENCE_THRESHOLD = 0.35

    def __init__(
        self,
        model_size: str = "s",  # n=nano, s=small, m=medium, l=large, x=xlarge
        confidence_threshold: float = 0.5,
        crowd_threshold: int = 5,
        loiter_threshold_seconds: float = 10.0,
        enable_loitering: bool = True,
        device: str = "cpu",
    ):
        """
        Initialize YOLO detector

        Args:
            model_size: YOLO model size (n, s, m, l, x)
            confidence_threshold: Minimum detection confidence
            crowd_threshold: Number of people to trigger crowd alert
            loiter_threshold_seconds: Time to trigger loitering alert
            enable_loitering: Whether stationary people trigger loitering alerts
            device: 'cpu' or 'cuda'
        """
        self.confidence_threshold = confidence_threshold
        self.crowd_threshold = crowd_threshold
        self.loiter_threshold = loiter_threshold_seconds
        self.enable_loitering = enable_loitering
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

        # COCO does not include handguns. Load the local specialist model when
        # available and report all of its pistol/knife detections as WEAPON.
        self.weapon_model = None
        weapon_model_path = (
            Path(__file__).resolve().parents[2] / "models" / "weapon_detector.pt"
        )
        if weapon_model_path.exists():
            try:
                self.weapon_model = YOLO(str(weapon_model_path))
                print("Weapon detection model loaded!")
            except Exception as e:
                print(f"Weapon detection model unavailable: {e}")
        else:
            print(f"Weapon detection model not found: {weapon_model_path}")

        # Tracking for loitering and velocity
        self.person_tracks: Dict[int, List[Tuple[float, float, float]]] = defaultdict(list)
        self.person_stationary_since: Dict[int, Tuple[float, Tuple[int, int]]] = {}
        self.object_velocities: Dict[int, float] = {}
        self.frame_count = 0

    def detect_objects(
        self,
        frame: np.ndarray,
        timestamp: Optional[float] = None,
        cached_detections: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Detect objects in a single frame

        Returns:
            Dictionary with detections and anomaly flags
        """
        detections = {
            "persons": [],
            "vehicles": [],
            "weapons": [],
            "other_objects": [],
            "all_boxes": [],
        }

        if cached_detections is not None:
            for key in detections:
                detections[key] = list(cached_detections.get(key, []))
        else:
            # Run YOLO tracking (ByteTrack is built-in and fast).
            results = self.model.track(
                frame,
                conf=min(self.confidence_threshold, self.VEHICLE_CONFIDENCE_THRESHOLD),
                persist=self.frame_count > 0,
                verbose=False,
                tracker="bytetrack.yaml",
            )

            if len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes

                for i, box in enumerate(boxes):
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].cpu().numpy()
                    id = int(box.id[0]) if box.id is not None else -1
                    x1, y1, x2, y2 = map(int, xyxy)

                    minimum_confidence = (
                        self.VEHICLE_CONFIDENCE_THRESHOLD
                        if cls in self.VEHICLE_CLASSES
                        else self.confidence_threshold
                    )
                    if conf < minimum_confidence:
                        continue

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

        # Run the specialist weapon model at the same every-third-frame rate
        # as the general detector, while retaining its last result between checks.
        if self.frame_count % self.WEAPON_CHECK_INTERVAL_FRAMES == 0:
            specialist_weapons = self._detect_specialist_weapons(frame)
            detections["weapons"] = [
                weapon for weapon in detections["weapons"]
                if weapon.get("category") != "weapon"
            ]
            detections["all_boxes"] = [
                box for box in detections["all_boxes"]
                if box.get("category") != "weapon"
            ]
            detections["weapons"].extend(specialist_weapons)
            detections["all_boxes"].extend(specialist_weapons)

        return detections

    def _detect_specialist_weapons(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect guns and knives with the local weapon-specific YOLO model."""
        if self.weapon_model is None:
            return []

        results = self.weapon_model.predict(
            frame, conf=self.WEAPON_CONFIDENCE_THRESHOLD, verbose=False
        )
        weapons = []
        if not results or results[0].boxes is None:
            return weapons

        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
            weapons.append(
                {
                    "class_id": -1,
                    "class_name": "WEAPON",
                    "confidence": float(box.conf[0]),
                    "bbox": [x1, y1, x2, y2],
                    "center": ((x1 + x2) // 2, (y1 + y2) // 2),
                    "id": -1,
                    "category": "weapon",
                }
            )

        return weapons

    def check_anomalies(
        self,
        detections: Dict[str, Any],
        fps: float = 30.0,
        timestamp: Optional[float] = None,
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
        loitering_count, running_count = self._track_person_motion(
            detections["persons"], timestamp if timestamp is not None else time.monotonic()
        )

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

        if self.enable_loitering and loitering_count:
            anomalies["is_anomaly"] = True
            anomalies["anomaly_types"].append("LOITERING")
            anomalies["anomaly_details"].append(
                f"Loitering detected: {loitering_count} person(s) stationary for at least {self.loiter_threshold:.0f} seconds"
            )
            if anomalies["risk_level"] == "normal":
                anomalies["risk_level"] = "medium"

        if running_count:
            anomalies["is_anomaly"] = True
            anomalies["anomaly_types"].append("FAST_MOVEMENT")
            anomalies["anomaly_details"].append(
                f"Fast movement detected: {running_count} person(s)"
            )
            if anomalies["risk_level"] == "normal":
                anomalies["risk_level"] = "medium"

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
                0, f"WEAPON DETECTED: {', '.join(weapon_names)}"
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

    def _get_detections_summary(self, detections: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build a human-readable summary of all detected classes for demo display.
        """
        summary = []
        for det in detections.get("all_boxes", []):
            category = det.get("category")
            if category is None:
                if det["class_id"] == self.PERSON_CLASS:
                    category = "person"
                elif det["class_id"] in self.VEHICLE_CLASSES:
                    category = "vehicle"
                elif det["class_id"] in self.WEAPON_CLASSES:
                    category = "weapon"
                else:
                    category = "other"
            summary.append(
                {
                    "class_name": det["class_name"],
                    "confidence": round(det["confidence"], 2),
                    "id": det["id"],
                    "category": category,
                }
            )
        return summary

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

    def _track_person_motion(
        self, persons: List[Dict[str, Any]], timestamp: float
    ) -> Tuple[int, int]:
        """Update tracked person motion and return loitering and running counts."""
        stationary_radius = 50
        running_speed = 250
        current_ids = set()
        loitering_count = 0
        running_count = 0

        for person in persons:
            track_id = person.get("id", -1)
            if track_id == -1:
                continue
            current_ids.add(track_id)
            center = person["center"]
            history = self.person_tracks[track_id]
            history.append((timestamp, center[0], center[1]))
            if len(history) > 10:
                history.pop(0)

            stationary_since, anchor = self.person_stationary_since.get(
                track_id, (timestamp, center)
            )
            displacement = np.hypot(center[0] - anchor[0], center[1] - anchor[1])
            if displacement > stationary_radius:
                stationary_since, anchor = timestamp, center
            self.person_stationary_since[track_id] = (stationary_since, anchor)
            if timestamp - stationary_since >= self.loiter_threshold:
                loitering_count += 1

            if len(history) >= 3:
                start_time, start_x, start_y = history[0]
                elapsed = timestamp - start_time
                if elapsed > 0:
                    speed = np.hypot(center[0] - start_x, center[1] - start_y) / elapsed
                    self.object_velocities[track_id] = speed
                    if speed >= running_speed:
                        running_count += 1

        for track_id in set(self.person_tracks) - current_ids:
            self.person_tracks.pop(track_id, None)
            self.person_stationary_since.pop(track_id, None)
            self.object_velocities.pop(track_id, None)

        return loitering_count, running_count

    def reset_tracking(self):
        """Reset state before processing a new video source."""
        self.person_tracks.clear()
        self.person_stationary_since.clear()
        self.object_velocities.clear()
        self.frame_count = 0

    def process_frame(
        self,
        frame: np.ndarray,
        draw_detections: bool = True,
        fps: float = 30.0,
        timestamp: Optional[float] = None,
        cached_detections: Optional[Dict[str, Any]] = None,
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
        detections = self.detect_objects(frame, timestamp, cached_detections)

        # Check for anomalies
        anomalies = self.check_anomalies(detections, fps, timestamp)

        # Combine results
        results = {
            **detections,
            **anomalies,
            "person_count": len(detections["persons"]),
            "vehicle_count": len(detections["vehicles"]),
            "weapon_count": len(detections["weapons"]),
            "detections_summary": self._get_detections_summary(detections),
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
            label = f"WEAPON {det['confidence']:.0%}"

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
            status_text = "ANOMALY DETECTED"
            detail_text = ", ".join(anomalies["anomaly_types"])
        else:
            status_color = (0, 150, 0)  # Dark Green
            status_text = "NORMAL"
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
        should_cancel: Optional[callable] = None,
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

        self.reset_tracking()

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
        sample_interval_frames = 3
        last_detections = None

        while True:
            if should_cancel and should_cancel():
                cap.release()
                out.release()
                raise AnalysisCancelled("Analysis cancelled by user")

            # Update progress
            if progress_callback and frame_num % 10 == 0:
                progress = int((frame_num / total_frames) * 100)
                progress_callback(progress)

            ret, frame = cap.read()
            if not ret:
                break

            # Analyze every third frame for a practical accuracy/speed balance.
            if frame_num % sample_interval_frames == 0:
                annotated_frame, results = self.process_frame(
                    frame, draw_detections=True, fps=fps, timestamp=frame_num / fps
                )
                last_results = results
                last_annotated = annotated_frame
                last_detections = {
                    key: list(results.get(key, []))
                    for key in ("persons", "vehicles", "weapons", "other_objects", "all_boxes")
                }
            else:
                # Reuse general detections between every-third-frame checks.
                if last_detections is not None:
                    annotated_frame, results = self.process_frame(
                        frame,
                        draw_detections=True,
                        fps=fps,
                        timestamp=frame_num / fps,
                        cached_detections=last_detections,
                    )
                    last_results = results
                    last_detections = {
                        key: list(results.get(key, []))
                        for key in ("persons", "vehicles", "weapons", "other_objects", "all_boxes")
                    }
                else:
                    # First frame fallback
                    annotated_frame, results = self.process_frame(
                        frame, draw_detections=True, fps=fps, timestamp=frame_num / fps
                    )
                    last_results = results
                    last_detections = {
                        key: list(results.get(key, []))
                        for key in ("persons", "vehicles", "weapons", "other_objects", "all_boxes")
                    }

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


# Cache detectors by the settings that affect their behavior.
_detector_instances: Dict[Tuple[str, str, float, int, float], YOLOAnomalyDetector] = {}


def get_yolo_detector(
    model_size: str = "s",
    device: str = "cpu",
    confidence_threshold: float = 0.5,
    crowd_threshold: int = 5,
    loiter_threshold_seconds: float = 10.0,
) -> YOLOAnomalyDetector:
    """Get or create a detector matching the requested analysis settings."""
    settings = (
        model_size,
        device,
        confidence_threshold,
        crowd_threshold,
        loiter_threshold_seconds,
    )
    if settings not in _detector_instances:
        _detector_instances[settings] = YOLOAnomalyDetector(
            model_size=model_size,
            device=device,
            confidence_threshold=confidence_threshold,
            crowd_threshold=crowd_threshold,
            loiter_threshold_seconds=loiter_threshold_seconds,
        )
    return _detector_instances[settings]
