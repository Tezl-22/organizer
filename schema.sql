-- Схема бази даних органайзера (SQLite)
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS notes;
DROP TABLE IF EXISTS reminders;

-- Задачі: пріоритет 1 - низький, 2 - середній, 3 - високий
CREATE TABLE tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    priority    INTEGER NOT NULL DEFAULT 2 CHECK (priority IN (1, 2, 3)),
    due_date    TEXT,                       -- формат YYYY-MM-DD, може бути порожнім
    is_done     INTEGER NOT NULL DEFAULT 0 CHECK (is_done IN (0, 1)),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Нотатки
CREATE TABLE notes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    content     TEXT    NOT NULL DEFAULT '',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Нагадування: remind_at у форматі YYYY-MM-DD HH:MM
CREATE TABLE reminders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    remind_at   TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX idx_tasks_due ON tasks (due_date);
CREATE INDEX idx_reminders_at ON reminders (remind_at);
