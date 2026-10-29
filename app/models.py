"""Модель задачи, состояния питомца и преобразователи даты."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from uuid import uuid4

from PySide6.QtCore import QDate, QDateTime, QTime


MONTHS_SHORT = (
    "янв.", "фев.", "мар.", "апр.", "мая", "июн.",
    "июл.", "авг.", "сен.", "окт.", "ноя.", "дек.",
)


def to_qdatetime(value: datetime) -> QDateTime:
    """Convert Python datetime to Qt's date/time type for QDateTimeEdit."""
    date = QDate(value.year, value.month, value.day)
    time = QTime(
        value.hour,
        value.minute,
        value.second,
        value.microsecond // 1000,
    )
    return QDateTime(date, time)


@dataclass
class Task:
    title: str = "Новая задача"
    description: str = ""
    deadline: datetime = field(
        default_factory=lambda: datetime.now() + timedelta(days=2)
    )
    completed: bool = False
    completed_at: datetime | None = None
    task_id: str = field(default_factory=lambda: str(uuid4()))
    icon: str = "document"
    reminder_minutes: int | None = None
    reminded_deadline: str | None = None

    def to_dict(self) -> dict[str, str | bool | int | None]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "deadline": self.deadline.isoformat(),
            "completed": self.completed,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "icon": self.icon,
            "reminder_minutes": self.reminder_minutes,
            "reminded_deadline": self.reminded_deadline,
        }

    @classmethod
    def from_dict(cls, data: object) -> Task:
        if not isinstance(data, dict):
            raise ValueError("Запись задачи должна быть объектом")
        title = data["title"]
        description = data.get("description", "")
        completed = data["completed"]
        if (
            not isinstance(title, str)
            or not isinstance(description, str)
            or not isinstance(completed, bool)
        ):
            raise ValueError("У задачи неверный формат текста или статуса")

        completed_at_value = data.get("completed_at")
        icon = data.get("icon", "document")
        if not isinstance(icon, str):
            icon = "document"
        reminder_minutes = data.get("reminder_minutes")
        if reminder_minutes not in {None, 0, 15, 60, 1440}:
            reminder_minutes = None
        reminded_deadline = data.get("reminded_deadline")
        if not isinstance(reminded_deadline, str):
            reminded_deadline = None
        return cls(
            task_id=str(data.get("task_id", uuid4())),
            title=title,
            description=description,
            deadline=datetime.fromisoformat(data["deadline"]),
            completed=completed,
            completed_at=(
                datetime.fromisoformat(completed_at_value)
                if completed_at_value
                else None
            ),
            icon=icon,
            reminder_minutes=reminder_minutes,
            reminded_deadline=reminded_deadline,
        )


class Mood(Enum):
    POSITIVE = "Положительное", "😊", "Дедлайны пока не горят"
    TENSE = "Напряжённое", "😟", "Скоро дедлайн — пора за дело"
    ANGRY = "Гнев", "😠", "Дедлайн уже близко или прошёл"

    def __init__(self, title: str, face: str, message: str) -> None:
        self.title = title
        self.face = face
        self.message = message


def evaluate_mood(tasks: list[Task], now: datetime | None = None) -> Mood:
    """Настроение зависит от ближайшего срока незавершённой задачи."""
    current_time = now or datetime.now()
    open_tasks = [task for task in tasks if not task.completed]
    if not open_tasks:
        return Mood.POSITIVE

    nearest = min(task.deadline - current_time for task in open_tasks)
    if nearest <= timedelta(hours=2):
        return Mood.ANGRY
    if nearest <= timedelta(hours=24):
        return Mood.TENSE
    return Mood.POSITIVE
