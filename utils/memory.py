"""
Persistent memory management for workflows using SQLite.
"""

import json
import time
import logging
import sqlite3
from typing import Optional, Dict, Any
from pathlib import Path
from contextlib import contextmanager
from langgraph.checkpoint.sqlite import SqliteSaver


logger = logging.getLogger(__name__)


class PersistentMemoryManager:
    """Manages persistent storage for workflow states."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.checkpointer = SqliteSaver.from_conn_string(str(db_path))

    def _init_db(self):
        """Initialize database tables."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_sessions (
                    user_id TEXT PRIMARY KEY,
                    workflow_type TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    response TEXT NOT NULL,
                    intent TEXT,
                    confidence REAL,
                    timestamp REAL NOT NULL
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_user_id 
                ON workflow_sessions(user_id)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_expires_at 
                ON workflow_sessions(expires_at)
            """
            )

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _serialize_state(self, state: Dict[str, Any]) -> str:
        """Convert non-serializable LangChain/LangGraph objects to JSON-safe."""

        def serialize(obj):
            # Handle LangChain message objects
            if hasattr(obj, "to_dict"):
                try:
                    return obj.to_dict()
                except Exception:
                    return str(obj)

            # Handle lists/tuples recursively
            if isinstance(obj, (list, tuple)):
                return [serialize(o) for o in obj]

            # Handle dicts recursively
            if isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}

            # Fallback for everything else
            try:
                json.dumps(obj)
                return obj
            except Exception:
                return str(obj)

        return json.dumps(serialize(state))

    def _deserialize_state(self, state_json: str) -> Dict[str, Any]:
        """Reconstruct LangChain messages from saved JSON."""
        from langchain_core.messages import HumanMessage, AIMessage

        def reconstruct(d):
            if isinstance(d, dict) and "type" in d:
                if d["type"] == "human":
                    return HumanMessage(**d)
                elif d["type"] == "ai":
                    return AIMessage(**d)
            elif isinstance(d, dict):
                return {k: reconstruct(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [reconstruct(x) for x in d]
            return d

        return reconstruct(json.loads(state_json))

    def save_workflow_state(
        self, user_id: str, workflow_type: str, state: Dict[str, Any], timeout: int
    ):
        """Save workflow state to database."""
        now = time.time()
        # state_json = json.dumps(state)
        state_json = self._serialize_state(state)

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO workflow_sessions 
                (user_id, workflow_type, state, created_at, updated_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (user_id, workflow_type, state_json, now, now, now + timeout),
            )

        logger.debug(f"Saved workflow state for user {user_id}")

    def get_workflow_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve workflow state from database."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT workflow_type, state, expires_at 
                FROM workflow_sessions 
                WHERE user_id = ?
            """,
                (user_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        # Check expiration
        if time.time() > row["expires_at"]:
            self.delete_workflow_state(user_id)
            logger.info(f"Workflow expired for user {user_id}")
            return None

        return {
            "workflow_type": row["workflow_type"],
            "state": json.loads(row["state"]),
        }

    def delete_workflow_state(self, user_id: str):
        """Delete workflow state from database."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM workflow_sessions WHERE user_id = ?", (user_id,))
        logger.debug(f"Deleted workflow state for user {user_id}")

    def save_conversation(
        self,
        user_id: str,
        message: str,
        response: str,
        intent: Optional[str] = None,
        confidence: Optional[float] = None,
    ):
        """Save conversation to history."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO conversation_history 
                (user_id, message, response, intent, confidence, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (user_id, message, response, intent, confidence, time.time()),
            )

    def get_conversation_history(self, user_id: str, limit: int = 10) -> list:
        """Retrieve conversation history."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT message, response, intent, confidence, timestamp
                FROM conversation_history
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (user_id, limit),
            )
            rows = cursor.fetchall()

        r = [dict(row) for row in rows]
        state = self._deserialize_state(r["state"])
        return state

    def cleanup_expired_sessions(self):
        """Remove expired workflow sessions."""
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM workflow_sessions WHERE expires_at < ?", (now,)
            )
            deleted = cursor.rowcount

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} expired sessions")

        return deleted
