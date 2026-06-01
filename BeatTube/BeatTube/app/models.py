"""
Models SQLAlchemy espelhando o schema beattube_final.sql (Azure SQL / T-SQL).
Schemas: shared.* e beattube.*
"""
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ─── shared.users ────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__  = "users"
    __table_args__ = {"schema": "shared"}

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(50),  unique=True, nullable=False)
    email         = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)   # NULL para login Google
    is_premium    = db.Column(db.Boolean, default=False)
    profile_image = db.Column(db.String(500), nullable=True)
    google_id     = db.Column(db.String(255), unique=True, nullable=True)
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relacionamentos
    playlists     = db.relationship("Playlist",    back_populates="user", lazy="dynamic")
    play_history  = db.relationship("PlayHistory", back_populates="user", lazy="dynamic")
    liked_songs   = db.relationship("LikedSong",   back_populates="user", lazy="dynamic")

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
    status       = db.Column(db.String(20), default="active")   # active | cancelled | expired
    started_at   = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at   = db.Column(db.DateTime, nullable=False)
    cancelled_at = db.Column(db.DateTime, nullable=True)


# ─── shared.payments ─────────────────────────────────────────────────────────
class Payment(db.Model):
    __tablename__  = "payments"
    __table_args__ = {"schema": "shared"}

    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey("shared.users.id", ondelete="CASCADE"), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey("shared.user_subscriptions.id"), nullable=False)
    amount          = db.Column(db.Numeric(10, 2), nullable=False)
    currency        = db.Column(db.String(3), default="BRL")
    status          = db.Column(db.String(20), default="pending")  # pending | paid | failed | refunded
    payment_method  = db.Column(db.String(50), nullable=True)
    external_ref    = db.Column(db.String(255), nullable=True)
    paid_at         = db.Column(db.DateTime, nullable=True)
    created_at      = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# ─── beattube.artists ────────────────────────────────────────────────────────
class Artist(db.Model):
    __tablename__  = "artists"
    __table_args__ = {"schema": "beattube"}

    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(150), nullable=False)
    bio       = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)

    albums    = db.relationship("Album", back_populates="artist", lazy="dynamic")
    


# ─── beattube.genres ─────────────────────────────────────────────────────────
class Genre(db.Model):
    __tablename__  = "genres"
    __table_args__ = {"schema": "beattube"}

    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)


# ─── beattube.albums ─────────────────────────────────────────────────────────
class Album(db.Model):
    __tablename__  = "albums"
    __table_args__ = {"schema": "beattube"}

    id           = db.Column(db.Integer, primary_key=True)
    title        = db.Column(db.String(255), nullable=False)
    cover_url    = db.Column(db.String(500), nullable=True)
    release_date = db.Column(db.Date, nullable=True)
    artist_id    = db.Column(db.Integer, db.ForeignKey("beattube.artists.id", ondelete="CASCADE"), nullable=False)

    artist = db.relationship("Artist", back_populates="albums")
    songs  = db.relationship("Song", secondary="beattube.album_songs", lazy="dynamic")


# ─── beattube.songs ──────────────────────────────────────────────────────────
class Song(db.Model):
    __tablename__  = "songs"
    __table_args__ = {"schema": "beattube"}

    id           = db.Column(db.Integer, primary_key=True)
    title        = db.Column(db.String(255), nullable=False)
    duration_sec = db.Column(db.Integer, nullable=False)
    file_url     = db.Column(db.String(500), nullable=False)
    cover_url    = db.Column(db.String(500), nullable=True)
    play_count   = db.Column(db.BigInteger, default=0)
    release_date = db.Column(db.Date, nullable=True)
    is_explicit  = db.Column(db.Boolean, default=False)

    artists      = db.relationship("Artist", secondary="beattube.song_artists", lazy="subquery")
    genres       = db.relationship("Genre",  secondary="beattube.song_genres",  lazy="subquery")

    @property
    def duration_str(self) -> str:
        """Converte segundos em MM:SS."""
        m, s = divmod(self.duration_sec, 60)
        return f"{m}:{s:02d}"

    @property
    def main_artist(self):
        return self.artists[0] if self.artists else None


# ─── Tabelas de junção (N:N) ─────────────────────────────────────────────────
song_artists_table = db.Table(
    "song_artists",
    db.metadata,
    db.Column("song_id",   db.Integer, db.ForeignKey("beattube.songs.id",   ondelete="CASCADE"), primary_key=True),
    db.Column("artist_id", db.Integer, db.ForeignKey("beattube.artists.id", ondelete="CASCADE"), primary_key=True),
    db.Column("is_main",   db.Boolean, default=True),
    schema="beattube",
)

album_songs_table = db.Table(
    "album_songs",
    db.metadata,
    db.Column("album_id",  db.Integer, db.ForeignKey("beattube.albums.id", ondelete="CASCADE"), primary_key=True),
    db.Column("song_id",   db.Integer, db.ForeignKey("beattube.songs.id",  ondelete="CASCADE"), primary_key=True),
    db.Column("track_num", db.Integer, nullable=True),
    schema="beattube",
)

song_genres_table = db.Table(
    "song_genres",
    db.metadata,
    db.Column("song_id",  db.Integer, db.ForeignKey("beattube.songs.id",  ondelete="CASCADE"), primary_key=True),
    db.Column("genre_id", db.Integer, db.ForeignKey("beattube.genres.id", ondelete="CASCADE"), primary_key=True),
    schema="beattube",
)


# ─── beattube.playlists ──────────────────────────────────────────────────────
class Playlist(db.Model):
    __tablename__  = "playlists"
    __table_args__ = {"schema": "beattube"}

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    cover_url   = db.Column(db.String(500), nullable=True)
    is_public   = db.Column(db.Boolean, default=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("shared.users.id", ondelete="CASCADE"), nullable=False)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user  = db.relationship("User", back_populates="playlists")
    songs = db.relationship("Song", secondary="beattube.playlist_songs", lazy="dynamic")


playlist_songs_table = db.Table(
    "playlist_songs",
    db.metadata,
    db.Column("playlist_id", db.Integer, db.ForeignKey("beattube.playlists.id", ondelete="CASCADE"), primary_key=True),
    db.Column("song_id",     db.Integer, db.ForeignKey("beattube.songs.id",     ondelete="CASCADE"), primary_key=True),
    db.Column("position",    db.Integer, default=0),
    db.Column("added_at",    db.DateTime, default=lambda: datetime.now(timezone.utc)),
    schema="beattube",
)


# ─── beattube.liked_songs ────────────────────────────────────────────────────
class LikedSong(db.Model):
    __tablename__  = "liked_songs"
    __table_args__ = {"schema": "beattube"}

    user_id  = db.Column(db.Integer, db.ForeignKey("shared.users.id",   ondelete="CASCADE"), primary_key=True)
    song_id  = db.Column(db.Integer, db.ForeignKey("beattube.songs.id", ondelete="CASCADE"), primary_key=True)
    liked_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="liked_songs")
    song = db.relationship("Song")


# ─── beattube.play_history ───────────────────────────────────────────────────
class PlayHistory(db.Model):
    __tablename__  = "play_history"
    __table_args__ = {"schema": "beattube"}

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey("shared.users.id",   ondelete="CASCADE"), nullable=False)
    song_id       = db.Column(db.Integer, db.ForeignKey("beattube.songs.id", ondelete="CASCADE"), nullable=False)
    played_at     = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    percent_heard = db.Column(db.SmallInteger, nullable=True)
    device        = db.Column(db.String(50), nullable=True)

    user = db.relationship("User", back_populates="play_history")
    song = db.relationship("Song")


# ─── beattube.user_follows_artist ────────────────────────────────────────────
class UserFollowsArtist(db.Model):
    __tablename__  = "user_follows_artist"
    __table_args__ = {"schema": "beattube"}

    user_id     = db.Column(db.Integer, db.ForeignKey("shared.users.id",       ondelete="CASCADE"), primary_key=True)
    artist_id   = db.Column(db.Integer, db.ForeignKey("beattube.artists.id",   ondelete="CASCADE"), primary_key=True)
    followed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
