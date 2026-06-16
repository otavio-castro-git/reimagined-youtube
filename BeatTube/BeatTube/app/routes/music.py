from flask import Blueprint, render_template, abort, jsonify, request, redirect, url_for, Response
from flask_login import current_user, login_required
from ..models import db, Song, Album, Artist, PlayHistory, LikedSong
import requests as req_lib

music_bp = Blueprint("music", __name__)


@music_bp.route("/musica/<int:song_id>")
def song_detail(song_id):
    song = Song.query.get_or_404(song_id)

    if current_user.is_authenticated:
        entry = PlayHistory(
            user_id=current_user.id,
            song_id=song.id,
            device=request.user_agent.platform,
        )
        db.session.add(entry)
        song.play_count = (song.play_count or 0) + 1
        db.session.commit()

    is_liked = False
    if current_user.is_authenticated:
        is_liked = LikedSong.query.filter_by(
            user_id=current_user.id, song_id=song.id
        ).first() is not None

    related_songs = []
    if song.artists:
        artist = song.artists[0]
        for album in artist.albums:
            for s in album.songs:
                if s.id != song.id and s not in related_songs:
                    related_songs.append(s)
            if len(related_songs) >= 6:
                break

    return render_template("music.html", song=song, related_songs=related_songs, is_liked=is_liked)


@music_bp.route("/album/<int:album_id>")
def album_detail(album_id):
    album = Album.query.get_or_404(album_id)
    songs = list(album.songs)
    return render_template("album.html", album=album, songs=songs)


@music_bp.route("/artista/<int:artist_id>")
def artist_detail(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    albums = list(artist.albums)

    all_songs = []
    for album in albums:
        for s in album.songs:
            if s not in all_songs:
                all_songs.append(s)
    all_songs.sort(key=lambda s: s.play_count or 0, reverse=True)
    popular_songs = list(enumerate(all_songs[:5], start=1))
    singles = all_songs[5:11]

    is_following = False
    if current_user.is_authenticated:
        from ..models import UserFollowsArtist
        is_following = UserFollowsArtist.query.filter_by(
            user_id=current_user.id, artist_id=artist_id
        ).first() is not None

    return render_template(
        "artist.html",
        artist=artist,
        albums=albums,
        popular_songs=popular_songs,
        singles=singles,
        is_following=is_following,
    )


# ─── Tendências ───────────────────────────────────────────────────────────────
@music_bp.route("/tendencias")
def tendencias():
    query = request.args.get("q", "").strip()
    if query:
        songs   = Song.query.filter(Song.title.ilike(f"%{query}%")).limit(20).all()
        artists = Artist.query.filter(Artist.name.ilike(f"%{query}%")).limit(10).all()
        albums  = Album.query.filter(Album.title.ilike(f"%{query}%")).limit(10).all()
    else:
        songs   = Song.query.order_by(Song.play_count.desc()).limit(10).all()
        artists = Artist.query.limit(6).all()
        albums  = Album.query.limit(6).all()

    return render_template(
        "tendencias.html",
        songs=songs,
        artists=artists,
        albums=albums,
        query=query,
    )


# ─── API: curtir / descurtir ──────────────────────────────────────────────────
@music_bp.route("/api/like/<int:song_id>", methods=["POST"])
@login_required
def toggle_like(song_id):
    Song.query.get_or_404(song_id)
    liked = LikedSong.query.filter_by(user_id=current_user.id, song_id=song_id).first()
    if liked:
        db.session.delete(liked)
        db.session.commit()
        return jsonify({"liked": False})
    db.session.add(LikedSong(user_id=current_user.id, song_id=song_id))
    db.session.commit()
    return jsonify({"liked": True})


# ─── API: dados da música (para o player) ────────────────────────────────────
@music_bp.route("/api/song/<int:song_id>")
def song_data(song_id):
    song = Song.query.get_or_404(song_id)
    return jsonify({
        "id":           song.id,
        "title":        song.title,
        "artist":       song.main_artist.name if song.main_artist else "Artista",
        "artist_id":    song.main_artist.id   if song.main_artist else None,
        "file_url":     f"/api/song/{song.id}/stream",  # proxy para suportar seek
        "cover_url":    song.cover_url,
        "duration":     song.duration_str,
        "duration_sec": song.duration_sec,
    })


# ─── Proxy de áudio — repassa Range headers pro Azure (necessário para seek) ──
@music_bp.route("/api/song/<int:song_id>/stream")
def song_stream(song_id):
    song = Song.query.get_or_404(song_id)

    range_header = request.headers.get("Range")
    headers = {}
    if range_header:
        headers["Range"] = range_header

    try:
        r = req_lib.get(song.file_url, headers=headers, stream=True, timeout=15)
    except Exception:
        abort(502)

    resp_headers = {
        "Content-Type":  r.headers.get("Content-Type", "audio/mpeg"),
        "Accept-Ranges": "bytes",
    }
    for h in ("Content-Length", "Content-Range"):
        if h in r.headers:
            resp_headers[h] = r.headers[h]

    return Response(
        r.iter_content(chunk_size=65536),
        status=r.status_code,
        headers=resp_headers,
        direct_passthrough=True,
    )


# ─── API: adicionar ao histórico ──────────────────────────────────────────────
@music_bp.route("/api/historico/add/<int:song_id>", methods=["POST"])
@login_required
def add_historico(song_id):
    song = Song.query.get_or_404(song_id)
    db.session.add(PlayHistory(user_id=current_user.id, song_id=song_id))
    song.play_count = (song.play_count or 0) + 1
    db.session.commit()
    return jsonify({"ok": True})


# ─── Rota: clicou numa música → vai pro álbum dela ────────────────────────────
@music_bp.route("/musica/<int:song_id>/album")
def song_album(song_id):
    song = Song.query.get_or_404(song_id)
    album = Album.query.join(Album.songs).filter(Song.id == song_id).first()
    if album:
        return redirect(url_for("music.album_detail", album_id=album.id))

    class FakeAlbum:
        def __init__(self, song):
            self.id        = None
            self.title     = song.title
            self.cover_url = song.cover_url
            self.artist    = song.artists[0] if song.artists else None
    return render_template("album.html", album=FakeAlbum(song), songs=[song])
