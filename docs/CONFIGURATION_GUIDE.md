# Configuration Guide

## CCTV Video Anomaly Detection System Configuration

**Version**: 3.0.0  
**Last Updated**: March 3, 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Environment Variables](#environment-variables)
3. [Configuration Files](#configuration-files)
4. [Model Configuration](#model-configuration)
5. [Detection Parameters](#detection-parameters)
6. [Email Alerts](#email-alerts)
7. [Database Configuration](#database-configuration)
8. [Performance Tuning](#performance-tuning)
9. [Network Configuration](#network-configuration)
10. [Logging Configuration](#logging-configuration)

---

## Overview

The system can be configured through:
1. **Environment Variables** (`.env` file)
2. **Configuration Files** (JSON)
3. **Command-line Arguments**
4. **Code-level Settings** (advanced)

---

## Environment Variables

### Creating .env File

Create a `.env` file in the project root directory:

```bash
touch .env
```

### Available Environment Variables

```bash
# ============================================
# MODEL CONFIGURATION
# ============================================

# Model size: n (nano), s (small), m (medium), l (large), x (extra large)
# Smaller = faster, less accurate | Larger = slower, more accurate
MODEL_SIZE=s

# Device: cpu, cuda, mps (Mac M1/M2)
DEVICE=cpu

# Detection confidence threshold (0.0 - 1.0)
CONFIDENCE_THRESHOLD=0.5

# ============================================
# ANOMALY DETECTION THRESHOLDS
# ============================================

# Number of people to trigger crowd alert
CROWD_THRESHOLD=5

# Loitering duration in seconds
LOITER_THRESHOLD=10.0

# Fast movement threshold (pixels per frame)
FAST_MOVEMENT_THRESHOLD=50.0

# Conflict proximity threshold (meters)
CONFLICT_PROXIMITY=0.5

# ============================================
# SERVER CONFIGURATION
# ============================================

# Server host (0.0.0.0 for all interfaces)
HOST=0.0.0.0

# Server port
PORT=8000

# Enable debug mode (true/false)
DEBUG=false

# Enable auto-reload on code changes
RELOAD=false

# Number of worker processes
WORKERS=1

# ============================================
# DATABASE CONFIGURATION
# ============================================

# Database path
DATABASE_PATH=./cctv_database.db

# Enable database logging
DB_LOGGING=false

# ============================================
# VIDEO PROCESSING
# ============================================

# Maximum video file size (MB)
MAX_FILE_SIZE=500

# Frame skip (process every Nth frame, 1 = no skip)
FRAME_SKIP=1

# Output video quality (0-100)
OUTPUT_QUALITY=85

# Enable video output saving
SAVE_OUTPUT_VIDEO=true

# ============================================
# LOGGING
# ============================================

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Log file path
LOG_FILE=./logs/app.log

# Enable console logging
CONSOLE_LOGGING=true

# ============================================
# EMAIL ALERTS
# ============================================

# Enable email alerts
ENABLE_EMAIL_ALERTS=true

# Email configuration file path
EMAIL_CONFIG_PATH=./email_config.json

# Only send alerts for critical anomalies
CRITICAL_ALERTS_ONLY=false

# ============================================
# SECURITY
# ============================================

# API key for authentication (optional, future feature)
# API_KEY=your-secret-key

# Enable CORS (true/false)
ENABLE_CORS=true

# Allowed origins (comma-separated)
CORS_ORIGINS=*

# ============================================
# OPENVINO OPTIMIZATION
# ============================================

# Enable OpenVINO optimization
USE_OPENVINO=true

# OpenVINO device (CPU, GPU, MYRIAD)
OPENVINO_DEVICE=CPU

# Number of inference requests
OPENVINO_NUM_REQUESTS=1

# ============================================
# CACHE AND STORAGE
# ============================================

# Enable model caching
CACHE_MODELS=true

# Cache directory
CACHE_DIR=./.cache

# Temporary files directory
TEMP_DIR=./temp

# Maximum number of stored videos
MAX_STORED_VIDEOS=100

# Auto-delete videos older than (days)
AUTO_DELETE_DAYS=30
```

### Example .env File

**For Development**:
```bash
MODEL_SIZE=n
DEVICE=cpu
DEBUG=true
RELOAD=true
LOG_LEVEL=DEBUG
ENABLE_EMAIL_ALERTS=false
```

**For Production**:
```bash
MODEL_SIZE=s
DEVICE=cpu
DEBUG=false
RELOAD=false
LOG_LEVEL=INFO
ENABLE_EMAIL_ALERTS=true
HOST=0.0.0.0
PORT=8000
USE_OPENVINO=true
```

**For High-Performance GPU Server**:
```bash
MODEL_SIZE=m
DEVICE=cuda
CONFIDENCE_THRESHOLD=0.6
USE_OPENVINO=false
WORKERS=4
MAX_FILE_SIZE=1000
```

---

## Configuration Files

### 1. Email Configuration

**File**: `email_config.json`

```json
{
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "sender_email": "security@company.com",
  "sender_password": "app-password-here",
  "receiver_emails": [
    "security-team@company.com",
    "operations@company.com"
  ],
  "enable_tls": true,
  "timeout": 30
}
```

**SMTP Providers**:

**Gmail**:
```json
{
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587
}
```

**Outlook/Office 365**:
```json
{
  "smtp_server": "smtp.office365.com",
  "smtp_port": 587
}
```

**Yahoo Mail**:
```json
{
  "smtp_server": "smtp.mail.yahoo.com",
  "smtp_port": 587
}
```

**Custom SMTP**:
```json
{
  "smtp_server": "mail.yourcompany.com",
  "smtp_port": 465,
  "enable_tls": false,
  "enable_ssl": true
}
```

### 2. Camera Configuration (Future Feature)

**File**: `cameras_config.json`

```json
{
  "cameras": [
    {
      "id": "cam01",
      "name": "Main Entrance",
      "rtsp_url": "rtsp://admin:pass@192.168.1.100:554/stream1",
      "enabled": true,
      "crowd_threshold": 5,
      "detect_weapons": true,
      "detect_loitering": true,
      "fps": 15
    },
    {
      "id": "cam02",
      "name": "Parking Lot",
      "rtsp_url": "rtsp://admin:pass@192.168.1.101:554/stream1",
      "enabled": true,
      "crowd_threshold": 10,
      "detect_vehicles": true,
      "fps": 10
    }
  ]
}
```

### 3. Zone Configuration (Future Feature)

**File**: `zones_config.json`

```json
{
  "zones": [
    {
      "zone_id": "entrance_zone",
      "camera_id": "cam01",
      "polygon": [[100, 200], [400, 200], [400, 500], [100, 500]],
      "rules": {
        "crowd_threshold": 3,
        "loiter_threshold": 5.0,
        "alert_on_entry": false
      }
    },
    {
      "zone_id": "restricted_zone",
      "camera_id": "cam01",
      "polygon": [[500, 300], [700, 300], [700, 600], [500, 600]],
      "rules": {
        "alert_on_entry": true,
        "allowed_time": "09:00-17:00"
      }
    }
  ]
}
```

---

## Model Configuration

### Choosing YOLO Model Size

| Model | Speed | Accuracy | Use Case |
|-------|-------|----------|----------|
| yolo11n | ⚡⚡⚡⚡⚡ | ⭐⭐ | Testing, low-end hardware |
| yolo11s | ⚡⚡⚡⚡ | ⭐⭐⭐ | Production, balanced |
| yolo11m | ⚡⚡⚡ | ⭐⭐⭐⭐ | High accuracy needs |
| yolo11l | ⚡⚡ | ⭐⭐⭐⭐⭐ | GPU servers |
| yolo11x | ⚡ | ⭐⭐⭐⭐⭐ | Maximum accuracy |

**Recommendation**:
- **Raspberry Pi**: yolo11n
- **Standard PC**: yolo11s
- **Server**: yolo11m
- **GPU Server**: yolo11l or yolo11x

### Model Download

Models are auto-downloaded on first run. Manual download:

```bash
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolo11s.pt
```

### Custom Trained Models

To use your own trained model:

1. **Place Model File**:
   ```bash
   cp my_custom_model.pt /path/to/project/
   ```

2. **Update Code** (`src/detection/yolo_detector.py`):
   ```python
   model_path = "my_custom_model.pt"
   ```

3. **Configure Classes**:
   ```python
   CUSTOM_CLASSES = {
       0: "person",
       1: "vehicle",
       2: "custom_object"
   }
   ```

---

## Detection Parameters

### Confidence Threshold

Controls minimum confidence for detections.

**Low Confidence (0.3 - 0.5)**:
- ✅ Detects more objects
- ❌ More false positives
- 📍 Use for: Critical security areas

**Medium Confidence (0.5 - 0.7)**:
- ✅ Balanced performance
- ✅ Recommended for most cases
- 📍 Use for: General surveillance

**High Confidence (0.7 - 0.9)**:
- ✅ Fewer false positives
- ❌ May miss some detections
- 📍 Use for: High-traffic areas

### IoU Threshold

Intersection over Union for Non-Maximum Suppression.

```python
# In yolo_detector.py
self.iou_threshold = 0.45  # Default
```

**Lower (0.3 - 0.4)**: Separate overlapping objects better  
**Higher (0.5 - 0.7)**: Merge similar detections

### Anomaly Thresholds

#### Crowd Threshold
```bash
CROWD_THRESHOLD=5
```

**Guidelines**:
- Small rooms: 3-5
- Offices: 5-10
- Hallways: 3-7
- Plazas: 10-20
- Stadiums: 50-100

#### Loitering Threshold
```bash
LOITER_THRESHOLD=10.0  # seconds
```

**Guidelines**:
- High security: 5-10 seconds
- Normal areas: 10-20 seconds
- Waiting areas: 30-60 seconds

#### Fast Movement Threshold
```bash
FAST_MOVEMENT_THRESHOLD=50.0  # pixels per frame
```

**Calculation**:
```
threshold = (expected_speed_m/s) * (pixels_per_meter) / fps
```

Example for 15 FPS, 100 pixels/meter, detect running (5 m/s):
```
threshold = 5 * 100 / 15 = 33 pixels/frame
```

---

## Email Alerts

### Configuration

**Enable/Disable**:
```bash
ENABLE_EMAIL_ALERTS=true
```

**Alert Triggers**:

Edit `src/alerts/email_alerts.py`:

```python
def should_send_alert(anomaly_types):
    """Determine if alert should be sent"""
    
    # Always alert on weapons
    if "weapon" in anomaly_types:
        return True
    
    # Alert on high anomaly count
    if len(anomaly_types) > 5:
        return True
    
    # Don't alert on minor issues
    if anomaly_types == ["loitering"]:
        return False
    
    return True
```

### Email Template Customization

**File**: `src/alerts/email_alerts.py`

```python
def create_email_body(anomalies, details):
    """Customize email content"""
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .alert {{ background-color: #ffebee; padding: 20px; }}
            .critical {{ color: #d32f2f; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="alert">
            <h2 class="critical">🚨 Security Alert</h2>
            <p>Anomalies detected in surveillance footage:</p>
            <ul>
                {''.join([f'<li>{a}</li>' for a in anomalies])}
            </ul>
            <h3>Details:</h3>
            <ul>
                {''.join([f'<li>{d}</li>' for d in details])}
            </ul>
            <p>Please review immediately.</p>
        </div>
    </body>
    </html>
    """
    return html
```

### Multiple Recipients

**Role-based Routing**:

```python
def get_recipients(anomaly_types):
    """Route alerts to appropriate personnel"""
    
    recipients = ["security@company.com"]
    
    if "weapon" in anomaly_types:
        recipients.append("police@company.com")
        recipients.append("director@company.com")
    
    if "crowd" in anomaly_types:
        recipients.append("operations@company.com")
    
    return recipients
```

---

## Database Configuration

### SQLite (Default)

**Configuration**:
```bash
DATABASE_PATH=./cctv_database.db
```

**Backup**:
```bash
# Backup database
cp cctv_database.db cctv_database_backup_$(date +%Y%m%d).db

# Automated backup (cron)
0 2 * * * cp /path/to/cctv_database.db /backup/cctv_db_$(date +\%Y\%m\%d).db
```

### PostgreSQL (Future)

**Configuration** (`.env`):
```bash
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cctv_detection
DB_USER=cctv_user
DB_PASSWORD=secure_password
```

**Connection String**:
```python
from sqlalchemy import create_engine

engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
```

### Database Maintenance

**Cleanup Old Records**:
```python
# In database.py
def cleanup_old_videos(days=30):
    """Delete videos older than N days"""
    cutoff_date = datetime.now() - timedelta(days=days)
    cursor.execute(
        "DELETE FROM videos WHERE timestamp < ?",
        (cutoff_date,)
    )
```

**Run Cleanup**:
```bash
# Add to cron
0 3 * * 0 python -c "from src.storage.database import cleanup_old_videos; cleanup_old_videos(30)"
```

---

## Performance Tuning

### CPU Optimization

```bash
# Use OpenVINO
USE_OPENVINO=true
OPENVINO_DEVICE=CPU

# Smaller model
MODEL_SIZE=s

# Frame skipping
FRAME_SKIP=2  # Process every 2nd frame

# Reduce workers
WORKERS=1
```

### GPU Acceleration

```bash
# Enable CUDA
DEVICE=cuda

# Use larger model
MODEL_SIZE=m

# Disable OpenVINO
USE_OPENVINO=false
```

**Check GPU Usage**:
```bash
nvidia-smi -l 1
```

### Memory Optimization

```python
# In yolo_detector.py
def process_video(self, video_path, output_path):
    # Release memory after each batch
    import gc
    
    for frame in video:
        # Process frame
        pass
        
        if frame_count % 100 == 0:
            gc.collect()
```

### Batch Processing

Process multiple videos overnight:

```bash
#!/bin/bash
# batch_process.sh

for video in /videos/*.mp4; do
    curl -X POST \
        -F "file=@$video" \
        -F "crowd_threshold=5" \
        http://localhost:8000/api/analyze
    
    # Wait for completion
    sleep 60
done
```

---

## Network Configuration

### Firewall Rules

**Allow Incoming**:
```bash
# UFW (Ubuntu)
sudo ufw allow 8000/tcp

# iptables
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
```

**Restrict to Local Network**:
```bash
sudo ufw allow from 192.168.1.0/24 to any port 8000
```

### Reverse Proxy (Nginx)

**Configuration** (`/etc/nginx/sites-available/cctv`):

```nginx
server {
    listen 80;
    server_name cctv.company.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # For SSE (live stream)
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_cache off;
    }
    
    # Upload limit
    client_max_body_size 500M;
}
```

**Enable**:
```bash
sudo ln -s /etc/nginx/sites-available/cctv /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL/TLS (HTTPS)

**Using Let's Encrypt**:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d cctv.company.com
```

**Update Nginx**:
```nginx
server {
    listen 443 ssl;
    server_name cctv.company.com;
    
    ssl_certificate /etc/letsencrypt/live/cctv.company.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cctv.company.com/privkey.pem;
    
    # ... rest of config
}
```

---

## Logging Configuration

### Log Levels

```bash
LOG_LEVEL=INFO
```

**DEBUG**: Detailed information, typically of interest only when diagnosing problems  
**INFO**: Confirmation that things are working as expected  
**WARNING**: Indication that something unexpected happened  
**ERROR**: More serious problem, software unable to perform function  
**CRITICAL**: Serious error, program may not be able to continue

### Log Format

**Edit** `app.py`:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
```

### Log Rotation

**Using logrotate** (`/etc/logrotate.d/cctv`):

```
/path/to/project/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 user user
    sharedscripts
    postrotate
        systemctl reload cctv-detection
    endscript
}
```

### Centralized Logging

**Using Syslog**:

```python
import logging
from logging.handlers import SysLogHandler

syslog_handler = SysLogHandler(address='/dev/log')
logger.addHandler(syslog_handler)
```

---

## Conclusion

This configuration guide covers all major configuration aspects. For specific use cases:

- **Development**: Use `.env` with DEBUG=true
- **Production**: Lock down security, enable monitoring
- **High-Performance**: GPU, larger models, optimized settings

**Next Steps**:
- Review [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for production setup
- See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for code-level configuration
- Check [MAINTENANCE_GUIDE.md](MAINTENANCE_GUIDE.md) for ongoing management

---

*Last Updated: March 3, 2026*  
*Version: 3.0.0*
