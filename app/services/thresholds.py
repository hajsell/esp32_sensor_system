import json
import os
from typing import Any

DEFAULT_WARNING = {
    "temperature": 35.0,
    "humidity": 75.0,
    "mq2": 2450.0,
    "mq7": 4200.0,
}


def _clamp_humidity(v: float) -> float:
    """Zapewnia, że wilgotność mieści się w zakresie 0-100%."""
    return max(0.0, min(100.0, float(v)))


def normalize_warning(warn: dict[str, Any]) -> dict[str, Any]:
    """Waliduje i uzupełnia brakujące progi wartościami domyślnymi."""
    out = {}
    for k in DEFAULT_WARNING.keys():
        try:
            fv = float(warn.get(k, DEFAULT_WARNING[k]))
            out[k] = _clamp_humidity(fv) if k == "humidity" else fv
        except (ValueError, TypeError):
            out[k] = DEFAULT_WARNING[k]
    return out


def load_warning_thresholds(path: str) -> dict[str, Any]:
    """Ładuje progi z pliku JSON lub tworzy nowe, jeśli plik nie istnieje."""
    if not os.path.exists(path):
        return save_warning_thresholds(path, DEFAULT_WARNING)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if "warning" in data else save_warning_thresholds(path, DEFAULT_WARNING)
    except (json.JSONDecodeError, IOError):
        return save_warning_thresholds(path, DEFAULT_WARNING)


def save_warning_thresholds(path: str, warning: dict[str, Any]) -> dict[str, Any]:
    """Zapisuje progi do pliku w uproszczonym formacie (tylko sekcja warning)."""
    warn_norm = normalize_warning(warning)
    full_data = {"warning": warn_norm}

    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(full_data, f, indent=2, ensure_ascii=False)
    return full_data


def thresholds_snapshot(path: str) -> dict[str, Any]:
    """Zwraca aktualny stan progów."""
    return load_warning_thresholds(path)


def check_violations(current_data: dict[str, Any], thresholds: dict[str, Any]) -> list[str]:
    """Porównuje dane z czujników z progami ostrzegawczymi."""
    violations = []
    warn_levels = thresholds.get("warning", {})

    for key, value in current_data.items():
        if key in warn_levels and value is not None:
            if value >= warn_levels[key]:
                violations.append(f"Ostrzeżenie: {key} wynosi {value} (próg: {warn_levels[key]})")

    return violations