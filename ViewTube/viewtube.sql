-- ========================================
-- DATABASE
-- ========================================
CREATE DATABASE IF NOT EXISTS viewtube;
USE viewtube;

-- ========================================
-- USERS
-- ========================================
CREATE TABLE users (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- CHANNELS
-- ========================================
CREATE TABLE channels (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    profile_image_url VARCHAR(255),
    banner_url VARCHAR(255),
    -- removido subscribers_count: calculado via COUNT em subscriptions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

-- ========================================
-- VIDEOS
-- ========================================
CREATE TABLE videos (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    channel_id INT UNSIGNED NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    video_url VARCHAR(255) NOT NULL,
    thumbnail_url VARCHAR(255),
    views INT UNSIGNED DEFAULT 0,
    duration INT UNSIGNED,         -- duração em segundos
    likes_count INT UNSIGNED DEFAULT 0,
    comments_count INT UNSIGNED DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (channel_id) REFERENCES channels(id)
        ON DELETE CASCADE,

    FULLTEXT (title, description),
    INDEX idx_videos_channel_id (channel_id),
    INDEX idx_videos_created_at (created_at)
);

-- ========================================
-- VIDEO LIKES
-- ========================================
CREATE TABLE video_likes (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    video_id INT UNSIGNED NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (user_id, video_id),

    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    FOREIGN KEY (video_id) REFERENCES videos(id)
        ON DELETE CASCADE,

    INDEX idx_video_likes_video_id (video_id)
);

-- ========================================
-- COMMENTS
-- ========================================
CREATE TABLE comments (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    video_id INT UNSIGNED NOT NULL,
    content TEXT NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    FOREIGN KEY (video_id) REFERENCES videos(id)
        ON DELETE CASCADE,

    INDEX idx_comments_video_id (video_id),
    INDEX idx_comments_user_id (user_id)
);

-- ========================================
-- SUBSCRIPTIONS
-- ========================================
CREATE TABLE subscriptions (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    subscriber_id INT UNSIGNED NOT NULL,
    channel_id INT UNSIGNED NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (subscriber_id, channel_id),

    FOREIGN KEY (subscriber_id) REFERENCES users(id)
        ON DELETE CASCADE,
    FOREIGN KEY (channel_id) REFERENCES channels(id)
        ON DELETE CASCADE,

    INDEX idx_subscriptions_channel_id (channel_id)
);

-- ========================================
-- TAGS
-- ========================================
CREATE TABLE tags (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- ========================================
-- VIDEO_TAGS
-- ========================================
CREATE TABLE video_tags (
    video_id INT UNSIGNED NOT NULL,
    tag_id INT UNSIGNED NOT NULL,

    PRIMARY KEY (video_id, tag_id),

    FOREIGN KEY (video_id) REFERENCES videos(id)
        ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id)
        ON DELETE CASCADE,

    INDEX idx_video_tags_tag_id (tag_id)
);

-- ========================================
-- PLAYLISTS
-- ========================================
CREATE TABLE playlists (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    thumbnail_url VARCHAR(255),
    is_public BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,

    INDEX idx_playlists_user_id (user_id)
);

-- ========================================
-- PLAYLIST VIDEOS
-- ========================================
CREATE TABLE playlist_videos (
    playlist_id INT UNSIGNED NOT NULL,
    video_id INT UNSIGNED NOT NULL,
    position INT UNSIGNED NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (playlist_id, video_id),

    FOREIGN KEY (playlist_id) REFERENCES playlists(id)
        ON DELETE CASCADE,
    FOREIGN KEY (video_id) REFERENCES videos(id)
        ON DELETE CASCADE,

    INDEX idx_playlist_videos_video_id (video_id)
);

-- ========================================
-- WATCH HISTORY
-- ========================================
CREATE TABLE watch_history (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    video_id INT UNSIGNED NOT NULL,
    watched_seconds INT UNSIGNED DEFAULT 0,  -- progresso em segundos
    watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE (user_id, video_id),   -- upsert: uma entrada por usuário/vídeo

    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    FOREIGN KEY (video_id) REFERENCES videos(id)
        ON DELETE CASCADE,

    INDEX idx_watch_history_user_id (user_id)
);
