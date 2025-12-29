from flask import Blueprint, render_template, jsonify, current_app
from app.services.storage import read_all

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

@bp.route("/data")
def get_data():
    data_file = current_app.config["DATA_FILE"]
    return jsonify(read_all(data_file))
