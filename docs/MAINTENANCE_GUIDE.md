# Maintenance Guide

## CCTV Video Anomaly Detection System Maintenance Documentation

**Version**: 3.0.0  
**Last Updated**: March 3, 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Routine Maintenance](#routine-maintenance)
3. [System Monitoring](#system-monitoring)
4. [Database Maintenance](#database-maintenance)
5. [Model Updates](#model-updates)
6. [Backup and Recovery](#backup-and-recovery)
7. [Performance Optimization](#performance-optimization)
8. [Troubleshooting Common Issues](#troubleshooting-common-issues)
9. [Security Updates](#security-updates)
10. [Hardware Maintenance](#hardware-maintenance)

---

## Overview

### Maintenance Schedule

| Task | Frequency | Estimated Time | Priority |
|------|-----------|----------------|----------|
| Log review | Daily | 10 min | Medium |
| Database backup | Daily | 5 min | High |
| Disk space check | Daily | 5 min | High |
| System health check | Weekly | 15 min | Medium |
| Database optimization | Weekly | 30 min | Medium |
| Dependency updates | Monthly | 1 hour | Medium |
| Model updates | Quarterly | 2 hours | Low |
| Security audit | Quarterly | 3 hours | High |
| Full system backup | Monthly | 1 hour | High |

### Maintenance Contacts

| Role | Name | Contact | Responsibility |
|------|------|---------|---------------|
| System Admin | [Name] | admin@company.com | Infrastructure |
| Developer | [Name] | dev@company.com | Code issues |
| Security | [Name] | security@company.com | Security incidents |
| Database Admin | [Name] | dba@company.com | Database issues |

---

## Routine Maintenance

### Daily Tasks

#### 1. Check System Health

```bash
#!/bin/bash
# daily_health_check.sh

echo "=== CCTV System Health Check ==="
echo "Date: $(date)"

# Check if service is running
if systemctl is-active --quiet cctv-detection; then
    echo "✓ Service is running"
else
    echo "✗ Service is NOT running"
    systemctl start cctv-detection
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "✗ Warning: Disk usage at ${DISK_USAGE}%"
else
    echo "✓ Disk usage: ${DISK_USAGE}%"
fi

# Check memory usage
MEM_USAGE=$(free | grep Mem | awk '{print ($3/$2) * 100.0}' | cut -d. -f1)
if [ "$MEM_USAGE" -gt 90 ]; then
    echo "✗ Warning: Memory usage at ${MEM_USAGE}%"
else
    echo "✓ Memory usage: ${MEM_USAGE}%"
fi

# Check CPU load
CPU_LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
echo "ℹ CPU load: ${CPU_LOAD}"

# Check log errors
ERROR_COUNT=$(grep -i error /var/log/cctv/app.log | wc -l)
if [ "$ERROR_COUNT" -gt 10 ]; then
    echo "✗ Warning: ${ERROR_COUNT} errors in log"
else
    echo "✓ Errors in log: ${ERROR_COUNT}"
fi

echo "================================"
```

**Schedule with cron**:
```bash
# Edit crontab
crontab -e

# Add daily check at 9 AM
0 9 * * * /path/to/daily_health_check.sh | mail -s "Daily Health Report" admin@company.com
```

#### 2. Review Logs

```bash
# Check for errors
tail -n 100 /var/log/cctv/app.log | grep -i error

# Check recent activity
tail -n 50 /var/log/cctv/app.log

# Check anomaly alerts (if any)
grep "ANOMALY" /var/log/cctv/app.log | tail -n 20
```

#### 3. Backup Database

```bash
#!/bin/bash
# daily_backup.sh

BACKUP_DIR="/backup/cctv"
DB_PATH="/path/to/cctv_database.db"
DATE=$(date +%Y%m%d)

# Create backup
cp $DB_PATH $BACKUP_DIR/cctv_db_$DATE.db

# Compress backup
gzip $BACKUP_DIR/cctv_db_$DATE.db

# Keep only last 30 days
find $BACKUP_DIR -name "cctv_db_*.db.gz" -mtime +30 -delete

echo "Backup completed: cctv_db_$DATE.db.gz"
```

**Schedule**:
```bash
# Daily backup at 2 AM
0 2 * * * /path/to/daily_backup.sh
```

### Weekly Tasks

#### 1. Database Optimization

```bash
#!/bin/bash
# weekly_db_optimize.sh

echo "Optimizing database..."

sqlite3 /path/to/cctv_database.db <<EOF
-- Analyze tables for query optimization
ANALYZE;

-- Remove fragmentation
VACUUM;

-- Rebuild indexes
REINDEX;

-- Check integrity
PRAGMA integrity_check;
EOF

echo "Database optimization complete"
```

**Schedule**:
```bash
# Weekly on Sunday at 3 AM
0 3 * * 0 /path/to/weekly_db_optimize.sh
```

#### 2. Clean Temporary Files

```bash
#!/bin/bash
# cleanup_temp.sh

echo "Cleaning temporary files..."

# Remove old temp uploads (>7 days)
find /path/to/temp -type f -mtime +7 -delete

# Remove old processed videos (>30 days)
find /path/to/static/videos -type f -mtime +30 -delete

# Clear Python cache
find /path/to/project -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

echo "Cleanup complete"
```

#### 3. Check System Updates

```bash
# Check for system updates
sudo apt update
sudo apt list --upgradable

# Security updates only
sudo apt upgrade --security-only
```

### Monthly Tasks

#### 1. Update Dependencies

```bash
# Backup current environment
pip freeze > requirements_backup_$(date +%Y%m%d).txt

# Check for outdated packages
pip list --outdated

# Update specific packages
pip install --upgrade ultralytics fastapi uvicorn openvino

# Or update all
pip install --upgrade -r requirements.txt

# Test after update
pytest tests/
```

#### 2. Full System Backup

```bash
#!/bin/bash
# monthly_full_backup.sh

BACKUP_ROOT="/backup/full"
PROJECT_DIR="/path/to/cctv-project"
DATE=$(date +%Y%m)

# Create backup directory
mkdir -p $BACKUP_ROOT/$DATE

# Backup entire project
tar -czf $BACKUP_ROOT/$DATE/project.tar.gz \
    -C $(dirname $PROJECT_DIR) \
    $(basename $PROJECT_DIR)

# Backup system configuration
tar -czf $BACKUP_ROOT/$DATE/system_config.tar.gz \
    /etc/systemd/system/cctv-detection.service \
    /etc/nginx/sites-available/cctv

# Keep only last 6 months
find $BACKUP_ROOT -type d -mtime +180 -exec rm -rf {} + 2>/dev/null

echo "Full backup completed"
```

#### 3. Performance Review

```bash
# Analyze processing times
python << EOF
import sqlite3
import statistics

conn = sqlite3.connect('cctv_database.db')
cursor = conn.cursor()

cursor.execute('SELECT processing_time FROM videos WHERE timestamp > date("now", "-30 days")')
times = [row[0] for row in cursor.fetchall()]

if times:
    print(f"Average processing time: {statistics.mean(times):.2f}s")
    print(f"Median processing time: {statistics.median(times):.2f}s")
    print(f"Max processing time: {max(times):.2f}s")
else:
    print("No videos processed in last 30 days")

conn.close()
EOF
```

---

## System Monitoring

### Monitoring Tools

#### 1. Real-time Monitoring Dashboard

**Install htop**:
```bash
sudo apt install htop
htop
```

#### 2. System Resource Monitoring Script

```python
#!/usr/bin/env python3
# monitor.py

import psutil
import time
import logging

logging.basicConfig(
    filename='/var/log/cctv/monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

while True:
    # CPU Usage
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # Memory Usage
    memory = psutil.virtual_memory()
    mem_percent = memory.percent
    
    # Disk Usage
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent
    
    # Network I/O
    net_io = psutil.net_io_counters()
    
    # Log metrics
    logging.info(
        f"CPU: {cpu_percent}% | "
        f"Memory: {mem_percent}% | "
        f"Disk: {disk_percent}% | "
        f"Network: {net_io.bytes_sent}/{net_io.bytes_recv}"
    )
    
    # Alert if high usage
    if cpu_percent > 90:
        logging.warning(f"High CPU usage: {cpu_percent}%")
    
    if mem_percent > 90:
        logging.warning(f"High memory usage: {mem_percent}%")
    
    if disk_percent > 90:
        logging.warning(f"High disk usage: {disk_percent}%")
    
    time.sleep(60)  # Check every minute
```

**Run as systemd service**:

```ini
# /etc/systemd/system/cctv-monitor.service
[Unit]
Description=CCTV System Monitor
After=network.target

[Service]
Type=simple
User=cctv
ExecStart=/usr/bin/python3 /path/to/monitor.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable cctv-monitor
sudo systemctl start cctv-monitor
```

### Application Metrics

**Add to app.py**:

```python
from fastapi import FastAPI
from datetime import datetime
import psutil

app_metrics = {
    'start_time': datetime.now(),
    'requests_total': 0,
    'requests_failed': 0,
    'videos_processed': 0
}

@app.get("/api/metrics")
async def get_metrics():
    """Return application metrics"""
    uptime = (datetime.now() - app_metrics['start_time']).total_seconds()
    
    return {
        'uptime_seconds': uptime,
        'requests_total': app_metrics['requests_total'],
        'requests_failed': app_metrics['requests_failed'],
        'videos_processed': app_metrics['videos_processed'],
        'system': {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }
    }
```

---

## Database Maintenance

### Database Health Checks

```bash
#!/bin/bash
# db_health_check.sh

DB_PATH="/path/to/cctv_database.db"

echo "=== Database Health Check ==="

# Check database size
DB_SIZE=$(du -h $DB_PATH | cut -f1)
echo "Database size: $DB_SIZE"

# Count records
RECORD_COUNT=$(sqlite3 $DB_PATH "SELECT COUNT(*) FROM videos;")
echo "Total records: $RECORD_COUNT"

# Check for corruption
echo "Checking integrity..."
sqlite3 $DB_PATH "PRAGMA integrity_check;" | head -1

# Check index status
echo "Indexes:"
sqlite3 $DB_PATH "SELECT name, type FROM sqlite_master WHERE type='index';"

# Check table sizes
echo "Table sizes:"
sqlite3 $DB_PATH "SELECT 
    name, 
    (SELECT COUNT(*) FROM sqlite_master WHERE tbl_name=name) as objects
FROM sqlite_master 
WHERE type='table';"
```

### Archive Old Data

```python
#!/usr/bin/env python3
# archive_old_data.py

import sqlite3
from datetime import datetime, timedelta
import json

def archive_old_videos(db_path, archive_path, days=90):
    """
    Archive videos older than N days to separate database
    
    Args:
        db_path: Main database path
        archive_path: Archive database path
        days: Archive videos older than this
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Connect to both databases
    main_conn = sqlite3.connect(db_path)
    archive_conn = sqlite3.connect(archive_path)
    
    main_cursor = main_conn.cursor()
    archive_cursor = archive_conn.cursor()
    
    # Create archive table if not exists
    archive_cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY,
            filename TEXT,
            timestamp DATETIME,
            frame_count INTEGER,
            anomaly_count INTEGER,
            anomaly_rate REAL,
            processing_time REAL,
            threshold_used INTEGER,
            output_video_path TEXT
        )
    ''')
    
    # Find old records
    main_cursor.execute(
        'SELECT * FROM videos WHERE timestamp < ?',
        (cutoff_date,)
    )
    old_records = main_cursor.fetchall()
    
    print(f"Found {len(old_records)} records to archive")
    
    # Copy to archive
    for record in old_records:
        archive_cursor.execute(
            'INSERT INTO videos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            record
        )
    
    # Delete from main database
    main_cursor.execute(
        'DELETE FROM videos WHERE timestamp < ?',
        (cutoff_date,)
    )
    
    # Commit and close
    main_conn.commit()
    archive_conn.commit()
    main_conn.close()
    archive_conn.close()
    
    print(f"Archived {len(old_records)} records")

if __name__ == '__main__':
    archive_old_videos(
        'cctv_database.db',
        'archive/cctv_archive_2026.db',
        days=90
    )
```

---

## Model Updates

### Update YOLO Model

```bash
#!/bin/bash
# update_model.sh

echo "Updating YOLO model..."

# Backup current model
if [ -f "yolo11s.pt" ]; then
    mv yolo11s.pt yolo11s_backup_$(date +%Y%m%d).pt
fi

# Download latest model
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolo11s.pt

# Test new model
python << EOF
from ultralytics import YOLO
import numpy as np

# Load model
model = YOLO('yolo11s.pt')

# Test inference
test_img = np.zeros((640, 640, 3), dtype=np.uint8)
results = model(test_img)

print("Model loaded successfully")
EOF

# If test passes, export to OpenVINO
python << EOF
from ultralytics import YOLO

model = YOLO('yolo11s.pt')
model.export(format='openvino')
print("OpenVINO export complete")
EOF

echo "Model update complete"

# Restart service
sudo systemctl restart cctv-detection
```

### Model Performance Testing

```python
# test_new_model.py

from src.detection.yolo_detector import YOLODetector
import time
import numpy as np

def benchmark_model(model_path, num_iterations=100):
    """Benchmark model performance"""
    detector = YOLODetector(model_path=model_path)
    
    # Create test frame
    frame = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
    
    # Warmup
    for _ in range(10):
        detector.detect_frame(frame)
    
    # Benchmark
    start_time = time.time()
    for _ in range(num_iterations):
        detector.detect_frame(frame)
    end_time = time.time()
    
    avg_time = (end_time - start_time) / num_iterations
    fps = 1.0 / avg_time
    
    print(f"Average inference time: {avg_time*1000:.2f}ms")
    print(f"FPS: {fps:.2f}")
    
    return fps

if __name__ == '__main__':
    old_fps = benchmark_model('yolo11s_backup.pt')
    new_fps = benchmark_model('yolo11s.pt')
    
    improvement = ((new_fps - old_fps) / old_fps) * 100
    print(f"Performance change: {improvement:+.2f}%")
```

---

## Backup and Recovery

### Backup Strategy

**3-2-1 Rule**:
- 3 copies of data
- 2 different storage media
- 1 offsite backup

### Automated Backup Script

```bash
#!/bin/bash
# comprehensive_backup.sh

BACKUP_ROOT="/backup"
DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="/path/to/cctv-project"

# 1. Database backup
echo "Backing up database..."
cp $PROJECT_DIR/cctv_database.db $BACKUP_ROOT/db_$DATE.db
gzip $BACKUP_ROOT/db_$DATE.db

# 2. Configuration backup
echo "Backing up configuration..."
tar -czf $BACKUP_ROOT/config_$DATE.tar.gz \
    $PROJECT_DIR/email_config.json \
    $PROJECT_DIR/.env

# 3. Logs backup
echo "Backing up logs..."
tar -czf $BACKUP_ROOT/logs_$DATE.tar.gz \
    /var/log/cctv/

# 4. Models backup (if updated)
echo "Backing up models..."
tar -czf $BACKUP_ROOT/models_$DATE.tar.gz \
    $PROJECT_DIR/*.pt \
    $PROJECT_DIR/*_openvino_model/

# 5. Sync to remote server (if configured)
if [ -n "$REMOTE_BACKUP_HOST" ]; then
    echo "Syncing to remote backup..."
    rsync -avz $BACKUP_ROOT/* \
        $REMOTE_BACKUP_HOST:/backup/cctv/
fi

# 6. Cleanup old backups (keep 30 days)
find $BACKUP_ROOT -type f -mtime +30 -delete

echo "Backup complete: $DATE"
```

### Recovery Procedures

#### Recover Database

```bash
# Stop service
sudo systemctl stop cctv-detection

# Restore from backup
gunzip -c /backup/db_20260303_020000.db.gz > /path/to/cctv_database.db

# Verify integrity
sqlite3 /path/to/cctv_database.db "PRAGMA integrity_check;"

# Start service
sudo systemctl start cctv-detection
```

#### Full System Recovery

```bash
#!/bin/bash
# recover_system.sh

BACKUP_DATE="20260303"
BACKUP_ROOT="/backup"
PROJECT_DIR="/path/to/cctv-project"

echo "=== System Recovery ==="
echo "Recovering from backup: $BACKUP_DATE"

# Stop service
sudo systemctl stop cctv-detection

# Restore database
echo "Restoring database..."
gunzip -c $BACKUP_ROOT/db_$BACKUP_DATE.db.gz > $PROJECT_DIR/cctv_database.db

# Restore configuration
echo "Restoring configuration..."
tar -xzf $BACKUP_ROOT/config_$BACKUP_DATE.tar.gz -C $PROJECT_DIR

# Restore models
echo "Restoring models..."
tar -xzf $BACKUP_ROOT/models_$BACKUP_DATE.tar.gz -C $PROJECT_DIR

# Verify files
echo "Verifying files..."
ls -lh $PROJECT_DIR/cctv_database.db
ls -lh $PROJECT_DIR/email_config.json
ls -lh $PROJECT_DIR/yolo11s.pt

# Start service
sudo systemctl start cctv-detection

# Check status
sleep 5
sudo systemctl status cctv-detection

echo "Recovery complete"
```

---

## Performance Optimization

### Optimize Video Processing

```python
# In yolo_detector.py

# 1. Use frame skipping
def process_video_optimized(self, video_path, output_path, frame_skip=2):
    """Process video with frame skipping"""
    for i, frame in enumerate(frames):
        if i % frame_skip != 0:
            # Duplicate previous frame in output
            writer.write(last_frame)
            continue
        
        # Process this frame
        detections = self.detect_frame(frame)
        # ...

# 2. Reduce output resolution
def create_output_video(self, input_path, output_path, scale=0.5):
    """Create output video at reduced resolution"""
    # Scale down resolution to 50% for faster encoding
    pass

# 3. Optimize encoding
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Fast encoding
# vs
fourcc = cv2.VideoWriter_fourcc(*'H264')  # Better compression, slower
```

### Database Optimization

```sql
-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_timestamp ON videos(timestamp);
CREATE INDEX IF NOT EXISTS idx_filename ON videos(filename);
CREATE INDEX IF NOT EXISTS idx_anomaly_count ON videos(anomaly_count);

-- Optimize query planner
ANALYZE;
```

---

## Troubleshooting Common Issues

### Issue 1: Service Won't Start

**Symptoms**: `systemctl start cctv-detection` fails

**Diagnosis**:
```bash
# Check service status
sudo systemctl status cctv-detection

# Check logs
sudo journalctl -u cctv-detection -n 50

# Test manually
cd /path/to/project
python app.py
```

**Solutions**:
- Check Python path in service file
- Verify virtual environment activation
- Check file permissions
- Ensure dependencies installed

### Issue 2: Out of Disk Space

**Symptoms**: "No space left on device"

**Diagnosis**:
```bash
# Check disk usage
df -h

# Find large files
du -sh /* | sort -h
du -sh /path/to/project/* | sort -h
```

**Solutions**:
```bash
# Clean old videos
find /path/to/static/videos -mtime +30 -delete

# Clean temp files
rm -rf /path/to/temp/*

# Clean logs
truncate -s 0 /var/log/cctv/app.log

# Archive old database records
python archive_old_data.py
```

### Issue 3: High Memory Usage

**Symptoms**: System slow, OOM (Out of Memory) errors

**Diagnosis**:
```bash
# Check memory usage
free -h
top
htop
```

**Solutions**:
- Restart service: `sudo systemctl restart cctv-detection`
- Reduce worker processes
- Add swap space
- Upgrade RAM

### Issue 4: Slow Detection Speed

**Symptoms**: Processing takes too long

**Diagnosis**:
```python
# Profile detection
import cProfile

pr = cProfile.Profile()
pr.enable()
# ... run detection ...
pr.disable()
pr.print_stats(sort='tottime')
```

**Solutions**:
- Use smaller YOLO model (yolo11n)
- Enable OpenVINO optimization
- Use frame skipping
- Reduce video resolution
- Upgrade CPU

---

## Security Updates

### Security Checklist

#### Monthly Security Tasks

- [ ] Update system packages: `sudo apt update && sudo apt upgrade`
- [ ] Update Python packages: `pip list --outdated` then update
- [ ] Check for security advisories
- [ ] Review access logs
- [ ] Verify firewall rules
- [ ] Check for unauthorized access attempts

#### Security Scanning

```bash
# Install security scanners
pip install bandit safety

# Scan Python code for security issues
bandit -r src/

# Check dependencies for vulnerabilities
safety check

# Check for outdated packages with known CVEs
pip-audit
```

### Apply Security Updates

```bash
#!/bin/bash
# security_update.sh

echo "=== Security Update ==="

# Update system
sudo apt update
sudo apt upgrade --security-only -y

# Update Python packages
pip install --upgrade pip
pip list --outdated | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 pip install -U

# Scan for vulnerabilities
safety check
bandit -r src/

echo "Security update complete"
```

---

## Hardware Maintenance

### Camera Maintenance

#### Monthly Camera Checks

```
Camera ID: [____]
Date: [________]

Physical Inspection:
[ ] Lens clean
[ ] No condensation
[ ] Mounting secure
[ ] Cables intact
[ ] No physical damage

Connectivity:
[ ] RTSP stream accessible
[ ] Network connection stable
[ ] Power supply OK
[ ] No packet loss

Image Quality:
[ ] Focus acceptable
[ ] Exposure correct
[ ] No IR issues (night)
[ ] Coverage area correct

Notes:
_________________________________
```

### Server Maintenance

#### Quarterly Server Maintenance

- **Clean dust** from server and fans
- **Check temperatures**: CPU, GPU
- **Test UPS**: Simulate power failure
- **Verify backups**: Test restoration
- **Check disk health**: `sudo smartctl -a /dev/sda`
- **Update firmware**: BIOS, network card

---

## Conclusion

Regular maintenance ensures system reliability and performance. Follow this guide and adjust schedules based on your specific needs.

**Quick Reference**:
- Daily: Logs, health check, backup
- Weekly: Database optimize, cleanup
- Monthly: Updates, full backup, performance review
- Quarterly: Security audit, model update

**For emergencies**: See [TROUBLESHOOTING section](#troubleshooting-common-issues)

---

*Last Updated: March 3, 2026*  
*Version: 3.0.0*
