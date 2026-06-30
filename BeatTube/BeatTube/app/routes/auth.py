"""
Autenticação: login por email/senha e login com Google OAuth 2.0.
"""
import os
import random
import time
import requests
from flask import Blueprint, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlencode
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import db, User, Playlist
from ..captcha_utils import validar_recaptcha
from ..email_utils import enviar_email_codigo

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_URL  = "https://www.googleapis.com/oauth2/v2/userinfo"


def get_google_redirect_uri():
    base = os.getenv("BASE_URL", "http://localhost:5000")
    return f"{base}/auth/google/callback"


# ─── Login com email/senha ────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["GET"])
def login_page():
    # O login é um modal no base.html que redireciona para home
    return redirect(url_for("home.index"))


@auth_bp.route("/login", methods=["POST"])
def login():
    data  = request.get_json() or request.form
    email = data.get("email", "").strip().lower()
    senha = data.get("password", "")

    def erro(msg, status=401):
        if request.is_json:
            return jsonify({"ok": False, "msg": msg}), status
        flash(msg, "error")
        return redirect(url_for("home.index"))

    # ── Captcha (reCAPTCHA v3) ──────────────────────────────────────────────
    captcha_token = data.get("captcha_token", "")
    captcha_ok, captcha_msg = validar_recaptcha(captcha_token, acao_esperada="login")
    if not captcha_ok:
        return erro(captcha_msg, 400)

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(senha):
        return erro("Email ou senha incorretos.")

    login_user(user, remember=True)

    if request.is_json:
        return jsonify({"ok": True, "redirect": url_for("home.index")})
    return redirect(url_for("home.index"))


# ─── Cadastro — Passo 1: validar dados + captcha e enviar código por email ────
@auth_bp.route("/register", methods=["POST"])
def register():
    data   = request.get_json() or request.form
    email  = data.get("email", "").strip().lower()
    senha  = data.get("password", "")
    senha2 = data.get("password2", "")

    def erro(msg, status=400):
        if request.is_json:
            return jsonify({"ok": False, "msg": msg}), status
        flash(msg, "error")
        return redirect(url_for("home.index"))

    # ── Captcha (reCAPTCHA v3) ──────────────────────────────────────────────
    captcha_token = data.get("captcha_token", "")
    captcha_ok, captcha_msg = validar_recaptcha(captcha_token, acao_esperada="register")
    if not captcha_ok:
        return erro(captcha_msg)

    if not email or not senha:
        return erro("Preencha todos os campos.")
    if senha != senha2:
        return erro("As senhas não coincidem.")

    # ── Aceite dos Termos de Uso e Política de Privacidade ──────────────────
    # Nunca confiar apenas na validação do front-end: o checkbox precisa
    # chegar marcado também na requisição.
    aceitou_termos = data.get("aceitou_termos") in (True, "true", "True", "1", 1, "on")
    if not aceitou_termos:
        return erro("Você precisa aceitar os Termos de Uso e a Política de Privacidade para se cadastrar.")

    if User.query.filter_by(email=email).first():
        return erro("Email já cadastrado.")

    # Gera o código de 6 dígitos e guarda temporariamente na sessão (cookie
    # assinado pelo Flask) até o usuário confirmar — nada disso vai pro banco.
    codigo = f"{random.randint(0, 999999):06d}"

    session["cadastro_pendente"] = {
        "email":         email,
        "code_hash":     generate_password_hash(codigo),
        "password_hash": generate_password_hash(senha),
        "attempts":      0,
        "expires_at":    time.time() + 10 * 60,  # 10 minutos
    }

    enviar_email_codigo(email, codigo)

    return jsonify({"ok": True, "etapa": "verificar_email", "email": email})


# ─── Cadastro — Passo 2: confirmar código e criar a conta ─────────────────────
@auth_bp.route("/register/confirmar", methods=["POST"])
def register_confirmar():
    data   = request.get_json() or request.form
    email  = data.get("email", "").strip().lower()
    codigo = data.get("codigo", "").strip()

    def erro(msg, status=400):
        if request.is_json:
            return jsonify({"ok": False, "msg": msg}), status
        flash(msg, "error")
        return redirect(url_for("home.index"))

    pendente = session.get("cadastro_pendente")

    if not email or not codigo:
        return erro("Informe o código recebido por email.")

    if not pendente or pendente.get("email") != email:
        return erro("Nenhum cadastro pendente para esse email. Comece o cadastro novamente.")

    if time.time() > pendente["expires_at"]:
        session.pop("cadastro_pendente", None)
        return erro("Esse código expirou. Comece o cadastro novamente.")

    if pendente.get("attempts", 0) >= 5:
        session.pop("cadastro_pendente", None)
        return erro("Muitas tentativas incorretas. Comece o cadastro novamente.")

    if not check_password_hash(pendente["code_hash"], codigo):
        pendente["attempts"] = pendente.get("attempts", 0) + 1
        session["cadastro_pendente"] = pendente
        return erro("Código incorreto. Verifique e tente novamente.")

    # Código correto: garante que o email ainda não foi cadastrado por outra via
    if User.query.filter_by(email=email).first():
        session.pop("cadastro_pendente", None)
        return erro("Email já cadastrado.")

    username = email.split("@")[0]
    base, i = username, 1
    while User.query.filter_by(username=username).first():
        username = f"{base}{i}"
        i += 1

    user = User(username=username, email=email)
    user.password_hash = pendente["password_hash"]  # já está em hash
    db.session.add(user)
    db.session.flush()  # gera o user.id antes do commit

    # Playlist "Músicas Curtidas" criada automaticamente
    liked_pl = Playlist(
        name="Músicas Curtidas",
        description="Suas músicas favoritas",
        cover_url=None,
        is_public=False,
        user_id=user.id,
    )
    db.session.add(liked_pl)
    db.session.commit()
    session.pop("cadastro_pendente", None)

    login_user(user, remember=True)

    if request.is_json:
        return jsonify({"ok": True, "redirect": url_for("home.index")})
    return redirect(url_for("home.index"))


# ─── Cadastro — reenviar código ────────────────────────────────────────────────
@auth_bp.route("/register/reenviar", methods=["POST"])
def register_reenviar():
    data  = request.get_json() or request.form
    email = data.get("email", "").strip().lower()

    def erro(msg, status=400):
        return jsonify({"ok": False, "msg": msg}), status

    pendente = session.get("cadastro_pendente")
    if not pendente or pendente.get("email") != email:
        return erro("Nenhum cadastro pendente para esse email. Comece o cadastro novamente.")

    codigo = f"{random.randint(0, 999999):06d}"
    pendente["code_hash"]  = generate_password_hash(codigo)
    pendente["attempts"]   = 0
    pendente["expires_at"] = time.time() + 10 * 60
    session["cadastro_pendente"] = pendente

    enviar_email_codigo(email, codigo)
    return jsonify({"ok": True})


# ─── Logout ───────────────────────────────────────────────────────────────────
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home.index"))


# ─── Google OAuth — Passo 1 ───────────────────────────────────────────────────
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


# ─── Google OAuth — Passo 2: callback ─────────────────────────────────────────
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
        db.session.flush()  # gera user.id
        # Playlist padrão
        db.session.add(Playlist(
            name="Músicas Curtidas",
            description="Suas músicas favoritas",
            cover_url=None,
            is_public=False,
            user_id=user.id,
        ))
    else:
        user.google_id     = google_id
        user.profile_image = user.profile_image or picture

    db.session.commit()
    login_user(user, remember=True)
    return redirect(url_for("home.index"))


# ─── API: trocar usuário ──────────────────────────────────────────────────────
@auth_bp.route("/trocar-usuario", methods=["POST"])
@login_required
def trocar_usuario():
    data     = request.get_json() or {}
    username = data.get("username", "").strip()
    if not username:
        return jsonify({"ok": False, "msg": "Informe o novo nome de usuário."}), 400
    if len(username) < 3:
        return jsonify({"ok": False, "msg": "O nome deve ter ao menos 3 caracteres."}), 400
    existing = User.query.filter_by(username=username).first()
    if existing and existing.id != current_user.id:
        return jsonify({"ok": False, "msg": "Esse nome de usuário já está em uso."}), 409
    current_user.username = username
    db.session.commit()
    return jsonify({"ok": True})


# ─── API: trocar senha ────────────────────────────────────────────────────────
@auth_bp.route("/trocar-senha", methods=["POST"])
@login_required
def trocar_senha():
    data        = request.get_json() or {}
    senha_atual = data.get("senha_atual", "")
    nova_senha  = data.get("nova_senha", "")
    nova_senha2 = data.get("nova_senha2", "")

    if not senha_atual or not nova_senha:
        return jsonify({"ok": False, "msg": "Preencha todos os campos."}), 400
    if nova_senha != nova_senha2:
        return jsonify({"ok": False, "msg": "As senhas não coincidem."}), 400
    if len(nova_senha) < 6:
        return jsonify({"ok": False, "msg": "A nova senha deve ter ao menos 6 caracteres."}), 400
    if not current_user.check_password(senha_atual):
        return jsonify({"ok": False, "msg": "Senha atual incorreta."}), 401

    current_user.set_password(nova_senha)
    db.session.commit()
    return jsonify({"ok": True})
