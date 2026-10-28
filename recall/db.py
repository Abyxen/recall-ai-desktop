from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS documents(
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, digest TEXT UNIQUE NOT NULL,
 subject TEXT NOT NULL, notebook TEXT NOT NULL, path TEXT NOT NULL,
 pages INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'ready',
 created TEXT NOT NULL DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS chunks(
 id INTEGER PRIMARY KEY, document_id INTEGER NOT NULL REFERENCES documents ON DELETE CASCADE,
 page INTEGER NOT NULL, text TEXT NOT NULL, vector TEXT NOT NULL, embedding TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS cards(
 id INTEGER PRIMARY KEY, document_id INTEGER REFERENCES documents ON DELETE SET NULL,
 deck TEXT NOT NULL, question TEXT NOT NULL, answer TEXT NOT NULL, topic TEXT NOT NULL,
 difficulty TEXT NOT NULL, source TEXT NOT NULL, interval INTEGER NOT NULL DEFAULT 0,
 ease REAL NOT NULL DEFAULT 2.5, repetitions INTEGER NOT NULL DEFAULT 0,
 due TEXT NOT NULL DEFAULT (date('now')), UNIQUE(deck, question));
CREATE TABLE IF NOT EXISTS reviews(
 id INTEGER PRIMARY KEY, card_id INTEGER REFERENCES cards ON DELETE SET NULL,
 rating INTEGER NOT NULL, created TEXT NOT NULL DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS quizzes(
 id INTEGER PRIMARY KEY, title TEXT NOT NULL, payload TEXT NOT NULL,
 created TEXT NOT NULL DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS attempts(
 id INTEGER PRIMARY KEY, quiz_id INTEGER NOT NULL REFERENCES quizzes ON DELETE CASCADE,
 score REAL NOT NULL, total INTEGER NOT NULL, answers TEXT NOT NULL, feedback TEXT NOT NULL,
 created TEXT NOT NULL DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS conversations(
 id INTEGER PRIMARY KEY, scope TEXT NOT NULL, question TEXT NOT NULL, answer TEXT NOT NULL,
 evidence TEXT NOT NULL, created TEXT NOT NULL DEFAULT (datetime('now')));
CREATE INDEX IF NOT EXISTS chunks_document ON chunks(document_id);
CREATE INDEX IF NOT EXISTS cards_due ON cards(due);
PRAGMA user_version=1;
"""


def default_home() -> Path:
    if os.environ.get("RECALL_DATA_DIR"):
        return Path(os.environ["RECALL_DATA_DIR"]).expanduser()
    return Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local/share")) / "RecallAI"


class Database:
    def __init__(self, home: Path | None = None):
        self.home = Path(home) if home else default_home()
        self.home.mkdir(parents=True, exist_ok=True)
        self.path = self.home / "recall.sqlite3"
        with self.connect() as con:
            con.executescript(SCHEMA)

    @contextmanager
    def connect(self):
        con = sqlite3.connect(self.path, timeout=30)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA journal_mode=WAL")
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def rows(self, query, params=()):
        with self.connect() as con:
            return [dict(row) for row in con.execute(query, params)]

    def execute(self, query, params=()):
        with self.connect() as con:
            return con.execute(query, params).lastrowid

    def setting(self, key, default=None):
        rows = self.rows("SELECT value FROM settings WHERE key=?", (key,))
        return json.loads(rows[0]["value"]) if rows else default

    def configure(self, **values):
        with self.connect() as con:
            con.executemany("INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                            [(key, json.dumps(value)) for key, value in values.items()])
