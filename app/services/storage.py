import json
import os
from datetime import datetime, timedelta
from typing import Any

TS_FMT = "%Y-%m-%d %H:%M:%S"

def parse_ts(ts: str) -> datetime | None:
    try:
        return datetime.strptime(ts, TS_FMT)
    except:
        return None

def read_all(path: str) -> list[dict[str, Any]]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read().strip()
            if not raw: return []
            data = json.loads(raw)
        return data if isinstance(data, list) else []
    except:
        return []

def _write_all(path: str, rows: list[dict[str, Any]]):
    dir_name = os.path.dirname(path)
    if dir_name: os.makedirs(dir_name, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

def prune_older_than_24h(rows: list[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
    cutoff = now - timedelta(hours=24)
    out = []
    for r in rows:
        ts_val = r.get("timestamp")
        if not ts_val: continue
        dt = parse_ts(str(ts_val))
        if dt and dt > cutoff:
            out.append(r)
    return out

def append_record(path: str, record: dict[str, Any], now: datetime | None = None):
    ref_now = now or datetime.now()
    raw_rows = read_all(path)
    clean_rows = prune_older_than_24h(raw_rows, ref_now)
    clean_rows.append(record)
    _write_all(path, clean_rows)

def _num(d: dict[str, Any], key: str) -> float | None:
    v = d.get(key)
    try:
        return float(v) if v is not None else None
    except:
        return None

def _level(value: float | None, warn: float | None, alarm: float | None) -> int:
    if value is None or warn is None: return 0
    if alarm is not None and value >= alarm: return 2
    if value >= warn: return 1
    return 0

def _any_threshold_state_change(new: dict[str, Any], last: dict[str, Any], thresholds: dict[str, Any]) -> bool:
    w = thresholds.get("warning", {})
    a = thresholds.get("alarm", {})
    for key in ("temperature", "humidity", "mq2", "mq7"):
        v_new = _num(new, key)
        v_last = _num(last, key)
        warn = _num(w, key)
        alarm = _num(a, key)
        if warn is None: continue
        if _level(v_new, warn, alarm) != _level(v_last, warn, alarm):
            return True
    return False

def should_save(new: dict[str, Any], last: dict[str, Any] | None, last_time: datetime | None, thresholds: dict[str, Any]) -> bool:
    if last is None or last_time is None: return True
    dt_new = parse_ts(str(new.get("timestamp", "")))
    if dt_new is None: return True
    if (dt_new - last_time).total_seconds() >= 300: return True
    return _any_threshold_state_change(new, last, thresholds)