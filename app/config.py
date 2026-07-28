import os
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _database_url() -> str | None:
    configured_url = os.getenv("DATABASE_URL")
    if configured_url:
        return configured_url

    host = os.getenv("DATABASE_HOST")
    if not host:
        return None

    user = quote(os.getenv("POSTGRES_USER", "sensor_app"), safe="")
    password = quote(os.getenv("POSTGRES_PASSWORD", ""), safe="")
    port = os.getenv("DATABASE_PORT", "5432")
    database = quote(os.getenv("POSTGRES_DB", "sensor_system"), safe="")
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() in {"1", "true", "yes"}

    MQTT_HOST = os.getenv("MQTT_HOST")
    MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
    MQTT_TOPIC = os.getenv("MQTT_TOPIC", "home/sensors/all")
    MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID")
    MQTT_USERNAME = os.getenv("MQTT_USERNAME_SERVER")
    MQTT_PASSWORD = os.getenv("MQTT_PASSWORD_SERVER")

    MQTT_DEVICE_ID = os.getenv("MQTT_DEVICE_ID", "esp32-1")
    THRESHOLDS_FILE = os.getenv("THRESHOLDS_FILE", "data/thresholds.json")

    DATABASE_URL = _database_url()
    APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Europe/Warsaw")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    OPENAI_VECTOR_STORE_ID = os.getenv("OPENAI_VECTOR_STORE_ID")

    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_HEADERS_ENABLED = True
    MAX_CONTENT_LENGTH = 32 * 1024
