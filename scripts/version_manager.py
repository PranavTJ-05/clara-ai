"""
version_manager.py — Manages deterministic versioned artifact storage.
"""

import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)
BASE = "outputs/accounts"


def save_artifact(account_id: str, version: str, filename: str, data: dict):
    """Save a JSON artifact to the correct versioned path."""
    path = os.path.join(BASE, account_id, version)
    os.makedirs(path, exist_ok=True)
    full_path = os.path.join(path, filename)
    with open(full_path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"[STORAGE] Saved {full_path}")


def load_artifact(account_id: str, version: str, filename: str) -> Optional[dict]:
    """Load a JSON artifact. Returns None if not found."""
    full_path = os.path.join(BASE, account_id, version, filename)
    if not os.path.exists(full_path):
        return None
    with open(full_path) as f:
        return json.load(f)


def version_exists(account_id: str, version: str) -> bool:
    """Check if a version directory already has artifacts (idempotency guard)."""
    path = os.path.join(BASE, account_id, version)
    if not os.path.exists(path):
        return False
    return bool(os.listdir(path))