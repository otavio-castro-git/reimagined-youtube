from flask import Blueprint, render_template, request
from flask_login import current_user
from ..models import Video, Tag, WatchHistory, Subscription, Channel

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    tag_filter = request.args.get("tag", "all")

    if tag_filter != "all":
        videos = (
            Video.query
            .join(Video.tags)
            .filter(Tag.name == tag_filter, Video.is_published == True)
            .order_by(Video.created_at.desc())
            .limit(24)
            .all()
        )
    else:
        videos = (
            Video.query
            .filter_by(is_published=True)
            .order_by(Video.created_at.desc())
            .limit(24)
            .all()
        )

    # Vídeos em destaque (mais views)
    featured = (
        Video.query
        .filter_by(is_published=True)
        .order_by(Video.views.desc())
        .first()
    )

    # "Continuar assistindo" para usuário logado
    continuar = []
    if current_user.is_authenticated:
        historico = (
            WatchHistory.query
            .filter_by(user_id=current_user.id)
            .order_by(WatchHistory.watched_at.desc())
            .limit(8)
            .all()
        )
        seen = set()
        for h in historico:
            if h.video_id not in seen and h.video and h.video.is_published:
                continuar.append(h.video)
                seen.add(h.video_id)

    # Subscriptions feed
    sub_videos = []
    if current_user.is_authenticated:
        subs = Subscription.query.filter_by(subscriber_id=current_user.id).all()
        channel_ids = [s.channel_id for s in subs]
        if channel_ids:
            sub_videos = (
                Video.query
                .filter(Video.channel_id.in_(channel_ids), Video.is_published == True)
                .order_by(Video.created_at.desc())
                .limit(12)
                .all()
            )

    tags = Tag.query.order_by(Tag.name).all()

    return render_template(
        "index.html",
        videos=videos,
        featured=featured,
        continuar=continuar,
        sub_videos=sub_videos,
        tags=tags,
        active_tag=tag_filter,
    )


@home_bp.route("/busca")
def busca():
    q = request.args.get("q", "").strip()
    videos = []
    if q:
        videos = (
            Video.query
            .filter(
                Video.title.ilike(f"%{q}%"),
                Video.is_published == True
            )
            .order_by(Video.views.desc())
            .limit(30)
            .all()
        )
    tags = Tag.query.order_by(Tag.name).all()
    return render_template("busca.html", videos=videos, query=q, tags=tags)


@home_bp.route("/tendencias")
def tendencias():
    videos = (
        Video.query
        .filter_by(is_published=True)
        .order_by(Video.views.desc())
        .limit(20)
        .all()
    )
    return render_template("tendencias.html", videos=videos)
