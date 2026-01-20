from app import create_app, socketio
from app.services.email_service import EmailService
from app.services.mqtt_service import MQTTService
from app.services.openai_agent import OpenAIAgent

app = create_app()
cfg = app.config

email = EmailService(cfg["EMAIL_SENDER"], cfg["EMAIL_PASSWORD"], cfg["EMAIL_RECIPIENT"])

openai_agent = None
if cfg.get("OPENAI_API_KEY"):
    openai_agent = OpenAIAgent(cfg["OPENAI_API_KEY"], cfg["OPENAI_MODEL"])

mqtt_service = MQTTService(
    cfg={
        "MQTT_BROKER": cfg["MQTT_BROKER"],
        "MQTT_PORT": cfg["MQTT_PORT"],
        "MQTT_TOPIC": cfg["MQTT_TOPIC"],
        "MQTT_CLIENT_ID": cfg["MQTT_CLIENT_ID"],
        "MQTT_USERNAME": cfg["MQTT_USERNAME"],
        "MQTT_PASSWORD": cfg["MQTT_PASSWORD"],
        "DATA_FILE": cfg["DATA_FILE"],
    },
    socketio=socketio,
    email_service=email,
    openai_agent=openai_agent
)
mqtt_service.start_in_background()


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
