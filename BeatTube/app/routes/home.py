from flask import Blueprint, render_template
from flask_login import current_user
from ..models import Song, Artist, PlayHistory

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    # Top músicas (mais ouvidas)
    top_songs = (
        Song.query
        .order_by(Song.play_count.desc())
        .limit(6)
        .all()
    )

    # "Ouvir novamente" — histórico do usuário logado
    ouvir_novamente = []
    if current_user.is_authenticated:
        historico = (
            PlayHistory.query
            .filter_by(user_id=current_user.id)
            .order_by(PlayHistory.played_at.desc())
            .limit(6)
            .all()
        )
        seen = set()
        for h in historico:
            if h.song_id not in seen:
                ouvir_novamente.append(h.song)
                seen.add(h.song_id)

    return render_template(
        "index.html",
        banner_song=top_songs[0] if top_songs else None,
        ouvir_novamente=ouvir_novamente,
        recomendacoes=top_songs,
    )
