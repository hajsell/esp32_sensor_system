import json
import ssl
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

import paho.mqtt.client as mqtt


class MqttGuiGenerator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Generator danych IoT -> MQTT")
        self.geometry("740x520")
        self.resizable(False, False)

        self.client = None
        self.connected = False
        self.sending_job = None

        self._build_ui()

    # ---------------- UI ----------------
    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        # ---- MQTT frame ----
        mqtt_frame = ttk.LabelFrame(self, text="Ustawienia MQTT")
        mqtt_frame.pack(fill="x", **pad)

        self.var_host = tk.StringVar(value="7d195151bce44ede9285bd5b8dcc8abe.s1.eu.hivemq.cloud")
        self.var_port = tk.IntVar(value=8883)
        self.var_topic = tk.StringVar(value="production/sensor/all")
        self.var_user = tk.StringVar(value="generator")
        self.var_pass = tk.StringVar(value="Generator1")
        self.var_tls = tk.BooleanVar(value=True)
        self.var_ca = tk.StringVar(value="")

        row = 0
        ttk.Label(mqtt_frame, text="Host:").grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(mqtt_frame, textvariable=self.var_host, width=32).grid(row=row, column=1, sticky="w", **pad)

        ttk.Label(mqtt_frame, text="Port:").grid(row=row, column=2, sticky="w", **pad)
        ttk.Spinbox(mqtt_frame, from_=1, to=65535, textvariable=self.var_port, width=8).grid(
            row=row, column=3, sticky="w", **pad
        )

        row += 1
        ttk.Label(mqtt_frame, text="Topic:").grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(mqtt_frame, textvariable=self.var_topic, width=52).grid(
            row=row, column=1, columnspan=3, sticky="w", **pad
        )

        row += 1
        ttk.Label(mqtt_frame, text="Username:").grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(mqtt_frame, textvariable=self.var_user, width=32).grid(row=row, column=1, sticky="w", **pad)

        ttk.Label(mqtt_frame, text="Password:").grid(row=row, column=2, sticky="w", **pad)
        ttk.Entry(mqtt_frame, textvariable=self.var_pass, show="*", width=20).grid(row=row, column=3, sticky="w", **pad)

        row += 1
        tls_cb = ttk.Checkbutton(mqtt_frame, text="Użyj TLS (np. 8883)", variable=self.var_tls, command=self._on_tls_toggle)
        tls_cb.grid(row=row, column=0, sticky="w", **pad)

        ttk.Label(mqtt_frame, text="CA cert (opcjonalnie):").grid(row=row, column=1, sticky="w", **pad)
        self.ca_entry = ttk.Entry(mqtt_frame, textvariable=self.var_ca, width=34, state="disabled")
        self.ca_entry.grid(row=row, column=2, sticky="w", **pad)

        self.btn_browse_ca = ttk.Button(mqtt_frame, text="Wybierz…", command=self._browse_ca, state="disabled")
        self.btn_browse_ca.grid(row=row, column=3, sticky="w", **pad)

        # ---- Data frame ----
        data_frame = ttk.LabelFrame(self, text="Dane")
        data_frame.pack(fill="x", **pad)

        self.var_temp = tk.DoubleVar(value=28.1)
        self.var_hum = tk.DoubleVar(value=41.2)
        self.var_mq2 = tk.StringVar(value="2579")
        self.var_mq7 = tk.StringVar(value="2346")

        row = 0
        ttk.Label(data_frame, text="Temperatura (°C):").grid(row=row, column=0, sticky="w", **pad)
        ttk.Scale(data_frame, from_=-10, to=50, variable=self.var_temp, command=lambda _: self._update_readouts()).grid(
            row=row, column=1, sticky="we", **pad
        )
        self.lbl_temp = ttk.Label(data_frame, text="28.10")
        self.lbl_temp.grid(row=row, column=2, sticky="w", **pad)

        row += 1
        ttk.Label(data_frame, text="Wilgotność (%):").grid(row=row, column=0, sticky="w", **pad)
        ttk.Scale(data_frame, from_=0, to=100, variable=self.var_hum, command=lambda _: self._update_readouts()).grid(
            row=row, column=1, sticky="we", **pad
        )
        self.lbl_hum = ttk.Label(data_frame, text="41.20")
        self.lbl_hum.grid(row=row, column=2, sticky="w", **pad)

        row += 1
        ttk.Label(data_frame, text="MQ2 (0–4095):").grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(data_frame, textvariable=self.var_mq2, width=16).grid(row=row, column=1, sticky="w", **pad)

        row += 1
        ttk.Label(data_frame, text="MQ7 (0–4095):").grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(data_frame, textvariable=self.var_mq7, width=16).grid(row=row, column=1, sticky="w", **pad)

        data_frame.columnconfigure(1, weight=1)

        # ---- Controls ----
        ctrl_frame = ttk.LabelFrame(self, text="Sterowanie")
        ctrl_frame.pack(fill="x", **pad)

        self.var_interval_ms = tk.IntVar(value=1000)

        ttk.Label(ctrl_frame, text="Interwał wysyłki (ms):").grid(row=0, column=0, sticky="w", **pad)
        ttk.Spinbox(ctrl_frame, from_=100, to=60000, increment=100, textvariable=self.var_interval_ms, width=10).grid(
            row=0, column=1, sticky="w", **pad
        )

        self.btn_connect = ttk.Button(ctrl_frame, text="Połącz", command=self.connect_mqtt)
        self.btn_connect.grid(row=0, column=2, **pad)

        self.btn_disconnect = ttk.Button(ctrl_frame, text="Rozłącz", command=self.disconnect_mqtt, state="disabled")
        self.btn_disconnect.grid(row=0, column=3, **pad)

        self.btn_start = ttk.Button(ctrl_frame, text="Start wysyłania", command=self.start_sending, state="disabled")
        self.btn_start.grid(row=1, column=2, **pad)

        self.btn_stop = ttk.Button(ctrl_frame, text="Stop", command=self.stop_sending, state="disabled")
        self.btn_stop.grid(row=1, column=3, **pad)

        self.lbl_status = ttk.Label(ctrl_frame, text="Status: rozłączony")
        self.lbl_status.grid(row=1, column=0, columnspan=2, sticky="w", **pad)

        # ---- Log / Preview ----
        log_frame = ttk.LabelFrame(self, text="Podgląd / log")
        log_frame.pack(fill="both", expand=True, **pad)

        self.txt = tk.Text(log_frame, height=14, wrap="word")
        self.txt.pack(fill="both", expand=True, padx=10, pady=10)
        self._log("Gotowe. Ustaw MQTT i kliknij Połącz.")

        self._update_readouts()

        # Close handler
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_tls_toggle(self):
        enabled = self.var_tls.get()
        self.ca_entry.configure(state="normal" if enabled else "disabled")
        self.btn_browse_ca.configure(state="normal" if enabled else "disabled")
        if enabled and self.var_port.get() == 1883:
            self.var_port.set(8883)  # typowo TLS
        elif not enabled and self.var_port.get() == 8883:
            self.var_port.set(1883)

    def _browse_ca(self):
        path = filedialog.askopenfilename(
            title="Wybierz plik CA cert",
            filetypes=[("Certificate files", "*.crt *.pem *.cer"), ("All files", "*.*")]
        )
        if path:
            self.var_ca.set(path)

    def _update_readouts(self):
        self.lbl_temp.config(text=f"{self.var_temp.get():.2f}")
        self.lbl_hum.config(text=f"{self.var_hum.get():.2f}")

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.txt.insert("end", f"[{ts}] {msg}\n")
        self.txt.see("end")

    # ---------------- MQTT ----------------
    def connect_mqtt(self):
        host = self.var_host.get().strip()
        topic = self.var_topic.get().strip()
        port = int(self.var_port.get())

        if not host or not topic:
            messagebox.showerror("Błąd", "Host i Topic nie mogą być puste.")
            return

        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

            user = self.var_user.get().strip()
            pwd = self.var_pass.get()
            if user:
                self.client.username_pw_set(user, pwd)

            # TLS
            if self.var_tls.get():
                ca = self.var_ca.get().strip()
                if ca:
                    self.client.tls_set(ca_certs=ca, cert_reqs=ssl.CERT_REQUIRED)
                else:
                    # systemowe CA
                    self.client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
                self.client.tls_insecure_set(False)

            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect

            self.client.connect(host, port, keepalive=60)
            self.client.loop_start()
            self._log(f"Łączenie z MQTT {host}:{port} ...")

        except Exception as e:
            messagebox.showerror("Błąd połączenia", str(e))
            self._log(f"Błąd połączenia: {e}")

    def disconnect_mqtt(self):
        self.stop_sending()
        try:
            if self.client:
                self.client.disconnect()
                self.client.loop_stop()
        except Exception:
            pass

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.connected = True
            self._log("Połączono z brokerem.")
            self._set_status("połączony")
            self.btn_connect.configure(state="disabled")
            self.btn_disconnect.configure(state="normal")
            self.btn_start.configure(state="normal")
        else:
            self._log(f"Nie udało się połączyć (reason_code={reason_code}).")
            self._set_status("błąd połączenia")

    def _on_disconnect(self, client, userdata, reason_code, properties, packet_from_broker):
        self.connected = False
        self._log(f"Rozłączono (reason_code={reason_code}).")
        self._set_status("rozłączony")
        self.btn_connect.configure(state="normal")
        self.btn_disconnect.configure(state="disabled")
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="disabled")

    def _set_status(self, status: str):
        self.lbl_status.config(text=f"Status: {status}")

    # ---------------- Sending ----------------
    def _build_payload(self) -> dict:
        # Format timestamp jak w Twoim przykładzie (YYYY-MM-DD HH:MM:SS) :contentReference[oaicite:2]{index=2}
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # walidacja MQ
        def parse_adc(s: str, name: str) -> int:
            try:
                v = int(s)
            except ValueError:
                raise ValueError(f"{name} musi być liczbą całkowitą.")
            if v < 0 or v > 4095:
                raise ValueError(f"{name} poza zakresem 0–4095.")
            return v

        mq2 = parse_adc(self.var_mq2.get().strip(), "MQ2")
        mq7 = parse_adc(self.var_mq7.get().strip(), "MQ7")

        payload = {
            "timestamp": ts,
            "temperature": round(float(self.var_temp.get()), 2),
            "humidity": round(float(self.var_hum.get()), 2),
            "mq2": mq2,
            "mq7": mq7,
        }
        return payload

    def publish_once(self):
        if not self.connected or not self.client:
            self._log("Niepołączony — nie wysyłam.")
            return

        topic = self.var_topic.get().strip()
        try:
            payload = self._build_payload()
            data = json.dumps(payload, ensure_ascii=False)

            info = self.client.publish(topic, data, qos=0, retain=False)
            if info.rc == mqtt.MQTT_ERR_SUCCESS:
                self._log(f"Wysłano na '{topic}': {data}")
            else:
                self._log(f"Błąd publish (rc={info.rc}).")

        except Exception as e:
            self._log(f"Błąd danych/wysyłki: {e}")

    def _sending_tick(self):
        self.publish_once()
        interval = max(100, int(self.var_interval_ms.get()))
        self.sending_job = self.after(interval, self._sending_tick)

    def start_sending(self):
        if not self.connected:
            messagebox.showwarning("Uwaga", "Najpierw połącz z brokerem.")
            return
        if self.sending_job is None:
            self._log("Start wysyłania cyklicznego.")
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
            self._sending_tick()

    def stop_sending(self):
        if self.sending_job is not None:
            self.after_cancel(self.sending_job)
            self.sending_job = None
            self._log("Zatrzymano wysyłanie.")
        if self.connected:
            self.btn_start.configure(state="normal")
            self.btn_stop.configure(state="disabled")

    def _on_close(self):
        try:
            self.disconnect_mqtt()
        finally:
            self.destroy()


if __name__ == "__main__":
    # Lepszy wygląd na Windows/Linux
    try:
        from tkinter import font
    except Exception:
        pass

    app = MqttGuiGenerator()
    app.mainloop()
