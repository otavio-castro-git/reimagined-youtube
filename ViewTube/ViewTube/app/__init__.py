import os
from flask import Flask
from flask_login import LoginManager
from .models import db, User
from .config import Config


def create_app(config_class=Config):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config_class)

    if app.config.get("OAUTHLIB_INSECURE_TRANSPORT"):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login_page"
    login_manager.login_message = "Faça login para acessar essa página."
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes.auth    import auth_bp
    from .routes.home    import home_bp
    from .routes.video   import video_bp
    from .routes.channel import channel_bp
    from .routes.upload  import upload_bp
    from .routes.api     import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(video_bp)
    app.register_blueprint(channel_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(api_bp)

    @app.template_filter("sidebar_subscriptions")
    def sidebar_subscriptions(user):
        from flask_login import current_user
        if not user or not user.is_authenticated:
            return []
        from .models import Subscription, Channel
        subs = (Subscription.query
                .filter_by(subscriber_id=user.id)
                .order_by(Subscription.subscribed_at.desc())
                .limit(5).all())
        return [Channel.query.get(s.channel_id) for s in subs if Channel.query.get(s.channel_id)]

    return app
