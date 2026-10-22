"""Робота з базою даних SQLite: підключення, створення схеми, запити."""
import sqlite3

from flask import current_app, g


def get_db():
    """Повертає підключення до БД для поточного запиту (одне на запит)."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        # LOWER у SQLite не працює з кирилицею, тому реєструємо str.lower з Python
        g.db.create_function("py_lower", 1, lambda s: s.lower() if s else s)
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Створює таблиці за файлом schema.sql (старі дані видаляються)."""
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf-8"))


class BaseRepository:
    """Спільні операції для всіх таблиць: отримання та видалення запису за id."""

    table = ""

    def get(self, item_id):
        return get_db().execute(
            f"SELECT * FROM {self.table} WHERE id = ?", (item_id,)
        ).fetchone()

    def delete(self, item_id):
        db = get_db()
        db.execute(f"DELETE FROM {self.table} WHERE id = ?", (item_id,))
        db.commit()
