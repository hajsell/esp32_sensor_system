import json
import threading
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
from app.services.thresholds import thresholds_snapshot

TS_FMT = "%Y-%m-%d %H:%M:%S"


class MQTTService:
    def __init__(self, cfg, socketio, database, openai_agent=None):
        self.cfg = cfg
        self.socketio = socketio
        self.database = database
        self.openai = openai_agent
        self._thresholds_path = self.cfg.get("THRESHOLDS_FILE") or "data/thresholds.json"
        self._device_id = self.cfg.get("MQTT_DEVICE_ID") or "esp32-1"
        self.last_history_refresh = None
        self.last_ai_alert_time = None
        self.ai_cooldown_seconds = 120
        self.active_violations = set()

    def start_in_background(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        client_id = f"{self.cfg.get('MQTT_CLIENT_ID')}_{datetime.now().strftime('%H%M%S')}"
        client = mqtt.Client(client_id=client_id)
        client.username_pw_set(self.cfg.get("MQTT_USERNAME"), self.cfg.get("MQTT_PASSWORD"))
        client.tls_set()
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.connect(self.cfg.get("MQTT_HOST"), int(self.cfg.get("MQTT_PORT", 8883)), 60)
        client.loop_forever()

    def _on_connect(self, client, userdata, flags, rc):
        client.subscribe(self.cfg.get("MQTT_TOPIC"))

    def _normalize_payload(self, data: dict) -> dict:
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

    def _get_violations(self, data: dict, thresholds: dict) -> list[str]:
        """Zwraca listę komunikatów o przekroczeniach."""
        violations = []
        warn = thresholds.get("warning", {})
        alarm = thresholds.get("alarm", {})

        for key in ["temperature", "humidity", "mq2", "mq7"]:
            val = data.get(key)
            if val is None: continue

            # Najpierw sprawdzamy Alarmy (wyższy priorytet)
            if key in alarm and val >= alarm[key]:
                violations.append(f"ALARM: {key} ({val} >= {alarm[key]})")
            # Potem Ostrzeżenia
            elif key in warn and val >= warn[key]:
                violations.append(f"Ostrzeżenie: {key} ({val} >= {warn[key]})")

        return violations

    def _on_message(self, client, userdata, msg):
        if msg.retain:
            return

        try:
            raw = msg.payload.decode("utf-8", errors="ignore").strip()
            if not raw.startswith("{"):
                return

            payload_dict = json.loads(raw)
            data = self._normalize_payload(payload_dict)
            thresholds = thresholds_snapshot(self._thresholds_path)

            # 1. Wyślij surowe dane do dashboardu (wykresy)
            self.socketio.emit("new_data", data)

            # Każda próbka trafia do bazy. Wykres historii odświeżamy rzadziej,
            # ponieważ korzysta z agregatów pięciominutowych.
            self.database.insert_reading(data, self._device_id)
            now = datetime.now()
            if (
                self.last_history_refresh is None
                or now - self.last_history_refresh >= timedelta(minutes=5)
            ):
                self.socketio.emit("data_saved")
                self.last_history_refresh = now

            # --- LOGIKA AI I ALARMÓW ---
            current_violations = self._get_violations(data, thresholds)

            # Wyciągamy same klucze (np. 'temperature', 'mq2'), które są w stanie naruszenia
            # Zakładamy, że _get_violations zwraca napisy typu "Ostrzeżenie: temperature (...)"
            current_violated_keys = set()
            for v in current_violations:
                for key in ["temperature", "humidity", "mq2", "mq7"]:
                    if key in v:
                        current_violated_keys.add(key)

            can_ask_ai = (self.last_ai_alert_time is None or
                          (now - self.last_ai_alert_time).total_seconds() > self.ai_cooldown_seconds)

            ai_response = None
            alert_level = None

            # PRZYPADEK A: Wykryto NOWE naruszenia lub trwają obecne (ALARM)
            if current_violations and can_ask_ai and self.openai:
                self.last_ai_alert_time = now
                violations_str = ", ".join(current_violations)
                prompt = f"System wykrył następujące naruszenia: {violations_str}. Przeanalizuj krótko ryzyko i daj konkretną poradę."
                alert_level = "danger" if any("ALARM" in v for v in current_violations) else "warning"

                try:
                    ai_response = self.openai.ask(message=prompt, current_db=data, thresholds=thresholds)
                except Exception as ai_err:
                    print(f"[AI Error Alert] {ai_err}")

            # PRZYPADEK B: Parametry WRÓCIŁY do normy
            # Sprawdzamy, co było w active_violations, a czego nie ma w current_violated_keys
            resolved = self.active_violations - current_violated_keys
            if resolved and not current_violations and can_ask_ai and self.openai:
                self.last_ai_alert_time = now
                resolved_str = ", ".join(resolved)
                prompt = f"Następujące parametry wróciły do normy: {resolved_str}. Poinformuj o tym użytkownika i krótko podsumuj, że sytuacja jest już bezpieczna."
                alert_level = "success"  # Zielony kolor na froncie

                try:
                    ai_response = self.openai.ask(message=prompt, current_db=data, thresholds=thresholds)
                except Exception as ai_err:
                    print(f"[AI Error Recovery] {ai_err}")

            # Jeśli AI wygenerowało odpowiedź (dla alarmu lub powrotu), wyślij ją
            if ai_response:
                self.socketio.emit("ai_alert", {
                    "content": ai_response,
                    "timestamp": data["timestamp"],
                    "level": alert_level
                })

            # Aktualizujemy stan aktywnych naruszeń na przyszłość
            self.active_violations = current_violated_keys

        except Exception as e:
            print(f"[MQTT] error: {e}")
