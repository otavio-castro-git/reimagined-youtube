import os
from flask import Flask
from flask_login import LoginManager
from .models import db, User
from .config import Config


def create_app(config_class=Config):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config_class)

    # Necessário para Google OAuth sem HTTPS em desenvolvimento
    if app.config.get("OAUTHLIB_INSECURE_TRANSPORT"):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    # ── Banco de dados ──────────────────────────────────────────────────────
    db.init_app(app)

    # ── Login manager ───────────────────────────────────────────────────────
    login_manager = LoginManager()
    login_manager.login_view = "auth.login_page"
    login_manager.login_message = "Faça login para acessar essa página."
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ── Blueprints ──────────────────────────────────────────────────────────
    from .routes.auth     import auth_bp
    from .routes.home     import home_bp
    from .routes.music    import music_bp
    from .routes.playlist import playlist_bp
    from .routes.history  import history_bp
    from .routes.upload   import upload_bp
    from .routes.seguindo import seguindo_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(music_bp)
    app.register_blueprint(playlist_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(seguindo_bp)

    return app
