from flask import Blueprint, render_template, abort, jsonify, request, redirect, url_for
from flask_login import current_user, login_required
from ..models import db, Video, WatchHistory, VideoLike, Comment, Channel, Tag, SearchHistory
import requests as req
from flask import Response, stream_with_context

video_bp = Blueprint("video", __name__)


@video_bp.route("/watch/<int:video_id>")
def watch(video_id):
    video = Video.query.filter_by(id=video_id, is_published=True).first_or_404()

    # Conta view + histórico
    if current_user.is_authenticated:
        existing = WatchHistory.query.filter_by(
            user_id=current_user.id, video_id=video.id
        ).first()
        if existing:
            existing.watched_at = db.func.now()
        else:
            db.session.add(WatchHistory(user_id=current_user.id, video_id=video.id))
    video.views = (video.views or 0) + 1
    db.session.commit()

    # Liked?
    is_liked = False
    if current_user.is_authenticated:
        is_liked = VideoLike.query.filter_by(
            user_id=current_user.id, video_id=video.id
        ).first() is not None

    # Subscribed?
    from ..models import Subscription
    is_subscribed = False
    if current_user.is_authenticated:
        is_subscribed = Subscription.query.filter_by(
            subscriber_id=current_user.id, channel_id=video.channel_id
        ).first() is not None

    # Comentários
    comments = (
        Comment.query
        .filter_by(video_id=video.id, is_deleted=False)
        .order_by(Comment.created_at.desc())
        .limit(50)
        .all()
    )

    # Recomendações — mesma tag ou mais views
    recommended = []
    if video.tags:
        tag_ids = [t.id for t in video.tags]
        recommended = (
            Video.query
            .join(Video.tags)
            .filter(
                Tag.id.in_(tag_ids),
                Video.id != video.id,
                Video.is_published == True
            )
            .order_by(Video.views.desc())
            .limit(12)
            .all()
        )
    if len(recommended) < 12:
        extra = (
            Video.query
            .filter(Video.id != video.id, Video.is_published == True)
            .order_by(Video.views.desc())
            .limit(12 - len(recommended))
            .all()
        )
        seen_ids = {v.id for v in recommended}
        for v in extra:
            if v.id not in seen_ids:
                recommended.append(v)

    return render_template(
        "watch.html",
        video=video,
        comments=comments,
        recommended=recommended,
        is_liked=is_liked,
        is_subscribed=is_subscribed,
    )


# ─── Like toggle ─────────────────────────────────────────────────────────────
@video_bp.route("/api/videos/<int:vid>/like", methods=["POST"])
@login_required
def like_video(vid):
    video = Video.query.get_or_404(vid)
    existing = VideoLike.query.filter_by(user_id=current_user.id, video_id=vid).first()
    if existing:
        db.session.delete(existing)
        video.likes_count = max(0, (video.likes_count or 0) - 1)
        liked = False
    else:
        db.session.add(VideoLike(user_id=current_user.id, video_id=vid))
        video.likes_count = (video.likes_count or 0) + 1
        liked = True
    db.session.commit()
    return jsonify({"liked": liked, "likes": video.likes_count})


# ─── Comentário ──────────────────────────────────────────────────────────────
@video_bp.route("/api/videos/<int:vid>/comment", methods=["POST"])
@login_required
def post_comment(vid):
    video = Video.query.get_or_404(vid)
    data    = request.get_json() or {}
    content = data.get("content", "").strip()
    if not content:
        return jsonify({"ok": False, "msg": "Comentário vazio"}), 400
    if len(content) > 1000:
        return jsonify({"ok": False, "msg": "Comentário muito longo"}), 400

    comment = Comment(user_id=current_user.id, video_id=vid, content=content)
    db.session.add(comment)
    db.session.commit()

    return jsonify({
        "ok": True,
        "id": comment.id,
        "content": comment.content,
        "username": current_user.username,
        "profile_image": current_user.profile_image,
        "created_at": comment.created_at.strftime("%d/%m/%Y"),
    })


# ─── Progress save ───────────────────────────────────────────────────────────
@video_bp.route("/api/videos/<int:vid>/progress", methods=["POST"])
@login_required
def save_progress(vid):
    data    = request.get_json() or {}
    seconds = int(data.get("seconds", 0))
    entry = WatchHistory.query.filter_by(user_id=current_user.id, video_id=vid).first()
    if entry:
        entry.watched_seconds = seconds
        entry.watched_at = db.func.now()
        db.session.commit()
    return jsonify({"ok": True})


# ─── Histórico ───────────────────────────────────────────────────────────────
@video_bp.route("/historico")
@login_required
def historico():
    entries = (
        WatchHistory.query
        .filter_by(user_id=current_user.id)
        .order_by(WatchHistory.watched_at.desc())
        .limit(60)
        .all()
    )
    videos = [e.video for e in entries if e.video and e.video.is_published]
    return render_template("historico.html", videos=videos)


# ─── Curtidos ────────────────────────────────────────────────────────────────
@video_bp.route("/curtidos")
@login_required
def curtidos():
    likes = (
        VideoLike.query
        .filter_by(user_id=current_user.id)
        .order_by(VideoLike.liked_at.desc())
        .all()
    )
    videos = [l.video for l in likes if l.video and l.video.is_published]
    return render_template("curtidos.html", videos=videos)


# ─── Limpar histórico ────────────────────────────────────────────────────────
@video_bp.route("/api/historico/clear", methods=["POST"])
@login_required
def clear_historico():
    WatchHistory.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"ok": True})


# ─── Deletar vídeo próprio ────────────────────────────────────────────────────
@video_bp.route("/api/videos/<int:vid>/delete", methods=["POST"])
@login_required
def delete_video(vid):
    video = Video.query.get_or_404(vid)
    if video.channel.user_id != current_user.id:
        return jsonify({"ok": False, "msg": "Sem permissão"}), 403
    try:
        # Apaga registros dependentes que não têm CASCADE automático
        Comment.query.filter_by(video_id=vid).delete()
        WatchHistory.query.filter_by(video_id=vid).delete()
        VideoLike.query.filter_by(video_id=vid).delete()
        # Remove da tabela de playlist_videos
        from ..models import playlist_videos_table
        db.session.execute(
            playlist_videos_table.delete().where(
                playlist_videos_table.c.video_id == vid
            )
        )
        db.session.delete(video)
        db.session.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "msg": str(e)}), 500
@video_bp.route("/api/videos/<int:vid>/duration", methods=["POST"])
def save_duration(vid):
    data = request.get_json() or {}
    seconds = int(data.get("seconds", 0))
    if seconds > 0:
        video = Video.query.get(vid)
        if video and not video.duration_sec:
            video.duration_sec = seconds
            db.session.commit()
    return jsonify({"ok": True})



@video_bp.route("/stream/<int:vid>")
def stream(vid):
    video = Video.query.get_or_404(vid)
    
    # Repassa o header Range se o browser mandar
    range_header = request.headers.get('Range', None)
    headers = {}
    if range_header:
        headers['Range'] = range_header

    # Busca do Blob
    r = req.get(video.video_url, headers=headers, stream=True)

    # Monta a resposta repassando os headers importantes
    response_headers = {
        'Content-Type':  r.headers.get('Content-Type', 'video/mp4'),
        'Accept-Ranges': 'bytes',
        'Cache-Control': 'public, max-age=3600',
    }
    if 'Content-Range' in r.headers:
        response_headers['Content-Range'] = r.headers['Content-Range']
    if 'Content-Length' in r.headers:
        response_headers['Content-Length'] = r.headers['Content-Length']

    return Response(
        stream_with_context(r.iter_content(chunk_size=1024 * 256)),
        status=r.status_code,
        headers=response_headers,
    )