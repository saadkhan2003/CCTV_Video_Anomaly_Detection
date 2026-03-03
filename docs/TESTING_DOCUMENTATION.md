# Testing Documentation

## CCTV Video Anomaly Detection System Testing Guide

**Version**: 3.0.0  
**Last Updated**: March 3, 2026

---

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Test Environment Setup](#test-environment-setup)
3. [Unit Testing](#unit-testing)
4. [Integration Testing](#integration-testing)
5. [API Testing](#api-testing)
6. [Performance Testing](#performance-testing)
7. [User Acceptance Testing](#user-acceptance-testing)
8. [Test Data](#test-data)
9. [Continuous Integration](#continuous-integration)
10. [Test Coverage](#test-coverage)

---

## Testing Overview

### Testing Strategy

The system employs a comprehensive testing approach:

```
┌─────────────────────────────────────────┐
│         Testing Pyramid                 │
├─────────────────────────────────────────┤
│                                         │
│           [E2E Tests]                   │
│       (User Workflows)                  │
│                                         │
│     [Integration Tests]                 │
│   (API, Database, Model)                │
│                                         │
│        [Unit Tests]                     │
│  (Individual Functions)                 │
│                                         │
└─────────────────────────────────────────┘
```

### Test Types

| Type | Purpose | Frequency | Tools |
|------|---------|-----------|-------|
| Unit | Test individual functions | Every commit | pytest |
| Integration | Test module interactions | Daily | pytest, httpx |
| API | Test REST endpoints | Daily | pytest, httpx |
| Performance | Benchmark speed/accuracy | Weekly | pytest-benchmark |
| Load | Test concurrent users | Before release | locust |
| Security | Vulnerability scanning | Monthly | bandit, safety |
| UAT | User acceptance | Before deployment | Manual |

---

## Test Environment Setup

### Install Testing Dependencies

```bash
# Install test requirements
pip install pytest pytest-asyncio pytest-cov pytest-benchmark httpx

# Or use requirements
pip install -r requirements-test.txt
```

### Create requirements-test.txt

```txt
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-benchmark>=4.0.0
pytest-mock>=3.11.0
httpx>=0.24.0
locust>=2.15.0
bandit>=1.7.5
safety>=2.3.0
```

### Setup Test Database

```python
# tests/conftest.py
import pytest
import tempfile
import os

@pytest.fixture
def test_db():
    """Create temporary test database"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        db_path = f.name
    
    # Initialize test database
    from src.storage.database import init_database
    init_database(db_path)
    
    yield db_path
    
    # Cleanup
    os.unlink(db_path)
```

### Setup Test Video

```python
@pytest.fixture
def test_video():
    """Create test video file"""
    import cv2
    import numpy as np
    
    # Create 30-frame test video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter('test_video.mp4', fourcc, 30.0, (640, 480))
    
    for i in range(30):
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        video.write(frame)
    
    video.release()
    yield 'test_video.mp4'
    
    os.unlink('test_video.mp4')
```

---

## Unit Testing

### Testing Detection Module

**File**: `tests/test_detection.py`

```python
import pytest
from src.detection.yolo_detector import YOLODetector

class TestYOLODetector:
    
    @pytest.fixture
    def detector(self):
        """Initialize detector for tests"""
        return YOLODetector(
            model_size='n',
            device='cpu',
            confidence_threshold=0.5
        )
    
    def test_detector_initialization(self, detector):
        """Test detector initializes correctly"""
        assert detector is not None
        assert detector.model is not None
        assert detector.confidence_threshold == 0.5
    
    def test_detect_objects_in_frame(self, detector):
        """Test object detection in single frame"""
        import numpy as np
        
        # Create dummy frame
        frame = np.zeros((640, 480, 3), dtype=np.uint8)
        
        # Run detection
        results = detector.detect_frame(frame)
        
        assert isinstance(results, list)
        assert all(isinstance(r, dict) for r in results)
    
    def test_crowd_detection(self, detector):
        """Test crowd anomaly detection"""
        # Simulate 10 person detections
        detections = [
            {'class': 'person', 'bbox': [i*50, 100, 50, 100]}
            for i in range(10)
        ]
        
        is_crowd = detector.is_crowd_anomaly(detections, threshold=5)
        assert is_crowd == True
    
    def test_weapon_detection(self, detector):
        """Test weapon detection"""
        detections = [
            {'class': 'knife', 'confidence': 0.8}
        ]
        
        has_weapon = detector.has_weapon(detections)
        assert has_weapon == True
    
    def test_loitering_detection(self, detector):
        """Test loitering detection"""
        # Simulate person staying in same position
        track_id = 1
        positions = [(100, 100)] * 15  # 15 frames at same position
        
        for pos in positions:
            detector.update_tracker(track_id, pos)
        
        is_loitering = detector.is_loitering(track_id, threshold=10.0)
        assert is_loitering == True
    
    @pytest.mark.parametrize("confidence,expected", [
        (0.3, True),   # Low confidence should detect
        (0.5, True),   # Medium confidence
        (0.9, False),  # High confidence filters out
    ])
    def test_confidence_thresholds(self, confidence, expected):
        """Test different confidence thresholds"""
        detector = YOLODetector(
            model_size='n',
            confidence_threshold=confidence
        )
        
        # Simulate detection with 0.6 confidence
        detection = {'class': 'person', 'confidence': 0.6}
        passed = detector.passes_threshold(detection)
        
        assert passed == expected
```

### Testing Database Module

**File**: `tests/test_database.py`

```python
import pytest
from src.storage.database import (
    init_database,
    save_video_analysis,
    get_video_by_id,
    get_all_videos,
    delete_video
)

class TestDatabase:
    
    def test_database_initialization(self, test_db):
        """Test database creates tables"""
        import sqlite3
        
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Check if videos table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='videos'"
        )
        assert cursor.fetchone() is not None
    
    def test_save_video_analysis(self, test_db):
        """Test saving video analysis results"""
        video_id = save_video_analysis(
            filename="test.mp4",
            frame_count=100,
            anomaly_count=10,
            anomaly_rate=0.1,
            processing_time=5.0,
            threshold_used=5,
            anomaly_scores=[0.0] * 100,
            anomaly_flags=[False] * 100,
            output_video_path="/videos/test.mp4",
            db_path=test_db
        )
        
        assert video_id > 0
    
    def test_get_video_by_id(self, test_db):
        """Test retrieving video by ID"""
        # Save video first
        video_id = save_video_analysis(
            filename="test.mp4",
            frame_count=100,
            anomaly_count=10,
            anomaly_rate=0.1,
            processing_time=5.0,
            threshold_used=5,
            anomaly_scores=[0.0] * 100,
            anomaly_flags=[False] * 100,
            output_video_path="/videos/test.mp4",
            db_path=test_db
        )
        
        # Retrieve video
        video = get_video_by_id(video_id, db_path=test_db)
        
        assert video is not None
        assert video['id'] == video_id
        assert video['filename'] == "test.mp4"
        assert video['frame_count'] == 100
    
    def test_get_all_videos(self, test_db):
        """Test retrieving all videos"""
        # Save multiple videos
        for i in range(3):
            save_video_analysis(
                filename=f"test_{i}.mp4",
                frame_count=100,
                anomaly_count=10,
                anomaly_rate=0.1,
                processing_time=5.0,
                threshold_used=5,
                anomaly_scores=[0.0] * 100,
                anomaly_flags=[False] * 100,
                output_video_path=f"/videos/test_{i}.mp4",
                db_path=test_db
            )
        
        videos = get_all_videos(db_path=test_db)
        assert len(videos) == 3
    
    def test_delete_video(self, test_db):
        """Test deleting video"""
        # Save video
        video_id = save_video_analysis(
            filename="test.mp4",
            frame_count=100,
            anomaly_count=10,
            anomaly_rate=0.1,
            processing_time=5.0,
            threshold_used=5,
            anomaly_scores=[0.0] * 100,
            anomaly_flags=[False] * 100,
            output_video_path="/videos/test.mp4",
            db_path=test_db
        )
        
        # Delete video
        result = delete_video(video_id, db_path=test_db)
        assert result == True
        
        # Verify deletion
        video = get_video_by_id(video_id, db_path=test_db)
        assert video is None
```

### Testing Email Alerts

**File**: `tests/test_email_alerts.py`

```python
import pytest
from unittest.mock import patch, MagicMock
from src.alerts.email_alerts import send_anomaly_alert

class TestEmailAlerts:
    
    @patch('src.alerts.email_alerts.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending"""
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Send email
        result = send_anomaly_alert(
            anomaly_types=['crowd', 'weapon'],
            details=['Test alert']
        )
        
        assert result == True
        mock_server.send_message.assert_called_once()
    
    @patch('src.alerts.email_alerts.smtplib.SMTP')
    def test_send_email_failure(self, mock_smtp):
        """Test email sending failure"""
        # Mock SMTP failure
        mock_smtp.side_effect = Exception("Connection failed")
        
        # Send email
        result = send_anomaly_alert(
            anomaly_types=['crowd'],
            details=['Test alert']
        )
        
        assert result == False
    
    def test_email_content_formatting(self):
        """Test email content is properly formatted"""
        from src.alerts.email_alerts import format_email_body
        
        body = format_email_body(
            anomaly_types=['crowd', 'weapon'],
            details=['5 people detected', 'Knife detected']
        )
        
        assert 'crowd' in body.lower()
        assert 'weapon' in body.lower()
        assert '5 people' in body
```

### Running Unit Tests

```bash
# Run all unit tests
pytest tests/

# Run specific test file
pytest tests/test_detection.py

# Run with coverage
pytest --cov=src tests/

# Run with verbose output
pytest -v tests/

# Run specific test
pytest tests/test_detection.py::TestYOLODetector::test_crowd_detection
```

---

## Integration Testing

### Testing API Endpoints

**File**: `tests/test_api.py`

```python
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

class TestAPI:
    
    def test_root_endpoint(self):
        """Test root endpoint returns HTML"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_video_upload(self, test_video):
        """Test video upload endpoint"""
        with open(test_video, 'rb') as f:
            response = client.post(
                "/api/analyze",
                files={"file": ("test.mp4", f, "video/mp4")},
                data={"crowd_threshold": 5, "confidence": 0.6}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["status"] in ["queued", "processing"]
    
    def test_get_task_status(self):
        """Test task status endpoint"""
        # Upload video first
        with open('test_video.mp4', 'rb') as f:
            response = client.post(
                "/api/analyze",
                files={"file": ("test.mp4", f, "video/mp4")}
            )
        
        task_id = response.json()["task_id"]
        
        # Check status
        response = client.get(f"/api/task/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "progress" in data
    
    def test_get_all_videos(self):
        """Test getting all videos"""
        response = client.get("/api/videos")
        assert response.status_code == 200
        data = response.json()
        assert "videos" in data
        assert isinstance(data["videos"], list)
    
    def test_get_video_by_id(self):
        """Test getting specific video"""
        response = client.get("/api/videos/1")
        
        # Either found or not found
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert data["id"] == 1
    
    def test_delete_video(self):
        """Test deleting video"""
        response = client.delete("/api/videos/1")
        assert response.status_code in [200, 404]
    
    def test_search_videos(self):
        """Test video search"""
        response = client.get("/api/search?query=test")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
    
    def test_statistics_endpoint(self):
        """Test statistics endpoint"""
        response = client.get("/api/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_videos" in data
        assert "total_anomalies" in data
```

### Testing Live Stream

**File**: `tests/test_live_stream.py`

```python
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

class TestLiveStream:
    
    def test_live_stream_webcam(self):
        """Test live stream with webcam"""
        with client.stream("GET", "/api/live-stream?source=0") as response:
            assert response.status_code == 200
            
            # Read first few events
            events = []
            for i, line in enumerate(response.iter_lines()):
                if i > 10:  # Read first 10 events
                    break
                events.append(line)
            
            assert len(events) > 0
    
    def test_live_stream_invalid_source(self):
        """Test live stream with invalid source"""
        response = client.get("/api/live-stream?source=invalid://url")
        assert response.status_code in [400, 503]
```

---

## API Testing

### Using cURL

```bash
# Health check
curl http://localhost:8000/api/health

# Upload video
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@test_video.mp4" \
  -F "crowd_threshold=5" \
  -F "confidence=0.6"

# Get task status
curl http://localhost:8000/api/task/{task_id}

# Get all videos
curl http://localhost:8000/api/videos

# Search videos
curl "http://localhost:8000/api/search?query=test"

# Get statistics
curl http://localhost:8000/api/statistics

# Delete video
curl -X DELETE http://localhost:8000/api/videos/1
```

### Using Python Requests

```python
import requests
import time

# Upload video
with open('test_video.mp4', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/analyze',
        files={'file': f},
        data={'crowd_threshold': 5, 'confidence': 0.6}
    )

task_id = response.json()['task_id']
print(f"Task ID: {task_id}")

# Poll for results
while True:
    response = requests.get(f'http://localhost:8000/api/task/{task_id}')
    task = response.json()
    
    print(f"Status: {task['status']}, Progress: {task['progress']}%")
    
    if task['status'] == 'completed':
        print("Analysis complete!")
        print(task['result'])
        break
    elif task['status'] == 'failed':
        print("Analysis failed!")
        break
    
    time.sleep(2)
```

---

## Performance Testing

### Benchmark Detection Speed

**File**: `tests/test_performance.py`

```python
import pytest
from src.detection.yolo_detector import YOLODetector
import numpy as np

class TestPerformance:
    
    @pytest.fixture
    def detector(self):
        return YOLODetector(model_size='s', device='cpu')
    
    @pytest.fixture
    def frame(self):
        return np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
    
    def test_detection_speed(self, detector, frame, benchmark):
        """Benchmark detection speed"""
        result = benchmark(detector.detect_frame, frame)
        assert result is not None
    
    def test_video_processing_speed(self, detector, benchmark):
        """Benchmark full video processing"""
        def process_test_video():
            # Process 100 frames
            frames = [
                np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
                for _ in range(100)
            ]
            for frame in frames:
                detector.detect_frame(frame)
        
        benchmark(process_test_video)
```

### Load Testing

**File**: `locustfile.py`

```python
from locust import HttpUser, task, between

class CCTVUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def get_videos(self):
        """Repeatedly fetch videos"""
        self.client.get("/api/videos")
    
    @task(2)
    def get_statistics(self):
        """Fetch statistics"""
        self.client.get("/api/statistics")
    
    @task(1)
    def search_videos(self):
        """Search videos"""
        self.client.get("/api/search?query=test")
    
    @task(1)
    def upload_video(self):
        """Upload small test video"""
        with open('test_video.mp4', 'rb') as f:
            self.client.post(
                "/api/analyze",
                files={"file": ("test.mp4", f, "video/mp4")},
                data={"crowd_threshold": 5}
            )
```

**Run Load Test**:
```bash
# Install locust
pip install locust

# Run test
locust -f locustfile.py --host=http://localhost:8000

# Open browser: http://localhost:8089
# Set users and spawn rate
```

---

## User Acceptance Testing

### UAT Test Cases

#### Test Case 1: Video Upload and Analysis
```
Preconditions: System is running
Steps:
1. Navigate to http://localhost:8000
2. Click "Analyze" tab
3. Upload test video (crowd_scene.mp4)
4. Set crowd threshold to 5
5. Click "Start Analysis"
6. Wait for completion

Expected Result:
- Progress bar shows 0-100%
- Analysis completes without errors
- Results show anomaly count
- Annotated video is playable

Pass/Fail: _____
```

#### Test Case 2: Live Stream Monitoring
```
Preconditions: Webcam available
Steps:
1. Navigate to "Live" tab
2. Select "Webcam"
3. Click "Start Monitoring"
4. Move in front of camera
5. Stop monitoring

Expected Result:
- Live video feed displays
- Bounding boxes appear around person
- FPS counter shows reasonable rate (>10 FPS)
- No errors or freezing

Pass/Fail: _____
```

#### Test Case 3: Email Alert
```
Preconditions: Email configured
Steps:
1. Upload video with crowd scene
2. Complete analysis
3. Check email inbox

Expected Result:
- Email received within 1 minute
- Subject contains "Anomaly Alert"
- Body lists detected anomalies
- Email is properly formatted

Pass/Fail: _____
```

---

## Test Data

### Creating Test Videos

**Script**: `create_test_videos.py`

```python
import cv2
import numpy as np

def create_empty_video(filename, duration=10, fps=30):
    """Create video with no objects"""
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(filename, fourcc, fps, (640, 480))
    
    for _ in range(duration * fps):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        video.write(frame)
    
    video.release()

def create_crowd_video(filename, num_people=10):
    """Create video simulating crowd"""
    # Use actual footage or synthetic with OpenCV
    pass

# Generate test videos
create_empty_video('test_empty.mp4')
create_crowd_video('test_crowd.mp4', num_people=10)
```

### Test Dataset

Download sample videos:
```bash
# Crowd detection
wget https://sample-videos.com/crowd_scene.mp4

# Weapon detection
wget https://sample-videos.com/knife_scene.mp4

# Normal scene
wget https://sample-videos.com/normal_scene.mp4
```

---

## Continuous Integration

### GitHub Actions Workflow

**File**: `.github/workflows/test.yml`

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

---

## Test Coverage

### Generate Coverage Report

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html tests/

# Open report
open htmlcov/index.html
```

### Coverage Goals

| Module | Target Coverage |
|--------|----------------|
| detection | 90% |
| storage | 85% |
| alerts | 80% |
| API endpoints | 85% |
| Overall | 85% |

---

## Conclusion

Comprehensive testing ensures system reliability and quality. For deployment:

1. **Run all tests**: `pytest tests/`
2. **Check coverage**: Aim for >85%
3. **Performance test**: Ensure acceptable speed
4. **UAT**: Get user sign-off

**Next Steps**:
- See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for development workflow
- Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for production testing

---

*Last Updated: March 3, 2026*  
*Version: 3.0.0*
