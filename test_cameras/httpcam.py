import cv2
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

frame = None
LOCK = threading.Lock()
FPS = 20

class MJPEGHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global frame
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=ff")
        self.end_headers()
        try:
            while True:
                with LOCK:
                    f = frame
                if f is not None:
                    _, jpg = cv2.imencode(".jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    self.wfile.write(b"--ff\r\n")
                    self.wfile.write(b"Content-Type: image/jpeg\r\n\r\n")
                    self.wfile.write(jpg.tobytes())
                    self.wfile.write(b"\r\n")
                time.sleep(1 / FPS)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, *a):
        return


def read_video():
    global frame
    import os
    import sys

    # Check for --video argument first, otherwise use samples dir
    if len(sys.argv) > 2 and sys.argv[1] == "--video":
        source = sys.argv[2]
    else:
        samples_dir = os.path.join(
            os.path.dirname(__file__), "..", "static", "videos", "samples"
        )
        mp4s = sorted(
            [f for f in os.listdir(samples_dir) if f.endswith(".mp4")]
        ) if os.path.isdir(samples_dir) else []
        source = os.path.join(samples_dir, mp4s[0]) if mp4s else None

    if not source:
        print("No .mp4 found in static/videos/samples/ — using test pattern")
        while True:
            import numpy as np
            frame = np.random.randint(0, 255, (540, 960, 3), dtype=np.uint8)
            time.sleep(1 / FPS)
    else:
        print(f"Streaming: {os.path.basename(source)}")
        cap = cv2.VideoCapture(source)
        while True:
            ret, f = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            f = cv2.resize(f, (960, 540))
            with LOCK:
                frame = f
            time.sleep(1 / FPS)


if __name__ == "__main__":
    t = threading.Thread(target=read_video, daemon=True)
    t.start()
    print("=" * 50)
    print("  HTTP Camera running!")
    print("  Paste this URL into your web UI:")
    print("  http://127.0.0.1:8080/video.mjpg")
    print("=" * 50)
    HTTPServer(("0.0.0.0", 8080), MJPEGHandler).serve_forever()
