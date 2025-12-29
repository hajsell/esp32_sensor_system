import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_socketio import SocketIO
from .config import Config
from .routes.dashboard import bp as dashboard_bp

socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    socketio.init_app(app)
    app.register_blueprint(dashboard_bp)

    return app
