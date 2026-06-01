from flask import Blueprint, render_template, abort, jsonify, request, redirect, url_for
from flask_login import current_user, login_required
from ..models import db, Song, Album, Artist, PlayHistory, LikedSong

music_bp = Blueprint("music", __name__)


@music_bp.route("/musica/<int:song_id>")
def song_detail(song_id):
    song = Song.query.get_or_404(song_id)

    # Registra no histórico >>>se logado
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

    # Músicas relacionadas (mesmo artista, exclui a atual)
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
    album  = Album.query.get_or_404(album_id)
    songs  = list(album.songs)
    # Usa music.html com a primeira música como âncora, ou renderiza sem song
    return render_template("album.html", album=album, songs=songs)


@music_bp.route("/artista/<int:artist_id>")
def artist_detail(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    albums = list(artist.albums)

    # Top 5 músicas do artista por play_count
    all_songs = []
    for album in albums:
        for s in album.songs:
            if s not in all_songs:
                all_songs.append(s)
    all_songs.sort(key=lambda s: s.play_count or 0, reverse=True)
    popular_songs = list(enumerate(all_songs[:5], start=1))
    singles = all_songs[5:11]  # próximas como singles

    return render_template(
        "artist.html",
        artist=artist,
        albums=albums,
        popular_songs=popular_songs,
        singles=singles,
    )


# ─── Tendências ───────────────────────────────────────────────────────────────
@music_bp.route("/tendencias")
def tendencias():
    query   = request.args.get("q", "").strip()
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


# ─── API: dados da música (para o player popup) ───────────────────────────────
@music_bp.route("/api/song/<int:song_id>")
def song_data(song_id):
    song = Song.query.get_or_404(song_id)
    return jsonify({
        "id":         song.id,
        "title":      song.title,
        "artist":     song.main_artist.name if song.main_artist else "Artista",
        "artist_id":  song.main_artist.id   if song.main_artist else None,
        "file_url":   song.file_url,
        "cover_url":  song.cover_url,
        "duration":   song.duration_str,
        "duration_sec": song.duration_sec,
    })


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
    # Descobre o álbum da música
    album = Album.query.join(Album.songs).filter(Song.id == song_id).first()
    if album:
        return redirect(url_for("music.album_detail", album_id=album.id))
    # Single: sem álbum → cria um "álbum virtual" de 1 faixa
    class FakeAlbum:
        def __init__(self, song):
            self.id       = None
            self.title    = song.title
            self.cover_url = song.cover_url
            self.artist   = song.artists[0] if song.artists else None
    return render_template("album.html", album=FakeAlbum(song), songs=[song])
