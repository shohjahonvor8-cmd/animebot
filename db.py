import sqlite3

conn = sqlite3.connect("anime_bot.db", check_same_thread=False)
cursor = conn.cursor()

# =========================
# 👤 USERS TABLE
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE
)
""")

# =========================
# 🎬 ANIMES TABLE
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS animes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT UNIQUE,
    episodes INTEGER DEFAULT 0,
    video TEXT
)
""")

# =========================
# 📺 EPISODES TABLE
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anime_id INTEGER NOT NULL,
    episode_number INTEGER NOT NULL,
    video TEXT NOT NULL,
    UNIQUE(anime_id, episode_number),
    FOREIGN KEY (anime_id) REFERENCES animes(id)
)
""")

# =========================
# 📢 CHANNELS TABLE
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT DEFAULT 'Telegram Channel',
    link TEXT NOT NULL
)
""")

# =========================
# 🔥 INDEX (tezlik uchun)
# =========================
cursor.execute("CREATE INDEX IF NOT EXISTS idx_anime_code ON animes(code)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_episode_anime ON episodes(anime_id)")

conn.commit()