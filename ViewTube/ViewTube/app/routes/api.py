from flask import Blueprint, jsonify, request
from flask_login import current_user
from ..models import Video, Tag, Channel

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/videos")
def videos():
    tag  = request.args.get("tag", "all")
    page = int(request.args.get("page", 1))
    per_page = 24

    q = Video.query.filter_by(is_published=True)
    if tag != "all":
        q = q.join(Video.tags).filter(Tag.name == tag)
    q = q.order_by(Video.created_at.desc())

    videos = q.offset((page - 1) * per_page).limit(per_page).all()
    return jsonify([_video_dict(v) for v in videos])


@api_bp.route("/videos/trending")
def trending():
    videos = Video.query.filter_by(is_published=True).order_by(Video.views.desc()).limit(12).all()
    return jsonify([_video_dict(v) for v in videos])


@api_bp.route("/videos/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    videos = (
        Video.query
        .filter(Video.title.ilike(f"%{q}%"), Video.is_published == True)
        .order_by(Video.views.desc())
        .limit(20)
        .all()
    )
    return jsonify([_video_dict(v) for v in videos])


@api_bp.route("/tags")
def tags():
    tags = Tag.query.order_by(Tag.name).all()
    return jsonify([{"id": t.id, "name": t.name} for t in tags])


def _video_dict(v):
    return {
        "id":            v.id,
        "title":         v.title,
        "video_url":     v.video_url,
        "thumbnail_url": v.thumbnail_url,
        "views":         v.views,
        "views_fmt":     v.views_fmt,
        "duration_str":  v.duration_str,
        "age":           v.age_str,
        "likes":         v.likes_count,
        "channel":       v.channel.name if v.channel else "",
        "channel_id":    v.channel_id,
    }
