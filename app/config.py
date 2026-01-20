import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    MQTT_BROKER = os.getenv("MQTT_BROKER")
    MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
    MQTT_TOPIC = os.getenv("MQTT_TOPIC", "home/sensors/all")
    MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID")
    MQTT_USERNAME = os.getenv("MQTT_USERNAME")
    MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

    DATA_FILE = os.getenv("DATA_FILE", "data.json")
    THRESHOLDS_FILE = os.getenv("THRESHOLDS_FILE", "data/thresholds.json")

    EMAIL_SENDER = os.getenv("EMAIL_SENDER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
