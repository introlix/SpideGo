import string
import sqlite3
import json
from hashlib import sha256
from datetime import datetime, timedelta

DB_PATH = "cache.db"


def init_cache():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)
        db.commit()


init_cache()


def get_cache(key: str):
    with sqlite3.connect(DB_PATH) as db:
        row = db.execute(
            """
            SELECT value
            FROM cache
            WHERE key = ? AND expires_at > ?
            """,
            (key, datetime.now().isoformat())
        ).fetchone()

        if row:
            return json.loads(row[0])


def save_cache(key: str, value, ttl: int):
    expires_at = datetime.now() + timedelta(seconds=ttl)

    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            """
            INSERT OR REPLACE INTO cache (key, value, expires_at)
            VALUES (?, ?, ?)
            """,
            (key, json.dumps(value), expires_at.isoformat())
        )
        db.commit()


def get_cached_feature_snippets(query: str):
    query = query.translate(str.maketrans("", "", string.punctuation))
    key = f"search:{query.strip().lower()}"

    return get_cache(key)


def save_feature_snippets(query: str, results: list[dict]):
    query = query.translate(str.maketrans("", "", string.punctuation))
    key = f"search:{query.strip().lower()}"

    save_cache(
        key,
        results,
        60 * 60
    )


def get_cached_page(url: str):
    key = f"page:{sha256(url.strip().encode()).hexdigest()}"

    return get_cache(key)


def save_page(url: str, results: dict):
    key = f"page:{sha256(url.strip().encode()).hexdigest()}"

    save_cache(
        key,
        results,
        60 * 60 * 24
    )