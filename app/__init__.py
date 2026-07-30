from flask import Flask
from flask_socketio import SocketIO
from .config import Config
from .routes.dashboard import bp as dashboard_bp
from .extensions import limiter

socketio = SocketIO(async_mode="threading")

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    limiter.init_app(app)
    socketio.init_app(
        app,
        cors_allowed_origins=app.config["SOCKETIO_ALLOWED_ORIGINS"],
    )
    app.register_blueprint(dashboard_bp)

    return app
