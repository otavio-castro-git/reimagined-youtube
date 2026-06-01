-- ============================================================
--  ViewTube — Patch SQL
--  Roda NO MESMO banco do BeatTube (Azure SQL / T-SQL)
--  O schema "shared" já existe — NÃO recrie.
--  Execute este arquivo no Query Editor do Azure SQL.
-- ============================================================

-- 1. Schema viewtube
CREATE SCHEMA viewtube;
GO

-- 2. Coluna google_id na shared.users (se ainda não existir)
IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('shared.users') AND name = 'google_id'
)
    ALTER TABLE shared.users ADD google_id NVARCHAR(255) NULL;
GO

-- ============================================================
-- viewtube.channels
-- ============================================================
CREATE TABLE viewtube.channels (
    id                INT IDENTITY(1,1) PRIMARY KEY,
    user_id           INT           NOT NULL,
    name              NVARCHAR(150) NOT NULL,
    description       NVARCHAR(MAX) NULL,
    profile_image_url NVARCHAR(500) NULL,
    banner_url        NVARCHAR(500) NULL,
    created_at        DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),

    CONSTRAINT fk_ch_user FOREIGN KEY (user_id) REFERENCES shared.users(id) ON DELETE CASCADE
);

-- ============================================================
-- viewtube.videos
-- ============================================================
CREATE TABLE viewtube.videos (
    id            INT IDENTITY(1,1) PRIMARY KEY,
    channel_id    INT           NOT NULL,
    title         NVARCHAR(255) NOT NULL,
    description   NVARCHAR(MAX) NULL,
    video_url     NVARCHAR(500) NOT NULL,
    thumbnail_url NVARCHAR(500) NULL,
    duration_sec  INT           NULL,
    views         BIGINT        NOT NULL DEFAULT 0,
    likes_count   INT           NOT NULL DEFAULT 0,
    is_published  BIT           NOT NULL DEFAULT 1,
    created_at    DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),

    CONSTRAINT fk_vid_channel FOREIGN KEY (channel_id) REFERENCES viewtube.channels(id) ON DELETE CASCADE
);

-- ============================================================
-- viewtube.tags
-- ============================================================
CREATE TABLE viewtube.tags (
    id   INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL UNIQUE
);

-- ============================================================
-- viewtube.video_tags
-- ============================================================
CREATE TABLE viewtube.video_tags (
    video_id INT NOT NULL,
    tag_id   INT NOT NULL,

    CONSTRAINT pk_vt PRIMARY KEY (video_id, tag_id),
    CONSTRAINT fk_vt_video FOREIGN KEY (video_id) REFERENCES viewtube.videos(id) ON DELETE CASCADE,
    CONSTRAINT fk_vt_tag   FOREIGN KEY (tag_id)   REFERENCES viewtube.tags(id)   ON DELETE CASCADE
);

-- ============================================================
-- viewtube.video_likes
-- ============================================================
CREATE TABLE viewtube.video_likes (
    user_id    INT       NOT NULL,
    video_id   INT       NOT NULL,
    liked_at   DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),

    CONSTRAINT pk_vl PRIMARY KEY (user_id, video_id),
    CONSTRAINT fk_vl_user  FOREIGN KEY (user_id)  REFERENCES shared.users(id)     ON DELETE CASCADE,
    CONSTRAINT fk_vl_video FOREIGN KEY (video_id) REFERENCES viewtube.videos(id)  ON DELETE CASCADE
);

-- ============================================================
-- viewtube.comments
-- ============================================================
CREATE TABLE viewtube.comments (
    id         INT IDENTITY(1,1) PRIMARY KEY,
    user_id    INT           NOT NULL,
    video_id   INT           NOT NULL,
    content    NVARCHAR(MAX) NOT NULL,
    is_deleted BIT           NOT NULL DEFAULT 0,
    created_at DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),

    CONSTRAINT fk_cm_user  FOREIGN KEY (user_id)  REFERENCES shared.users(id)    ON DELETE NO ACTION,
    CONSTRAINT fk_cm_video FOREIGN KEY (video_id) REFERENCES viewtube.videos(id) ON DELETE CASCADE
);

-- ============================================================
-- viewtube.subscriptions  (canal → subscriber)
-- ============================================================
CREATE TABLE viewtube.subscriptions (
    subscriber_id INT       NOT NULL,
    channel_id    INT       NOT NULL,
    subscribed_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),

    CONSTRAINT pk_sub PRIMARY KEY (subscriber_id, channel_id),
    CONSTRAINT fk_sub_user    FOREIGN KEY (subscriber_id) REFERENCES shared.users(id)      ON DELETE CASCADE,
    CONSTRAINT fk_sub_channel FOREIGN KEY (channel_id)    REFERENCES viewtube.channels(id) ON DELETE NO ACTION
);

-- ============================================================
-- viewtube.playlists
-- ============================================================
CREATE TABLE viewtube.playlists (
    id            INT IDENTITY(1,1) PRIMARY KEY,
    user_id       INT           NOT NULL,
    name          NVARCHAR(255) NOT NULL,
    description   NVARCHAR(500) NULL,
    thumbnail_url NVARCHAR(500) NULL,
    is_public     BIT           NOT NULL DEFAULT 1,
    created_at    DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),

    CONSTRAINT fk_pl_user FOREIGN KEY (user_id) REFERENCES shared.users(id) ON DELETE CASCADE
);

-- ============================================================
-- viewtube.playlist_videos
-- ============================================================
CREATE TABLE viewtube.playlist_videos (
    playlist_id INT       NOT NULL,
    video_id    INT       NOT NULL,
    position    INT       NOT NULL DEFAULT 0,
    added_at    DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),

    CONSTRAINT pk_pv PRIMARY KEY (playlist_id, video_id),
    CONSTRAINT fk_pv_playlist FOREIGN KEY (playlist_id) REFERENCES viewtube.playlists(id) ON DELETE CASCADE,
    CONSTRAINT fk_pv_video    FOREIGN KEY (video_id)    REFERENCES viewtube.videos(id)    ON DELETE CASCADE
);

-- ============================================================
-- viewtube.watch_history
-- ============================================================
CREATE TABLE viewtube.watch_history (
    id               INT IDENTITY(1,1) PRIMARY KEY,
    user_id          INT       NOT NULL,
    video_id         INT       NOT NULL,
    watched_seconds  INT       NOT NULL DEFAULT 0,
    watched_at       DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),

    CONSTRAINT fk_wh_user  FOREIGN KEY (user_id)  REFERENCES shared.users(id)    ON DELETE CASCADE,
    CONSTRAINT fk_wh_video FOREIGN KEY (video_id) REFERENCES viewtube.videos(id) ON DELETE CASCADE
);

-- ============================================================
-- viewtube.search_history
-- ============================================================
CREATE TABLE viewtube.search_history (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    user_id     INT           NOT NULL,
    query       NVARCHAR(255) NOT NULL,
    searched_at DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),

    CONSTRAINT fk_svh_user FOREIGN KEY (user_id) REFERENCES shared.users(id) ON DELETE CASCADE
);

-- ============================================================
-- ÍNDICES
-- ============================================================
CREATE INDEX ix_vt_videos_channel    ON viewtube.videos(channel_id);
CREATE INDEX ix_vt_videos_created    ON viewtube.videos(created_at DESC);
CREATE INDEX ix_vt_videos_views      ON viewtube.videos(views DESC);
CREATE INDEX ix_vt_channels_user     ON viewtube.channels(user_id);
CREATE INDEX ix_vt_comments_video    ON viewtube.comments(video_id);
CREATE INDEX ix_vt_subs_channel      ON viewtube.subscriptions(channel_id);
CREATE INDEX ix_vt_wh_user           ON viewtube.watch_history(user_id, watched_at DESC);
CREATE INDEX ix_vt_wh_video          ON viewtube.watch_history(video_id);
CREATE INDEX ix_vt_search_user       ON viewtube.search_history(user_id, searched_at DESC);
CREATE INDEX ix_vt_video_tags_tag    ON viewtube.video_tags(tag_id);

-- ============================================================
-- SEED — Tags padrão
-- ============================================================
INSERT INTO viewtube.tags (name) VALUES
    ('Entretenimento'), ('Música'), ('Gaming'), ('Tecnologia'), ('Esportes'),
    ('Notícias'), ('Educação'), ('Comédia'), ('Culinária'), ('Viagem');
GO
