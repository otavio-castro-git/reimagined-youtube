"""
Upload de vídeos e thumbnails para Azure Blob Storage.
Fluxo: browser → SAS URL → Blob direto (sem passar pelo Flask).
Apenas usuários premium podem fazer upload.
"""
import os
import uuid
from datetime import datetime, timezone, timedelta
from flask import Blueprint, render_template, jsonify, request, url_for, current_app
from flask_login import login_required, current_user
from ..models import db, Video, Channel, Tag

upload_bp = Blueprint("upload", __name__)


def _account_name() -> str:
    conn = current_app.config.get("AZURE_STORAGE_CONNECTION_STRING", "")
    return conn.split("AccountName=")[1].split(";")[0]


def _blob_service():
    from azure.storage.blob import BlobServiceClient
    conn = current_app.config.get("AZURE_STORAGE_CONNECTION_STRING", "")
    if not conn:
        raise ValueError("AZURE_STORAGE_CONNECTION_STRING não configurado")
    return BlobServiceClient.from_connection_string(conn)


def generate_sas_url(container: str, blob_name: str, content_type: str) -> str:
    """Gera uma SAS URL de escrita válida por 2 horas."""
    from azure.storage.blob import generate_blob_sas, BlobSasPermissions
    conn = current_app.config.get("AZURE_STORAGE_CONNECTION_STRING", "")
    account_name = _account_name()
    account_key  = conn.split("AccountKey=")[1].split(";")[0]

    sas_token = generate_blob_sas(
        account_name=account_name,
        container_name=container,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(write=True, create=True),
        expiry=datetime.now(timezone.utc) + timedelta(hours=2),
        content_type=content_type,
    )
    return f"https://{account_name}.blob.core.windows.net/{container}/{blob_name}?{sas_token}"


def public_url(container: str, blob_name: str) -> str:
    return f"https://{_account_name()}.blob.core.windows.net/{container}/{blob_name}"


# ─── Página de upload ─────────────────────────────────────────
@upload_bp.route("/upload")
@login_required
def upload_page():
    if not current_user.is_premium:
        return render_template("upload_bloqueado.html")
    channel = Channel.query.filter_by(user_id=current_user.id).first()
    tags = Tag.query.order_by(Tag.name).all()
    return render_template("upload.html", channel=channel, tags=tags)


# ─── Gera SAS URLs para o browser fazer upload direto ─────────
@upload_bp.route("/upload/sas", methods=["POST"])
@login_required
def get_sas():
    if not current_user.is_premium:
        return jsonify({"ok": False, "msg": "Apenas usuários premium podem fazer upload"}), 403

    channel = Channel.query.filter_by(user_id=current_user.id).first()
    if not channel:
        return jsonify({"ok": False, "msg": "Crie um canal primeiro"}), 400

    data      = request.get_json() or {}
    video_ext = data.get("video_ext", ".mp4").lower()
    thumb_ext = data.get("thumb_ext", "")

    allowed_video = {".mp4", ".webm", ".mov", ".avi", ".mkv"}
    allowed_image = {".jpg", ".jpeg", ".png", ".webp"}

    if video_ext not in allowed_video:
        return jsonify({"ok": False, "msg": "Formato de vídeo não suportado"}), 400

    video_blob = f"{uuid.uuid4()}{video_ext}"
    thumb_blob = f"{uuid.uuid4()}{thumb_ext}" if thumb_ext in allowed_image else None

    container_videos = current_app.config.get("AZURE_CONTAINER_VIDEOS", "videos")
    container_thumbs = current_app.config.get("AZURE_CONTAINER_THUMBNAILS", "thumbnails")

    video_content_types = {
        ".mp4": "video/mp4", ".webm": "video/webm",
        ".mov": "video/quicktime", ".avi": "video/x-msvideo", ".mkv": "video/x-matroska",
    }
    thumb_content_types = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
    }

    result = {
        "ok": True,
        "video_sas":  generate_sas_url(container_videos, video_blob, video_content_types.get(video_ext, "video/mp4")),
        "video_url":  public_url(container_videos, video_blob),
        "thumb_sas":  generate_sas_url(container_thumbs, thumb_blob, thumb_content_types.get(thumb_ext, "image/jpeg")) if thumb_blob else None,
        "thumb_url":  public_url(container_thumbs, thumb_blob) if thumb_blob else None,
    }
    return jsonify(result)


# ─── Salva registro no banco após upload direto ───────────────
@upload_bp.route("/upload/confirm", methods=["POST"])
@login_required
def confirm_upload():
    if not current_user.is_premium:
        return jsonify({"ok": False, "msg": "Acesso negado"}), 403

    channel = Channel.query.filter_by(user_id=current_user.id).first()
    if not channel:
        return jsonify({"ok": False, "msg": "Canal não encontrado"}), 400

    data        = request.get_json() or {}
    title       = data.get("title", "").strip()
    description = data.get("description", "").strip()
    video_url   = data.get("video_url", "").strip()
    thumb_url   = data.get("thumb_url") or None
    tag_ids     = data.get("tags", [])
    duration    = data.get("duration")

    if not title or not video_url:
        return jsonify({"ok": False, "msg": "Título e vídeo são obrigatórios"}), 400

    try:
        video = Video(
            channel_id=channel.id,
            title=title,
            description=description,
            video_url=video_url,
            thumbnail_url=thumb_url,
            duration_sec=int(duration) if duration else None,
            is_published=True,
        )
        if tag_ids:
            tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
            video.tags = tags

        db.session.add(video)
        db.session.commit()
        return jsonify({"ok": True, "id": video.id, "redirect": url_for("video.watch", video_id=video.id)})

    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "msg": f"Erro ao salvar: {str(e)}"}), 500