from flask import Blueprint, render_template, jsonify
from flask_login import current_user, login_required
from ..models import db, Artist, UserFollowsArtist, Song, song_artists_table

seguindo_bp = Blueprint("seguindo", __name__)


@seguindo_bp.route("/seguindo")
@login_required
def seguindo():
    follows = (
        UserFollowsArtist.query
        .filter_by(user_id=current_user.id)
        .order_by(UserFollowsArtist.followed_at.desc())
        .all()
    )

    artists = []
    for f in follows:
        artist = Artist.query.get(f.artist_id)
        if not artist:
            continue

        # Busca as 3 músicas mais recentes do artista via tabela de junção
        recent = (
            Song.query
            .join(song_artists_table, song_artists_table.c.song_id == Song.id)
            .filter(song_artists_table.c.artist_id == artist.id)
            .order_by(Song.id.desc())
            .limit(3)
            .all()
        )
        artist.recent_songs = recent
        artists.append(artist)

    return render_template("seguindo.html", artists=artists)


@seguindo_bp.route("/api/seguir/<int:artist_id>", methods=["POST"])
@login_required
def toggle_seguir(artist_id):
    Artist.query.get_or_404(artist_id)
    follow = UserFollowsArtist.query.filter_by(
        user_id=current_user.id, artist_id=artist_id
    ).first()
    if follow:
        db.session.delete(follow)
        db.session.commit()
        return jsonify({"seguindo": False})
    db.session.add(UserFollowsArtist(user_id=current_user.id, artist_id=artist_id))
    db.session.commit()
    return jsonify({"seguindo": True})


@seguindo_bp.route("/api/seguindo/<int:artist_id>")
@login_required
def check_seguindo(artist_id):
    follow = UserFollowsArtist.query.filter_by(
        user_id=current_user.id, artist_id=artist_id
    ).first()
    return jsonify({"seguindo": follow is not None})
