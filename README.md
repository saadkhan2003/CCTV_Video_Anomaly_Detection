# 📹 CCTV Video Anomaly Detection System

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![YOLOv8](https://img.shields.io/badge/Model-YOLOv8-green)
![OpenVINO](https://img.shields.io/badge/Inference-OpenVINO-purple)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-teal)

A high-performance, real-time video anomaly detection system designed for CCTV surveillance. Optimized for CPU inference using OpenVINO, featuring a modern glassmorphism UI.

## 🌟 Key Features

### 🔍 Advanced Detection
-   **Objects**: Detects Persons, Vehicles, and specific **Weapons** (Knives, Baseball Bats, Scissors).
-   **Tracking**: robust object tracking using ByteTrack.

### 🚨 Anomaly Rules
-   **Crowd Detection**: Alerts when specific number of people (configurable) gather in an area.
-   **Loitering**: Identifies individuals staying in one spot for too long.
-   **Fast Movement**: Detects running or panic situations based on velocity.
-   **Potential Conflicts**: Flags groups in very close proximity (fight detection).
-   **Traffic**: Detects vehicle congestion or vehicles in pedestrian areas.

### ⚡ Performance & UI
-   **OpenVINO Optimization**: Automatically exports YOLO models to OpenVINO format for **2-3x detection speedup** on Intel CPUs.
-   **Async Processing**: Background task management ensures the UI never freezes during analysis.
-   **Progress Tracking**: Real-time progress bar for long video uploads.
-   **Modern UI**: Premium dark theme with glassmorphism, responsive design, and smooth animations.

### 📧 Alerts
-   **Email Notifications**: Sends automated emails with analysis summaries when critical anomalies are detected.

---

## 🛠️ Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/cctv-anomaly-detection.git
    cd cctv-anomaly-detection
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: This includes `ultralytics`, `fastapi`, `openvino`, and other core libraries.*

---

## 🚀 Usage

1.  **Start the Application**
    ```bash
    python app.py
    ```
    *First run will automatically download the YOLO model and export it to OpenVINO format (takes ~1-2 mins).*

2.  **Access the Dashboard**
    Open your browser and navigate to:
    `http://localhost:8000`

3.  **Analyze Video**
    -   Go to the "Analyze" tab.
    -   Upload a video file (MP4, AVI, etc.).
    -   Set your **Crowd Threshold** (e.g., 5 people).
    -   Click **Start Analysis**.

4.  **Live Stream**
    -   Go to the "Live Stream" tab.
    -   Select "Webcam" or enter an RTSP URL.
    -   Click "Start Monitoring".

---

## ⚙️ Configuration

### Email Alerts
To enable email alerts, create or update `email_config.json` in the root directory:

```json
{
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your-email@gmail.com",
    "sender_password": "your-app-password",
    "receiver_emails": ["admin@example.com"]
}
```
*Note: For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833), not your login password.*

---

## 📁 Project Structure

```
├── app.py                 # FastAPI backend entry point
├── requirements.txt       # Python dependencies
├── email_config.json      # Email alert configuration
├── src/
│   ├── detection/         # YOLO & OpenVINO detection logic
│   ├── storage/           # SQLite database management
│   └── alerts/            # Email alert system
├── static/
│   ├── style.css          # Modern Dark UI styles
│   └── videos/            # Processed output videos
└── templates/             # HTML Frontend
    ├── index.html         # Main dashboard
    └── live.html          # Live stream monitor
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.