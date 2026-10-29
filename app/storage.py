"""Загрузка, проверка и атомарное сохранение задач и настроек."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QStandardPaths

from .models import Task


class TaskStorageError(Exception):
    """Ошибка чтения или проверки файла задач."""


class TaskStorage:
    def __init__(self) -> None:
        app_data_dir = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation
        )
        self.path = Path(app_data_dir) / "tasks.json"

    def load(self) -> tuple[list[Task], dict[str, object]]:
        if not self.path.exists():
            return [], {}
        return self.load_file(self.path)

    @staticmethod
    def load_file(path: str | Path) -> tuple[list[Task], dict[str, object]]:
        """Read and validate an app data file without changing current state."""
        try:
            saved_data = json.loads(Path(path).read_text(encoding="utf-8"))
            if (
                not isinstance(saved_data, dict)
                or type(saved_data.get("version")) is not int
                or saved_data["version"] != 1
            ):
                raise ValueError("Неподдерживаемая версия файла задач")
            saved_tasks = saved_data.get("tasks")
            if not isinstance(saved_tasks, list):
                raise ValueError("В файле нет корректного списка задач")
            settings = saved_data.get("settings", {})
            if not isinstance(settings, dict):
                raise ValueError("В файле нет корректного набора настроек")
            tasks = [Task.from_dict(item) for item in saved_tasks]
            task_ids = [task.task_id for task in tasks]
            if len(task_ids) != len(set(task_ids)):
                raise ValueError("В файле повторяются идентификаторы задач")
            return tasks, settings
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            raise TaskStorageError(str(error)) from error

    @staticmethod
    def save_file(path: str | Path, tasks: list[Task], settings: dict[str, object]) -> None:
        """Write a portable backup atomically."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = target.with_suffix(target.suffix + ".tmp")
        saved_data = {
            "version": 1,
            "tasks": [task.to_dict() for task in tasks],
            "settings": settings,
        }
        try:
            temporary_path.write_text(
                json.dumps(saved_data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary_path.replace(target)
        finally:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass

    def save(self, tasks: list[Task], settings: dict[str, object]) -> None:
        self.save_file(self.path, tasks, settings)
