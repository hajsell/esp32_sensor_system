import json
import os
import queue
import random
import ssl
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

import paho.mqtt.client as mqtt
from dotenv import load_dotenv


# Konfiguracja MQTT
load_dotenv()
MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = os.getenv("MQTT_PORT")
MQTT_TOPIC = os.getenv("MQTT_TOPIC")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_USE_TLS = os.getenv("MQTT_USE_TLS")
MQTT_CA_FILE = None


class MqttGuiGenerator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Generator danych IoT → MQTT")
        self.geometry("680x640")
        self.minsize(620, 580)

        self.client = None
        self.connected = False
        self.sending_job = None
        self.closing = False
        self.mqtt_events = queue.SimpleQueue()
        self.auto_values = {
            "temperature": 28.1,
            "humidity": 41.2,
            "mq2": 2579.0,
            "mq7": 2346.0,
        }

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._process_mqtt_events)

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        data_frame = ttk.LabelFrame(self, text="Dane")
        data_frame.pack(fill="x", **pad)

        self.var_temp = tk.DoubleVar(value=28.1)
        self.var_hum = tk.DoubleVar(value=41.2)
        self.var_mq2 = tk.StringVar(value="2579")
        self.var_mq7 = tk.StringVar(value="2346")

        ttk.Label(data_frame, text="Temperatura (°C):").grid(row=0, column=0, sticky="w", **pad)
        ttk.Scale(
            data_frame, from_=-10, to=50, variable=self.var_temp,
            command=lambda _: self._update_readouts()
        ).grid(row=0, column=1, sticky="ew", **pad)
        self.lbl_temp = ttk.Label(data_frame, width=7)
        self.lbl_temp.grid(row=0, column=2, sticky="w", **pad)

        ttk.Label(data_frame, text="Wilgotność (%):").grid(row=1, column=0, sticky="w", **pad)
        ttk.Scale(
            data_frame, from_=0, to=100, variable=self.var_hum,
            command=lambda _: self._update_readouts()
        ).grid(row=1, column=1, sticky="ew", **pad)
        self.lbl_hum = ttk.Label(data_frame, width=7)
        self.lbl_hum.grid(row=1, column=2, sticky="w", **pad)

        ttk.Label(data_frame, text="MQ2 (0–4095):").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(data_frame, textvariable=self.var_mq2, width=16).grid(row=2, column=1, sticky="w", **pad)

        ttk.Label(data_frame, text="MQ7 (0–4095):").grid(row=3, column=0, sticky="w", **pad)
        ttk.Entry(data_frame, textvariable=self.var_mq7, width=16).grid(row=3, column=1, sticky="w", **pad)
        data_frame.columnconfigure(1, weight=1)

        auto_frame = ttk.LabelFrame(self, text="Automatyczna symulacja")
        auto_frame.pack(fill="x", **pad)
        self.var_auto = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            auto_frame,
            text="Płynnie zmieniaj wartości w podanych zakresach",
            variable=self.var_auto,
            command=self._toggle_auto,
        ).grid(row=0, column=0, columnspan=5, sticky="w", **pad)

        self.range_vars = {}
        ranges = (
            ("Temperatura", "temperature", "24", "30"),
            ("Wilgotność", "humidity", "35", "55"),
            ("MQ2", "mq2", "1800", "2800"),
            ("MQ7", "mq7", "1600", "2600"),
        )
        for row, (label, key, low, high) in enumerate(ranges, start=1):
            low_var, high_var = tk.StringVar(value=low), tk.StringVar(value=high)
            self.range_vars[key] = (low_var, high_var)
            ttk.Label(auto_frame, text=label).grid(row=row, column=0, sticky="w", **pad)
            ttk.Label(auto_frame, text="od").grid(row=row, column=1, sticky="e")
            ttk.Entry(auto_frame, textvariable=low_var, width=9).grid(row=row, column=2, sticky="w", padx=4)
            ttk.Label(auto_frame, text="do").grid(row=row, column=3, sticky="e")
            ttk.Entry(auto_frame, textvariable=high_var, width=9).grid(row=row, column=4, sticky="w", padx=4)

        controls = ttk.LabelFrame(self, text="Sterowanie")
        controls.pack(fill="x", **pad)

        self.var_interval_ms = tk.StringVar(value="1000")
        ttk.Label(controls, text="Interwał wysyłki (ms):").grid(row=0, column=0, sticky="w", **pad)
        ttk.Spinbox(
            controls, from_=100, to=60000, increment=100,
            textvariable=self.var_interval_ms, width=10
        ).grid(row=0, column=1, sticky="w", **pad)

        self.btn_connect = ttk.Button(controls, text="Połącz", command=self.connect_mqtt)
        self.btn_connect.grid(row=0, column=2, **pad)
        self.btn_disconnect = ttk.Button(
            controls, text="Rozłącz", command=self.disconnect_mqtt, state="disabled"
        )
        self.btn_disconnect.grid(row=0, column=3, **pad)

        self.lbl_status = ttk.Label(controls, text="Status: rozłączony")
        self.lbl_status.grid(row=1, column=0, columnspan=2, sticky="w", **pad)
        self.btn_start = ttk.Button(
            controls, text="Start wysyłania", command=self.start_sending, state="disabled"
        )
        self.btn_start.grid(row=1, column=2, **pad)
        self.btn_stop = ttk.Button(controls, text="Stop", command=self.stop_sending, state="disabled")
        self.btn_stop.grid(row=1, column=3, **pad)

        log_frame = ttk.LabelFrame(self, text="Podgląd / log")
        log_frame.pack(fill="both", expand=True, **pad)
        self.txt = tk.Text(log_frame, height=10, wrap="word", state="disabled")
        self.txt.pack(fill="both", expand=True, padx=10, pady=10)

        self._update_readouts()
        self._log("Gotowe. Kliknij Połącz.")

    def _update_readouts(self):
        self.lbl_temp.config(text=f"{self.var_temp.get():.2f}")
        self.lbl_hum.config(text=f"{self.var_hum.get():.2f}")

    def _toggle_auto(self):
        if not self.var_auto.get():
            return
        try:
            self.auto_values = {
                "temperature": self.var_temp.get(),
                "humidity": self.var_hum.get(),
                "mq2": float(self._parse_adc(self.var_mq2.get().strip(), "MQ2")),
                "mq7": float(self._parse_adc(self.var_mq7.get().strip(), "MQ7")),
            }
            self._read_ranges()
        except (ValueError, tk.TclError) as error:
            self.var_auto.set(False)
            messagebox.showerror("Błąd zakresu", str(error))

    def _read_ranges(self):
        ranges = {}
        limits = {
            "temperature": (-50.0, 100.0),
            "humidity": (0.0, 100.0),
            "mq2": (0.0, 4095.0),
            "mq7": (0.0, 4095.0),
        }
        for key, (low_var, high_var) in self.range_vars.items():
            try:
                low, high = float(low_var.get()), float(high_var.get())
            except ValueError as error:
                raise ValueError(f"Zakres {key} musi zawierać liczby.") from error
            allowed_low, allowed_high = limits[key]
            if not allowed_low <= low < high <= allowed_high:
                raise ValueError(
                    f"Niepoprawny zakres {key}: wymagane {allowed_low:g} ≤ od < do ≤ {allowed_high:g}."
                )
            ranges[key] = (low, high)
        return ranges

    def _advance_simulation(self):
        ranges = self._read_ranges()
        for key, (low, high) in ranges.items():
            current = min(high, max(low, self.auto_values[key]))
            center = (low + high) / 2
            span = high - low
            # Powolny powrót ku środkowi + mały losowy krok daje naturalny,
            # płynny dryf bez skakania między przypadkowymi wartościami.
            current += 0.04 * (center - current) + random.gauss(0, span * 0.012)
            self.auto_values[key] = min(high, max(low, current))

        self.var_temp.set(round(self.auto_values["temperature"], 2))
        self.var_hum.set(round(self.auto_values["humidity"], 2))
        self.var_mq2.set(str(round(self.auto_values["mq2"])))
        self.var_mq7.set(str(round(self.auto_values["mq7"])))
        self._update_readouts()

    def _log(self, message):
        if self.closing:
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.txt.configure(state="normal")
        self.txt.insert("end", f"[{timestamp}] {message}\n")
        self.txt.see("end")
        self.txt.configure(state="disabled")

    def _set_connected_ui(self, connected):
        self.connected = connected
        self.lbl_status.config(text=f"Status: {'połączony' if connected else 'rozłączony'}")
        self.btn_connect.config(state="disabled" if connected else "normal")
        self.btn_disconnect.config(state="normal" if connected else "disabled")
        self.btn_start.config(state="normal" if connected else "disabled")
        if not connected:
            self.stop_sending()

    # Callbacki MQTT działają w innym wątku. Do GUI przekazują tylko dane przez kolejkę.
    def _on_connect(self, client, userdata, flags, reason_code, properties):
        self.mqtt_events.put(("connect", client, reason_code))

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        self.mqtt_events.put(("disconnect", client, reason_code))

    @staticmethod
    def _reason_code_value(reason_code):
        return getattr(reason_code, "value", reason_code)

    def _process_mqtt_events(self):
        if self.closing:
            return
        while True:
            try:
                event, client, code = self.mqtt_events.get_nowait()
            except queue.Empty:
                break
            if client is not self.client:
                continue

            code_value = self._reason_code_value(code)
            if event == "connect" and code_value == 0:
                self._set_connected_ui(True)
                self._log("Połączono z brokerem.")
            elif event == "connect":
                self._stop_client()
                self._set_connected_ui(False)
                self._log(f"Nie udało się połączyć: {code}.")
            else:
                self._stop_client()
                self._set_connected_ui(False)
                self._log(f"Rozłączono: {code}.")
        self.after(100, self._process_mqtt_events)

    def connect_mqtt(self):
        if not MQTT_USERNAME or not MQTT_PASSWORD:
            messagebox.showerror(
                "Brak konfiguracji",
                "Ustaw MQTT_USERNAME i MQTT_PASSWORD w lokalnym pliku .env.",
            )
            return
        self.btn_connect.config(state="disabled")
        self.btn_disconnect.config(state="normal")
        self.lbl_status.config(text="Status: łączenie…")
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
            if MQTT_USE_TLS:
                client.tls_set(ca_certs=MQTT_CA_FILE, cert_reqs=ssl.CERT_REQUIRED)
                client.tls_insecure_set(False)
            client.on_connect = self._on_connect
            client.on_disconnect = self._on_disconnect
            client.connect_async(MQTT_HOST, int(MQTT_PORT), keepalive=60)
            client.loop_start()
            self.client = client
            self._log(f"Łączenie z {MQTT_HOST}:{MQTT_PORT}…")
        except Exception as error:
            self.btn_connect.config(state="normal")
            self.lbl_status.config(text="Status: błąd połączenia")
            self._log(f"Błąd połączenia: {error}")
            messagebox.showerror("Błąd połączenia", str(error))

    def _stop_client(self):
        client, self.client = self.client, None
        if client is not None:
            try:
                client.disconnect()
            finally:
                client.loop_stop()

    def disconnect_mqtt(self):
        self.stop_sending()
        self._stop_client()
        self._set_connected_ui(False)

    @staticmethod
    def _parse_adc(value, name):
        try:
            number = int(value)
        except ValueError as error:
            raise ValueError(f"{name} musi być liczbą całkowitą.") from error
        if not 0 <= number <= 4095:
            raise ValueError(f"{name} musi być w zakresie 0–4095.")
        return number

    def _build_payload(self):
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "temperature": round(self.var_temp.get(), 2),
            "humidity": round(self.var_hum.get(), 2),
            "mq2": self._parse_adc(self.var_mq2.get().strip(), "MQ2"),
            "mq7": self._parse_adc(self.var_mq7.get().strip(), "MQ7"),
        }

    def publish_once(self):
        if not self.connected or self.client is None:
            self.stop_sending()
            return
        try:
            if self.var_auto.get():
                self._advance_simulation()
            data = json.dumps(self._build_payload(), ensure_ascii=False)
            result = self.client.publish(MQTT_TOPIC, data, qos=0, retain=False)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self._log(f"Wysłano: {data}")
            else:
                self._log(f"Błąd wysyłki (kod {result.rc}).")
        except Exception as error:
            self.stop_sending()
            self._log(f"Błąd danych lub wysyłki: {error}")
            messagebox.showerror("Błąd wysyłki", str(error))

    def _sending_tick(self):
        self.sending_job = None
        self.publish_once()
        if not self.connected:
            return
        try:
            interval = max(100, int(self.var_interval_ms.get()))
        except ValueError:
            self.stop_sending()
            messagebox.showerror("Błąd danych", "Interwał musi być liczbą całkowitą.")
            return
        self.sending_job = self.after(interval, self._sending_tick)

    def start_sending(self):
        if self.connected and self.sending_job is None:
            self.btn_start.config(state="disabled")
            self.btn_stop.config(state="normal")
            self._log("Uruchomiono wysyłanie.")
            self._sending_tick()

    def stop_sending(self):
        if self.sending_job is not None:
            try:
                self.after_cancel(self.sending_job)
            except tk.TclError:
                pass
            self.sending_job = None
        self.btn_stop.config(state="disabled")
        self.btn_start.config(state="normal" if self.connected else "disabled")

    def _on_close(self):
        self.closing = True
        self.stop_sending()
        self._stop_client()
        self.destroy()


if __name__ == "__main__":
    MqttGuiGenerator().mainloop()
