"""Domain model and validation for Training Planner."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from itertools import count
from time import time_ns
from typing import Any, Iterable, Mapping

DATE_FORMAT = "%d.%m.%Y"
_COUNTER = count()


class ValidationError(ValueError):
    """Raised when user input does not match application rules."""


def make_id() -> str:
    """Return a stable enough local identifier for one workout record."""
    return f"{time_ns()}-{next(_COUNTER)}"


def validate_date(value: str) -> str:
    clean = str(value).strip()
    try:
        parsed = datetime.strptime(clean, DATE_FORMAT)
    except ValueError as exc:
        raise ValidationError("Дата должна быть в формате ДД.ММ.ГГГГ и быть реальной датой.") from exc
    return parsed.strftime(DATE_FORMAT)


def validate_training_type(value: str) -> str:
    clean = str(value).strip()
    if not clean:
        raise ValidationError("Введите тип тренировки.")
    if len(clean) > 80:
        raise ValidationError("Тип тренировки слишком длинный: максимум 80 символов.")
    return clean


def validate_duration(value: Any) -> int:
    clean = str(value).strip()
    try:
        duration = int(clean)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Длительность должна быть положительным целым числом.") from exc

    if duration <= 0:
        raise ValidationError("Длительность должна быть больше нуля.")
    if duration > 1440:
        raise ValidationError("Длительность не может быть больше 1440 минут.")
    return duration


@dataclass(frozen=True)
class Training:
    """One workout record."""

    id: str
    date: str
    training_type: str
    duration: int

    @classmethod
    def create(cls, date: str, training_type: str, duration: Any) -> "Training":
        return cls(
            id=make_id(),
            date=validate_date(date),
            training_type=validate_training_type(training_type),
            duration=validate_duration(duration),
        )

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "Training":
        record_id = str(raw.get("id") or make_id())
        training_type = raw.get("training_type", raw.get("type", ""))
        return cls(
            id=record_id,
            date=validate_date(str(raw.get("date", ""))),
            training_type=validate_training_type(str(training_type)),
            duration=validate_duration(raw.get("duration", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["type"] = data.pop("training_type")
        return data


class TrainingBook:
    """Collection of workout records with filtering and update helpers."""

    def __init__(self, trainings: Iterable[Training] | None = None) -> None:
        self._items: list[Training] = list(trainings or [])

    def all(self) -> list[Training]:
        return list(self._items)

    def add(self, training: Training) -> None:
        self._items.append(training)

    def replace(self, training_id: str, updated: Training) -> bool:
        for index, training in enumerate(self._items):
            if training.id == training_id:
                self._items[index] = updated
                return True
        return False

    def remove(self, training_id: str) -> bool:
        old_length = len(self._items)
        self._items = [training for training in self._items if training.id != training_id]
        return len(self._items) != old_length

    def get(self, training_id: str) -> Training | None:
        return next((training for training in self._items if training.id == training_id), None)

    def filter(self, date: str = "", training_type: str = "") -> list[Training]:
        clean_date = str(date).strip()
        clean_type = str(training_type).strip().lower()

        if clean_date:
            clean_date = validate_date(clean_date)

        result: list[Training] = []
        for training in self._items:
            matches_date = training.date == clean_date if clean_date else True
            matches_type = clean_type in training.training_type.lower() if clean_type else True
            if matches_date and matches_type:
                result.append(training)
        return result

    def total_duration(self, items: Iterable[Training] | None = None) -> int:
        return sum(training.duration for training in (items if items is not None else self._items))

    def to_json_ready(self) -> list[dict[str, Any]]:
        return [training.to_dict() for training in self._items]

    @classmethod
    def from_json_ready(cls, raw_items: Iterable[Mapping[str, Any]]) -> "TrainingBook":
        return cls(Training.from_dict(raw_item) for raw_item in raw_items)
