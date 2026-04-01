"""
Model Registry — SQLite Database and API
==========================================
Tracks all trained model versions, active model per type, rollback history.
Separate from the main PostgreSQL database. Includes Redis integration so
inference workers immediately pick up the new active model upon promotion.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

# Note: assuming REDIS_URL or similar is in a global config, falling back to localhost
import redis

from training.config import REGISTRY_DIR, MODELS_DIR


REGISTRY_DB_PATH = REGISTRY_DIR / "registry.db"
# Initialize a simple Redis client (in production, use config params)
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


def init_registry() -> None:
    """Initialize the SQLite registry table."""
    REGISTRY_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(REGISTRY_DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_type TEXT NOT NULL,        -- efficientnetv2 | bilstm | vit | lora
            version TEXT NOT NULL,           -- v1.0, v1.1, lora_20260101_143000
            checkpoint_path TEXT NOT NULL,
            s3_path TEXT,
            val_auc REAL,
            val_eer REAL,
            test_auc REAL,
            test_eer REAL,
            is_active INTEGER DEFAULT 0,
            config_json TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        )
    """)
    con.commit()
    con.close()


def register(
    model_type: str,
    checkpoint_path: Path | str,
    val_auc: float | None = None,
    val_eer: float | None = None,
    config: dict | None = None,
    notes: str | None = None,
    upload_s3: bool = True,
) -> int:
    """Register a new model checkpoint version in SQLite and optionally upload to S3."""
    if not REGISTRY_DB_PATH.exists():
        init_registry()

    con = sqlite3.connect(REGISTRY_DB_PATH)
    
    # Auto-version: count existing versions of this model_type + 1
    count = con.execute("SELECT COUNT(*) FROM models WHERE model_type=?", (model_type,)).fetchone()[0]
    version = f"v{count + 1}.0"

    
    # Optional S3 Upload
    s3_path = None
    if upload_s3:
        try:
            s3_client = boto3.client('s3')
            s3_key = f"models/{model_type}/{version}/{Path(checkpoint_path).name}"
            s3_client.upload_file(str(checkpoint_path), "truthlens-media", s3_key)
            s3_path = f"s3://truthlens-media/{s3_key}"
            print(f"Uploaded model to {s3_path}")
        except Exception as e:
            print(f"S3 upload failed for {model_type} {version}: {e}")

    con.execute("""
        INSERT INTO models (model_type, version, checkpoint_path, s3_path, val_auc, val_eer,
                           config_json, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        model_type,
        version,
        str(checkpoint_path),
        s3_path,
        val_auc,
        val_eer,
        json.dumps(config) if config else None,
        notes,
        datetime.utcnow().isoformat()
    ))
    
    model_id = con.lastrowid
    con.commit()
    con.close()
    
    print(f"Registered {model_type} {version} (id={model_id})")
    return model_id


def set_active(model_id: int) -> None:
    """Promote a specific model ID to active and update Redis."""
    con = sqlite3.connect(REGISTRY_DB_PATH)
    model = con.execute("SELECT model_type FROM models WHERE id=?", (model_id,)).fetchone()
    if not model:
        con.close()
        raise ValueError(f"Model id={model_id} not found in registry")
    
    model_type = model[0]
    # Deactivate all versions of this model_type
    con.execute("UPDATE models SET is_active=0 WHERE model_type=?", (model_type,))
    # Activate selected version
    con.execute("UPDATE models SET is_active=1 WHERE id=?", (model_id,))
    con.commit()
    con.close()
    
    # Update Redis so inference workers pick up new active model
    try:
        redis_client.set(f"model:active:{model_type}", str(model_id))
        print(f"Activated model id={model_id} ({model_type}) and updated Redis.")
    except redis.ConnectionError:
        print(f"Activated model id={model_id} ({model_type}) in SQLite, but Redis is unreachable.")


def get_active(model_type: str) -> dict:
    """Retrieve metadata for the currently active model version of a category."""
    con = sqlite3.connect(REGISTRY_DB_PATH)
    row = con.execute(
        "SELECT * FROM models WHERE model_type=? AND is_active=1", (model_type,)
    ).fetchone()
    
    if not row:
        con.close()
        raise ValueError(f"No active model found for type: {model_type}")
        
    cols = [d[0] for d in con.description]
    con.close()
    
    return dict(zip(cols, row))


def rollback(model_type: str) -> None:
    """Activate the previous sequential version of a model type."""
    con = sqlite3.connect(REGISTRY_DB_PATH)
    rows = con.execute(
        "SELECT id FROM models WHERE model_type=? ORDER BY id DESC LIMIT 2", (model_type,)
    ).fetchall()
    con.close()
    
    if len(rows) < 2:
        raise ValueError(f"No previous version to roll back to for {model_type}")
        
    previous_id = rows[1][0]
    set_active(previous_id)
    print(f"Rolled back {model_type} to id={previous_id}")

def update_test_metrics(model_id: int, test_auc: float, test_eer: float) -> None:
    """Persist final test evaluation metrics into the registry."""
    con = sqlite3.connect(REGISTRY_DB_PATH)
    con.execute(
        "UPDATE models SET test_auc=?, test_eer=? WHERE id=?", 
        (test_auc, test_eer, model_id)
    )
    con.commit()
    con.close()
    print(f"Updated test metrics for model id={model_id}: AUC={test_auc:.4f}, EER={test_eer:.4f}")

