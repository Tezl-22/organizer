"""Органайзер: вебзастосунок на Flask (маршрути та перевірка введених даних)."""
import os
from datetime import date

from flask import Flask, abort, flash, redirect, render_template, request, url_for

import db

PRIORITIES = {1: "Низький", 2: "Середній", 3: "Високий"}


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

    # ---------- Задачі ----------
    @app.route("/")
    def index():
        return redirect(url_for("task_list"))

    @app.route("/tasks")
    def task_list():
        return render_template("tasks.html", tasks=db.tasks.list(), priorities=PRIORITIES)

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

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
