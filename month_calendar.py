"""Побудова сітки місяця для сторінки календаря."""
import calendar
from datetime import date

MONTH_NAMES = ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень",
               "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"]
WEEKDAY_NAMES = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]


class CalendarMonth:
    """Місяць календаря: тижні (з понеділка), сусідні місяці, назва."""

    def __init__(self, year, month):
        self.year = year
        self.month = month
        # список тижнів, кожен тиждень - 7 об'єктів date (включно з днями сусідніх місяців)
        self.weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)

    @property
    def title(self):
        return f"{MONTH_NAMES[self.month - 1]} {self.year}"

    @property
    def first_day(self):
        return self.weeks[0][0]

    @property
    def last_day(self):
        return self.weeks[-1][-1]

    def prev(self):
        return (self.year - 1, 12) if self.month == 1 else (self.year, self.month - 1)

    def next(self):
        return (self.year + 1, 1) if self.month == 12 else (self.year, self.month + 1)

    def is_current_month(self, day: date):
        return day.month == self.month
