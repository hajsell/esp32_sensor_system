import json, os
from datetime import datetime

def read_all(path: str):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        content = f.read().strip()
        return json.loads(content) if content else []

def append_record(path: str, record: dict):
    existing = read_all(path)
    existing.append(record)
    with open(path, "w") as f:
        json.dump(existing, f, indent=2)

def should_save(new: dict, last: dict | None, last_time):
    if last_time is None or last is None:
        return True

    dt_new = datetime.strptime(new["timestamp"], "%Y-%m-%d %H:%M:%S")
    if (dt_new - last_time).total_seconds() >= 300:
        return True
    if abs(new["temperature"] - last["temperature"]) > 1:
        return True
    if abs(new["humidity"] - last["humidity"]) > 20:
        return True
    if abs(new["mq2"] - last["mq2"]) > 1000 or abs(new["mq7"] - last["mq7"]) > 1000:
        return True
    return False
