"""
Models SQLAlchemy para o ViewTube.
Schemas: shared.* (compartilhado com BeatTube) e viewtube.*
"""
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ─── shared.users (mesma tabela do BeatTube) ─────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__  = "users"
    __table_args__ = {"schema": "shared"}

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(50),  unique=True, nullable=False)
    email         = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    is_premium    = db.Column(db.Boolean, default=False)
    profile_image = db.Column(db.String(500), nullable=True)
    google_id     = db.Column(db.String(255), unique=True, nullable=True)
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    channels      = db.relationship("Channel",      back_populates="user",    lazy="dynamic")
    playlists     = db.relationship("Playlist",     back_populates="user",    lazy="dynamic")
    watch_history = db.relationship("WatchHistory", back_populates="user",    lazy="dynamic")
    liked_videos  = db.relationship("VideoLike",    back_populates="user",    lazy="dynamic")
    comments      = db.relationship("Comment",      back_populates="user",    lazy="dynamic")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


# ─── shared.user_subscriptions ───────────────────────────────────────────────
class UserSubscription(db.Model):
    __tablename__  = "user_subscriptions"
    __table_args__ = {"schema": "shared"}

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("shared.users.id", ondelete="CASCADE"), nullable=False)
    status       = db.Column(db.String(20), default="active")
    started_at   = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at   = db.Column(db.DateTime, nullable=False)
    cancelled_at = db.Column(db.DateTime, nullable=True)


# ─── viewtube.channels ───────────────────────────────────────────────────────
class Channel(db.Model):
    __tablename__  = "channels"
    __table_args__ = {"schema": "viewtube"}

    id                = db.Column(db.Integer, primary_key=True)
    user_id           = db.Column(db.Integer, db.ForeignKey("shared.users.id", ondelete="CASCADE"), nullable=False)
    name              = db.Column(db.String(150), nullable=False)
    description       = db.Column(db.Text, nullable=True)
    profile_image_url = db.Column(db.String(500), nullable=True)
    banner_url        = db.Column(db.String(500), nullable=True)
    created_at        = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user    = db.relationship("User",    back_populates="channels")
    videos  = db.relationship("Video",   back_populates="channel",  lazy="dynamic")

    @property
    def subscriber_count(self):
        return Subscription.query.filter_by(channel_id=self.id).count()


# ─── viewtube.videos ─────────────────────────────────────────────────────────
class Video(db.Model):
    __tablename__  = "videos"
    __table_args__ = {"schema": "viewtube"}

    id            = db.Column(db.Integer, primary_key=True)
    channel_id    = db.Column(db.Integer, db.ForeignKey("viewtube.channels.id", ondelete="CASCADE"), nullable=False)
    title         = db.Column(db.String(255), nullable=False)
    description   = db.Column(db.Text, nullable=True)
    video_url     = db.Column(db.String(500), nullable=False)
    thumbnail_url = db.Column(db.String(500), nullable=True)
    duration_sec  = db.Column(db.Integer, nullable=True)
    views         = db.Column(db.BigInteger, default=0)
    likes_count   = db.Column(db.Integer, default=0)
    is_published  = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    channel       = db.relationship("Channel",  back_populates="videos")
    tags          = db.relationship("Tag",       secondary="viewtube.video_tags", lazy="subquery")
    comments      = db.relationship("Comment",   back_populates="video",  lazy="dynamic",
                                    primaryjoin="and_(Comment.video_id==Video.id, Comment.is_deleted==False)")
    watch_entries = db.relationship("WatchHistory", back_populates="video", lazy="dynamic")

    @property
    def duration_str(self) -> str:
        if not self.duration_sec:
            return "0:00"
        m, s = divmod(int(self.duration_sec), 60)
        h, m2 = divmod(m, 60)
        if h:
            return f"{h}:{m2:02d}:{s:02d}"
        return f"{m}:{s:02d}"

    @property
    def views_fmt(self) -> str:
        n = self.views or 0
        if n >= 1_000_000_000:
            return f"{n/1e9:.1f}B"
        if n >= 1_000_000:
            return f"{n/1e6:.1f}M"
        if n >= 1_000:
            return f"{n/1e3:.1f}K"
        return str(n)

    @property
    def age_str(self) -> str:
        from datetime import timezone as tz
        now = datetime.now(tz.utc)
        created = self.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=tz.utc)
        diff = now - created
        days = diff.days
        if days == 0:
            return "hoje"
        if days < 7:
            return f"há {days} dia{'s' if days > 1 else ''}"
        if days < 30:
            w = days // 7
            return f"há {w} semana{'s' if w > 1 else ''}"
        if days < 365:
            mo = days // 30
            return f"há {mo} mês" if mo == 1 else f"há {mo} meses"
        y = days // 365
        return f"há {y} ano{'s' if y > 1 else ''}"


# ─── viewtube.tags ───────────────────────────────────────────────────────────
class Tag(db.Model):
    __tablename__  = "tags"
    __table_args__ = {"schema": "viewtube"}

    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)


video_tags_table = db.Table(
    "video_tags",
    db.metadata,
    db.Column("video_id", db.Integer, db.ForeignKey("viewtube.videos.id", ondelete="CASCADE"), primary_key=True),
    db.Column("tag_id",   db.Integer, db.ForeignKey("viewtube.tags.id",   ondelete="CASCADE"), primary_key=True),
    schema="viewtube",
)


# ─── viewtube.video_likes ────────────────────────────────────────────────────
class VideoLike(db.Model):
    __tablename__  = "video_likes"
    __table_args__ = {"schema": "viewtube"}

    user_id  = db.Column(db.Integer, db.ForeignKey("shared.users.id",     ondelete="CASCADE"), primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey("viewtube.videos.id",  ondelete="CASCADE"), primary_key=True)
    liked_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user  = db.relationship("User",  back_populates="liked_videos")
    video = db.relationship("Video")


# ─── viewtube.comments ───────────────────────────────────────────────────────
class Comment(db.Model):
    __tablename__  = "comments"
    __table_args__ = {"schema": "viewtube"}

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("shared.users.id",    ondelete="NO ACTION"), nullable=False)
    video_id   = db.Column(db.Integer, db.ForeignKey("viewtube.videos.id", ondelete="CASCADE"),   nullable=False)
    content    = db.Column(db.Text, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user  = db.relationship("User",  back_populates="comments")
    video = db.relationship("Video", back_populates="comments",
                            primaryjoin="and_(Comment.video_id==Video.id, Comment.is_deleted==False)")


# ─── viewtube.subscriptions ──────────────────────────────────────────────────
class Subscription(db.Model):
    __tablename__  = "subscriptions"
    __table_args__ = {"schema": "viewtube"}

    subscriber_id = db.Column(db.Integer, db.ForeignKey("shared.users.id",      ondelete="CASCADE"),    primary_key=True)
    channel_id    = db.Column(db.Integer, db.ForeignKey("viewtube.channels.id", ondelete="NO ACTION"),  primary_key=True)
    subscribed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# ─── viewtube.playlists ──────────────────────────────────────────────────────
class Playlist(db.Model):
    __tablename__  = "playlists"
    __table_args__ = {"schema": "viewtube"}

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey("shared.users.id", ondelete="CASCADE"), nullable=False)
    name          = db.Column(db.String(255), nullable=False)
    description   = db.Column(db.String(500), nullable=True)
    thumbnail_url = db.Column(db.String(500), nullable=True)
    is_public     = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user   = db.relationship("User",  back_populates="playlists")
    videos = db.relationship("Video", secondary="viewtube.playlist_videos", lazy="dynamic")


playlist_videos_table = db.Table(
    "playlist_videos",
    db.metadata,
    db.Column("playlist_id", db.Integer, db.ForeignKey("viewtube.playlists.id", ondelete="CASCADE"), primary_key=True),
    db.Column("video_id",    db.Integer, db.ForeignKey("viewtube.videos.id",    ondelete="CASCADE"), primary_key=True),
    db.Column("position",    db.Integer, default=0),
    db.Column("added_at",    db.DateTime, default=lambda: datetime.now(timezone.utc)),
    schema="viewtube",
)


# ─── viewtube.watch_history ──────────────────────────────────────────────────
class WatchHistory(db.Model):
    __tablename__  = "watch_history"
    __table_args__ = {"schema": "viewtube"}

    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey("shared.users.id",    ondelete="CASCADE"), nullable=False)
    video_id        = db.Column(db.Integer, db.ForeignKey("viewtube.videos.id", ondelete="CASCADE"), nullable=False)
    watched_seconds = db.Column(db.Integer, default=0)
    watched_at      = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user  = db.relationship("User",  back_populates="watch_history")
    video = db.relationship("Video", back_populates="watch_entries")


# ─── viewtube.search_history ─────────────────────────────────────────────────
class SearchHistory(db.Model):
    __tablename__  = "search_history"
    __table_args__ = {"schema": "viewtube"}

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("shared.users.id", ondelete="CASCADE"), nullable=False)
    query       = db.Column(db.String(255), nullable=False)
    searched_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
