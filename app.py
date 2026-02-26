"""
CCTV Video Anomaly Detection API
================================
YOLOv8-based anomaly detection with email alerts.
"""

import os
import sys
import tempfile
import time
import uuid
from typing import List, Optional, Dict, Any
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, BackgroundTasks

# Load config from .env file
load_dotenv()

# Config from .env
MODEL_SIZE = os.getenv("MODEL_SIZE", "s")
DEVICE = os.getenv("DEVICE", "cpu")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
CROWD_THRESHOLD = int(os.getenv("CROWD_THRESHOLD", "5"))
LOITER_THRESHOLD = float(os.getenv("LOITER_THRESHOLD", "10.0"))
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Imports
from storage.database import (
    init_database,
    save_video_analysis,
    get_all_videos,
    get_video_by_id,
    search_videos,
    delete_video,
    get_statistics,
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
VIDEOS_DIR = os.path.join(STATIC_DIR, "videos")

os.makedirs(VIDEOS_DIR, exist_ok=True)

# FastAPI App
app = FastAPI(
    title="CCTV Anomaly Detection",
    description="YOLOv8-based video anomaly detection",
    version="3.0.0",
)

import mimetypes

mimetypes.add_type("video/mp4", ".mp4")
mimetypes.add_type("video/x-msvideo", ".avi")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ============= Task Management =============
TASKS = {}


def run_analysis_task(
    task_id: str,
    file_path: str,
    output_path: str,
    crowd_threshold: int,
    confidence: float,
    original_filename: str,
):
    """Background task wrapper for analysis"""
    try:
        from detection.yolo_detector import get_yolo_detector

        TASKS[task_id]["status"] = "processing"

        def update_progress(p):
            TASKS[task_id]["progress"] = p

        yolo = get_yolo_detector(
            model_size=MODEL_SIZE,
            device=DEVICE,
            confidence_threshold=CONFIDENCE_THRESHOLD,
            crowd_threshold=crowd_threshold,
            loiter_threshold_seconds=LOITER_THRESHOLD,
            confidence=confidence,
        )
        stats = yolo.process_video(
            file_path, output_path, progress_callback=update_progress
        )

        # Save to DB logic (moved here)
        video_id = save_video_analysis(
            filename=original_filename,
            frame_count=stats["total_frames"],
            anomaly_count=stats["anomaly_frames"],
            anomaly_rate=stats["anomaly_rate"],
            processing_time=stats["processing_time"],
            threshold_used=crowd_threshold,
            anomaly_scores=[
                1.0 if r["is_anomaly"] else 0.0 for r in stats["frame_results"]
            ],
            anomaly_flags=[r["is_anomaly"] for r in stats["frame_results"]],
            output_video_path=output_path,
        )

        # Email logic
        if stats["anomaly_frames"] > 0:
            try:
                from alerts.email_alerts import send_anomaly_alert

                send_anomaly_alert(
                    anomaly_types=list(stats["anomaly_types_count"].keys()),
                    details=[
                        f"Video: {original_filename}",
                        f"Anomalies: {stats['anomaly_frames']} frames",
                        f"Rate: {stats['anomaly_rate'] * 100:.1f}%",
                    ],
                    video_filename=original_filename,
                    video_id=video_id,
                )
            except Exception as e:
                logger.error(f"Email error: {e}")

        # Update task result
        TASKS[task_id]["status"] = "completed"
        TASKS[task_id]["progress"] = 100
        TASKS[task_id]["result"] = {
            "video_id": video_id,
            "total_frames": stats["total_frames"],
            "anomaly_frames": stats["anomaly_frames"],
            "anomaly_rate": stats["anomaly_rate"],
            "max_people_detected": stats["max_people"],
            "max_vehicles_detected": stats["max_vehicles"],
            "anomaly_types": stats["anomaly_types_count"],
            "processing_time": stats["processing_time"],
            "annotated_video_url": f"/static/videos/{os.path.basename(output_path)}",
        }

    except Exception as e:
        logger.error(f"Task failed: {e}")
        TASKS[task_id]["status"] = "failed"
        TASKS[task_id]["error"] = str(e)
    finally:
        # Cleanup temp file
        if os.path.exists(file_path):
            os.unlink(file_path)


# ============= Models =============


class HealthResponse(BaseModel):
    status: str
    version: str


# ============= Startup =============


@app.on_event("startup")
async def startup():
    init_database()
    logger.info("✅ Application started")


# ============= Routes =============


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve main page"""
    template_path = os.path.join(TEMPLATES_DIR, "index.html")
    with open(template_path, "r") as f:
        return HTMLResponse(content=f.read())


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "3.0.0"}


@app.post("/analyze-yolo")
async def analyze_yolo(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    crowd_threshold: int = Query(5),
    confidence: float = Query(0.5),
):
    """Analyze video with YOLO detection (Async)"""
    if not file.content_type.startswith("video/"):
        raise HTTPException(400, "File must be a video")

    # Save temp file
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    try:
        content = await file.read()
        temp.write(content)
        temp.close()
        temp_path = temp.name
    except:
        temp.close()
        raise HTTPException(500, "Failed to save file")

    task_id = str(uuid.uuid4())
    output_filename = f"yolo_{task_id}.mp4"
    output_path = os.path.join(VIDEOS_DIR, output_filename)

    TASKS[task_id] = {"status": "queued", "progress": 0, "result": None}

    background_tasks.add_task(
        run_analysis_task,
        task_id,
        temp_path,
        output_path,
        crowd_threshold,
        confidence,
        file.filename,
    )

    return {"task_id": task_id}


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of an analysis task"""
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task


# ============= History Endpoints =============


@app.get("/history")
async def get_history(
    filename: Optional[str] = None, min_anomaly_rate: Optional[float] = None
):
    """Get video analysis history"""
    if filename or min_anomaly_rate:
        return search_videos(filename=filename, min_anomaly_rate=min_anomaly_rate)
    return get_all_videos()


@app.get("/history/{video_id}")
async def get_history_item(video_id: int):
    """Get specific video analysis"""
    result = get_video_by_id(video_id)
    if not result:
        raise HTTPException(404, "Video not found")
    return result


@app.delete("/history/{video_id}")
async def delete_history_item(video_id: int):
    """Delete video analysis"""
    video = get_video_by_id(video_id)
    if video and video.get("output_video_path"):
        try:
            os.remove(video["output_video_path"])
        except:
            pass

    success = delete_video(video_id)
    if not success:
        raise HTTPException(404, "Video not found")
    return {"deleted": True}


# ============= Email Endpoints =============


@app.post("/configure-email")
async def configure_email(
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 587,
    sender_email: str = "",
    sender_password: str = "",
    admin_emails: str = "",
):
    """Configure email alerts"""
    from alerts.email_alerts import configure_email as config_email

    admin_list = [e.strip() for e in admin_emails.split(",") if e.strip()]
    success = config_email(
        smtp_server, smtp_port, sender_email, sender_password, admin_list
    )

    return {"configured": success}


@app.get("/email-status")
async def email_status():
    """Get email config status"""
    from alerts.email_alerts import get_email_status

    return get_email_status()


# ============= Live Stream Endpoints =============

from fastapi.responses import StreamingResponse


@app.get("/live", response_class=HTMLResponse)
async def live_page():
    """Serve live stream page"""
    template_path = os.path.join(TEMPLATES_DIR, "live.html")
    with open(template_path, "r") as f:
        return HTMLResponse(content=f.read())


@app.post("/live/start")
async def start_live_stream(data: dict):
    """Start a live stream"""
    from detection.live_stream import create_stream

    stream_id = data.get("stream_id", "main")
    source = data.get("source", 0)
    threshold = data.get("crowd_threshold", 3)

    # Convert source to int if it's a camera index
    if isinstance(source, str) and source.isdigit():
        source = int(source)

    stream = create_stream(
        stream_id=stream_id, source=source, crowd_threshold=threshold
    )

    success = stream.start()

    return {"success": success, "stream_id": stream_id}


@app.post("/live/stop")
async def stop_live_stream(data: dict):
    """Stop a live stream"""
    from detection.live_stream import stop_stream

    stream_id = data.get("stream_id", "main")
    success = stop_stream(stream_id)

    return {"success": success}


@app.get("/live/feed/{stream_id}")
async def live_feed(stream_id: str):
    """Get live video feed (MJPEG stream)"""
    from detection.live_stream import get_stream

    stream = get_stream(stream_id)
    if not stream or not stream.is_running:
        raise HTTPException(404, "Stream not found or not running")

    return StreamingResponse(
        stream.generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/live/status/{stream_id}")
async def live_status(stream_id: str):
    """Get live stream status"""
    from detection.live_stream import get_stream

    stream = get_stream(stream_id)
    if not stream:
        return {"is_running": False}

    return stream.get_status()


@app.get("/live/cameras")
async def detect_cameras():
    """Detect available cameras"""
    from detection.live_stream import detect_cameras

    return detect_cameras()


# ============= Run =============

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
