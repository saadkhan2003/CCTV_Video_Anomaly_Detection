# API Documentation

## CCTV Video Anomaly Detection System API Reference

Version: 3.0.0  
Base URL: `http://localhost:8000`

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Endpoints](#endpoints)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Examples](#examples)

---

## Overview

The CCTV Video Anomaly Detection API provides RESTful endpoints for:
- Video upload and analysis
- Live stream monitoring
- Database queries and statistics
- Task management and progress tracking

### Technology Stack
- **Framework**: FastAPI
- **ML Engine**: YOLOv11 with OpenVINO optimization
- **Database**: SQLite
- **Real-time**: Server-Sent Events (SSE)

---

## Authentication

Currently, the API does not require authentication. For production deployment, consider implementing:
- API Key authentication
- JWT tokens
- OAuth2 integration

---

## Endpoints

### 1. Core Pages

#### GET `/`
Returns the main dashboard HTML page.

**Response**: HTML
**Status Codes**:
- `200 OK`: Success

---

#### GET `/live`
Returns the live stream monitoring page.

**Response**: HTML
**Status Codes**:
- `200 OK`: Success

---

### 2. Video Analysis

#### POST `/api/analyze`
Upload and analyze a video file for anomalies.

**Request**:
```http
POST /api/analyze
Content-Type: multipart/form-data

Parameters:
- file: Video file (MP4, AVI, MOV, MKV)
- crowd_threshold: int (default: 5) - Number of people to trigger crowd alert
- confidence: float (default: 0.5) - Detection confidence threshold (0.0-1.0)
```

**Example**:
```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -F "file=@surveillance.mp4" \
  -F "crowd_threshold=5" \
  -F "confidence=0.6"
```

**Response**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Analysis started"
}
```

**Status Codes**:
- `200 OK`: Task created successfully
- `400 Bad Request`: Invalid file format
- `413 Payload Too Large`: File too large

---

#### GET `/api/task/{task_id}`
Get the status and progress of an analysis task.

**Parameters**:
- `task_id` (path): UUID of the task

**Response**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 45,
  "result": null
}
```

**Status Values**:
- `queued`: Task is waiting to start
- `processing`: Analysis in progress
- `completed`: Analysis finished successfully
- `failed`: Analysis encountered an error

**Completed Result**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "result": {
    "video_id": 1,
    "stats": {
      "total_frames": 1800,
      "anomaly_frames": 120,
      "anomaly_rate": 0.067,
      "processing_time": 45.2,
      "anomaly_types_count": {
        "crowd": 50,
        "weapon": 30,
        "loitering": 40
      }
    },
    "output_video": "/static/videos/output_550e8400.mp4"
  }
}
```

**Status Codes**:
- `200 OK`: Task found
- `404 Not Found`: Task ID does not exist

---

### 3. Live Stream

#### GET `/api/live-stream`
Start real-time anomaly detection on a video stream.

**Parameters (Query)**:
- `source` (string): 
  - `"0"` or `"webcam"` for webcam
  - RTSP URL for IP camera (e.g., `rtsp://admin:pass@192.168.1.100:554/stream1`)
- `crowd_threshold` (int, default: 5): Crowd detection threshold
- `confidence` (float, default: 0.5): Detection confidence

**Response**: Server-Sent Events (SSE) stream

**Event Types**:
1. **frame**: JPEG frame data (base64 encoded)
2. **anomaly**: Anomaly detection event
3. **stats**: Real-time statistics
4. **error**: Error message
5. **end**: Stream ended

**Example Connection (JavaScript)**:
```javascript
const eventSource = new EventSource(
  '/api/live-stream?source=rtsp://192.168.1.100:554/stream1&crowd_threshold=5'
);

eventSource.addEventListener('frame', (event) => {
  const data = JSON.parse(event.data);
  // Update video display with base64 image
  videoElement.src = 'data:image/jpeg;base64,' + data.frame;
});

eventSource.addEventListener('anomaly', (event) => {
  const data = JSON.parse(event.data);
  console.log('Anomaly detected:', data);
  // data.type: "crowd" | "weapon" | "loitering" | "fast_movement"
  // data.details: additional information
});

eventSource.addEventListener('stats', (event) => {
  const data = JSON.parse(event.data);
  // data.fps, data.people_count, data.vehicles_count
});
```

**Status Codes**:
- `200 OK`: Stream started
- `400 Bad Request`: Invalid source
- `503 Service Unavailable`: Camera not accessible

---

### 4. Database Operations

#### GET `/api/videos`
Retrieve all analyzed videos from the database.

**Parameters (Query)**:
- `limit` (int, optional): Maximum number of results
- `offset` (int, optional): Skip N results (pagination)

**Response**:
```json
{
  "videos": [
    {
      "id": 1,
      "filename": "lobby_cam.mp4",
      "timestamp": "2026-03-03T14:30:00",
      "frame_count": 1800,
      "anomaly_count": 120,
      "anomaly_rate": 0.067,
      "processing_time": 45.2,
      "threshold_used": 5,
      "output_video_path": "/static/videos/output_1.mp4"
    }
  ],
  "total": 1
}
```

**Status Codes**:
- `200 OK`: Success

---

#### GET `/api/videos/{video_id}`
Get detailed information about a specific video.

**Parameters**:
- `video_id` (path): Video ID

**Response**:
```json
{
  "id": 1,
  "filename": "lobby_cam.mp4",
  "timestamp": "2026-03-03T14:30:00",
  "frame_count": 1800,
  "anomaly_count": 120,
  "anomaly_rate": 0.067,
  "processing_time": 45.2,
  "threshold_used": 5,
  "anomaly_scores": [0.0, 0.0, 1.0, ...],
  "anomaly_flags": [false, false, true, ...],
  "output_video_path": "/static/videos/output_1.mp4"
}
```

**Status Codes**:
- `200 OK`: Video found
- `404 Not Found`: Video ID does not exist

---

#### DELETE `/api/videos/{video_id}`
Delete a video and its analysis results.

**Parameters**:
- `video_id` (path): Video ID

**Response**:
```json
{
  "message": "Video deleted successfully",
  "video_id": 1
}
```

**Status Codes**:
- `200 OK`: Deleted successfully
- `404 Not Found`: Video not found

---

#### GET `/api/search`
Search videos by filename or date range.

**Parameters (Query)**:
- `query` (string, optional): Search term for filename
- `start_date` (string, optional): ISO format date (e.g., `2026-03-01`)
- `end_date` (string, optional): ISO format date

**Example**:
```bash
curl "http://localhost:8000/api/search?query=lobby&start_date=2026-03-01"
```

**Response**:
```json
{
  "results": [
    {
      "id": 1,
      "filename": "lobby_cam.mp4",
      "timestamp": "2026-03-03T14:30:00",
      "anomaly_count": 120
    }
  ],
  "count": 1
}
```

**Status Codes**:
- `200 OK`: Success

---

#### GET `/api/statistics`
Get aggregated statistics across all analyzed videos.

**Response**:
```json
{
  "total_videos": 15,
  "total_frames": 27000,
  "total_anomalies": 1800,
  "average_anomaly_rate": 0.067,
  "total_processing_time": 450.5,
  "anomaly_breakdown": {
    "crowd": 800,
    "weapon": 300,
    "loitering": 400,
    "fast_movement": 300
  },
  "daily_stats": [
    {
      "date": "2026-03-03",
      "videos": 5,
      "anomalies": 600
    }
  ]
}
```

**Status Codes**:
- `200 OK`: Success

---

### 5. System Health

#### GET `/api/health`
Check API health status.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-03T15:45:00",
  "version": "3.0.0",
  "model_loaded": true,
  "database_connected": true
}
```

**Status Codes**:
- `200 OK`: System healthy
- `503 Service Unavailable`: System unhealthy

---

## Data Models

### Video Record
```python
{
  "id": int,
  "filename": str,
  "timestamp": datetime,
  "frame_count": int,
  "anomaly_count": int,
  "anomaly_rate": float,
  "processing_time": float,
  "threshold_used": int,
  "anomaly_scores": List[float],
  "anomaly_flags": List[bool],
  "output_video_path": str
}
```

### Anomaly Types
- **crowd**: More people than threshold detected
- **weapon**: Knife, baseball bat, or scissors detected
- **loitering**: Person staying in one spot too long (>10 seconds)
- **fast_movement**: Rapid movement detected (potential running/panic)
- **conflict**: Multiple people in very close proximity
- **vehicle**: Vehicle detection or traffic anomaly

---

## Error Handling

### Standard Error Response
```json
{
  "detail": "Error message description",
  "error_code": "ERROR_CODE",
  "timestamp": "2026-03-03T15:45:00"
}
```

### Common Error Codes

| Status Code | Error Code | Description |
|-------------|-----------|-------------|
| 400 | INVALID_FILE_FORMAT | File format not supported |
| 400 | INVALID_PARAMETERS | Invalid request parameters |
| 404 | RESOURCE_NOT_FOUND | Video or task not found |
| 413 | FILE_TOO_LARGE | Uploaded file exceeds limit |
| 500 | INTERNAL_ERROR | Server error during processing |
| 503 | SERVICE_UNAVAILABLE | Model not loaded or system overloaded |

---

## Rate Limiting

**Current Policy**: No rate limiting implemented

**Recommended for Production**:
- 100 requests per minute per IP
- 10 concurrent video analyses per user
- 5 live streams per IP

---

## Examples

### Complete Workflow Example

```python
import requests
import time

# 1. Upload video for analysis
files = {'file': open('surveillance.mp4', 'rb')}
data = {'crowd_threshold': 5, 'confidence': 0.6}
response = requests.post('http://localhost:8000/api/analyze', files=files, data=data)
task_id = response.json()['task_id']

# 2. Poll for progress
while True:
    response = requests.get(f'http://localhost:8000/api/task/{task_id}')
    task_data = response.json()
    
    if task_data['status'] == 'completed':
        print(f"Analysis complete! Video ID: {task_data['result']['video_id']}")
        break
    elif task_data['status'] == 'failed':
        print("Analysis failed!")
        break
    else:
        print(f"Progress: {task_data['progress']}%")
        time.sleep(2)

# 3. Get video details
video_id = task_data['result']['video_id']
response = requests.get(f'http://localhost:8000/api/videos/{video_id}')
video_data = response.json()
print(f"Anomaly rate: {video_data['anomaly_rate'] * 100:.2f}%")

# 4. Get statistics
response = requests.get('http://localhost:8000/api/statistics')
stats = response.json()
print(f"Total videos analyzed: {stats['total_videos']}")
```

### JavaScript Fetch Example

```javascript
// Upload and analyze video
async function analyzeVideo(file, crowdThreshold = 5) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('crowd_threshold', crowdThreshold);
  formData.append('confidence', 0.6);

  const response = await fetch('/api/analyze', {
    method: 'POST',
    body: formData
  });

  const data = await response.json();
  return data.task_id;
}

// Check task status
async function checkTaskStatus(taskId) {
  const response = await fetch(`/api/task/${taskId}`);
  return await response.json();
}

// Get all videos
async function getAllVideos() {
  const response = await fetch('/api/videos');
  return await response.json();
}
```

---

## WebSocket Alternative (Future Enhancement)

For real-time bidirectional communication, consider implementing WebSocket endpoints:

```
ws://localhost:8000/ws/live-stream?source=0&threshold=5
```

This would allow:
- Control commands (pause, resume, stop)
- Real-time alerts without SSE
- Better connection management

---

## Changelog

### Version 3.0.0 (Current)
- YOLOv11 model integration
- OpenVINO optimization
- Live stream SSE support
- Enhanced anomaly detection rules

### Version 2.0.0
- YOLOv8 integration
- Database storage
- Email alerts

### Version 1.0.0
- Basic video analysis
- Simple object detection

---

## Support

For API issues or questions:
- GitHub Issues: [Project Repository Issues]
- Email: support@example.com
- Documentation: See `/docs` folder

---

## License

MIT License - See LICENSE file for details
