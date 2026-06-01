"""
Autenticação: email/senha + Google OAuth 2.0
Compartilha shared.users com o BeatTube.
"""
import os
import requests
from flask import Blueprint, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlencode
from ..models import db, User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_URL  = "https://www.googleapis.com/oauth2/v2/userinfo"


def get_google_redirect_uri():
    base = os.getenv("BASE_URL", "http://localhost:5001")
    return f"{base}/auth/google/callback"


# ─── Login page ──────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["GET"])
def login_page():
    return redirect(url_for("home.index"))


# ─── Login email/senha ───────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data  = request.get_json() or request.form
    email = data.get("email", "").strip().lower()
    senha = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(senha):
        if request.is_json:
            return jsonify({"ok": False, "msg": "Email ou senha incorretos."}), 401
        flash("Email ou senha incorretos.", "error")
        return redirect(url_for("home.index"))

    login_user(user, remember=True)
    if request.is_json:
        return jsonify({"ok": True, "redirect": url_for("home.index")})
    return redirect(url_for("home.index"))


# ─── Cadastro ────────────────────────────────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    data   = request.get_json() or request.form
    email  = data.get("email", "").strip().lower()
    senha  = data.get("password", "")
    senha2 = data.get("password2", "")
    username_raw = data.get("username", "").strip()

    def erro(msg):
        if request.is_json:
            return jsonify({"ok": False, "msg": msg}), 400
        flash(msg, "error")
        return redirect(url_for("home.index"))

    if not email or not senha:
        return erro("Preencha todos os campos.")
    if senha != senha2:
        return erro("As senhas não coincidem.")
    if len(senha) < 6:
        return erro("A senha deve ter pelo menos 6 caracteres.")
    if User.query.filter_by(email=email).first():
        return erro("Email já cadastrado.")

    username = username_raw or email.split("@")[0]
    base, i = username, 1
    while User.query.filter_by(username=username).first():
        username = f"{base}{i}"
        i += 1

    user = User(username=username, email=email)
    user.set_password(senha)
    db.session.add(user)
    db.session.commit()

    login_user(user, remember=True)
    if request.is_json:
        return jsonify({"ok": True, "redirect": url_for("home.index")})
    return redirect(url_for("home.index"))


# ─── Logout ──────────────────────────────────────────────────────────────────
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home.index"))


# ─── Google OAuth — Passo 1 ──────────────────────────────────────────────────
@auth_bp.route("/google")
def google_login():
    params = {
        "client_id":     os.getenv("GOOGLE_CLIENT_ID"),
        "redirect_uri":  get_google_redirect_uri(),
        "response_type": "code",
        "scope":         "openid email profile",
        "access_type":   "offline",
    }
    return redirect(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


# ─── Google OAuth — Callback ─────────────────────────────────────────────────
@auth_bp.route("/google/callback")
def google_callback():
    code  = request.args.get("code")
    error = request.args.get("error")

    if error or not code:
        flash("Login com Google cancelado.", "error")
        return redirect(url_for("home.index"))

    token_resp = requests.post(GOOGLE_TOKEN_URL, data={
        "code":          code,
        "client_id":     os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uri":  get_google_redirect_uri(),
        "grant_type":    "authorization_code",
    })
    tokens = token_resp.json()

    if "error" in tokens:
        flash("Erro ao autenticar com Google.", "error")
        return redirect(url_for("home.index"))

    user_info = requests.get(
        GOOGLE_USER_URL,
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    ).json()

    google_id = user_info.get("id")
    email     = user_info.get("email", "").lower()
    name      = user_info.get("name", email.split("@")[0])
    picture   = user_info.get("picture")

    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User.query.filter_by(email=email).first()

    if not user:
        username = name.replace(" ", "").lower()
        base, i = username, 1
        while User.query.filter_by(username=username).first():
            username = f"{base}{i}"
            i += 1
        user = User(username=username, email=email, google_id=google_id, profile_image=picture)
        db.session.add(user)
    else:
        user.google_id     = google_id
        user.profile_image = user.profile_image or picture

    db.session.commit()
    login_user(user, remember=True)
    return redirect(url_for("home.index"))
