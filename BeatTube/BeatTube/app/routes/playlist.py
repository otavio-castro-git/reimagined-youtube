import os
import uuid
from flask import Blueprint, render_template, request, jsonify, abort, current_app
from flask_login import current_user, login_required
from ..models import db, Playlist, Song, LikedSong
from werkzeug.utils import secure_filename

playlist_bp = Blueprint("playlist", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_cover(file) -> str | None:
    """Salva o arquivo de capa e retorna a URL estática."""
    if not file or file.filename == "":
        return None
    ext = "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = os.path.join(current_app.root_path, "static", "uploads", "playlist_covers")
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))
    return f"/static/uploads/playlist_covers/{filename}"


# ─── Página de playlists do usuário ──────────────────────────────────────────
@playlist_bp.route("/playlists")
@login_required
def playlists():
    user_playlists = (
        Playlist.query
        .filter_by(user_id=current_user.id)
        .order_by(Playlist.created_at.desc())
        .all()
    )
    for pl in user_playlists:
        pl.song_count = pl.songs.count()
    return render_template("playlist.html", playlists=user_playlists)


# ─── Detalhe de uma playlist ──────────────────────────────────────────────────
@playlist_bp.route("/playlist/<int:playlist_id>")
def playlist_detail(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    if not playlist.is_public and (
        not current_user.is_authenticated or current_user.id != playlist.user_id
    ):
        abort(403)
    songs = list(playlist.songs)

    # Marca músicas curtidas pelo usuário atual
    liked_ids = set()
    if current_user.is_authenticated:
        liked_ids = {
            ls.song_id for ls in
            LikedSong.query.filter_by(user_id=current_user.id).all()
        }

    return render_template(
        "playlist_detail.html",
        playlist=playlist,
        songs=songs,
        liked_ids=liked_ids,
    )


# ─── API: listar playlists do usuário (para modal) ────────────────────────────
@playlist_bp.route("/api/playlists/minhas")
@login_required
def minhas_playlists():
    song_id = request.args.get("song_id", type=int)
    pls = (
        Playlist.query
        .filter_by(user_id=current_user.id)
        .order_by(Playlist.created_at.desc())
        .all()
    )
    result = []
    for pl in pls:
        has_song = False
        if song_id:
            has_song = db.session.execute(
                db.select(db.func.count()).select_from(
                    db.text("beattube.playlist_songs")
                ).where(
                    db.text(f"playlist_id = {pl.id} AND song_id = {song_id}")
                )
            ).scalar() > 0
        result.append({
            "id":        pl.id,
            "name":      pl.name,
            "cover_url": pl.cover_url,
            "song_count": pl.songs.count(),
            "has_song":  has_song,
        })
    return jsonify({"playlists": result})


# ─── API: criar playlist (com capa) ──────────────────────────────────────────
@playlist_bp.route("/api/playlist/criar", methods=["POST"])
@login_required
def create_playlist():
    # Aceita JSON (legado) ou multipart (com capa)
    if request.content_type and "application/json" in request.content_type:
        data = request.get_json()
        name = (data.get("name") or "").strip()
        desc = data.get("description", "")
        cover_url = None
    else:
        name = (request.form.get("name") or "").strip()
        desc = request.form.get("description", "")
        cover_url = save_cover(request.files.get("cover"))

    if not name:
        return jsonify({"ok": False, "error": "Nome obrigatório."}), 400

    p = Playlist(
        name=name,
        description=desc,
        cover_url=cover_url,
        user_id=current_user.id,
        is_public=True,
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({"ok": True, "playlist_id": p.id})


# ─── API: adicionar música à playlist ─────────────────────────────────────────
@playlist_bp.route("/api/playlist/<int:playlist_id>/add/<int:song_id>", methods=["POST"])
@login_required
def add_to_playlist(playlist_id, song_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.user_id != current_user.id:
        abort(403)
    song = Song.query.get_or_404(song_id)
    already = song in playlist.songs.all()
    if not already:
        playlist.songs.append(song)
        db.session.commit()
    return jsonify({"ok": True, "added": True})


# ─── API: remover música da playlist ─────────────────────────────────────────
@playlist_bp.route("/api/playlist/<int:playlist_id>/remove/<int:song_id>", methods=["POST"])
@login_required
def remove_from_playlist(playlist_id, song_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.user_id != current_user.id:
        abort(403)
    song = Song.query.get_or_404(song_id)
    if song in playlist.songs.all():
        playlist.songs.remove(song)
        db.session.commit()
    return jsonify({"ok": True, "added": False})
