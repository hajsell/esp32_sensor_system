from flask import Blueprint, render_template, jsonify, current_app, request
from app.services.storage import read_all
from app.services.openai_agent import OpenAIAgent

agent = OpenAIAgent(
    model="gpt-4o-mini",
    context_file="../../data/cyfryzacja reguły.docx"
)

bp = Blueprint(
    "dashboard",
    __name__,
    template_folder="../../frontend/templates",
    static_folder="../../frontend/static",
    static_url_path="/frontend-static"
)

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

    data_file = current_app.config["DATA_FILE"]
    data = read_all(data_file)
    last = data[-1] if data else None

    db_snapshot = {"last": last}

    reply = agent.ask(message, history=history, db_snapshot=db_snapshot)
    return jsonify({"reply": reply})

@bp.route("/api/data")
def get_data():
    data_file = current_app.config["DATA_FILE"]
    return jsonify(read_all(data_file))
