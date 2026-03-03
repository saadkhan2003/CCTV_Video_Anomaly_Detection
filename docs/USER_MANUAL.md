# User Manual

## CCTV Video Anomaly Detection System

**Version**: 3.0.0  
**Last Updated**: March 3, 2026

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Dashboard Overview](#dashboard-overview)
4. [Video Analysis](#video-analysis)
5. [Live Stream Monitoring](#live-stream-monitoring)
6. [Understanding Results](#understanding-results)
7. [Managing Videos](#managing-videos)
8. [Alert Configuration](#alert-configuration)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)
11. [FAQ](#faq)

---

## Introduction

### What is the CCTV Video Anomaly Detection System?

The CCTV Video Anomaly Detection System is an AI-powered surveillance tool that automatically identifies unusual or suspicious activities in video footage. It uses advanced computer vision (YOLOv11) to detect:

- **People and Crowds**: Alerts when too many people gather
- **Weapons**: Detects knives, baseball bats, scissors
- **Loitering**: Identifies people staying in one spot too long
- **Fast Movement**: Detects running or panic situations
- **Conflicts**: Flags groups in close proximity (potential fights)
- **Vehicles**: Traffic congestion or vehicles in pedestrian areas

### Key Benefits

✅ **Automated Monitoring**: Reduces manual video review time by 90%  
✅ **Real-time Alerts**: Instant email notifications for critical events  
✅ **Fast Processing**: Optimized with OpenVINO for CPU inference  
✅ **Easy to Use**: Web-based interface, no technical skills required  
✅ **Cost-effective**: Runs on standard hardware without GPU

---

## Getting Started

### System Requirements

**Minimum**:
- Intel i5 or AMD Ryzen 5
- 8 GB RAM
- 10 GB free disk space
- Ubuntu 22.04 / Windows 10 / macOS 12+

**Recommended**:
- Intel i7 or AMD Ryzen 7
- 16 GB RAM
- 50 GB SSD storage
- GPU (optional, for faster processing)

### First Launch

1. **Start the Application**
   ```bash
   python app.py
   ```
   
2. **Wait for Model Loading**
   - First launch downloads YOLO model (~50MB)
   - Converts to OpenVINO format (~1-2 minutes)
   - You'll see: "Model loaded successfully"

3. **Open Dashboard**
   - Open browser: `http://localhost:8000`
   - Dashboard should appear with dark theme

### Initial Setup Checklist

- [ ] Application starts without errors
- [ ] Dashboard opens in browser
- [ ] Can upload a test video
- [ ] Email alerts configured (optional)
- [ ] Live stream source tested (if using cameras)

---

## Dashboard Overview

### Main Interface

The dashboard has three main tabs:

```
┌─────────────────────────────────────────┐
│  🏠 Dashboard  |  📹 Analyze  |  🎥 Live │
├─────────────────────────────────────────┤
│                                         │
│  [Content Area]                         │
│                                         │
│  Statistics, Videos, or Live Stream     │
│                                         │
└─────────────────────────────────────────┘
```

### 1. Dashboard Tab (Statistics)

Shows overview of all analyzed videos:

- **Total Videos Processed**: Count of videos analyzed
- **Total Anomalies Detected**: Number of anomalous frames
- **Average Processing Speed**: Frames per second
- **Recent Activity**: Timeline of latest analyses

### 2. Analyze Tab (Video Upload)

Upload and analyze pre-recorded videos:

- Drag & drop or click to select video
- Set crowd threshold (default: 5 people)
- Adjust confidence level (default: 60%)
- View real-time progress bar
- Download annotated video

### 3. Live Tab (Real-time Monitoring)

Monitor live camera feeds:

- Select webcam or enter RTSP URL
- Real-time anomaly detection
- Instant alerts on screen
- FPS and object count display

---

## Video Analysis

### Step-by-Step: Analyzing a Video

#### Step 1: Navigate to Analyze Tab

Click **"Analyze"** in the top navigation.

#### Step 2: Upload Video

**Option A: Drag & Drop**
- Drag video file into the upload area
- Supported formats: MP4, AVI, MOV, MKV

**Option B: Click to Browse**
- Click "Choose File" button
- Navigate to video location
- Select and open

#### Step 3: Configure Settings

**Crowd Threshold** (Default: 5)
- Number of people to trigger crowd alert
- Example: Set to 3 for small indoor spaces, 10 for large plazas

**Confidence** (Default: 0.6)
- Detection confidence level (0.0 - 1.0)
- Higher = fewer false positives, might miss some detections
- Lower = more detections, might have false positives
- Recommended: 0.5 - 0.7

#### Step 4: Start Analysis

Click **"Start Analysis"** button.

#### Step 5: Monitor Progress

- Progress bar shows completion percentage
- Estimated time remaining displayed
- Can navigate away and return later

#### Step 6: View Results

When complete:
- **Statistics Summary**:
  - Total frames processed
  - Anomaly frames detected
  - Anomaly rate percentage
  - Processing time

- **Anomaly Breakdown**:
  - Crowd events: X occurrences
  - Weapon detections: X occurrences
  - Loitering incidents: X occurrences
  - Fast movement: X occurrences

- **Output Video**:
  - Annotated video with bounding boxes
  - Frame numbers marked
  - Timestamp overlay

#### Step 7: Download or Share

- **Download Video**: Click download button
- **Share Link**: Copy video ID for reference
- **Export Report**: (Future feature)

### Example Use Cases

#### Security Camera Review
```
Scenario: Review 8 hours of night security footage
Settings: Crowd Threshold = 3, Confidence = 0.6
Result: 45 anomalies found in 28,800 frames (0.16% anomaly rate)
Time Saved: Instead of 8 hours, review only 3 minutes of flagged events
```

#### Event Monitoring
```
Scenario: Analyze concert crowd for safety concerns
Settings: Crowd Threshold = 20, Confidence = 0.7
Result: 120 crowd alerts, 5 fast movement events
Action: Security dispatched to high-density areas
```

---

## Live Stream Monitoring

### Webcam Monitoring

#### Step 1: Select Source
1. Go to **Live** tab
2. Select **"Webcam"** from dropdown
3. Click **"Start Monitoring"**

#### Step 2: View Stream
- Live video feed appears
- Bounding boxes around detected objects
- Real-time FPS counter
- People and vehicle counts

#### Step 3: Monitor Alerts
Anomalies appear as:
- 🚨 Red border flashing
- Alert message: "ANOMALY: Crowd Detected"
- Timestamp and details

#### Step 4: Stop Monitoring
- Click **"Stop"** button
- Stream ends gracefully

### IP Camera (RTSP) Monitoring

#### Step 1: Get Camera RTSP URL

Most IP cameras use this format:
```
rtsp://[username]:[password]@[ip-address]:[port]/[stream-path]
```

**Common Examples**:

**Hikvision**:
```
rtsp://admin:password123@192.168.1.100:554/Streaming/Channels/101
```

**Dahua**:
```
rtsp://admin:password123@192.168.1.101:554/cam/realmonitor?channel=1&subtype=0
```

**Reolink**:
```
rtsp://admin:password123@192.168.1.102:554/h264Preview_01_main
```

**Generic**:
```
rtsp://admin:password123@192.168.1.103:554/stream1
```

#### Step 2: Configure Camera in System
1. Go to **Live** tab
2. Select **"RTSP Stream"**
3. Enter RTSP URL
4. Set crowd threshold
5. Click **"Start Monitoring"**

#### Step 3: Troubleshooting Camera Connection

**Camera not connecting?**

✅ **Check network connection**:
```bash
ping 192.168.1.100
```

✅ **Test RTSP URL with VLC**:
- Open VLC Media Player
- Media → Open Network Stream
- Paste RTSP URL
- If VLC can't play, URL is incorrect

✅ **Verify credentials**:
- Check username and password
- Some cameras require enabling RTSP in settings

✅ **Check firewall**:
- Ensure port 554 is open
- Disable firewall temporarily to test

✅ **Check camera settings**:
- Enable RTSP in camera web interface
- Set authentication to basic (not digest)

### Multi-Camera Setup (Future Enhancement)

Current version supports **one stream at a time**.

For multiple cameras:
- Run multiple instances on different ports
- Or wait for multi-stream support in v4.0

---

## Understanding Results

### Anomaly Types Explained

#### 1. Crowd Detection
**Trigger**: More people than threshold in one frame

**Example**:
```
Frame 1250: [CROWD] 8 people detected (threshold: 5)
Location: Main entrance
```

**What to do**:
- Check if it's normal (e.g., shift change)
- Dispatch security if unusual time/location

#### 2. Weapon Detection
**Trigger**: Knife, baseball bat, or scissors detected

**Example**:
```
Frame 3450: [WEAPON] Knife detected
Person ID: 7
Confidence: 0.87
```

**What to do**:
- ⚠️ High priority - review immediately
- Contact authorities if verified
- Note: Kitchen areas may trigger false positives

#### 3. Loitering
**Trigger**: Person stays in one spot > 10 seconds

**Example**:
```
Frame 5200-5800: [LOITERING] Person ID 3
Duration: 20 seconds
Location: Near exit door
```

**What to do**:
- Check if person needs assistance
- Verify not waiting for someone
- Monitor if behavior is suspicious

#### 4. Fast Movement
**Trigger**: Rapid displacement between frames

**Example**:
```
Frame 7100: [FAST_MOVEMENT] Person ID 5
Speed: 8.5 m/s (estimated running)
Direction: Towards exit
```

**What to do**:
- Check for emergency situation
- Look for pursuit or panic
- Could be normal (e.g., late for class)

#### 5. Potential Conflict
**Trigger**: Multiple people very close together

**Example**:
```
Frame 9000: [CONFLICT] 3 people within 0.5m radius
Group coherence: High
```

**What to do**:
- Check body language
- Monitor for escalation
- Position security nearby

### Interpreting Anomaly Rates

**Anomaly Rate = (Anomalous Frames / Total Frames) × 100**

| Rate | Interpretation | Action |
|------|---------------|--------|
| 0-1% | Normal activity | Routine review |
| 1-5% | Moderate activity | Review highlights |
| 5-10% | High activity | Detailed review needed |
| >10% | Very high activity or misconfiguration | Check threshold settings |

### False Positives

Common false positives:

❌ **Crowd**: People naturally gathering (bus stop, cafeteria)  
**Solution**: Increase crowd threshold for that area

❌ **Weapon**: Tools, umbrellas, sports equipment  
**Solution**: Adjust confidence or exclude specific zones

❌ **Loitering**: Security guard, receptionist at desk  
**Solution**: Increase loiter threshold or use zone exclusions (future feature)

❌ **Fast Movement**: Children playing, athletes training  
**Solution**: Context-aware zones (future feature)

---

## Managing Videos

### Viewing Video History

1. Go to **Dashboard** tab
2. Scroll to **"Recent Videos"** section
3. See list of all analyzed videos

**Information Displayed**:
- Filename
- Date/Time processed
- Anomaly count
- Anomaly rate
- Processing time

### Searching Videos

**By Name**:
```
Search box: "lobby_cam"
Results: All videos with "lobby_cam" in filename
```

**By Date**:
```
Date range: 2026-03-01 to 2026-03-03
Results: Videos processed in that period
```

### Downloading Results

**Download Annotated Video**:
1. Click video entry
2. Click **"Download Video"** button
3. MP4 file saved to Downloads folder

**Export Data** (Future):
- CSV of frame-by-frame results
- JSON report for integration

### Deleting Videos

1. Click video entry
2. Click **"Delete"** button
3. Confirm deletion
4. Video and database entry removed

⚠️ **Warning**: Deletion is permanent!

---

## Alert Configuration

### Email Alerts

Enable email notifications for high-priority anomalies.

#### Step 1: Create Configuration File

Create `email_config.json` in project root:

```json
{
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "sender_email": "security-system@company.com",
  "sender_password": "your-app-password",
  "receiver_emails": [
    "security-head@company.com",
    "operations@company.com"
  ]
}
```

#### Step 2: Set Up Gmail App Password

For Gmail:
1. Go to Google Account settings
2. Security → 2-Step Verification
3. App Passwords → Generate
4. Copy 16-character password
5. Use in `email_config.json`

#### Step 3: Test Email

Run test command:
```bash
python -c "from src.alerts.email_alerts import send_anomaly_alert; send_anomaly_alert(['test'], ['Test alert'])"
```

#### Step 4: Configure Alert Triggers

Emails are sent when:
- Video analysis completes with anomalies
- Weapon detection occurs
- Anomaly rate > 10% (future configurable)

### Alert Content

Email includes:
- Subject: "🚨 Anomaly Alert: [Video Name]"
- Anomaly types detected
- Frame counts
- Anomaly rate percentage
- Link to view video (if accessible)

### Customizing Alerts

Edit `src/alerts/email_alerts.py` to customize:
- Email template
- Trigger conditions
- Recipient rules (e.g., weapon alerts to police)

---

## Troubleshooting

### Common Issues

#### 1. Application Won't Start

**Error**: `ModuleNotFoundError: No module named 'ultralytics'`

**Solution**:
```bash
pip install -r requirements.txt
```

---

**Error**: `Port 8000 already in use`

**Solution**:
```bash
# Find and kill process on port 8000
sudo lsof -i :8000
kill -9 <PID>

# Or use different port
python app.py --port 8080
```

---

#### 2. Model Not Loading

**Error**: `Failed to download YOLO model`

**Solution**:
- Check internet connection
- Download manually: https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov11s.pt
- Place in project root directory

---

**Error**: `OpenVINO conversion failed`

**Solution**:
```bash
pip install --upgrade openvino
```

---

#### 3. Video Upload Fails

**Error**: `File format not supported`

**Solution**:
- Supported: MP4, AVI, MOV, MKV
- Convert video using:
```bash
ffmpeg -i input.webm -c:v libx264 output.mp4
```

---

**Error**: `Video too large`

**Solution**:
- Max file size: 500 MB (default)
- Compress video or split into parts

---

#### 4. Live Stream Not Working

**Error**: `Cannot connect to camera`

**Solution**:
1. Test RTSP URL in VLC
2. Check camera IP and port
3. Verify username/password
4. Ensure camera RTSP is enabled
5. Check network connectivity

---

**Error**: `Stream lags or freezes`

**Solution**:
- Reduce video resolution on camera
- Use "sub-stream" instead of "main-stream"
- Close other applications
- Upgrade CPU/RAM

---

#### 5. Poor Detection Accuracy

**Problem**: Missing people or vehicles

**Solution**:
- Lower confidence threshold (0.5 → 0.4)
- Ensure good lighting in video
- Use higher resolution camera
- Update to latest YOLO model

---

**Problem**: Too many false positives

**Solution**:
- Increase confidence threshold (0.6 → 0.7)
- Adjust crowd threshold
- Check for reflections or shadows

---

#### 6. Slow Processing

**Problem**: Video analysis taking too long

**Solution**:
- Ensure OpenVINO is installed
- Close other applications
- Use smaller YOLO model (yolo11n instead of yolo11m)
- Skip frames (future feature)

---

### Getting Help

**Check Logs**:
```bash
tail -f logs/app.log
```

**Enable Debug Mode**:
```python
# In app.py
logging.basicConfig(level=logging.DEBUG)
```

**Contact Support**:
- GitHub Issues: [repository-link]
- Email: support@company.com
- Documentation: `/docs` folder

---

## Best Practices

### Video Quality

✅ **Resolution**: Minimum 720p (1080p recommended)  
✅ **Frame Rate**: 15-30 FPS  
✅ **Lighting**: Ensure adequate lighting  
✅ **Angle**: Mount cameras at 10-15° downward angle  
✅ **Compression**: Use H.264 codec

### Threshold Tuning

**Start Conservative**:
- Crowd: 5 people
- Confidence: 0.6
- Loiter: 10 seconds

**Adjust Based on Results**:
- Too many alerts → Increase thresholds
- Missing events → Decrease thresholds

**Location-Specific Settings**:
- Entrance: Lower crowd threshold (3)
- Plaza: Higher crowd threshold (15)
- Parking: Focus on vehicles
- Corridors: Focus on loitering

### Performance Optimization

🚀 **Use OpenVINO**: 2-3x speedup on CPU  
🚀 **Smaller Models**: yolo11s vs yolo11m (faster but less accurate)  
🚀 **Frame Skipping**: Process every 2nd frame for 2x speed  
🚀 **Batch Processing**: Analyze videos overnight  
🚀 **Dedicated Hardware**: No other applications running

### Security Considerations

🔒 **Change Default Passwords**: Camera credentials  
🔒 **Network Segmentation**: Cameras on separate VLAN  
🔒 **HTTPS**: Enable for production (future)  
🔒 **Authentication**: Add user login (future)  
🔒 **Data Retention**: Delete old videos regularly  
🔒 **Backup**: Backup database weekly

---

## FAQ

### General Questions

**Q: Does this system record video?**  
A: It processes video but doesn't record by default. Analyzed videos are saved if you choose "Save Output Video".

**Q: Can I use this commercially?**  
A: Yes, MIT license allows commercial use. Check YOLOv11 license separately.

**Q: Does it work offline?**  
A: Yes, after initial model download. No internet required for analysis.

**Q: How accurate is the detection?**  
A: 85-95% accuracy on clear footage with good lighting. Accuracy varies by scenario.

**Q: What languages are supported?**  
A: Currently English only. UI internationalization planned for v4.0.

### Technical Questions

**Q: Can I run this on Raspberry Pi?**  
A: Technically yes, but very slow. Raspberry Pi 4 (8GB) recommended minimum.

**Q: GPU support?**  
A: Yes, automatically detected. NVIDIA GPUs with CUDA supported.

**Q: Can I train on custom objects?**  
A: Advanced users can fine-tune YOLO model. See Developer Guide.

**Q: API available?**  
A: Yes, REST API documented in API_DOCUMENTATION.md.

**Q: Database type?**  
A: SQLite (default). PostgreSQL support planned for v4.0.

### Deployment Questions

**Q: How many cameras can I monitor?**  
A: Depends on hardware. ~4 cameras per CPU core (estimate).

**Q: Cloud deployment?**  
A: Yes, see DEPLOYMENT_GUIDE.md for AWS/Azure instructions.

**Q: Docker support?**  
A: Yes, Dockerfile available (see Developer Guide).

**Q: Mobile app?**  
A: Not yet. Mobile-responsive web UI works on tablets/phones.

---

## Conclusion

This user manual covers the essential operations of the CCTV Video Anomaly Detection System. For advanced topics, see:

- **API Documentation**: `/docs/API_DOCUMENTATION.md`
- **Deployment Guide**: `/docs/DEPLOYMENT_GUIDE.md`
- **Developer Guide**: `/docs/DEVELOPER_GUIDE.md`
- **Configuration Guide**: `/docs/CONFIGURATION_GUIDE.md`

**Need Help?**  
Contact support or file an issue on GitHub.

**Enjoy secure, automated surveillance! 🎥🔒**

---

*Last Updated: March 3, 2026*  
*Version: 3.0.0*
