"""
tracker.py — Simulates task/CRM integration by writing to tasks.json.
No paid APIs required.
"""

import json
import os
import uuid
from datetime import datetime, timezone

TASKS_FILE = "tasks/tasks.json"


def create_task(account_id: str, task_type: str, metadata: dict = None):
    """Append a task entry to tasks.json."""
    os.makedirs("tasks", exist_ok=True)

    existing = []
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE) as f:
                existing = json.load(f)
        except Exception:
            existing = []

    task = {
        "task_id": str(uuid.uuid4()),
        "account_id": account_id,
        "task_type": task_type,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata or {}
    }

    existing.append(task)

    with open(TASKS_FILE, "w") as f:
        json.dump(existing, f, indent=2)