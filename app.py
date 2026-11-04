"""Органайзер: вебзастосунок на Flask (маршрути та перевірка введених даних)."""
import os
from datetime import date, datetime, timedelta

from flask import Flask, abort, flash, redirect, render_template, request, url_for

import db

PRIORITIES = {1: "Низький", 2: "Середній", 3: "Високий"}
DATETIME_FORMAT = "%Y-%m-%d %H:%M"
UPCOMING_DAYS = 7  # скільки днів наперед показувати найближчі нагадування


def parse_date(value):
    """Перетворює рядок YYYY-MM-DD на дату; None, якщо рядок некоректний."""
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def validate_task(form):
    """Перевіряє дані форми задачі, повертає список помилок."""
    errors = []
    if not form["title"]:
        errors.append("Назва задачі не може бути порожньою.")
    elif len(form["title"]) > 200:
        errors.append("Назва задачі не може бути довшою за 200 символів.")
    if form["priority"] not in ("1", "2", "3"):
        errors.append("Оберіть пріоритет зі списку.")
    if form["due_date"] and parse_date(form["due_date"]) is None:
        errors.append("Некоректна дата терміну виконання (потрібно РРРР-ММ-ДД).")
    return errors


def task_form_data():
    return {
        "title": request.form.get("title", "").strip(),
        "description": request.form.get("description", "").strip(),
        "priority": request.form.get("priority", "2"),
        "due_date": request.form.get("due_date", "").strip(),
    }


def validate_note(form):
    errors = []
    if not form["title"]:
        errors.append("Назва нотатки не може бути порожньою.")
    elif len(form["title"]) > 200:
        errors.append("Назва нотатки не може бути довшою за 200 символів.")
    return errors


def note_form_data():
    return {
        "title": request.form.get("title", "").strip(),
        "content": request.form.get("content", "").strip(),
    }


def parse_datetime(value):
    """Приймає 'YYYY-MM-DDTHH:MM' (поле datetime-local) або 'YYYY-MM-DD HH:MM'."""
    try:
        return datetime.strptime(value.replace("T", " "), DATETIME_FORMAT)
    except ValueError:
        return None


def validate_reminder(form):
    errors = []
    if not form["title"]:
        errors.append("Назва нагадування не може бути порожньою.")
    elif len(form["title"]) > 200:
        errors.append("Назва нагадування не може бути довшою за 200 символів.")
    if not form["remind_at"]:
        errors.append("Вкажіть дату і час нагадування.")
    elif parse_datetime(form["remind_at"]) is None:
        errors.append("Некоректні дата і час нагадування.")
    return errors


def reminder_form_data():
    return {
        "title": request.form.get("title", "").strip(),
        "description": request.form.get("description", "").strip(),
        "remind_at": request.form.get("remind_at", "").strip(),
    }


def now_str(delta=timedelta()):
    return (datetime.now() + delta).strftime(DATETIME_FORMAT)


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",  # локальний навчальний застосунок
        DATABASE=os.path.join(app.instance_path, "organizer.db"),
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)

    app.teardown_appcontext(db.close_db)

    # створюємо таблиці під час першого запуску
    with app.app_context():
        if not db.get_db().execute(
            "SELECT name FROM sqlite_master WHERE name = 'tasks'"
        ).fetchone():
            db.init_db()

    @app.context_processor
    def reminder_banner():
        """Дані для банера на кожній сторінці: прострочені та найближчі за добу."""
        return {
            "banner_overdue": len(db.reminders.overdue(now_str())),
            "banner_soon": db.reminders.upcoming(now_str(), now_str(timedelta(days=1))),
        }

    # ---------- Задачі ----------
    @app.route("/")
    def index():
        return redirect(url_for("task_list"))

    @app.route("/tasks")
    def task_list():
        status = request.args.get("status", "all")
        priority = request.args.get("priority", type=int)
        if priority not in PRIORITIES:
            priority = None
        return render_template("tasks.html", tasks=db.tasks.list(status, priority),
                               priorities=PRIORITIES, status=status, priority=priority,
                               today=date.today().isoformat())

    @app.route("/tasks/new", methods=["GET", "POST"])
    def task_new():
        form = {"title": "", "description": "", "priority": "2", "due_date": ""}
        errors = []
        if request.method == "POST":
            form = task_form_data()
            errors = validate_task(form)
            if not errors:
                db.tasks.create(form["title"], form["description"],
                                int(form["priority"]), form["due_date"] or None)
                flash("Задачу додано.")
                return redirect(url_for("task_list"))
        return render_template("task_form.html", form=form, errors=errors,
                               priorities=PRIORITIES, task_id=None), 400 if errors else 200

    @app.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
    def task_edit(task_id):
        task = db.tasks.get(task_id) or abort(404)
        form = dict(task)
        errors = []
        if request.method == "POST":
            form = task_form_data()
            errors = validate_task(form)
            if not errors:
                db.tasks.update(task_id, form["title"], form["description"],
                                int(form["priority"]), form["due_date"] or None)
                flash("Задачу оновлено.")
                return redirect(url_for("task_list"))
        return render_template("task_form.html", form=form, errors=errors,
                               priorities=PRIORITIES, task_id=task_id), 400 if errors else 200

    @app.post("/tasks/<int:task_id>/toggle")
    def task_toggle(task_id):
        db.tasks.toggle(task_id)
        return redirect(request.referrer or url_for("task_list"))

    @app.post("/tasks/<int:task_id>/delete")
    def task_delete(task_id):
        db.tasks.delete(task_id)
        flash("Задачу видалено.")
        return redirect(url_for("task_list"))

    # ---------- Нотатки ----------
    @app.route("/notes")
    def note_list():
        search = request.args.get("q", "").strip()
        return render_template("notes.html", notes=db.notes.list(search), search=search)

    @app.route("/notes/new", methods=["GET", "POST"])
    def note_new():
        form = {"title": "", "content": ""}
        errors = []
        if request.method == "POST":
            form = note_form_data()
            errors = validate_note(form)
            if not errors:
                db.notes.create(form["title"], form["content"])
                flash("Нотатку додано.")
                return redirect(url_for("note_list"))
        return render_template("note_form.html", form=form, errors=errors,
                               note_id=None), 400 if errors else 200

    @app.route("/notes/<int:note_id>/edit", methods=["GET", "POST"])
    def note_edit(note_id):
        note = db.notes.get(note_id) or abort(404)
        form = dict(note)
        errors = []
        if request.method == "POST":
            form = note_form_data()
            errors = validate_note(form)
            if not errors:
                db.notes.update(note_id, form["title"], form["content"])
                flash("Нотатку оновлено.")
                return redirect(url_for("note_list"))
        return render_template("note_form.html", form=form, errors=errors,
                               note_id=note_id), 400 if errors else 200

    @app.post("/notes/<int:note_id>/delete")
    def note_delete(note_id):
        db.notes.delete(note_id)
        flash("Нотатку видалено.")
        return redirect(url_for("note_list"))

    # ---------- Нагадування ----------
    @app.route("/reminders")
    def reminder_list():
        now = now_str()
        return render_template(
            "reminders.html",
            overdue=db.reminders.overdue(now),
            upcoming=db.reminders.upcoming(now, now_str(timedelta(days=UPCOMING_DAYS))),
            reminders=db.reminders.list(),
            now=now,
            upcoming_days=UPCOMING_DAYS,
        )

    @app.route("/reminders/new", methods=["GET", "POST"])
    def reminder_new():
        form = {"title": "", "description": "", "remind_at": ""}
        errors = []
        if request.method == "POST":
            form = reminder_form_data()
            errors = validate_reminder(form)
            if not errors:
                remind_at = parse_datetime(form["remind_at"]).strftime(DATETIME_FORMAT)
                db.reminders.create(form["title"], form["description"], remind_at)
                flash("Нагадування додано.")
                return redirect(url_for("reminder_list"))
        return render_template("reminder_form.html", form=form, errors=errors,
                               reminder_id=None), 400 if errors else 200

    @app.route("/reminders/<int:reminder_id>/edit", methods=["GET", "POST"])
    def reminder_edit(reminder_id):
        reminder = db.reminders.get(reminder_id) or abort(404)
        form = dict(reminder)
        errors = []
        if request.method == "POST":
            form = reminder_form_data()
            errors = validate_reminder(form)
            if not errors:
                remind_at = parse_datetime(form["remind_at"]).strftime(DATETIME_FORMAT)
                db.reminders.update(reminder_id, form["title"], form["description"], remind_at)
                flash("Нагадування оновлено.")
                return redirect(url_for("reminder_list"))
        return render_template("reminder_form.html", form=form, errors=errors,
                               reminder_id=reminder_id), 400 if errors else 200

    @app.post("/reminders/<int:reminder_id>/delete")
    def reminder_delete(reminder_id):
        db.reminders.delete(reminder_id)
        flash("Нагадування видалено.")
        return redirect(url_for("reminder_list"))

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
