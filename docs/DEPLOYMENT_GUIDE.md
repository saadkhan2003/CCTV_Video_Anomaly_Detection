# CCTV Anomaly Detection System - Deployment Guide

## University Campus Installation

This guide covers permanent deployment of the AI-powered CCTV anomaly detection system for campus security.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CAMPUS NETWORK                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  [PoE Camera 1]──┐                                               │
│  [PoE Camera 2]──┼──► [PoE Switch] ──► [Server PC]               │
│  [PoE Camera 3]──┘                          │                    │
│                                             │                    │
│                    ┌────────────────────────┘                    │
│                    ▼                                              │
│             ┌─────────────┐                                      │
│             │  Detection  │──► Email Alerts to Security          │
│             │   Server    │                                      │
│             └─────────────┘                                      │
│                    │                                              │
│                    ▼                                              │
│             ┌─────────────┐                                      │
│             │    Web      │ ◄─── Campus Network Access           │
│             │  Dashboard  │                                      │
│             └─────────────┘                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Hardware Requirements

### Server PC
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | Intel i5 / Ryzen 5 | Intel i7 / Ryzen 7 |
| RAM | 8 GB | 16-32 GB |
| Storage | 256 GB SSD | 512 GB SSD + 2TB HDD |
| GPU | Not required | NVIDIA GTX 1650+ (faster processing) |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

### IP Cameras
| Type | Resolution | Features | Approx. Cost (PKR) |
|------|------------|----------|-------------------|
| Budget | 2MP (1080p) | Night vision, PoE | 8,000-12,000 |
| Standard | 4MP | Wide angle, PoE | 15,000-25,000 |
| Premium | 4K | AI features, PoE | 30,000-50,000 |

**Recommended Brands:** Hikvision, Dahua, Reolink, TP-Link

### Network Equipment
| Equipment | Purpose | Approx. Cost (PKR) |
|-----------|---------|-------------------|
| PoE Switch (8-port) | Power + data for cameras | 15,000-25,000 |
| PoE Switch (16-port) | Larger deployments | 25,000-40,000 |
| Cat6 Ethernet Cable | Camera connections | 50/meter |
| UPS (1500VA) | 24/7 uninterrupted power | 15,000-25,000 |

---

## 2. Network Configuration

### Camera Network Setup
1. Assign static IPs to all cameras (e.g., 192.168.10.101, 192.168.10.102...)
2. Configure RTSP credentials on each camera
3. Note down all RTSP URLs:
   ```
   rtsp://admin:password@192.168.10.101:554/stream1
   rtsp://admin:password@192.168.10.102:554/stream1
   ```

### Server Network Setup
1. Assign static IP to server (e.g., 192.168.10.10)
2. Configure firewall to allow port 8000 (or custom)
3. Ensure server is on same subnet as cameras

---

## 3. Software Installation

### Step 1: Install Python Environment
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+
sudo apt install python3.10 python3.10-venv python3-pip -y

# Install system dependencies
sudo apt install git ffmpeg libsm6 libxext6 -y
```

### Step 2: Clone and Setup Project
```bash
# Clone the repository
git clone https://github.com/your-repo/cctv-video-anomaly-detection.git
cd cctv-video-anomaly-detection

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Email Alerts
Edit or create `email_config.json`:
```json
{
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "security@university.edu",
    "sender_password": "app-password-here",
    "admin_emails": ["guard1@university.edu", "security-head@university.edu"]
}
```

---

## 4. Running as System Service

### Create Service File
```bash
sudo nano /etc/systemd/system/anomaly-detection.service
```

```ini
[Unit]
Description=CCTV Anomaly Detection System
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/cctv-video-anomaly-detection
Environment="PATH=/home/your-username/cctv-video-anomaly-detection/venv/bin"
ExecStart=/home/your-username/cctv-video-anomaly-detection/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable anomaly-detection

# Start service
sudo systemctl start anomaly-detection

# Check status
sudo systemctl status anomaly-detection

# View logs
journalctl -u anomaly-detection -f
```

---

## 5. Accessing the Dashboard

### From Campus Network
- **URL:** `http://SERVER-IP:8000`
- **Live Monitor:** `http://SERVER-IP:8000/live`

### Remote Access (Optional)
For remote access, set up:
1. VPN connection to campus network
2. Or configure reverse proxy with HTTPS

---

## 6. Adding Camera Streams

### In the Web Dashboard
1. Go to `http://SERVER-IP:8000/live`
2. Select **RTSP/IP Camera**
3. Enter camera URL: `rtsp://admin:password@CAMERA-IP:554/stream1`
4. Click **Start Stream**

### Multiple Cameras
For monitoring multiple cameras simultaneously, the system can be extended to support a multi-camera grid view.

---

## 7. Anomaly Detection Rules

The system detects:
| Anomaly Type | Trigger Condition |
|--------------|-------------------|
| CROWD_GATHERING | 3+ people in frame |
| POTENTIAL_CONFLICT | 2+ people within 150px |
| TRAFFIC_CONGESTION | 3+ vehicles |
| ACTIVITY_DETECTED | People near vehicles |

---

## 8. Security Recommendations

### Add Login Authentication
Protect the dashboard with password authentication.

### Enable HTTPS
Use SSL certificate for encrypted connections:
```bash
# Using Certbot for Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.edu
```

### Restrict Network Access
- Only allow campus network IPs
- Block external access or use VPN

### Regular Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python dependencies
pip install --upgrade -r requirements.txt
```

---

## 9. Maintenance

### Daily
- Check service status: `sudo systemctl status anomaly-detection`
- Review email alerts

### Weekly
- Check disk space for video recordings
- Review detection accuracy

### Monthly
- Update software packages
- Backup database: `cp anomaly_history.db anomaly_history_backup.db`
- Review and clean old recordings

---

## 10. Troubleshooting

| Issue | Solution |
|-------|----------|
| Camera not connecting | Check RTSP URL, credentials, network |
| Service not starting | Check logs: `journalctl -u anomaly-detection` |
| High CPU usage | Reduce video resolution or add GPU |
| Email not sending | Verify SMTP settings and app password |

---

## Contact & Support

For technical support, contact the system administrator or development team.

**Project:** CCTV Video Anomaly Detection System  
**Version:** 1.0  
**Last Updated:** December 2024
