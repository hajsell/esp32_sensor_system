import os
import json
from flask import Blueprint, render_template, jsonify, current_app, request
from dotenv import load_dotenv

from app.services.openai_agent import OpenAIAgent


# Wczytaj .env (raz przy imporcie modułu)
load_dotenv()

bp = Blueprint(
    "dashboard",
    __name__,
    template_folder="../../frontend/templates",
    static_folder="../../frontend/static",
    static_url_path="/frontend-static",
)

agent = OpenAIAgent()


def _read_json_file(path: str):
    # DATA_FILE/THRESHOLDS_FILE w .env mogą mieć cudzysłowy; os.getenv już je zwróci bez problemu,
    # ale na wszelki wypadek strip.
    path = (path or "").strip().strip('"').strip("'")
    if not path:
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@bp.route("/")
def index():
    return render_template("dashboard/index.html")


@bp.route("/api/chat", methods=["POST"])
def chat():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    history = payload.get("history") or []

    if not message:
        return jsonify({"reply": "Podaj wiadomość :)"}), 400

    data_path = os.getenv("DATA_FILE") or current_app.config.get("DATA_FILE")
    thr_path = os.getenv("THRESHOLDS_FILE") or current_app.config.get("THRESHOLDS_FILE")

    if not data_path:
        return jsonify({"reply": "Brak DATA_FILE w .env / config."}), 500
    if not thr_path:
        return jsonify({"reply": "Brak THRESHOLDS_FILE w .env / config."}), 500

    # 24h baza + progi
    data_24h = _read_json_file(data_path)
    thresholds = _read_json_file(thr_path)

    # Jeżeli data_24h to lista rekordów, zostawiamy jak jest.
    # Jeżeli to dict, też OK — model dostanie to jako JSON.
    current_db = {
        "window": "24h",
        "data": data_24h,
    }

    reply = agent.ask(
        message=message,
        history=history,
        current_db=current_db,
        thresholds=thresholds,
    )
    return jsonify({"reply": reply})


@bp.route("/api/data")
def get_data():
    data_path = os.getenv("DATA_FILE") or current_app.config.get("DATA_FILE")
    if not data_path:
        return jsonify({"error": "Brak DATA_FILE w .env / config."}), 500
    return jsonify(_read_json_file(data_path))


def _get_thresholds_path():
    path = os.getenv("THRESHOLDS_FILE") or current_app.config.get("THRESHOLDS_FILE")
    return (path or "").strip().strip('"').strip("'")


@bp.route("/api/thresholds", methods=["GET"])
def get_thresholds():
    path = _get_thresholds_path()
    if not path or not os.path.exists(path):
        return jsonify({"temp": 0, "humidity": 0, "mq2": 0, "mq7": 0}), 200

    data = _read_json_file(path)
    return jsonify(data)


@bp.route("/api/thresholds", methods=["POST"])
def update_thresholds():
    path = _get_thresholds_path()
    if not path:
        return jsonify({"error": "Brak ścieżki do pliku progów"}), 500

    new_data = request.get_json()
    # Walidacja (opcjonalnie) - upewniamy się, że mamy liczby
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(new_data, f, indent=4)
        return jsonify({"message": "Zapisano pomyślnie", "data": new_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500