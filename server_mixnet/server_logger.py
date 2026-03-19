# Incomplete Server Logger
import json, time, os, threading

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

_lock = threading.Lock()

def log_event(server_id, event, **fields):
    record = {
        "timestamp": time.time(),
        "server": server_id,
        "event": event,
        **fields
    }

    filename = os.path.join(LOG_DIR, f"server_{server_id}.log")

    with _lock:
        with open(filename, "a") as f:
            f.write(json.dumps(record) + "\n")