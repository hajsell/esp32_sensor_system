from app import create_app, socketio
from app.services.mqtt_service import MQTTService
from app.services.openai_agent import OpenAIAgent
from app.services.database import get_database

app = create_app()
cfg = app.config

openai_agent = None
if cfg.get("OPENAI_API_KEY"):
    openai_agent = OpenAIAgent(cfg["OPENAI_API_KEY"], cfg["OPENAI_MODEL"])

database = get_database(cfg["DATABASE_URL"], cfg["APP_TIMEZONE"])

mqtt_service = MQTTService(
    cfg={
        "MQTT_HOST": cfg["MQTT_HOST"],
        "MQTT_PORT": cfg["MQTT_PORT"],
        "MQTT_TOPIC": cfg["MQTT_TOPIC"],
        "MQTT_CLIENT_ID": cfg["MQTT_CLIENT_ID"],
        "MQTT_USERNAME": cfg["MQTT_USERNAME"],
        "MQTT_PASSWORD": cfg["MQTT_PASSWORD"],
        "MQTT_DEVICE_ID": cfg["MQTT_DEVICE_ID"],
        "THRESHOLDS_FILE": cfg["THRESHOLDS_FILE"],
    },
    socketio=socketio,
    database=database,
    openai_agent=openai_agent
)
mqtt_service.start_in_background()


if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=cfg["DEBUG"],
        use_reloader=False,
    )
