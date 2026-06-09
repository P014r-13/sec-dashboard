from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from datetime import timedelta

from config import Config
from database.db import init_db

from routes.auth         import auth_bp
from routes.projects     import projects_bp
from routes.login_events import events_bp
from routes.alerts       import alerts_bp
from routes.settings     import settings_bp


def create_app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"]          = Config.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

    CORS(app, origins=[Config.FRONTEND_URL], supports_credentials=True)
    JWTManager(app)
    Bcrypt(app)

    for bp in (auth_bp, projects_bp, events_bp, alerts_bp, settings_bp):
        app.register_blueprint(bp)

    @app.route("/api/health")
    def health():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    init_db()          # ساخت جداول — seed حذف شد
    app = create_app()
    app.run(debug=True, port=Config.FLASK_PORT)