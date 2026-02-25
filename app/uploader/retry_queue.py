import sqlite3
import threading
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger()

DB_PATH = "data/queue.db"


class RetryQueue:

    def __init__(self):
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_path TEXT NOT NULL,
                    species TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    captured_at TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def add_event(self, image_path, species, confidence):
        with self.lock:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("""
                    INSERT INTO events 
                    (image_path, species, confidence, captured_at, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    image_path,
                    species,
                    confidence,
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat()
                ))
                conn.commit()

        logger.info("Event added to local queue.")

    def get_pending_events(self, limit=5):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("""
                SELECT id, image_path, species, confidence, retry_count
                FROM events
                WHERE status = 'pending'
                ORDER BY id ASC
                LIMIT ?
            """, (limit,))
            return cursor.fetchall()

    def mark_uploaded(self, event_id):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                UPDATE events
                SET status = 'uploaded'
                WHERE id = ?
            """, (event_id,))
            conn.commit()

    def mark_failed(self, event_id):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                UPDATE events
                SET retry_count = retry_count + 1
                WHERE id = ?
            """, (event_id,))
            conn.commit()