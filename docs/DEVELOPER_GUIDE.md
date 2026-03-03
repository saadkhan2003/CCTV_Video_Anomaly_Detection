# Developer Guide

## CCTV Video Anomaly Detection System Developer Documentation

**Version**: 3.0.0  
**Last Updated**: March 3, 2026

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Architecture Overview](#architecture-overview)
3. [Project Structure](#project-structure)
4. [Core Components](#core-components)
5. [Development Workflow](#development-workflow)
6. [Adding New Features](#adding-new-features)
7. [Code Style Guide](#code-style-guide)
8. [Debugging](#debugging)
9. [Performance Optimization](#performance-optimization)
10. [Contributing](#contributing)

---

## Getting Started

### Development Environment Setup

```bash
# Clone repository
git clone https://github.com/your-org/cctv-anomaly-detection.git
cd cctv-anomaly-detection

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Development Dependencies

**File**: `requirements-dev.txt`

```txt
# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
httpx>=0.24.0

# Code Quality
black>=23.0.0
flake8>=6.0.0
isort>=5.12.0
mypy>=1.4.0
pylint>=2.17.0

# Documentation
sphinx>=7.0.0
sphinx-rtd-theme>=1.2.0

# Debugging
ipdb>=0.13.13
memory_profiler>=0.61.0

# Git hooks
pre-commit>=3.3.0
```

### IDE Setup

#### VS Code

**File**: `.vscode/settings.json`

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

#### PyCharm

1. Enable Black formatter: Settings → Tools → Black
2. Enable pylint: Settings → Tools → External Tools
3. Configure pytest: Settings → Tools → Python Integrated Tools

---

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT (Web Browser)                     │
│                     HTML + CSS + JavaScript                  │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTP/SSE
┌─────────────────▼───────────────────────────────────────────┐
│                   FASTAPI APPLICATION                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Endpoints (app.py)                  │  │
│  │  - Video Upload & Analysis                           │  │
│  │  - Live Stream Monitoring                            │  │
│  │  - Database CRUD Operations                          │  │
│  └────┬────────────────────────┬───────────────┬────────┘  │
│       │                        │               │            │
│  ┌────▼──────┐  ┌──────────────▼────┐  ┌──────▼──────┐    │
│  │ Detection │  │     Storage       │  │   Alerts    │    │
│  │  Module   │  │     Module        │  │   Module    │    │
│  └────┬──────┘  └──────────────┬────┘  └──────┬──────┘    │
│       │                        │               │            │
└───────┼────────────────────────┼───────────────┼────────────┘
        │                        │               │
   ┌────▼────────┐         ┌────▼─────┐   ┌────▼──────┐
   │   YOLOv11   │         │  SQLite  │   │   SMTP    │
   │  OpenVINO   │         │ Database │   │  Server   │
   └─────────────┘         └──────────┘   └───────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | HTML5, CSS3, JavaScript | User interface |
| Backend | FastAPI, Python 3.10+ | REST API, async processing |
| ML/AI | YOLOv11, OpenVINO | Object detection, anomaly detection |
| Database | SQLite | Data persistence |
| Tracking | ByteTrack | Multi-object tracking |
| Alerts | SMTP | Email notifications |

---

## Project Structure

```
/media/saad/Data/CCTV Video Anomaly Detection/
│
├── app.py                      # Main FastAPI application
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── run.sh                      # Launch script
├── .env                        # Environment variables
├── email_config.json          # Email configuration
├── README.md                  # Project overview
├── LICENSE                    # MIT License
│
├── src/                       # Source code
│   ├── __init__.py
│   ├── detection/             # Detection module
│   │   ├── __init__.py
│   │   ├── yolo_detector.py   # YOLO detection logic
│   │   ├── visualization.py   # Drawing bounding boxes
│   │   └── live_stream.py     # Live stream processing
│   │
│   ├── storage/               # Database module
│   │   ├── __init__.py
│   │   └── database.py        # SQLite operations
│   │
│   └── alerts/                # Alerts module
│       ├── __init__.py
│       └── email_alerts.py    # Email notification logic
│
├── static/                    # Static files
│   ├── style.css              # UI styles
│   └── videos/                # Processed videos
│
├── templates/                 # HTML templates
│   ├── index.html             # Main dashboard
│   └── live.html              # Live stream page
│
├── docs/                      # Documentation
│   ├── API_DOCUMENTATION.md
│   ├── USER_MANUAL.md
│   ├── CONFIGURATION_GUIDE.md
│   ├── TESTING_DOCUMENTATION.md
│   ├── DEVELOPER_GUIDE.md     # This file
│   ├── MAINTENANCE_GUIDE.md
│   └── DEPLOYMENT_GUIDE.md
│
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── conftest.py            # Test fixtures
│   ├── test_detection.py      # Detection tests
│   ├── test_database.py       # Database tests
│   ├── test_api.py            # API tests
│   └── test_email_alerts.py   # Email tests
│
├── yolo11*.pt                 # YOLO model files
└── yolo11*_openvino_model/    # OpenVINO models
```

---

## Core Components

### 1. YOLO Detector (`src/detection/yolo_detector.py`)

#### Key Classes

```python
class YOLODetector:
    """Main detection class using YOLOv11"""
    
    def __init__(self, model_size='s', device='cpu', 
                 confidence_threshold=0.5, crowd_threshold=5,
                 loiter_threshold_seconds=10.0):
        """
        Initialize YOLO detector
        
        Args:
            model_size: Model size (n, s, m, l, x)
            device: Device (cpu, cuda, mps)
            confidence_threshold: Detection confidence (0-1)
            crowd_threshold: Number of people for crowd alert
            loiter_threshold_seconds: Duration for loitering alert
        """
        pass
    
    def process_video(self, video_path, output_path, 
                     progress_callback=None):
        """
        Process video file and detect anomalies
        
        Args:
            video_path: Input video file path
            output_path: Output video file path
            progress_callback: Function to report progress
            
        Returns:
            dict: Statistics including frame count, anomaly count, etc.
        """
        pass
    
    def detect_frame(self, frame):
        """
        Run detection on single frame
        
        Args:
            frame: numpy array (H, W, C)
            
        Returns:
            list: List of detection dictionaries
        """
        pass
```

#### Detection Logic Flow

```python
def process_video(self, video_path, output_path, progress_callback=None):
    # 1. Open video
    cap = cv2.VideoCapture(video_path)
    
    # 2. Initialize output
    writer = cv2.VideoWriter(...)
    
    # 3. Per-frame loop
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 4. Run YOLO detection
        results = self.model.track(frame, persist=True)
        
        # 5. Extract detections
        detections = self._parse_results(results)
        
        # 6. Check for anomalies
        anomalies = self._check_anomalies(detections)
        
        # 7. Annotate frame
        annotated_frame = self._draw_boxes(frame, detections, anomalies)
        
        # 8. Write output
        writer.write(annotated_frame)
        
        # 9. Update progress
        if progress_callback:
            progress_callback(frame_count / total_frames * 100)
    
    # 10. Cleanup
    cap.release()
    writer.release()
    
    return stats
```

#### Anomaly Detection Methods

```python
def _check_crowd_anomaly(self, detections):
    """Check if crowd threshold exceeded"""
    person_count = sum(1 for d in detections if d['class'] == 'person')
    return person_count > self.crowd_threshold

def _check_weapon_anomaly(self, detections):
    """Check for weapon detections"""
    weapon_classes = ['knife', 'baseball bat', 'scissors']
    return any(d['class'] in weapon_classes for d in detections)

def _check_loitering_anomaly(self, track_id):
    """Check if person has been stationary too long"""
    if track_id in self.tracks:
        duration = time.time() - self.tracks[track_id]['start_time']
        movement = self._calculate_movement(track_id)
        return duration > self.loiter_threshold and movement < 0.1
    return False

def _check_fast_movement_anomaly(self, track_id):
    """Check for unusually fast movement"""
    if track_id in self.tracks:
        velocity = self._calculate_velocity(track_id)
        return velocity > self.fast_movement_threshold
    return False
```

### 2. Database Module (`src/storage/database.py`)

#### Key Functions

```python
def init_database(db_path='cctv_database.db'):
    """
    Initialize SQLite database with required tables
    
    Args:
        db_path: Path to database file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            frame_count INTEGER,
            anomaly_count INTEGER,
            anomaly_rate REAL,
            processing_time REAL,
            threshold_used INTEGER,
            anomaly_scores TEXT,
            anomaly_flags TEXT,
            output_video_path TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def save_video_analysis(filename, frame_count, anomaly_count, 
                       anomaly_rate, processing_time, threshold_used,
                       anomaly_scores, anomaly_flags, output_video_path,
                       db_path='cctv_database.db'):
    """
    Save video analysis results to database
    
    Args:
        All video metadata and results
        
    Returns:
        int: Video ID
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO videos (
            filename, frame_count, anomaly_count, anomaly_rate,
            processing_time, threshold_used, anomaly_scores,
            anomaly_flags, output_video_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        filename, frame_count, anomaly_count, anomaly_rate,
        processing_time, threshold_used,
        json.dumps(anomaly_scores),
        json.dumps(anomaly_flags),
        output_video_path
    ))
    
    video_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return video_id
```

### 3. Email Alerts (`src/alerts/email_alerts.py`)

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

def send_anomaly_alert(anomaly_types, details, video_filename=None, 
                      video_id=None, config_path='email_config.json'):
    """
    Send email alert for detected anomalies
    
    Args:
        anomaly_types: List of anomaly types detected
        details: List of detail strings
        video_filename: Original video filename
        video_id: Database video ID
        config_path: Path to email config JSON
        
    Returns:
        bool: True if sent successfully
    """
    try:
        # Load config
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🚨 Anomaly Alert: {video_filename}"
        msg['From'] = config['sender_email']
        msg['To'] = ', '.join(config['receiver_emails'])
        
        # Create HTML body
        html = create_html_body(anomaly_types, details, video_id)
        msg.attach(MIMEText(html, 'html'))
        
        # Send email
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['sender_email'], config['sender_password'])
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
```

### 4. FastAPI Application (`app.py`)

#### Key Endpoints

```python
@app.post("/api/analyze")
async def analyze_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    crowd_threshold: int = Query(5),
    confidence: float = Query(0.6)
):
    """
    Upload and analyze video
    
    Returns:
        dict: Task ID and status
    """
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Save uploaded file
    temp_path = f"temp/{task_id}_{file.filename}"
    with open(temp_path, 'wb') as f:
        f.write(await file.read())
    
    # Create task
    TASKS[task_id] = {
        'status': 'queued',
        'progress': 0,
        'result': None
    }
    
    # Start background processing
    output_path = f"static/videos/output_{task_id}.mp4"
    background_tasks.add_task(
        run_analysis_task,
        task_id, temp_path, output_path,
        crowd_threshold, confidence, file.filename
    )
    
    return {
        'task_id': task_id,
        'status': 'queued',
        'message': 'Analysis started'
    }

@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Get analysis task status
    
    Returns:
        dict: Task status, progress, and result
    """
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TASKS[task_id]
```

---

## Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/new-anomaly-rule

# Make changes
# ... edit files ...

# Run tests
pytest tests/

# Format code
black src/ tests/
isort src/ tests/

# Check code quality
flake8 src/ tests/
pylint src/ tests/

# Commit changes
git add .
git commit -m "feat: Add vehicle congestion detection"

# Push and create PR
git push origin feature/new-anomaly-rule
```

### 2. Code Review Checklist

- [ ] Code follows style guide
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No security vulnerabilities
- [ ] Performance acceptable
- [ ] Error handling robust
- [ ] Logging appropriate

### 3. Release Process

```bash
# 1. Update version
# Edit app.py: version="3.1.0"

# 2. Update CHANGELOG.md

# 3. Run full test suite
pytest tests/ --cov

# 4. Build documentation
cd docs && make html

# 5. Create release tag
git tag -a v3.1.0 -m "Release version 3.1.0"
git push origin v3.1.0

# 6. Deploy to production
# See DEPLOYMENT_GUIDE.md
```

---

## Adding New Features

### Example: Adding Zone-Based Detection

#### Step 1: Define Zone Class

**File**: `src/detection/zones.py`

```python
from typing import List, Tuple

class DetectionZone:
    """Define a polygon zone for zone-based detection"""
    
    def __init__(self, zone_id: str, polygon: List[Tuple[int, int]], 
                 rules: dict):
        """
        Initialize detection zone
        
        Args:
            zone_id: Unique zone identifier
            polygon: List of (x, y) points defining zone
            rules: Zone-specific detection rules
        """
        self.zone_id = zone_id
        self.polygon = polygon
        self.rules = rules
    
    def contains_point(self, point: Tuple[int, int]) -> bool:
        """Check if point is inside zone"""
        import cv2
        import numpy as np
        
        contour = np.array(self.polygon)
        result = cv2.pointPolygonTest(contour, point, False)
        return result >= 0
    
    def apply_rules(self, detections: List[dict]) -> List[dict]:
        """
        Apply zone-specific rules to detections
        
        Args:
            detections: List of detections
            
        Returns:
            List of anomalies specific to this zone
        """
        zone_detections = [
            d for d in detections 
            if self.contains_point(d['center'])
        ]
        
        anomalies = []
        
        # Apply zone-specific crowd threshold
        if 'crowd_threshold' in self.rules:
            person_count = sum(
                1 for d in zone_detections 
                if d['class'] == 'person'
            )
            if person_count > self.rules['crowd_threshold']:
                anomalies.append({
                    'type': 'zone_crowd',
                    'zone_id': self.zone_id,
                    'count': person_count
                })
        
        return anomalies
```

#### Step 2: Integrate into YOLODetector

```python
class YOLODetector:
    def __init__(self, ..., zones=None):
        # ... existing code ...
        self.zones = zones or []
    
    def _check_anomalies(self, detections):
        anomalies = []
        
        # ... existing anomaly checks ...
        
        # Check zone-specific rules
        for zone in self.zones:
            zone_anomalies = zone.apply_rules(detections)
            anomalies.extend(zone_anomalies)
        
        return anomalies
```

#### Step 3: Add API Endpoint

```python
@app.post("/api/zones")
async def create_zone(zone: ZoneCreate):
    """Create new detection zone"""
    # Save zone to database/config
    pass

@app.get("/api/zones")
async def get_zones():
    """Get all detection zones"""
    pass
```

#### Step 4: Add Tests

```python
def test_zone_detection():
    """Test zone-based detection"""
    zone = DetectionZone(
        zone_id='entrance',
        polygon=[(100, 100), (300, 100), (300, 300), (100, 300)],
        rules={'crowd_threshold': 3}
    )
    
    detections = [
        {'center': (150, 150), 'class': 'person'},
        {'center': (200, 200), 'class': 'person'},
        {'center': (250, 250), 'class': 'person'},
        {'center': (400, 400), 'class': 'person'}  # Outside zone
    ]
    
    anomalies = zone.apply_rules(detections)
    assert len(anomalies) == 1
    assert anomalies[0]['type'] == 'zone_crowd'
```

---

## Code Style Guide

### Python Style (PEP 8)

```python
# Good
def process_video(video_path: str, output_path: str) -> dict:
    """
    Process video and detect anomalies.
    
    Args:
        video_path: Path to input video file
        output_path: Path to save output video
        
    Returns:
        Dictionary containing processing statistics
        
    Raises:
        FileNotFoundError: If video_path doesn't exist
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")
    
    stats = {
        'total_frames': 0,
        'anomaly_frames': 0
    }
    
    return stats


# Bad
def processVideo(videoPath,outputPath):
    stats={'total_frames':0,'anomaly_frames':0}
    return stats
```

### Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Classes | PascalCase | `YOLODetector` |
| Functions | snake_case | `process_video()` |
| Variables | snake_case | `video_path` |
| Constants | UPPER_CASE | `MAX_FILE_SIZE` |
| Private | _leading_underscore | `_internal_method()` |

### Documentation

**Docstrings** (Google Style):

```python
def detect_anomalies(frame: np.ndarray, threshold: float = 0.5) -> List[dict]:
    """
    Detect anomalies in a video frame.
    
    This function runs object detection and applies anomaly rules
    to identify suspicious activities.
    
    Args:
        frame: Input frame as numpy array with shape (H, W, C)
        threshold: Detection confidence threshold, 0.0 to 1.0
        
    Returns:
        List of anomaly dictionaries containing:
            - type: Anomaly type string
            - confidence: Detection confidence
            - bbox: Bounding box coordinates [x, y, w, h]
            
    Raises:
        ValueError: If frame is empty or invalid shape
        
    Example:
        >>> frame = cv2.imread('test.jpg')
        >>> anomalies = detect_anomalies(frame, threshold=0.6)
        >>> print(f"Found {len(anomalies)} anomalies")
    """
    pass
```

---

## Debugging

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def process_video(video_path):
    logger.info(f"Processing video: {video_path}")
    
    try:
        # ... processing ...
        logger.debug(f"Frame {frame_count}: {len(detections)} objects")
        
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        raise
    
    logger.info("Processing complete")
```

### Debugging with ipdb

```python
# Add breakpoint
import ipdb; ipdb.set_trace()

# Or use built-in
breakpoint()
```

### Memory Profiling

```python
from memory_profiler import profile

@profile
def process_video(video_path):
    # Function will show memory usage per line
    pass
```

---

## Performance Optimization

### 1. Frame Skip for Speed

```python
FRAME_SKIP = 2  # Process every 2nd frame

for i, frame in enumerate(frames):
    if i % FRAME_SKIP != 0:
        continue
    
    detections = detector.detect(frame)
```

### 2. Batch Processing

```python
# Process frames in batches
batch_size = 4
frames_batch = []

for frame in video:
    frames_batch.append(frame)
    
    if len(frames_batch) == batch_size:
        results = model.predict(frames_batch, batch=True)
        frames_batch = []
```

### 3. Use OpenVINO

```python
# Export to OpenVINO format
model = YOLO('yolo11s.pt')
model.export(format='openvino')

# Load OpenVINO model
model = YOLO('yolo11s_openvino_model/')
```

---

## Contributing

### Contributing Guidelines

1. **Fork the repository**
2. **Create feature branch** (`git checkout -b feature/amazing-feature`)
3. **Write tests** for new functionality
4. **Ensure tests pass** (`pytest tests/`)
5. **Format code** (`black src/`)
6. **Commit changes** (`git commit -m 'Add amazing feature'`)
7. **Push to branch** (`git push origin feature/amazing-feature`)
8. **Open Pull Request**

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Tests pass
```

---

## Conclusion

This developer guide provides the foundation for contributing to the project. For specific areas:

- **Testing**: See [TESTING_DOCUMENTATION.md](TESTING_DOCUMENTATION.md)
- **Configuration**: See [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)
- **Deployment**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

**Happy coding! 🚀**

---

*Last Updated: March 3, 2026*  
*Version: 3.0.0*
