from flask import Blueprint, render_template, jsonify, abort
from flask_login import current_user, login_required
from ..models import db, Artist, UserFollowsArtist

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
    artists = [f.artist for f in follows]
    return render_template("seguindo.html", artists=artists)


# ─── API: seguir / deixar de seguir ──────────────────────────────────────────
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


# ─── API: checa se está seguindo ─────────────────────────────────────────────
@seguindo_bp.route("/api/seguindo/<int:artist_id>")
@login_required
def check_seguindo(artist_id):
    follow = UserFollowsArtist.query.filter_by(
        user_id=current_user.id, artist_id=artist_id
    ).first()
    return jsonify({"seguindo": follow is not None})
