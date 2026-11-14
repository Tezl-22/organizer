"""Модульні та функціональні тести органайзера (pytest + тестовий клієнт Flask)."""
import os
import sys
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db  # noqa: E402
from app import create_app, parse_date, parse_datetime  # noqa: E402
from month_calendar import CalendarMonth  # noqa: E402


@pytest.fixture
def app(tmp_path):
    # кожен тест працює з окремою тимчасовою базою
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})


@pytest.fixture
def client(app):
    return app.test_client()


def html(response):
    return response.get_data(as_text=True)


def dtl(delta):
    """Значення для поля datetime-local відносно поточного часу."""
    return (datetime.now() + delta).strftime("%Y-%m-%dT%H:%M")


# ---------- Задачі ----------

def test_task_create_and_list(client):
    r = client.post("/tasks/new", data={"title": "Підготувати звіт", "priority": "3",
                                        "due_date": "2026-11-20"}, follow_redirects=True)
    assert r.status_code == 200
    assert "Задачу додано." in html(r)
    assert "Підготувати звіт" in html(r)
    assert "Високий" in html(r)


def test_task_edit(client, app):
    client.post("/tasks/new", data={"title": "Стара назва", "priority": "2"})
    client.post("/tasks/1/edit", data={"title": "Нова назва", "priority": "1",
                                       "due_date": "2026-12-01"})
    with app.app_context():
        task = db.tasks.get(1)
    assert task["title"] == "Нова назва"
    assert task["priority"] == 1
    assert task["due_date"] == "2026-12-01"


def test_task_toggle_status(client, app):
    client.post("/tasks/new", data={"title": "Купити квитки", "priority": "2"})
    client.post("/tasks/1/toggle")
    with app.app_context():
        assert db.tasks.get(1)["is_done"] == 1
    client.post("/tasks/1/toggle")
    with app.app_context():
        assert db.tasks.get(1)["is_done"] == 0


def test_task_delete(client, app):
    client.post("/tasks/new", data={"title": "Тимчасова", "priority": "2"})
    r = client.post("/tasks/1/delete", follow_redirects=True)
    assert "Задачу видалено." in html(r)
    with app.app_context():
        assert db.tasks.get(1) is None


def test_task_filter_by_status_and_priority(client):
    client.post("/tasks/new", data={"title": "Виконана задача", "priority": "3"})
    client.post("/tasks/new", data={"title": "Активна низька", "priority": "1"})
    client.post("/tasks/new", data={"title": "Активна висока", "priority": "3"})
    client.post("/tasks/1/toggle")

    page = html(client.get("/tasks?status=active"))
    assert "Активна низька" in page and "Виконана задача" not in page

    page = html(client.get("/tasks?status=done"))
    assert "Виконана задача" in page and "Активна низька" not in page

    page = html(client.get("/tasks?status=active&priority=3"))
    assert "Активна висока" in page and "Активна низька" not in page


def test_task_empty_title_rejected(client, app):
    r = client.post("/tasks/new", data={"title": "   ", "priority": "2"})
    assert r.status_code == 400
    assert "Назва задачі не може бути порожньою." in html(r)
    with app.app_context():
        assert db.tasks.list() == []


def test_task_bad_date_rejected(client):
    r = client.post("/tasks/new", data={"title": "Задача", "priority": "2",
                                        "due_date": "2026-02-30"})
    assert r.status_code == 400
    assert "Некоректна дата" in html(r)


def test_task_bad_priority_rejected(client):
    r = client.post("/tasks/new", data={"title": "Задача", "priority": "7"})
    assert r.status_code == 400
    assert "Оберіть пріоритет" in html(r)


def test_task_title_too_long_rejected(client):
    r = client.post("/tasks/new", data={"title": "а" * 201, "priority": "2"})
    assert r.status_code == 400


def test_edit_missing_task_returns_404(client):
    assert client.get("/tasks/999/edit").status_code == 404


# ---------- Нотатки ----------

def test_note_crud(client, app):
    client.post("/notes/new", data={"title": "Ідеї", "content": "Перший запис"})
    client.post("/notes/1/edit", data={"title": "Ідеї для проєкту", "content": "Оновлено"})
    with app.app_context():
        note = db.notes.get(1)
        assert note["title"] == "Ідеї для проєкту"
        assert note["content"] == "Оновлено"
    client.post("/notes/1/delete")
    with app.app_context():
        assert db.notes.get(1) is None


def test_note_search_case_insensitive(client):
    client.post("/notes/new", data={"title": "Список покупок", "content": "Молоко, хліб"})
    client.post("/notes/new", data={"title": "Конспект", "content": "Бази даних"})
    page = html(client.get("/notes?q=МОЛОКО"))
    assert "Список покупок" in page and "Конспект" not in page
    page = html(client.get("/notes?q=неіснуюче"))
    assert "Нічого не знайдено." in page


def test_note_empty_title_rejected(client):
    r = client.post("/notes/new", data={"title": "", "content": "Текст без назви"})
    assert r.status_code == 400
    assert "Назва нотатки не може бути порожньою." in html(r)


# ---------- Нагадування ----------

def test_reminder_crud(client, app):
    client.post("/reminders/new", data={"title": "Зустріч", "remind_at": "2026-12-10T09:30"})
    with app.app_context():
        assert db.reminders.get(1)["remind_at"] == "2026-12-10 09:30"
    client.post("/reminders/1/edit", data={"title": "Зустріч з керівником",
                                           "remind_at": "2026-12-11T10:00"})
    with app.app_context():
        r = db.reminders.get(1)
        assert r["title"] == "Зустріч з керівником" and r["remind_at"] == "2026-12-11 10:00"
    client.post("/reminders/1/delete")
    with app.app_context():
        assert db.reminders.get(1) is None


def test_reminder_validation(client):
    r = client.post("/reminders/new", data={"title": "Без часу", "remind_at": ""})
    assert r.status_code == 400 and "Вкажіть дату і час" in html(r)
    r = client.post("/reminders/new", data={"title": "Час", "remind_at": "2026-11-10T25:00"})
    assert r.status_code == 400 and "Некоректні дата і час" in html(r)
    r = client.post("/reminders/new", data={"title": "", "remind_at": "2026-11-10T10:00"})
    assert r.status_code == 400 and "Назва нагадування не може бути порожньою." in html(r)


def test_overdue_and_upcoming_reminders(client, app):
    client.post("/reminders/new", data={"title": "Минуле", "remind_at": dtl(timedelta(-1))})
    client.post("/reminders/new", data={"title": "Скоро", "remind_at": dtl(timedelta(hours=3))})
    client.post("/reminders/new", data={"title": "Далеко", "remind_at": dtl(timedelta(30))})

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M")
    with app.app_context():
        assert [r["title"] for r in db.reminders.overdue(now)] == ["Минуле"]
        assert [r["title"] for r in db.reminders.upcoming(now, week)] == ["Скоро"]


def test_reminder_banner_on_every_page(client):
    client.post("/reminders/new", data={"title": "Минуле", "remind_at": dtl(timedelta(hours=-2))})
    client.post("/reminders/new", data={"title": "Мамі", "remind_at": dtl(timedelta(hours=1))})
    for url in ("/tasks", "/notes", "/calendar"):
        page = html(client.get(url))
        assert "Прострочених нагадувань: <strong>1</strong>" in page
        assert "Мамі" in page


# ---------- Календар ----------

def test_calendar_month_shows_tasks_and_reminders(client):
    client.post("/tasks/new", data={"title": "Курсова", "priority": "3", "due_date": "2026-12-15"})
    client.post("/reminders/new", data={"title": "Новий рік", "remind_at": "2026-12-31T23:59"})
    client.post("/tasks/new", data={"title": "Лютий", "priority": "2", "due_date": "2027-02-01"})
    page = html(client.get("/calendar?year=2026&month=12"))
    assert "Грудень 2026" in page
    assert "Курсова" in page and "Новий рік" in page
    assert "Лютий" not in page
    # посилання на сусідні місяці (перехід через рік)
    assert "year=2026&amp;month=11" in page and "year=2027&amp;month=1" in page


def test_calendar_invalid_month_falls_back_to_current(client):
    r = client.get("/calendar?year=2026&month=13")
    assert r.status_code == 200


def test_calendar_month_grid():
    cal = CalendarMonth(2026, 11)
    assert cal.first_day.weekday() == 0          # тиждень починається з понеділка
    assert all(len(week) == 7 for week in cal.weeks)
    assert cal.prev() == (2026, 10) and cal.next() == (2026, 12)
    assert CalendarMonth(2026, 1).prev() == (2025, 12)
    assert cal.title == "Листопад 2026"


def test_parse_helpers():
    assert parse_date("2026-11-14") is not None
    assert parse_date("14.11.2026") is None
    assert parse_datetime("2026-11-14T08:00") is not None
    assert parse_datetime("2026-11-14 8 ранку") is None
