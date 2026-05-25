from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import current_user, login_required
from ..models import db, Playlist, Song

playlist_bp = Blueprint("playlist", __name__)


@playlist_bp.route("/playlists")
@login_required
def playlists():
    user_playlists = (
        Playlist.query
        .filter_by(user_id=current_user.id)
        .order_by(Playlist.created_at.desc())
        .all()
    )
    # Adiciona song_count como atributo temporário
    for pl in user_playlists:
        pl.song_count = pl.songs.count()

    return render_template("playlist.html", playlists=user_playlists)


@playlist_bp.route("/playlist/<int:playlist_id>")
def playlist_detail(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    if not playlist.is_public and (
        not current_user.is_authenticated or current_user.id != playlist.user_id
    ):
        abort(403)
    songs = list(playlist.songs)
    return render_template("playlist_detail.html", playlist=playlist, songs=songs)


# ─── API: criar playlist ──────────────────────────────────────────────────────

# O JS chama /api/playlist/criar

@playlist_bp.route("/api/playlist/criar", methods=["POST"])
@login_required
def create_playlist():
    data = request.get_json()
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"ok": False, "error": "Nome obrigatório."}), 400

    p = Playlist(
        name=name,
        description=data.get("description", ""),
        user_id=current_user.id,
        is_public=data.get("is_public", True),
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
    if song not in playlist.songs:
        playlist.songs.append(song)
        db.session.commit()
    return jsonify({"ok": True})
