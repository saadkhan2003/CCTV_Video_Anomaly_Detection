"""
Visualization Module for Anomaly Detection
==========================================

Creates visual overlays on video frames showing detected anomalies:
- Heatmaps showing reconstruction error regions
- Bounding boxes around high-error areas
- Annotated output videos with anomaly highlights
"""

import cv2
import numpy as np
import torch
from typing import List, Tuple, Dict, Optional
import os


def compute_error_heatmap(
    original: np.ndarray,
    reconstructed: np.ndarray
) -> np.ndarray:
    """
    Compute pixel-wise reconstruction error heatmap
    
    Args:
        original: Original frame (64x64)
        reconstructed: Reconstructed frame from autoencoder (64x64)
    
    Returns:
        Heatmap showing error intensity (64x64)
    """
    # Compute absolute difference
    error = np.abs(original - reconstructed)
    
    # Normalize to 0-255 range
    error_normalized = (error * 255).astype(np.uint8)
    
    return error_normalized


def find_anomaly_regions(
    error_heatmap: np.ndarray,
    threshold_percentile: float = 90,
    min_area: int = 50
) -> List[Dict]:
    """
    Find regions with high reconstruction error
    
    Args:
        error_heatmap: Error intensity map
        threshold_percentile: Percentile threshold for anomaly regions
        min_area: Minimum contour area to consider
    
    Returns:
        List of bounding boxes with anomaly info
    """
    # Threshold the heatmap
    threshold_value = np.percentile(error_heatmap, threshold_percentile)
    _, binary = cv2.threshold(error_heatmap, threshold_value, 255, cv2.THRESH_BINARY)
    
    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    regions = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area >= min_area:
            x, y, w, h = cv2.boundingRect(contour)
            regions.append({
                'x': int(x),
                'y': int(y),
                'width': int(w),
                'height': int(h),
                'area': int(area),
                'avg_error': float(np.mean(error_heatmap[y:y+h, x:x+w]))
            })
    
    # Sort by error intensity (highest first)
    regions.sort(key=lambda r: r['avg_error'], reverse=True)
    
    return regions


def draw_bounding_boxes(
    frame: np.ndarray,
    regions: List[Dict],
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    color: Tuple[int, int, int] = (0, 0, 255),  # Red in BGR
    thickness: int = 2,
    show_score: bool = True
) -> np.ndarray:
    """
    Draw bounding boxes on frame with improved visibility
    """
    frame_copy = frame.copy()
    
    # Only draw top 3 most significant regions to avoid clutter
    for i, region in enumerate(regions[:3]):
        # Scale coordinates to original frame size
        x = int(region['x'] * scale_x)
        y = int(region['y'] * scale_y)
        w = int(region['width'] * scale_x)
        h = int(region['height'] * scale_y)
        
        # Ensure minimum box size for visibility
        w = max(w, 40)
        h = max(h, 40)
        
        # Draw rectangle with thicker line
        cv2.rectangle(frame_copy, (x, y), (x + w, y + h), color, thickness + 1)
        
        # Draw corner markers for better visibility
        corner_len = min(20, w // 4, h // 4)
        # Top-left
        cv2.line(frame_copy, (x, y), (x + corner_len, y), (255, 255, 255), 3)
        cv2.line(frame_copy, (x, y), (x, y + corner_len), (255, 255, 255), 3)
        # Top-right
        cv2.line(frame_copy, (x + w, y), (x + w - corner_len, y), (255, 255, 255), 3)
        cv2.line(frame_copy, (x + w, y), (x + w, y + corner_len), (255, 255, 255), 3)
        # Bottom-left
        cv2.line(frame_copy, (x, y + h), (x + corner_len, y + h), (255, 255, 255), 3)
        cv2.line(frame_copy, (x, y + h), (x, y + h - corner_len), (255, 255, 255), 3)
        # Bottom-right
        cv2.line(frame_copy, (x + w, y + h), (x + w - corner_len, y + h), (255, 255, 255), 3)
        cv2.line(frame_copy, (x + w, y + h), (x + w, y + h - corner_len), (255, 255, 255), 3)
    
    return frame_copy


def apply_heatmap_overlay(
    frame: np.ndarray,
    error_heatmap: np.ndarray,
    alpha: float = 0.3
) -> np.ndarray:
    """
    Apply error heatmap as a colored overlay on the frame
    
    Args:
        frame: Original BGR frame
        error_heatmap: 64x64 error intensity map
        alpha: Blend factor (0 = no overlay, 1 = full overlay)
    
    Returns:
        Frame with heatmap overlay
    """
    h, w = frame.shape[:2]
    
    # Resize heatmap to frame size
    heatmap_resized = cv2.resize(error_heatmap, (w, h))
    
    # Apply Gaussian blur to smooth the heatmap
    heatmap_smooth = cv2.GaussianBlur(heatmap_resized, (31, 31), 0)
    
    # Normalize and enhance contrast
    heatmap_normalized = cv2.normalize(heatmap_smooth, None, 0, 255, cv2.NORM_MINMAX)
    
    # Apply colormap (JET: blue=low, red=high)
    heatmap_color = cv2.applyColorMap(heatmap_normalized.astype(np.uint8), cv2.COLORMAP_JET)
    
    # Blend with original frame
    output = cv2.addWeighted(frame, 1 - alpha, heatmap_color, alpha, 0)
    
    return output


def add_anomaly_indicator(
    frame: np.ndarray,
    is_anomaly: bool,
    anomaly_score: float,
    threshold: float,
    frame_number: int
) -> np.ndarray:
    """
    Add status indicator overlay to frame
    
    Args:
        frame: Video frame
        is_anomaly: Whether this frame is anomalous
        anomaly_score: Reconstruction error score
        threshold: Current threshold value
        frame_number: Current frame number
    
    Returns:
        Frame with status overlay
    """
    frame_copy = frame.copy()
    h, w = frame_copy.shape[:2]
    
    # Status bar at top
    bar_height = 50
    
    # Create gradient-like bar with semi-transparency
    overlay = frame_copy.copy()
    bar_color = (0, 0, 200) if is_anomaly else (0, 130, 0)  # Red or Green
    cv2.rectangle(overlay, (0, 0), (w, bar_height), bar_color, -1)
    cv2.addWeighted(overlay, 0.85, frame_copy, 0.15, 0, frame_copy)
    
    # Status text (NO EMOJIS - use plain text)
    if is_anomaly:
        status = "[!] ANOMALY DETECTED"
    else:
        status = "[OK] Normal"
    
    cv2.putText(frame_copy, status, (15, 35), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
    
    # Score display on right side
    score_text = f"Score: {anomaly_score:.4f}"
    threshold_text = f"Threshold: {threshold:.4f}"
    
    # Position text on right
    cv2.putText(frame_copy, score_text, (w - 200, 25), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(frame_copy, threshold_text, (w - 200, 42), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
    
    # Frame number bar at bottom
    bottom_bar_height = 30
    cv2.rectangle(frame_copy, (0, h - bottom_bar_height), (w, h), (30, 30, 30), -1)
    cv2.putText(frame_copy, f"Frame: {frame_number}", (15, h - 10), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Add confidence bar
    confidence = min(anomaly_score / threshold, 2.0) if threshold > 0 else 0
    bar_width = int((w - 250) * min(confidence, 1.0))
    bar_x = 120
    
    # Background bar
    cv2.rectangle(frame_copy, (bar_x, h - 22), (w - 130, h - 12), (60, 60, 60), -1)
    
    # Confidence bar with color gradient
    if confidence > 1.0:
        bar_color = (0, 0, 255)  # Red for anomaly
    elif confidence > 0.7:
        bar_color = (0, 165, 255)  # Orange
    else:
        bar_color = (0, 200, 0)  # Green
    
    cv2.rectangle(frame_copy, (bar_x, h - 22), (bar_x + bar_width, h - 12), bar_color, -1)
    cv2.putText(frame_copy, f"{confidence*100:.0f}%", (w - 120, h - 10), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
    
    return frame_copy


def create_annotated_video(
    input_path: str,
    output_path: str,
    model,
    device: torch.device,
    threshold: float,
    preprocessor=None
) -> Tuple[List[float], List[bool], List[List[Dict]]]:
    """
    Create annotated video with bounding boxes and overlays
    
    Args:
        input_path: Path to input video
        output_path: Path for output annotated video
        model: Trained autoencoder model
        device: Torch device (cpu/cuda)
        threshold: Anomaly threshold
        preprocessor: Optional video preprocessor
    
    Returns:
        Tuple of (anomaly_scores, anomaly_flags, frame_bboxes)
    """
    # Open input video
    cap = cv2.VideoCapture(input_path)
    
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {input_path}")
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Calculate scale factors (from 64x64 to original size)
    scale_x = width / 64
    scale_y = height / 64
    
    # Setup output video writer - keep mp4 format for consistency
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Process frames
    anomaly_scores = []
    anomaly_flags = []
    frame_bboxes = []
    
    model.eval()
    frame_number = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Preprocess frame for model
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (64, 64))
        normalized = resized.astype(np.float32) / 255.0
        
        # Get reconstruction
        with torch.no_grad():
            input_tensor = torch.FloatTensor(normalized).unsqueeze(0).unsqueeze(0).to(device)
            reconstructed_tensor = model(input_tensor)
            reconstructed = reconstructed_tensor.squeeze().cpu().numpy()
        
        # Calculate error
        error = float(torch.mean((input_tensor - reconstructed_tensor) ** 2).item())
        is_anomaly = error > threshold
        
        anomaly_scores.append(error)
        anomaly_flags.append(is_anomaly)
        
        # Find anomaly regions
        error_heatmap = compute_error_heatmap(normalized, reconstructed)
        regions = find_anomaly_regions(error_heatmap) if is_anomaly else []
        frame_bboxes.append(regions)
        
        # For anomaly frames, apply heatmap overlay to show error regions
        if is_anomaly:
            # Apply subtle heatmap overlay to show where errors are highest
            frame = apply_heatmap_overlay(frame, error_heatmap, alpha=0.25)
        
        # Add status overlay
        frame = add_anomaly_indicator(frame, is_anomaly, error, threshold, frame_number)
        
        # Write frame
        out.write(frame)
        frame_number += 1
    
    # Cleanup
    cap.release()
    out.release()
    
    return anomaly_scores, anomaly_flags, frame_bboxes


def create_comparison_frame(
    original: np.ndarray,
    reconstructed: np.ndarray,
    error_heatmap: np.ndarray,
    target_width: int = 640
) -> np.ndarray:
    """
    Create side-by-side comparison frame
    
    Args:
        original: Original frame
        reconstructed: Reconstructed frame
        error_heatmap: Error heatmap
        target_width: Width of each panel
    
    Returns:
        Combined comparison image
    """
    # Resize all to same size
    h = int(target_width * 0.75)  # 4:3 aspect ratio
    
    orig_resized = cv2.resize(original, (target_width, h))
    recon_resized = cv2.resize(reconstructed, (target_width, h))
    
    # Convert heatmap to color
    heatmap_color = cv2.applyColorMap(
        cv2.resize(error_heatmap, (target_width, h)),
        cv2.COLORMAP_JET
    )
    
    # Add labels
    cv2.putText(orig_resized, "Original", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(recon_resized, "Reconstructed", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(heatmap_color, "Error Heatmap", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Stack horizontally
    if len(orig_resized.shape) == 2:
        orig_resized = cv2.cvtColor(orig_resized, cv2.COLOR_GRAY2BGR)
    if len(recon_resized.shape) == 2:
        recon_resized = cv2.cvtColor(recon_resized, cv2.COLOR_GRAY2BGR)
    
    comparison = np.hstack([orig_resized, recon_resized, heatmap_color])
    
    return comparison


# Create output directory for annotated videos
ANNOTATED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'annotated_videos')
os.makedirs(ANNOTATED_DIR, exist_ok=True)
