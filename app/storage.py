import sqlite3
from pathlib import Path

APP_DIR = Path.home() / '.future_browser'
DATA_DIR = APP_DIR / 'data'
CACHE_DIR = APP_DIR / 'cache'
DOWNLOAD_DIR = APP_DIR / 'downloads'
DB_PATH = APP_DIR / 'browser.db'

DEFAULT_SPEED_DIALS = [
    ('Google', 'https://www.google.com'),
    ('YouTube', 'https://www.youtube.com'),
    ('GitHub', 'https://github.com'),
    ('Stack Overflow', 'https://stackoverflow.com'),
    ('Wikipedia', 'https://www.wikipedia.org'),
    ('Perplexity', 'https://www.perplexity.ai'),
]


def ensure_dirs():
    APP_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)
    CACHE_DIR.mkdir(exist_ok=True)
    DOWNLOAD_DIR.mkdir(exist_ok=True)


def get_connection():
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT NOT NULL,
            visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS speed_dials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE
        )
    """)
    conn.commit()
    count = conn.execute('SELECT COUNT(*) FROM speed_dials').fetchone()[0]
    if count == 0:
        conn.executemany('INSERT INTO speed_dials (title, url) VALUES (?, ?)', DEFAULT_SPEED_DIALS)
        conn.commit()
    return conn
