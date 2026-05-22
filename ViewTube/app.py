from flask import Flask, render_template, jsonify, request, session
import mysql.connector
import os
import hashlib
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
app.secret_key = "viewtube_secret_key_change_in_production"

# ─── DB CONFIG ────────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "viewtube"),
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def db_query(sql, params=None, fetch=True):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        if fetch:
            rows = cursor.fetchall()
            conn.close()
            return rows
        else:
            conn.commit()
            last_id = cursor.lastrowid
            conn.close()
            return last_id
    except Exception as e:
        conn.close()
        raise e

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def format_duration(seconds):
    if not seconds:
        return "0:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

def format_views(n):
    if n is None:
        return "0"
    n = int(n)
    if n >= 1_000_000_000:
        return f"{n/1e9:.1f}B"
    if n >= 1_000_000:
        return f"{n/1e6:.1f}M"
    if n >= 1_000:
        return f"{n/1e3:.1f}K"
    return str(n)

CURRENT_USER_ID = 1  # usuário logado fixo para demo

# ─── PAGES ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

# ─── API: VIDEOS ──────────────────────────────────────────────────────────────
@app.route("/api/videos")
def api_videos():
    tag = request.args.get("tag", "all")
    if tag == "all":
        rows = db_query("""
            SELECT v.id, v.title, v.video_url, v.thumbnail_url,
                   v.views, v.duration, v.likes_count, v.created_at,
                   c.name AS channel, c.id AS channel_id
            FROM videos v
            JOIN channels c ON c.id = v.channel_id
            ORDER BY v.created_at DESC
        """)
    else:
        rows = db_query("""
            SELECT v.id, v.title, v.video_url, v.thumbnail_url,
                   v.views, v.duration, v.likes_count, v.created_at,
                   c.name AS channel, c.id AS channel_id
            FROM videos v
            JOIN channels c ON c.id = v.channel_id
            JOIN video_tags vt ON vt.video_id = v.id
            JOIN tags t ON t.id = vt.tag_id
            WHERE t.name = %s
            ORDER BY v.created_at DESC
        """, (tag,))

    for r in rows:
        r["duration_fmt"] = format_duration(r["duration"])
        r["views_fmt"] = format_views(r["views"])
        r["created_at"] = str(r["created_at"])
    return jsonify(rows)

@app.route("/api/videos/trending")
def api_trending():
    rows = db_query("""
        SELECT v.id, v.title, v.video_url, v.thumbnail_url,
               v.views, v.duration, v.likes_count, v.created_at,
               c.name AS channel, c.id AS channel_id
        FROM videos v
        JOIN channels c ON c.id = v.channel_id
        ORDER BY v.views DESC
        LIMIT 8
    """)
    for r in rows:
        r["duration_fmt"] = format_duration(r["duration"])
        r["views_fmt"] = format_views(r["views"])
        r["created_at"] = str(r["created_at"])
    return jsonify(rows)

@app.route("/api/videos/search")
def api_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    rows = db_query("""
        SELECT v.id, v.title, v.video_url, v.thumbnail_url,
               v.views, v.duration, v.likes_count, v.created_at,
               c.name AS channel, c.id AS channel_id
        FROM videos v
        JOIN channels c ON c.id = v.channel_id
        WHERE v.title LIKE %s OR c.name LIKE %s
        ORDER BY v.views DESC
        LIMIT 20
    """, (f"%{q}%", f"%{q}%"))
    for r in rows:
        r["duration_fmt"] = format_duration(r["duration"])
        r["views_fmt"] = format_views(r["views"])
        r["created_at"] = str(r["created_at"])
    return jsonify(rows)

@app.route("/api/videos/<int:vid>/like", methods=["POST"])
def api_like(vid):
    user_id = CURRENT_USER_ID
    # toggle like
    existing = db_query(
        "SELECT id FROM video_likes WHERE user_id=%s AND video_id=%s",
        (user_id, vid)
    )
    if existing:
        db_query("DELETE FROM video_likes WHERE user_id=%s AND video_id=%s",
                 (user_id, vid), fetch=False)
        db_query("UPDATE videos SET likes_count = GREATEST(0, likes_count-1) WHERE id=%s",
                 (vid,), fetch=False)
        liked = False
    else:
        db_query("INSERT INTO video_likes (user_id, video_id) VALUES (%s, %s)",
                 (user_id, vid), fetch=False)
        db_query("UPDATE videos SET likes_count = likes_count+1 WHERE id=%s",
                 (vid,), fetch=False)
        liked = True

    row = db_query("SELECT likes_count FROM videos WHERE id=%s", (vid,))
    return jsonify({"liked": liked, "likes": row[0]["likes_count"] if row else 0})

@app.route("/api/videos/<int:vid>/watch", methods=["POST"])
def api_watch(vid):
    user_id = CURRENT_USER_ID
    db_query("""
        INSERT INTO watch_history (user_id, video_id, watched_seconds)
        VALUES (%s, %s, 0)
        ON DUPLICATE KEY UPDATE watched_at = CURRENT_TIMESTAMP
    """, (user_id, vid), fetch=False)
    db_query("UPDATE videos SET views = views+1 WHERE id=%s", (vid,), fetch=False)
    return jsonify({"ok": True})

@app.route("/api/videos/upload", methods=["POST"])
def api_upload():
    data = request.json
    title = data.get("title", "").strip()
    url = data.get("url", "").strip()
    thumb = data.get("thumbnail", "").strip()
    channel_name = data.get("channel", "").strip()
    category = data.get("category", "music").strip()

    if not title or not url or not channel_name:
        return jsonify({"error": "Campos obrigatórios faltando"}), 400

    # find or create channel
    ch = db_query("SELECT id FROM channels WHERE name=%s", (channel_name,))
    if ch:
        channel_id = ch[0]["id"]
    else:
        channel_id = db_query(
            "INSERT INTO channels (user_id, name) VALUES (%s, %s)",
            (CURRENT_USER_ID, channel_name), fetch=False
        )

    vid_id = db_query("""
        INSERT INTO videos (channel_id, title, video_url, thumbnail_url)
        VALUES (%s, %s, %s, %s)
    """, (channel_id, title, url, thumb or None), fetch=False)

    # tag
    tag_rows = db_query("SELECT id FROM tags WHERE name=%s", (category,))
    if tag_rows:
        tag_id = tag_rows[0]["id"]
    else:
        tag_id = db_query("INSERT INTO tags (name) VALUES (%s)", (category,), fetch=False)
    db_query("INSERT IGNORE INTO video_tags (video_id, tag_id) VALUES (%s,%s)",
             (vid_id, tag_id), fetch=False)

    return jsonify({"id": vid_id, "title": title})

# ─── API: CHANNELS ────────────────────────────────────────────────────────────
@app.route("/api/channels")
def api_channels():
    rows = db_query("""
        SELECT c.id, c.name, c.description, c.profile_image_url, c.banner_url,
               COUNT(DISTINCT s.id) AS subscribers,
               COUNT(DISTINCT v.id) AS video_count
        FROM channels c
        LEFT JOIN subscriptions s ON s.channel_id = c.id
        LEFT JOIN videos v ON v.channel_id = c.id
        GROUP BY c.id
    """)
    for r in rows:
        r["subscribers_fmt"] = format_views(r["subscribers"])
    return jsonify(rows)

@app.route("/api/channels/<int:cid>/videos")
def api_channel_videos(cid):
    rows = db_query("""
        SELECT v.id, v.title, v.video_url, v.thumbnail_url,
               v.views, v.duration, v.likes_count, v.created_at,
               c.name AS channel, c.id AS channel_id
        FROM videos v
        JOIN channels c ON c.id = v.channel_id
        WHERE v.channel_id = %s
        ORDER BY v.created_at DESC
    """, (cid,))
    for r in rows:
        r["duration_fmt"] = format_duration(r["duration"])
        r["views_fmt"] = format_views(r["views"])
        r["created_at"] = str(r["created_at"])
    return jsonify(rows)

@app.route("/api/channels/<int:cid>/subscribe", methods=["POST"])
def api_subscribe(cid):
    user_id = CURRENT_USER_ID
    existing = db_query(
        "SELECT id FROM subscriptions WHERE subscriber_id=%s AND channel_id=%s",
        (user_id, cid)
    )
    if existing:
        db_query("DELETE FROM subscriptions WHERE subscriber_id=%s AND channel_id=%s",
                 (user_id, cid), fetch=False)
        subscribed = False
    else:
        db_query("INSERT INTO subscriptions (subscriber_id, channel_id) VALUES (%s,%s)",
                 (user_id, cid), fetch=False)
        subscribed = True
    count = db_query(
        "SELECT COUNT(*) AS n FROM subscriptions WHERE channel_id=%s", (cid,)
    )
    return jsonify({"subscribed": subscribed, "subscribers": count[0]["n"]})

# ─── API: PLAYLISTS ───────────────────────────────────────────────────────────
@app.route("/api/playlists")
def api_playlists():
    rows = db_query("""
        SELECT p.id, p.name, p.description, p.thumbnail_url, p.is_public, p.created_at,
               COUNT(pv.video_id) AS video_count
        FROM playlists p
        LEFT JOIN playlist_videos pv ON pv.playlist_id = p.id
        WHERE p.user_id = %s
        GROUP BY p.id
        ORDER BY p.created_at DESC
    """, (CURRENT_USER_ID,))
    for r in rows:
        r["created_at"] = str(r["created_at"])
        r["is_public"] = bool(r["is_public"])
    return jsonify(rows)

@app.route("/api/playlists", methods=["POST"])
def api_create_playlist():
    data = request.json
    name = data.get("name", "").strip()
    desc = data.get("description", "").strip()
    is_public = data.get("isPublic", False)
    if not name:
        return jsonify({"error": "Nome obrigatório"}), 400
    pid = db_query("""
        INSERT INTO playlists (user_id, name, description, is_public)
        VALUES (%s, %s, %s, %s)
    """, (CURRENT_USER_ID, name, desc, int(is_public)), fetch=False)
    return jsonify({"id": pid, "name": name})

# ─── API: HISTORY ─────────────────────────────────────────────────────────────
@app.route("/api/history")
def api_history():
    rows = db_query("""
        SELECT v.id, v.title, v.video_url, v.thumbnail_url,
               v.views, v.duration, v.likes_count, wh.watched_at,
               c.name AS channel, c.id AS channel_id
        FROM watch_history wh
        JOIN videos v ON v.id = wh.video_id
        JOIN channels c ON c.id = v.channel_id
        WHERE wh.user_id = %s
        ORDER BY wh.watched_at DESC
        LIMIT 50
    """, (CURRENT_USER_ID,))
    for r in rows:
        r["duration_fmt"] = format_duration(r["duration"])
        r["views_fmt"] = format_views(r["views"])
        r["watched_at"] = str(r["watched_at"])
        r["created_at"] = r["watched_at"]
    return jsonify(rows)

# ─── API: LIKED VIDEOS ────────────────────────────────────────────────────────
@app.route("/api/liked")
def api_liked():
    rows = db_query("""
        SELECT v.id, v.title, v.video_url, v.thumbnail_url,
               v.views, v.duration, v.likes_count, v.created_at,
               c.name AS channel, c.id AS channel_id
        FROM video_likes vl
        JOIN videos v ON v.id = vl.video_id
        JOIN channels c ON c.id = v.channel_id
        WHERE vl.user_id = %s
        ORDER BY vl.created_at DESC
    """, (CURRENT_USER_ID,))
    for r in rows:
        r["duration_fmt"] = format_duration(r["duration"])
        r["views_fmt"] = format_views(r["views"])
        r["created_at"] = str(r["created_at"])
    return jsonify(rows)

# ─── API: TAGS ────────────────────────────────────────────────────────────────
@app.route("/api/tags")
def api_tags():
    rows = db_query("SELECT name FROM tags ORDER BY name")
    return jsonify([r["name"] for r in rows])

# ─── API: DATABASE EXPLORER ───────────────────────────────────────────────────
ALLOWED_TABLES = {
    "videos", "channels", "users", "playlists", "playlist_videos",
    "subscriptions", "tags", "video_tags", "video_likes",
    "comments", "watch_history"
}

@app.route("/api/db/tables")
def api_db_tables():
    rows = db_query("SHOW TABLES")
    tables = []
    for r in rows:
        tname = list(r.values())[0]
        count = db_query(f"SELECT COUNT(*) AS n FROM `{tname}`")
        tables.append({"name": tname, "count": count[0]["n"]})
    return jsonify(tables)

@app.route("/api/db/query", methods=["POST"])
def api_db_query():
    sql = (request.json or {}).get("sql", "").strip()
    if not sql:
        return jsonify({"error": "Query vazia"}), 400

    sql_upper = sql.upper().lstrip()
    if not sql_upper.startswith("SELECT") and not sql_upper.startswith("SHOW") and not sql_upper.startswith("DESCRIBE"):
        return jsonify({"error": "Apenas queries SELECT, SHOW e DESCRIBE são permitidas."}), 403

    try:
        rows = db_query(sql)
        # convert non-serializable types
        safe = []
        for r in rows:
            safe.append({k: str(v) if not isinstance(v, (int, float, bool, type(None), str)) else v
                         for k, v in r.items()})
        return jsonify({"rows": safe, "count": len(safe)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/db/schema/<table>")
def api_db_schema(table):
    if table not in ALLOWED_TABLES:
        return jsonify({"error": "Tabela não permitida"}), 403
    rows = db_query(f"DESCRIBE `{table}`")
    return jsonify(rows)

# ─── STATS ────────────────────────────────────────────────────────────────────
@app.route("/api/stats")
def api_stats():
    videos = db_query("SELECT COUNT(*) AS n FROM videos")[0]["n"]
    channels = db_query("SELECT COUNT(*) AS n FROM channels")[0]["n"]
    playlists = db_query("SELECT COUNT(*) AS n FROM playlists WHERE user_id=%s",
                         (CURRENT_USER_ID,))[0]["n"]
    return jsonify({"totalVideos": videos, "totalChannels": channels,
                    "totalPlaylists": playlists})

if __name__ == "__main__":
    app.run(debug=True, port=5000, use_reloader=False)
