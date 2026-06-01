from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from azure.storage.blob import BlobServiceClient
from PIL import Image
import os, uuid, io

upload_bp = Blueprint('upload', __name__)

AZURE_CONN       = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")
CONTAINER_MP3    = "musicas"
CONTAINER_COVERS = "imagens"


def blob_upload(container, file, filename):
    client = BlobServiceClient.from_connection_string(AZURE_CONN)
    blob   = client.get_blob_client(container=container, blob=filename)
    blob.upload_blob(file, overwrite=True)
    return blob.url


def processar_capa(file):
    """Valida tamanho mínimo, recorta no centro e redimensiona pra 1000x1000."""
    img  = Image.open(file).convert("RGB")
    w, h = img.size

    # Rejeita imagens menores que 1280x720
    if w < 1280 or h < 720:
        return None, f"A imagem deve ter pelo menos 1280x720 pixels. A sua tem {w}x{h}."

    lado = min(w, h)
    left = (w - lado) // 2
    top  = (h - lado) // 2
    img  = img.crop((left, top, left + lado, top + lado))
    img  = img.resize((1000, 1000), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    buf.seek(0)
    return buf, None


@upload_bp.route("/api/upload/postar", methods=["POST"])
@login_required
def postar():

    # if not current_user.is_premium:
    #     return jsonify({"ok": False, "error": "Somente usuários premium podem postar."}), 403

    from ..models import db, Song, Album, Artist

    musicas    = request.files.getlist("musicas")
    nomes      = request.form.getlist("nomes")
    capa       = request.files.get("capa")
    album_nome = request.form.get("album_nome", "").strip()

    # Validações
    if not musicas:
        return jsonify({"ok": False, "error": "Envie ao menos um MP3."}), 400
    if len(musicas) > 30:
        return jsonify({"ok": False, "error": "Máximo de 30 músicas."}), 400
    if len(musicas) != len(nomes):
        return jsonify({"ok": False, "error": "Número de nomes diferente do de arquivos."}), 400
    if len(musicas) > 1 and not album_nome:
        return jsonify({"ok": False, "error": "Informe o nome do álbum."}), 400

    # Busca ou cria Artist vinculado ao usuário
    artist = Artist.query.filter_by(name=current_user.username).first()
    if not artist:
        artist = Artist(name=current_user.username)
        db.session.add(artist)
        db.session.flush()

    # Upload da capa — valida qualidade mínima e salva 1000x1000
    cover_url = None
    if capa and capa.filename:
        capa_processada, erro_capa = processar_capa(capa)
        if erro_capa:
            return jsonify({"ok": False, "error": erro_capa}), 400
        cover_url = blob_upload(CONTAINER_COVERS, capa_processada, f"{uuid.uuid4()}.jpg")

    # Cria álbum se tiver mais de 1 música
    album = None
    if len(musicas) > 1:
        album = Album(
            title     = album_nome,
            cover_url = cover_url,
            artist_id = artist.id
        )
        db.session.add(album)
        db.session.flush()

    # Upload de cada MP3
    for i, (mp3, nome) in enumerate(zip(musicas, nomes)):
        file_url = blob_upload(CONTAINER_MP3, mp3, f"{uuid.uuid4()}.mp3")

        song = Song(
            title        = nome,
            file_url     = file_url,
            cover_url    = cover_url,
            duration_sec = 0
        )
        db.session.add(song)
        db.session.flush()

        # Liga artista à música
        db.session.execute(
            db.text("INSERT INTO beattube.song_artists (song_id, artist_id, is_main) VALUES (:s, :a, 1)"),
            {"s": song.id, "a": artist.id}
        )

        # Liga música ao álbum
        if album:
            db.session.execute(
                db.text("INSERT INTO beattube.album_songs (album_id, song_id, track_num) VALUES (:al, :s, :t)"),
                {"al": album.id, "s": song.id, "t": i + 1}
            )

    db.session.commit()
    return jsonify({"ok": True})


@upload_bp.route("/api/song/<int:song_id>/play", methods=["POST"])
@login_required
def registrar_play(song_id):
    from ..models import db, Song, PlayHistory

    song = Song.query.get_or_404(song_id)
    song.play_count += 1

    db.session.add(PlayHistory(
        user_id = current_user.id,
        song_id = song_id
    ))
    db.session.commit()

    return jsonify({"ok": True, "play_count": song.play_count})