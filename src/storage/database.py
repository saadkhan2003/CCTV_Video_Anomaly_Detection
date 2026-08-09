"""
SQLite Database Layer for Anomaly Detection History
====================================================

Stores and retrieves video analysis history, enabling search and filtering
of past anomaly detection results.
"""

import sqlite3
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import json

# Store application data in the project root. Older releases wrote to src/storage;
# that database is imported once during startup without modifying the source file.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, "anomaly_history.db")
LEGACY_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "anomaly_history.db")


def get_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create videos table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            frame_count INTEGER,
            anomaly_count INTEGER,
            anomaly_rate REAL,
            processing_time REAL,
            threshold_used REAL,
            output_video_path TEXT,
            original_video_path TEXT,
            avg_anomaly_score REAL,
            max_anomaly_score REAL
        )
    ''')
    
    # Create anomaly_events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anomaly_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            frame_number INTEGER,
            anomaly_score REAL,
            timestamp_in_video REAL,
            is_anomaly BOOLEAN,
            bounding_boxes TEXT,
            FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_tasks (
            task_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            progress INTEGER NOT NULL DEFAULT 0,
            result_json TEXT,
            error TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS legacy_video_imports (
            source_path TEXT NOT NULL,
            legacy_video_id INTEGER NOT NULL,
            imported_video_id INTEGER NOT NULL,
            PRIMARY KEY (source_path, legacy_video_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    _import_legacy_database()
    _normalize_legacy_timestamps()
    print("✅ Database initialized successfully!")


def _import_legacy_database():
    """Import analyses from the pre-v3 storage location exactly once."""
    if not os.path.exists(LEGACY_DB_PATH) or os.path.samefile(DB_PATH, LEGACY_DB_PATH):
        return

    source_path = os.path.abspath(LEGACY_DB_PATH)
    legacy_conn = sqlite3.connect(LEGACY_DB_PATH)
    legacy_conn.row_factory = sqlite3.Row
    conn = get_connection()

    try:
        legacy_videos = legacy_conn.execute("SELECT * FROM videos ORDER BY id").fetchall()
        for legacy_video in legacy_videos:
            already_imported = conn.execute(
                "SELECT 1 FROM legacy_video_imports WHERE source_path = ? AND legacy_video_id = ?",
                (source_path, legacy_video["id"]),
            ).fetchone()
            if already_imported:
                continue

            fields = (
                "filename", "upload_time", "frame_count", "anomaly_count", "anomaly_rate",
                "processing_time", "threshold_used", "output_video_path", "original_video_path",
                "avg_anomaly_score", "max_anomaly_score",
            )
            conn.execute(
                f"INSERT INTO videos ({', '.join(fields)}) VALUES ({', '.join('?' for _ in fields)})",
                tuple(legacy_video[field] for field in fields),
            )
            imported_video_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute(
                "INSERT INTO legacy_video_imports VALUES (?, ?, ?)",
                (source_path, legacy_video["id"], imported_video_id),
            )

            legacy_events = legacy_conn.execute(
                "SELECT frame_number, anomaly_score, timestamp_in_video, is_anomaly, bounding_boxes "
                "FROM anomaly_events WHERE video_id = ?",
                (legacy_video["id"],),
            ).fetchall()
            conn.executemany(
                "INSERT INTO anomaly_events "
                "(video_id, frame_number, anomaly_score, timestamp_in_video, is_anomaly, bounding_boxes) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [(imported_video_id, *tuple(event)) for event in legacy_events],
            )
        conn.commit()
    except sqlite3.Error as exc:
        conn.rollback()
        print(f"Warning: could not import legacy database: {exc}")
    finally:
        legacy_conn.close()
        conn.close()


def _normalize_legacy_timestamps():
    """Mark SQLite's older timezone-less UTC values as UTC for browsers."""
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE videos
            SET upload_time = REPLACE(upload_time, ' ', 'T') || 'Z'
            WHERE upload_time GLOB '????-??-?? ??:??:??'
            """
        )
        conn.commit()
    finally:
        conn.close()


def create_analysis_task(task_id: str):
    """Persist a newly queued analysis task."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO analysis_tasks (task_id, status, progress) VALUES (?, 'queued', 0)",
        (task_id,),
    )
    conn.commit()
    conn.close()


def update_analysis_task(
    task_id: str,
    *,
    status: Optional[str] = None,
    progress: Optional[int] = None,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
):
    """Update the durable task record while retaining unspecified fields."""
    updates = []
    values = []
    if status is not None:
        updates.append("status = ?")
        values.append(status)
    if progress is not None:
        updates.append("progress = ?")
        values.append(progress)
    if result is not None:
        updates.append("result_json = ?")
        values.append(json.dumps(result))
    if error is not None:
        updates.append("error = ?")
        values.append(error)
    if not updates:
        return

    updates.append("updated_at = CURRENT_TIMESTAMP")
    values.append(task_id)
    conn = get_connection()
    conn.execute(f"UPDATE analysis_tasks SET {', '.join(updates)} WHERE task_id = ?", values)
    conn.commit()
    conn.close()


def get_analysis_task(task_id: str) -> Optional[Dict[str, Any]]:
    """Return a persisted task in the API response shape."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM analysis_tasks WHERE task_id = ?", (task_id,)).fetchone()
    conn.close()
    if not row:
        return None

    task = dict(row)
    task["result"] = json.loads(task.pop("result_json")) if task.get("result_json") else None
    task.pop("created_at", None)
    task.pop("updated_at", None)
    return task


def mark_interrupted_tasks_failed():
    """Make restart behavior explicit because in-process background work cannot resume."""
    conn = get_connection()
    conn.execute(
        "UPDATE analysis_tasks SET status = 'failed', "
        "error = 'Server restarted before analysis could finish', updated_at = CURRENT_TIMESTAMP "
        "WHERE status IN ('queued', 'processing')"
    )
    conn.commit()
    conn.close()


def save_video_analysis(
    filename: str,
    frame_count: int,
    anomaly_count: int,
    anomaly_rate: float,
    processing_time: float,
    threshold_used: float,
    anomaly_scores: List[float],
    anomaly_flags: List[bool],
    output_video_path: Optional[str] = None,
    original_video_path: Optional[str] = None,
    frame_bboxes: Optional[List[List[Dict]]] = None
) -> int:
    """
    Save video analysis results to database
    
    Returns:
        video_id: The ID of the saved video record
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Calculate additional stats
    avg_score = sum(anomaly_scores) / len(anomaly_scores) if anomaly_scores else 0
    max_score = max(anomaly_scores) if anomaly_scores else 0
    
    # Insert video record
    cursor.execute('''
        INSERT INTO videos (
            filename, upload_time, frame_count, anomaly_count, anomaly_rate,
            processing_time, threshold_used, output_video_path,
            original_video_path, avg_anomaly_score, max_anomaly_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        filename, datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        frame_count, anomaly_count, anomaly_rate,
        processing_time, threshold_used, output_video_path,
        original_video_path, avg_score, max_score
    ))
    
    video_id = cursor.lastrowid
    if video_id is None:
        conn.close()
        raise RuntimeError("Failed to insert video record and retrieve its ID.")
    
    # Insert anomaly events for each frame
    fps = 30  # Assume 30 fps, can be made dynamic
    for i, (score, is_anomaly) in enumerate(zip(anomaly_scores, anomaly_flags)):
        bboxes_json = None
        if frame_bboxes and i < len(frame_bboxes):
            bboxes_json = json.dumps(frame_bboxes[i])
        
        cursor.execute('''
            INSERT INTO anomaly_events (
                video_id, frame_number, anomaly_score,
                timestamp_in_video, is_anomaly, bounding_boxes
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (video_id, i, score, i / fps, is_anomaly, bboxes_json))
    
    conn.commit()
    conn.close()
    
    return video_id


def get_all_videos(limit: int = 50, offset: int = 0) -> List[Dict]:
    """Get all video analyses with pagination"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM videos
        ORDER BY upload_time DESC
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_video_by_id(video_id: int) -> Optional[Dict]:
    """Get a specific video analysis by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM videos WHERE id = ?', (video_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def get_anomaly_events(video_id: int) -> List[Dict]:
    """Get all anomaly events for a video"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM anomaly_events
        WHERE video_id = ?
        ORDER BY frame_number
    ''', (video_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        event = dict(row)
        # Parse bounding boxes JSON
        if event.get('bounding_boxes'):
            event['bounding_boxes'] = json.loads(event['bounding_boxes'])
        result.append(event)
    
    return result


def search_videos(
    filename: Optional[str] = None,
    min_anomaly_rate: Optional[float] = None,
    max_anomaly_rate: Optional[float] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50
) -> List[Dict]:
    """Search videos with various filters"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM videos WHERE 1=1'
    params = []
    
    if filename:
        query += ' AND filename LIKE ?'
        params.append(f'%{filename}%')
    
    if min_anomaly_rate is not None:
        query += ' AND anomaly_rate >= ?'
        params.append(min_anomaly_rate)
    
    if max_anomaly_rate is not None:
        query += ' AND anomaly_rate <= ?'
        params.append(max_anomaly_rate)
    
    if start_date:
        query += ' AND date(upload_time) >= date(?)'
        params.append(start_date)
    
    if end_date:
        query += ' AND date(upload_time) <= date(?)'
        params.append(end_date)
    
    query += ' ORDER BY upload_time DESC LIMIT ?'
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def delete_video(video_id: int) -> bool:
    """Delete a video analysis and its events"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get video info first to delete associated files
    cursor.execute('SELECT output_video_path FROM videos WHERE id = ?', (video_id,))
    row = cursor.fetchone()
    
    if row and row['output_video_path']:
        video_path = row['output_video_path']
        if os.path.exists(video_path):
            os.remove(video_path)
    
    # Delete from database (cascade will delete anomaly_events)
    cursor.execute('DELETE FROM videos WHERE id = ?', (video_id,))
    deleted = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    
    return deleted


def get_statistics() -> Dict[str, Any]:
    """Get overall statistics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total_videos,
            SUM(frame_count) as total_frames,
            AVG(anomaly_rate) as avg_anomaly_rate,
            SUM(anomaly_count) as total_anomalies,
            AVG(processing_time) as avg_processing_time
        FROM videos
    ''')
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else {}


# Initialize database on import
init_database()
