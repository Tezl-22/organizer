"""Заповнює базу демонстраційними даними (стара база очищується).

Запуск: python seed.py
"""
from datetime import date, datetime, timedelta

import db
from app import create_app


def day(offset):
    return (date.today() + timedelta(days=offset)).isoformat()


def moment(days, hour, minute=0):
    t = datetime.now().replace(hour=hour, minute=minute) + timedelta(days=days)
    return t.strftime("%Y-%m-%d %H:%M")


def seed():
    app = create_app()
    with app.app_context():
        db.init_db()
        tasks = [
            ("Підготувати звіт з лабораторної роботи №5", "Бази даних, нормалізація", 3, day(2)),
            ("Оплатити інтернет", "", 2, day(-1)),
            ("Записатися до стоматолога", "", 2, day(5)),
            ("Прочитати розділ 3 підручника з ООП", "Наслідування та поліморфізм", 1, day(9)),
            ("Купити подарунок сестрі", "До дня народження", 3, day(12)),
            ("Здати книги в бібліотеку", "", 1, day(-3)),
            ("Оновити резюме", "Додати курсовий проєкт", 2, None),
        ]
        for t in tasks:
            db.tasks.create(*t)
        db.tasks.toggle(6)  # книги вже здано

        db.notes.create("Список покупок", "Молоко\nХліб\nЯйця\nКава")
        db.notes.create("Ідеї для курсової", "Органайзер на Flask: задачі, нотатки,\n"
                                             "нагадування та календар.")
        db.notes.create("Конспект: SQL JOIN", "INNER JOIN повертає лише збіги,\n"
                                              "LEFT JOIN - усі рядки лівої таблиці.")
        db.notes.create("Паролі не зберігати тут!", "Нагадування самому собі.")

        db.reminders.create("Консультація з керівником", "Ауд. 215", moment(-1, 10, 0))
        db.reminders.create("Подзвонити батькам", "", moment(0, 23, 0)
                            if datetime.now().hour < 23 else moment(1, 9, 0))
        db.reminders.create("Вебінар з Python", "Посилання в пошті", moment(2, 18, 30))
        db.reminders.create("Продовжити підписку", "", moment(6, 12, 0))
        db.reminders.create("Захист курсової роботи", "Підготувати презентацію", moment(16, 9, 0))
    print("Демонстраційні дані додано.")


if __name__ == "__main__":
    seed()
