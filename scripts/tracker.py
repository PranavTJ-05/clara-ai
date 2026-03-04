import json
import os
from datetime import datetime

TRACKER_FILE = os.path.join(os.path.dirname(__file__), "..", "tasks.json")

def create_task(account_id: str, summary: str, status: str = "Triage"):
    """
    Mocks an API call to a task tracker (like Asana) by appending to a local JSON array.
    This fulfills the zero-cost and no-paid-API requirements of the test.
    """
    tasks = []
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "r") as f:
            try:
                tasks = json.load(f)
            except json.JSONDecodeError:
                tasks = []
                
    new_task = {
        "id": f"task_{int(datetime.now().timestamp())}",
        "account_id": account_id,
        "summary": summary,
        "status": status,
        "created_at": datetime.now().isoformat()
    }
    
    tasks.append(new_task)
    
    with open(TRACKER_FILE, "w") as f:
        json.dump(tasks, f, indent=2)
        
    print(f"Task created in tracker: {summary}")
