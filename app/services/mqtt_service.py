import json
import threading
from datetime import datetime
import paho.mqtt.client as mqtt
from app.services.storage import should_save, append_record

class MQTTService:
    def __init__(self, cfg, socketio, email_service, openai_agent=None):
        self.cfg = cfg
        self.socketio = socketio
        self.email = email_service
        self.openai = openai_agent

        self.last_saved_data = None
        self.last_saved_time = None

    def start_in_background(self):
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def _run(self):
        client = mqtt.Client(client_id=self.cfg["MQTT_CLIENT_ID"])
        client.username_pw_set(self.cfg["MQTT_USERNAME"], self.cfg["MQTT_PASSWORD"])
        client.tls_set()

        client.on_connect = self._on_connect
        client.on_message = self._on_message

        client.connect(self.cfg["MQTT_BROKER"], self.cfg["MQTT_PORT"], 60)
        client.loop_forever()

    def _on_connect(self, client, userdata, flags, rc):
        client.subscribe(self.cfg["MQTT_TOPIC"])

    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())

            # websocket: push do UI
            self.socketio.emit("new_data", data)

            # alert mail
            if self.last_saved_data and (data["mq2"] > 3000 or data["mq7"] > 3000):
                mq2_diff = abs(data["mq2"] - self.last_saved_data["mq2"])
                mq7_diff = abs(data["mq7"] - self.last_saved_data["mq7"])
                body = (
                    f"Wykryto wysokie wartości MQ:\n"
                    f"MQ2: {self.last_saved_data['mq2']} → {data['mq2']} (Δ {mq2_diff})\n"
                    f"MQ7: {self.last_saved_data['mq7']} → {data['mq7']} (Δ {mq7_diff})\n"
                    f"Czas: {data['timestamp']}"
                )
                self.email.send_alert_async("ALERT: Wysokie MQ2/MQ7", body)

                # (opcjonalnie) analiza OpenAI
                if self.openai:
                    self.openai.enqueue_event(data)

            # zapis warunkowy
            if should_save(data, self.last_saved_data, self.last_saved_time):
                append_record(self.cfg["DATA_FILE"], data)
                self.socketio.emit("data_saved")
                self.last_saved_data = data
                self.last_saved_time = datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S")

        except Exception as e:
            print(f"[MQTT] error: {e}")
