import json
import os
from typing import Any

DEFAULT_WARNING = {
    "temperature": 30.0,
    "humidity": 75.0,
    "mq2": 1750.0,
    "mq7": 4200.0,
}

def _clamp_humidity(v: float) -> float:
    return max(0.0, min(100.0, float(v)))

def compute_alarm(warn: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for k, v in warn.items():
        try:
            fv = float(v)
            av = fv * 1.2
            out[k] = _clamp_humidity(av) if k == "humidity" else av
        except:
            out[k] = None
    return out

def normalize_warning(warn: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for k in DEFAULT_WARNING.keys():
        try:
            fv = float(warn.get(k, DEFAULT_WARNING[k]))
            out[k] = _clamp_humidity(fv) if k == "humidity" else fv
        except:
            out[k] = DEFAULT_WARNING[k]
    return out

def load_warning_thresholds(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        return save_warning_thresholds(path, DEFAULT_WARNING)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if "warning" in data else save_warning_thresholds(path, DEFAULT_WARNING)
    except:
        return save_warning_thresholds(path, DEFAULT_WARNING)

def save_warning_thresholds(path: str, warning: dict[str, Any]) -> dict[str, Any]:
    warn_norm = normalize_warning(warning)
    full_data = {"warning": warn_norm, "alarm": compute_alarm(warn_norm)}
    dir_name = os.path.dirname(path)
    if dir_name: os.makedirs(dir_name, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(full_data, f, indent=2, ensure_ascii=False)
    return full_data

def thresholds_snapshot(path: str) -> dict[str, Any]:
    return load_warning_thresholds(path)


def check_violations(current_data: dict[str, Any], thresholds: dict[str, Any]) -> list[str]:
    violations = []
    warn_levels = thresholds.get("warning", {})
    alarm_levels = thresholds.get("alarm", {})

    for key, value in current_data.items():
        if key in alarm_levels and value >= alarm_levels[key]:
            violations.append(f"ALARM: {key} wynosi {value} (próg: {alarm_levels[key]})")
        elif key in warn_levels and value >= warn_levels[key]:
            violations.append(f"Ostrzeżenie: {key} wynosi {value} (próg: {warn_levels[key]})")

    return violations