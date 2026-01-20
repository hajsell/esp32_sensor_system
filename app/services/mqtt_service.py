import json
import threading
from datetime import datetime
import paho.mqtt.client as mqtt
from app.services.storage import should_save, append_record
from app.services.thresholds import thresholds_snapshot

TS_FMT = "%Y-%m-%d %H:%M:%S"


class MQTTService:
    def __init__(self, cfg, socketio, email_service, openai_agent=None):
        self.cfg = cfg
        self.socketio = socketio
        self.email = email_service
        self.openai = openai_agent
        self.last_saved_data = None
        self.last_saved_time = None
        self._thresholds_path = self.cfg.get("THRESHOLDS_FILE") or "data/thresholds.json"
        self._data_path = self.cfg.get("DATA_FILE") or "data/data.json"

    def start_in_background(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        # Generujemy unikalne Client ID, aby uniknąć konfliktów z innymi sesjami
        client_id = f"{self.cfg.get('MQTT_CLIENT_ID')}_{datetime.now().strftime('%H%M%S')}"
        client = mqtt.Client(client_id=client_id)

        client.username_pw_set(self.cfg.get("MQTT_USERNAME"), self.cfg.get("MQTT_PASSWORD"))
        client.tls_set()
        client.on_connect = self._on_connect
        client.on_message = self._on_message

        client.connect(self.cfg.get("MQTT_BROKER"), int(self.cfg.get("MQTT_PORT", 8883)), 60)
        client.loop_forever()

    def _on_connect(self, client, userdata, flags, rc):
        client.subscribe(self.cfg.get("MQTT_TOPIC"))

    def _normalize_payload(self, data: dict) -> dict:
        # Używamy czasu z teraz TYLKO dla świeżych wiadomości
        now_str = datetime.now().strftime(TS_FMT)

        def to_float(v):
            try:
                return float(v) if v is not None else None
            except:
                return None

        return {
            "timestamp": now_str,
            "temperature": to_float(data.get("temperature")),
            "humidity": to_float(data.get("humidity")),
            "mq2": to_float(data.get("mq2")),
            "mq7": to_float(data.get("mq7")),
        }

    def _is_alarm(self, data: dict, thresholds: dict) -> bool:
        alarm = thresholds.get("alarm", {})
        mq2, mq7 = data.get("mq2"), data.get("mq7")
        mq2_a, mq7_a = alarm.get("mq2"), alarm.get("mq7")
        return any([
            mq2_a is not None and mq2 is not None and mq2 >= mq2_a,
            mq7_a is not None and mq7 is not None and mq7 >= mq7_a
        ])

    def _on_message(self, client, userdata, msg):
        # KLUCZOWA POPRAWKA: Ignorujemy wiadomości "zachowane" (stare śmieci z brokera)
        if msg.retain:
            return

        try:
            raw = msg.payload.decode("utf-8", errors="ignore").strip()
            if not raw.startswith("{"):
                return

            payload_dict = json.loads(raw)
            data = self._normalize_payload(payload_dict)
            thresholds = thresholds_snapshot(self._thresholds_path)

            # Wysyłamy do dashboardu przez SocketIO
            self.socketio.emit("new_data", data)

            # Obsługa AI / Alarmu
            if self.last_saved_data and self._is_alarm(data, thresholds):
                if self.openai and hasattr(self.openai, "ask"):
                    prompt = f"Wykryto ALARM IoT.\nDANE: {data}\nPROGI: {thresholds}"
                    try:
                        self.openai.ask(message=prompt, history=[],
                                        db_snapshot={"last": data, "thresholds": thresholds})
                    except:
                        pass

            # Zapis do pliku tylko jeśli funkcja logiczna na to pozwala
            if should_save(data, self.last_saved_data, self.last_saved_time, thresholds):
                append_record(self._data_path, data)
                self.socketio.emit("data_saved")
                self.last_saved_data = data
                self.last_saved_time = datetime.now()

        except Exception as e:
            print(f"[MQTT] error: {e}")