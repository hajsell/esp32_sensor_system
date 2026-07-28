import os
import json
from flask import Blueprint, render_template, jsonify, current_app, request

from app.services.openai_agent import OpenAIAgent
from app.services.database import get_database
from app.extensions import limiter

from pydantic import ValidationError

from app.schemas import ChatRequest, ThresholdsRequest

bp = Blueprint(
    "dashboard",
    __name__,
    template_folder="../../frontend/templates",
    static_folder="../../frontend/static",
    static_url_path="/frontend-static",
)

agent = None


def _database():
    return get_database(
        current_app.config.get("DATABASE_URL"),
        current_app.config.get("APP_TIMEZONE", "Europe/Warsaw"),
    )


def _history():
    device_id = current_app.config.get("MQTT_DEVICE_ID", "esp32-1")
    return _database().history_24h(device_id)


def _read_json_file(path: str):
    # THRESHOLDS_FILE w .env może być zapisany w cudzysłowie.
    path = (path or "").strip().strip('"').strip("'")
    if not path:
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@bp.route("/")
def index():
    return render_template("dashboard/index.html")


@bp.route("/api/chat", methods=["POST"])
@limiter.limit("5 per minute; 30 per hour")
def chat():
    global agent
    try:
        chat_request = ChatRequest.model_validate(
            request.get_json(silent=True)
        )
    except ValidationError as error:
        return _validation_error_response(error)

    message = chat_request.message
    history = [
        item.model_dump()
        for item in chat_request.history
    ]

    if agent is None:
        api_key = current_app.config.get("OPENAI_API_KEY")
        if not api_key:
            return jsonify({"reply": "Brak OPENAI_API_KEY w głównym pliku .env."}), 503
        agent = OpenAIAgent(
            api_key=api_key,
            model=current_app.config.get("OPENAI_MODEL"),
            vector_store_id=current_app.config.get("OPENAI_VECTOR_STORE_ID"),
            database=_database(),
            device_id=current_app.config.get("MQTT_DEVICE_ID", "esp32-1"),
        )

    thr_path = os.getenv("THRESHOLDS_FILE") or current_app.config.get("THRESHOLDS_FILE")

    if not thr_path:
        return jsonify({"reply": "Brak THRESHOLDS_FILE w .env / config."}), 500

    thresholds = _read_json_file(thr_path)

    try:
        reply = agent.ask(
            message=message,
            history=history,
            thresholds=thresholds,
        )
    except Exception:
        current_app.logger.exception("Błąd podczas obsługi zapytania OpenAI.")
        return jsonify({
            "reply": "Nie udało się teraz przeprowadzić analizy. Spróbuj ponownie."
        }), 502
    return jsonify({"reply": reply})


@bp.route("/api/data")
@limiter.limit("60 per minute")
def get_data():
    return jsonify(_history())


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

    try:
        thresholds_request = ThresholdsRequest.model_validate(
            request.get_json(silent=True)
        )
    except ValidationError as error:
        return _validation_error_response(error)

    new_data = thresholds_request.model_dump()
    # Walidacja (opcjonalnie) - upewniamy się, że mamy liczby
    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(
                new_data,
                file,
                indent=4,
                ensure_ascii=False,
            )
    except OSError:
        current_app.logger.exception(
            "Nie udało się zapisać progów."
        )
        return jsonify({
            "error": "Nie udało się zapisać progów."
        }), 500

    return jsonify({
        "message": "Zapisano pomyślnie.",
        "data": new_data,
    }), 200


def _validation_error_response(error: ValidationError):
    details = [
        {
            "path": ".".join(str(part) for part in item["loc"]),
            "message": item["msg"],
            "type": item["type"],
        }
        for item in error.errors(include_input=False)
    ]

    return jsonify({
        "error": "Niepoprawne dane wejściowe.",
        "details": details,
    }), 422
