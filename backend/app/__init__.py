from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_cors import CORS
from app.config import Config

db = SQLAlchemy()
socketio = SocketIO()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS for all routes
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    db.init_app(app)

    # Import all models to register them with SQLAlchemy
    from app.models import Agent, Task, Worktree, Event, Project
    from app.models.conversation import Conversation

    socketio.init_app(app, cors_allowed_origins="*")

    from app.api import agents, tasks, worktrees, events
    from app.api import workspace, orchestrator, evaluator_api
    from app.api import projects, chat, tools

    app.register_blueprint(agents.bp)
    app.register_blueprint(tasks.bp)
    app.register_blueprint(worktrees.bp)
    app.register_blueprint(events.bp)
    app.register_blueprint(workspace.bp)
    app.register_blueprint(orchestrator.bp)
    app.register_blueprint(evaluator_api.bp)
    app.register_blueprint(projects.bp)
    app.register_blueprint(chat.bp)
    app.register_blueprint(tools.bp)

    @app.route("/api/health")
    def health():
        return {"status": "ok", "service": "agent-harness-backend"}

    with app.app_context():
        db.create_all()

    # Import socket events module (triggers WebSocket handlers)
    __import__("app.socket_events", fromlist=[""])

    return app