from flask import Blueprint, render_template, request, jsonify
from flask_login import current_user, login_required
from ..models import db, PlayHistory
from sqlalchemy import func, cast, Date

history_bp = Blueprint("history", __name__)


@history_bp.route("/historico")
@login_required
def historico():
    # Agrupa por data (dia)
    entries = (
        PlayHistory.query
        .filter_by(user_id=current_user.id)
        .order_by(PlayHistory.played_at.desc())
        .limit(200)
        .all()
    )

    # Agrupa por data para exibir "Hoje", "Ontem", datas anteriores
    from collections import OrderedDict
    from datetime import date, timedelta

    today     = date.today()
    yesterday = today - timedelta(days=1)

    grouped = OrderedDict()
    for entry in entries:
        d = entry.played_at.date()
        if d == today:
            label = "Hoje"
        elif d == yesterday:
            label = "Ontem"
        else:
            meses = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                     "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
            label = f"{d.day} de {meses[d.month - 1]} de {d.year}"

        grouped.setdefault(label, []).append(entry)

    return render_template("historico.html", grouped=grouped)


@history_bp.route("/api/historico/apagar", methods=["POST"])
@login_required
def apagar_historico():
    PlayHistory.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"ok": True})
