"""JSON storage layer for Training Planner."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .model import TrainingBook


class StorageError(RuntimeError):
    """Raised when application data cannot be loaded or saved."""


class JsonStorage:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> TrainingBook:
        if not self.path.exists():
            return TrainingBook()

        try:
            text = self.path.read_text(encoding="utf-8")
            if not text.strip():
                return TrainingBook()
            data: Any = json.loads(text)
        except json.JSONDecodeError as exc:
            raise StorageError(f"Файл данных содержит некорректный JSON: {self.path}") from exc
        except OSError as exc:
            raise StorageError(f"Не удалось прочитать файл данных: {self.path}") from exc

        if not isinstance(data, list):
            raise StorageError("JSON-файл должен содержать список тренировок.")

        try:
            return TrainingBook.from_json_ready(data)
        except Exception as exc:
            raise StorageError("В JSON-файле есть некорректные записи тренировок.") from exc

    def save(self, book: TrainingBook) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(self.path.suffix + ".tmp")

        try:
            temporary_path.write_text(
                json.dumps(book.to_json_ready(), ensure_ascii=False, indent=4),
                encoding="utf-8",
            )
            os.replace(temporary_path, self.path)
        except OSError as exc:
            raise StorageError(f"Не удалось сохранить файл данных: {self.path}") from exc
        finally:
            if temporary_path.exists():
                try:
                    temporary_path.unlink()
                except OSError:
                    pass
