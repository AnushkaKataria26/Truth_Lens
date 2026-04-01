"""
Registry Database — SQLite Backend
=====================================
Provides the persistent storage layer for the model registry.
Schema: models table with id, name, version, path, metrics (JSON),
config_hash, status, and timestamps.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Generator

from training.config import REGISTRY_DIR

logger = logging.getLogger(__name__)

DB_PATH = REGISTRY_DIR / "model_registry.db"

# ── Schema ───────────────────────────────────────────────────────────────────

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS models (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    version     TEXT    NOT NULL,
    path        TEXT    NOT NULL,
    metrics     TEXT,                  -- JSON blob
    config_hash TEXT,
    status      TEXT    NOT NULL DEFAULT 'staged',
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL,
    UNIQUE(name, version)
);
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_models_name_status ON models(name, status);
"""


# ── Data transfer object ─────────────────────────────────────────────────────

@dataclass
class ModelRecord:
    id: int
    name: str
    version: str
    path: str
    metrics: dict | None
    config_hash: str | None
    status: str
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> ModelRecord:
        metrics = json.loads(row["metrics"]) if row["metrics"] else None
        return cls(
            id=row["id"],
            name=row["name"],
            version=row["version"],
            path=row["path"],
            metrics=metrics,
            config_hash=row["config_hash"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


# ── Database access ──────────────────────────────────────────────────────────

class RegistryDB:
    """Low-level SQLite registry database operations."""

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path or DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(CREATE_TABLE_SQL)
            conn.execute(CREATE_INDEX_SQL)

    # ── CRUD ─────────────────────────────────────────────────────────────

    def insert(
        self,
        name: str,
        version: str,
        path: str,
        metrics: dict | None = None,
        config_hash: str | None = None,
        status: str = "staged",
    ) -> int:
        """Insert a new model record. Returns the row id."""
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO models (name, version, path, metrics, config_hash, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, version, path, json.dumps(metrics) if metrics else None,
                 config_hash, status, now, now),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def get_by_id(self, row_id: int) -> ModelRecord | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM models WHERE id = ?", (row_id,)).fetchone()
        return ModelRecord.from_row(row) if row else None

    def get_active(self, name: str) -> ModelRecord | None:
        """Get the currently active model for a given model name."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM models WHERE name = ? AND status = 'active' ORDER BY id DESC LIMIT 1",
                (name,),
            ).fetchone()
        return ModelRecord.from_row(row) if row else None

    def get_all_versions(self, name: str) -> list[ModelRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM models WHERE name = ? ORDER BY id DESC", (name,),
            ).fetchall()
        return [ModelRecord.from_row(r) for r in rows]

    def update_status(self, row_id: int, status: str) -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                "UPDATE models SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, row_id),
            )

    def deactivate_all(self, name: str) -> None:
        """Set all versions of a model to 'archived'."""
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                "UPDATE models SET status = 'archived', updated_at = ? WHERE name = ? AND status = 'active'",
                (now, name),
            )

    def get_latest(self, name: str) -> ModelRecord | None:
        """Get the most recently registered version."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM models WHERE name = ? ORDER BY id DESC LIMIT 1",
                (name,),
            ).fetchone()
        return ModelRecord.from_row(row) if row else None

    def get_by_version(self, name: str, version: str) -> ModelRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM models WHERE name = ? AND version = ?",
                (name, version),
            ).fetchone()
        return ModelRecord.from_row(row) if row else None
