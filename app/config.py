import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


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

    DATABASE_URL = os.getenv("DATABASE_URL")
    APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Europe/Warsaw")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_HEADERS_ENABLED = True
    MAX_CONTENT_LENGHT = 32 * 1024