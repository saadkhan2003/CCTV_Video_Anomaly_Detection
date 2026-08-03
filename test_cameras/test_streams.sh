#!/bin/bash
# ============================================================
#  Test Cameras for CCTV Anomaly Detection
#  Run this BEFORE opening the web UI
# ============================================================

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$DIR")"
SAMPLES_DIR="$PROJECT_DIR/static/videos/samples"

# Allow: bash test_streams.sh /path/to/video.mp4
if [ -n "$1" ] && [ -f "$1" ]; then
    VIDEO="$1"
elif [ -d "$SAMPLES_DIR" ]; then
    VIDEO=$(ls "$SAMPLES_DIR"/*.mp4 2>/dev/null | head -1)
fi

if [ -z "$VIDEO" ]; then
    echo "No .mp4 found in static/videos/samples/"
    echo "Run: bash test_cameras/download_samples.sh"
    echo "Or:  bash test_streams.sh /path/to/video.mp4"
    exit 1
fi

echo ""
echo "=============================================="
echo "  Setting up fake cameras for testing..."
echo "=============================================="
echo ""

# --- 1. Start RTSP server via Docker mediamtx ---
echo "[1/3] Starting RTSP server (Docker mediamtx)..."
docker rm -f mediamtx 2>/dev/null || true
docker run -d --name mediamtx --rm \
    -p 8554:8554 -p 8888:8888 \
    bluenviron/mediamtx:latest >/dev/null 2>&1
sleep 3

echo "[2/3] Publishing RTSP stream from: $(basename "$VIDEO")"
ffmpeg -re -stream_loop -1 -i "$VIDEO" \
    -c copy -f rtsp -rtsp_transport tcp \
    rtsp://localhost:8554/camtest >/dev/null 2>&1 &
FFMPEG_PID=$!
sleep 3

# --- 2. Start HTTP MJPEG server ---
echo "[3/3] Starting HTTP MJPEG camera..."
python "$DIR/httpcam.py" --video "$VIDEO" &
HTTP_PID=$!
sleep 2

echo ""
echo "=============================================="
echo "  FAKE CAMERES ARE LIVE"
echo "  Streaming: $(basename "$VIDEO")"
echo "=============================================="
echo ""
echo "  RTSP / IP Camera URL:"
echo "    rtsp://127.0.0.1:8554/camtest"
echo ""
echo "  HTTP Stream URL:"
echo "    http://127.0.0.1:8080/video.mjpg"
echo ""
echo "  Webcam (default):"
echo "    Use 'Camera 0 (Default)' in dropdown"
echo ""
echo "=============================================="
echo "  Press Ctrl+C to stop all fake cameras"
echo "=============================================="
echo ""

# --- Trap Ctrl+C to cleanup ---
cleanup() {
    echo ""
    echo "Stopping fake cameras..."
    kill $FFMPEG_PID 2>/dev/null || true
    kill $HTTP_PID 2>/dev/null || true
    docker rm -f mediamtx 2>/dev/null || true
    echo "Done."
}
trap cleanup EXIT INT TERM

wait
