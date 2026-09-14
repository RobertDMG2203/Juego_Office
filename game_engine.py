"""Lógica independiente de la interfaz para facilitar pruebas y edición."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


ORDER = ("primaria", "secundaria", "preparatoria")


def cumulative_shortcuts(level: str, groups: dict[str, list[dict]]) -> list[dict]:
    """Devuelve los ejercicios acumulados hasta el grado seleccionado."""
    normalized = level.strip().lower()
    if normalized not in ORDER:
        raise ValueError(f"Nivel educativo desconocido: {level}")
    result: list[dict] = []
    for name in ORDER:
        result.extend(groups.get(name, []))
        if name == normalized:
            break
    return result


def normalize_shortcut(shortcut: str) -> str:
    aliases = {
        "CONTROL": "CTRL", "CMD": "META", "COMMAND": "META",
        "RETURN": "ENTER", "ESCAPE": "ESC", "DEL": "DELETE",
        "$": "4", "%": "5",
    }
    parts = [p.strip().upper() for p in shortcut.split("+") if p.strip()]
    parts = [aliases.get(p, p) for p in parts]
    order = {"CTRL": 0, "ALT": 1, "SHIFT": 2, "META": 3}
    modifiers = sorted((p for p in parts if p in order), key=order.get)
    keys = [p for p in parts if p not in order]
    return "+".join(modifiers + keys)


def shortcut_matches(expected: str | None, actual: str) -> bool:
    return bool(expected) and normalize_shortcut(expected) == normalize_shortcut(actual)


@dataclass
class TaskSequence:
    tasks: list[dict]
    index: int = 0

    @property
    def current(self) -> dict | None:
        return self.tasks[self.index] if self.index < len(self.tasks) else None

    @property
    def complete(self) -> bool:
        return self.index >= len(self.tasks)

    def accepts(self, *, action: str | None = None, shortcut: str | None = None) -> bool:
        task = self.current
        if not task:
            return False
        accepted_shortcuts = [task.get("atajo"), *task.get("alternativos", [])]
        return (
            action is not None and task.get("accion") == action
        ) or (
            shortcut is not None
            and any(shortcut_matches(expected, shortcut) for expected in accepted_shortcuts)
        )

    def attempt(self, *, action: str | None = None, shortcut: str | None = None) -> bool:
        if not self.accepts(action=action, shortcut=shortcut):
            return False
        self.index += 1
        return True


def unique_ids(task_groups: Iterable[Iterable[dict]]) -> bool:
    ids = [item["id"] for group in task_groups for item in group]
    return len(ids) == len(set(ids))
