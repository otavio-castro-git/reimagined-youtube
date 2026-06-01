from flask import Blueprint, render_template, redirect, url_for, jsonify, request, abort
from flask_login import current_user, login_required
from ..models import db, Channel, Video, Subscription, User, Playlist, playlist_videos_table

channel_bp = Blueprint("channel", __name__)


@channel_bp.route("/canal/<int:channel_id>")
def canal(channel_id):
    channel = Channel.query.get_or_404(channel_id)
    videos = (
        Video.query
        .filter_by(channel_id=channel_id, is_published=True)
        .order_by(Video.created_at.desc())
        .all()
    )
    is_subscribed = False
    if current_user.is_authenticated:
        is_subscribed = Subscription.query.filter_by(
            subscriber_id=current_user.id, channel_id=channel_id
        ).first() is not None

    public_playlists = Playlist.query.filter_by(user_id=channel.user_id, is_public=True).all()

    return render_template(
        "canal.html",
        channel=channel,
        videos=videos,
        is_subscribed=is_subscribed,
        subscriber_count=channel.subscriber_count,
        public_playlists=public_playlists,
    )


@channel_bp.route("/api/channels/<int:cid>/subscribe", methods=["POST"])
@login_required
def subscribe(cid):
    channel = Channel.query.get_or_404(cid)
    existing = Subscription.query.filter_by(
        subscriber_id=current_user.id, channel_id=cid
    ).first()
    if existing:
        db.session.delete(existing)
        subscribed = False
    else:
        db.session.add(Subscription(subscriber_id=current_user.id, channel_id=cid))
        subscribed = True
    db.session.commit()
    return jsonify({"subscribed": subscribed, "count": channel.subscriber_count})


@channel_bp.route("/meu-canal")
@login_required
def meu_canal():
    channel = Channel.query.filter_by(user_id=current_user.id).first()
    if not channel:
        return render_template("criar_canal.html")
    return redirect(url_for("channel.canal", channel_id=channel.id))


@channel_bp.route("/criar-canal", methods=["POST"])
@login_required
def criar_canal():
    data = request.get_json() or request.form
    name = data.get("name", "").strip()
    desc = data.get("description", "").strip()

    if not name:
        return jsonify({"ok": False, "msg": "Nome obrigatório"}), 400
    if Channel.query.filter_by(user_id=current_user.id).first():
        return jsonify({"ok": False, "msg": "Você já tem um canal"}), 400

    channel = Channel(user_id=current_user.id, name=name, description=desc)
    db.session.add(channel)
    db.session.commit()

    if request.is_json:
        return jsonify({"ok": True, "id": channel.id})
    return redirect(url_for("channel.canal", channel_id=channel.id))


@channel_bp.route("/inscricoes")
@login_required
def inscricoes():
    subs = Subscription.query.filter_by(subscriber_id=current_user.id).all()
    channel_ids = [s.channel_id for s in subs]
    channels = Channel.query.filter(Channel.id.in_(channel_ids)).all() if channel_ids else []
    videos = []
    if channel_ids:
        videos = (
            Video.query
            .filter(Video.channel_id.in_(channel_ids), Video.is_published == True)
            .order_by(Video.created_at.desc())
            .limit(24)
            .all()
        )
    return render_template("inscricoes.html", channels=channels, videos=videos)

# ─── Playlists ────────────────────────────────────────────────────────────────
@channel_bp.route("/playlists")
@login_required
def minhas_playlists():
    playlists = Playlist.query.filter_by(user_id=current_user.id).order_by(Playlist.created_at.desc()).all()
    return render_template("playlists.html", playlists=playlists)


@channel_bp.route("/api/playlists", methods=["POST"])
@login_required
def criar_playlist():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"ok": False, "msg": "Nome obrigatório"}), 400
    pl = Playlist(
        user_id=current_user.id,
        name=name,
        description=data.get("description", "").strip(),
        is_public=data.get("is_public", True),
    )
    db.session.add(pl)
    db.session.commit()
    return jsonify({"ok": True, "id": pl.id, "name": pl.name})


@channel_bp.route("/api/playlists/<int:pid>/delete", methods=["POST"])
@login_required
def deletar_playlist(pid):
    pl = Playlist.query.get_or_404(pid)
    if pl.user_id != current_user.id:
        return jsonify({"ok": False, "msg": "Sem permissão"}), 403
    db.session.delete(pl)
    db.session.commit()
    return jsonify({"ok": True})


@channel_bp.route("/api/playlists/<int:pid>/add-video", methods=["POST"])
@login_required
def add_video_playlist(pid):
    pl = Playlist.query.get_or_404(pid)
    if pl.user_id != current_user.id:
        return jsonify({"ok": False, "msg": "Sem permissão"}), 403
    data = request.get_json() or {}
    video_id = data.get("video_id")
    video = Video.query.get_or_404(video_id)
    # check if already in playlist
    existing = db.session.execute(
        playlist_videos_table.select().where(
            playlist_videos_table.c.playlist_id == pid,
            playlist_videos_table.c.video_id == video_id,
        )
    ).first()
    if existing:
        return jsonify({"ok": False, "msg": "Vídeo já está na playlist"})
    db.session.execute(playlist_videos_table.insert().values(
        playlist_id=pid, video_id=video_id, position=0
    ))
    db.session.commit()
    return jsonify({"ok": True})


@channel_bp.route("/api/playlists/<int:pid>/remove-video", methods=["POST"])
@login_required
def remove_video_playlist(pid):
    pl = Playlist.query.get_or_404(pid)
    if pl.user_id != current_user.id:
        return jsonify({"ok": False, "msg": "Sem permissão"}), 403
    data = request.get_json() or {}
    video_id = data.get("video_id")
    db.session.execute(
        playlist_videos_table.delete().where(
            playlist_videos_table.c.playlist_id == pid,
            playlist_videos_table.c.video_id == video_id,
        )
    )
    db.session.commit()
    return jsonify({"ok": True})


@channel_bp.route("/playlist/<int:pid>")
def ver_playlist(pid):
    pl = Playlist.query.get_or_404(pid)
    if not pl.is_public and (not current_user.is_authenticated or current_user.id != pl.user_id):
        abort(403)
    videos = pl.videos.all()
    is_owner = current_user.is_authenticated and current_user.id == pl.user_id
    return render_template("playlist.html", playlist=pl, videos=videos, is_owner=is_owner)


@channel_bp.route("/api/playlists/<int:pid>/toggle-visibility", methods=["POST"])
@login_required
def toggle_playlist_visibility(pid):
    pl = Playlist.query.get_or_404(pid)
    if pl.user_id != current_user.id:
        return jsonify({"ok": False, "msg": "Sem permissão"}), 403
    pl.is_public = not pl.is_public
    db.session.commit()
    return jsonify({"ok": True, "is_public": pl.is_public})


@channel_bp.route("/api/playlists/list")
@login_required
def listar_playlists_json():
    playlists = Playlist.query.filter_by(user_id=current_user.id).order_by(Playlist.created_at.desc()).all()
    return jsonify([{"id": pl.id, "name": pl.name, "is_public": pl.is_public} for pl in playlists])
