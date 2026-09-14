from __future__ import annotations

import json
import os
from pathlib import Path


def base_dir() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "MisionDigital"


def _safe(value: str) -> str:
    text = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value.strip())
    return text[:60] or "sin_matricula"


class ProgressStore:
    def __init__(self, enabled: bool = True, student_id: str = "general"):
        self.enabled = enabled
        self.student_id = student_id
        self.path = base_dir() / "progreso" / f"{_safe(student_id)}.json"

    def load(self) -> dict:
        default = {"levels": [0, 0, 0, 0], "last_level": 0, "completed": False}
        if not self.enabled or not self.path.exists():
            return default
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            # Compatibilidad con el formato anterior de un solo nivel/tarea.
            if "levels" not in data:
                levels = [0, 0, 0, 0]
                level = max(0, min(int(data.get("level", 0)), 3))
                levels[level] = max(0, int(data.get("task", 0)))
                data = {"levels": levels, "last_level": level, "completed": bool(data.get("completed", False))}
            levels = list(data.get("levels", [0, 0, 0, 0]))[:4]
            levels += [0] * (4 - len(levels))
            return {
                "levels": [max(0, int(v)) for v in levels],
                "last_level": max(0, min(int(data.get("last_level", 0)), 3)),
                "completed": bool(data.get("completed", False)),
            }
        except (OSError, ValueError, TypeError):
            return default

    def save(self, levels: list[int], last_level: int, completed: bool = False) -> None:
        if not self.enabled:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        payload = {"levels": list(levels[:4]), "last_level": int(last_level), "completed": bool(completed)}
        temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        temp.replace(self.path)

    def reset(self) -> None:
        if self.path.exists():
            self.path.unlink()
