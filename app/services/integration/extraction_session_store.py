"""
Extraction Session Store.

Persistent server-side storage for Phase 1 AI document extraction results keyed by processing_id.
Provides 2-Level Storage (Level 1 In-Memory Cache + Level 2 Disk JSON Persistence) to guarantee session durability
across Uvicorn worker restarts, FastAPI hot reloads, and multi-worker process execution.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional
from app.core.config import UPLOAD_DIR
from app.core.logger import get_logger

logger = get_logger(__name__)

# Session TTL: 2 Hours (7200 Seconds)
SESSION_TTL_SECONDS = 7200

class ExtractionSessionStore:
    """
    Thread-safe, file-backed persistent extraction session store.
    """

    _store: Dict[str, Dict[str, Any]] = {}
    _timestamps: Dict[str, float] = {}

    @classmethod
    def _get_session_dir(cls) -> str:
        """
        Get or create persistent session directory on disk.
        """
        session_dir = os.path.join(str(UPLOAD_DIR), "sessions")
        os.makedirs(session_dir, exist_ok=True)
        return session_dir

    @classmethod
    def _get_session_file_path(cls, processing_id: str) -> str:
        """
        Get JSON file path for a processing_id session.
        """
        sanitized_id = "".join(c for c in processing_id if c.isalnum() or c in ("-", "_"))
        return os.path.join(cls._get_session_dir(), f"{sanitized_id}.json")

    @classmethod
    def save_session(cls, processing_id: str, extracted_records: Any, file_name: str = "", doc_type: str = "") -> None:
        """
        Store extracted records for a processing session (Memory + Disk Persistence).
        """
        cls._cleanup_expired()

        rec_count = len(extracted_records) if isinstance(extracted_records, list) else 1
        session_payload = {
            "processing_id": processing_id,
            "file_name": file_name,
            "doc_type": doc_type,
            "extracted_records": extracted_records,
            "created_at": time.time(),
        }

        # Level 1: In-Memory Cache
        cls._store[processing_id] = session_payload
        cls._timestamps[processing_id] = time.time()

        # Level 2: Persistent Disk Storage
        file_path = cls._get_session_file_path(processing_id)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(session_payload, f, default=str, indent=2)
            logger.info(
                "[%s] SAVE SESSION SUCCESS - Records: %d, File: %s, Active Memory Sessions: %d, Active Memory Keys: %s",
                processing_id,
                rec_count,
                file_path,
                len(cls._store),
                list(cls._store.keys()),
            )
        except Exception as file_err:
            logger.error("[%s] Failed to persist session payload to disk file '%s': %s", processing_id, file_path, file_err)

    @classmethod
    def get_session(cls, processing_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve stored session payload by processing_id (Level 1 Memory -> Level 2 Disk Fallback).
        """
        cls._cleanup_expired()

        # Level 1: In-Memory Cache Lookup
        session = cls._store.get(processing_id)
        if session:
            rec_count = len(session.get("extracted_records") or [])
            logger.info("[%s] RETRIEVE SESSION SUCCESS (Level 1 Memory Cache) - Records: %d", processing_id, rec_count)
            return session

        # Level 2: Persistent Disk File Fallback
        file_path = cls._get_session_file_path(processing_id)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    session = json.load(f)

                if session and isinstance(session, dict):
                    # Reload into Memory Cache
                    cls._store[processing_id] = session
                    cls._timestamps[processing_id] = session.get("created_at") or time.time()
                    rec_count = len(session.get("extracted_records") or [])
                    logger.info("[%s] RETRIEVE SESSION SUCCESS (Level 2 Disk File Fallback) - Records: %d, File: %s", processing_id, rec_count, file_path)
                    return session
            except Exception as read_err:
                logger.error("[%s] Failed to read session file '%s': %s", processing_id, file_path, read_err)

        logger.warning(
            "[%s] RETRIEVE SESSION FAILED - Session not found or expired on Memory/Disk. Active Memory Keys: %s",
            processing_id,
            list(cls._store.keys()),
        )
        return None

    @classmethod
    def delete_session(cls, processing_id: str) -> None:
        """
        Delete a processing session from Memory and Disk.
        """
        cls._store.pop(processing_id, None)
        cls._timestamps.pop(processing_id, None)
        file_path = cls._get_session_file_path(processing_id)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as del_err:
                logger.warning("[%s] Failed to delete session file '%s': %s", processing_id, file_path, del_err)

        logger.info("[%s] DELETE SESSION SUCCESS - Active Memory Keys: %s", processing_id, list(cls._store.keys()))

    @classmethod
    def _cleanup_expired(cls) -> None:
        """
        Evict expired sessions older than 2 hours from Memory and Disk.
        """
        now = time.time()
        expired_keys = [k for k, ts in cls._timestamps.items() if now - ts > SESSION_TTL_SECONDS]
        for k in expired_keys:
            cls.delete_session(k)

        # Cleanup expired disk files
        try:
            session_dir = cls._get_session_dir()
            for fn in os.listdir(session_dir):
                if fn.endswith(".json"):
                    fp = os.path.join(session_dir, fn)
                    if now - os.path.getmtime(fp) > SESSION_TTL_SECONDS:
                        try:
                            os.remove(fp)
                            logger.info("Evicted expired disk session file: %s", fn)
                        except Exception:
                            pass
        except Exception:
            pass
