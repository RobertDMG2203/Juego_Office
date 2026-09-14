from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from pathlib import Path


def _safe(value: str) -> str:
    text = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value.strip())
    return text[:60] or "sin_matricula"


def logs_dir() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "MisionDigital" / "logs"
    base.mkdir(parents=True, exist_ok=True)
    return base


class SessionLogger:
    """Registra logros, no clics exploratorios ni combinaciones equivocadas.

    Una sesión conserva fecha y hora exactas. Cada misión conseguida se registra una
    sola vez y al cerrar la sesión se escribe un estado logrado/no logrado por tarea.
    Así el dashboard mide avance real, no una supuesta "precisión" del alumno.
    """

    def __init__(self, student: dict, total_tasks: int):
        self.student = dict(student)
        self.total_tasks = max(1, int(total_tasks))
        self.started_at = datetime.now()
        stamp = self.started_at.strftime("%Y%m%d_%H%M%S_%f")
        stem = f"{_safe(student.get('matricula', ''))}_{stamp}"
        self.jsonl_path = logs_dir() / f"{stem}.jsonl"
        self.summary_path = logs_dir() / "resumen_sesiones.csv"
        self.attempts = 0  # compatibilidad: ahora equivale a logros registrados en la sesión
        self.correct = 0
        self.incorrect = 0
        self.achievements: set[str] = set()
        self._event("session_start")

    def _event(self, event_type: str, **payload) -> None:
        record = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "event": event_type,
            "student": self.student,
            **payload,
        }
        with self.jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def attempt(self, level: int, level_name: str, task: dict | None, answer: str, correct: bool) -> None:
        """Conserva la API previa, pero ignora por completo intentos incorrectos."""
        if not correct or not task:
            return
        task_id = str(task.get("id", ""))
        if task_id and task_id in self.achievements:
            return
        if task_id:
            self.achievements.add(task_id)
        self.attempts += 1
        self.correct += 1
        self._event(
            "achievement",
            level=level + 1,
            level_name=level_name,
            task_id=task.get("id"),
            task_text=task.get("texto"),
            method=answer,
            achieved=True,
        )

    def level_completed(self, level: int, level_name: str) -> None:
        self._event("level_completed", level=level + 1, level_name=level_name)

    def final_grade(self, completed_tasks: int) -> int:
        return round(max(0, min(completed_tasks, self.total_tasks)) * 100 / self.total_tasks)

    def finish(self, completed_tasks: int, reason: str, task_results: list[dict] | None = None) -> dict:
        ended = datetime.now()
        grade = self.final_grade(completed_tasks)
        achieved = max(0, min(int(completed_tasks), self.total_tasks))
        not_achieved = max(0, self.total_tasks - achieved)

        if task_results:
            for result in task_results:
                self._event("task_result", **result)

        summary = {
            "nombre": self.student.get("nombre", ""),
            "matricula": self.student.get("matricula", ""),
            "grupo": self.student.get("grupo", ""),
            "nivel_educativo": self.student.get("nivel_educativo", ""),
            "inicio": self.started_at.isoformat(timespec="seconds"),
            "fin": ended.isoformat(timespec="seconds"),
            "motivo_salida": reason,
            # Se mantienen estos nombres para poder importar historiales de versiones previas.
            # Ya no representan clics/errores, sino misiones conseguidas.
            "intentos": achieved,
            "aciertos": achieved,
            "errores": 0,
            "logros": achieved,
            "no_logradas": not_achieved,
            "tareas_totales": self.total_tasks,
            "calificacion": grade,
            "completado": grade,
        }
        self._event("session_end", **summary)
        self._append_summary(summary)
        return summary

    def _append_summary(self, summary: dict) -> None:
        existing_rows: list[dict] = []
        fields = list(summary.keys())
        if self.summary_path.exists():
            try:
                with self.summary_path.open("r", encoding="utf-8-sig", newline="") as handle:
                    reader = csv.DictReader(handle)
                    existing_rows = list(reader)
                    for field in reader.fieldnames or []:
                        if field not in fields:
                            fields.append(field)
                    for field in summary:
                        if field not in fields:
                            fields.append(field)
            except OSError:
                existing_rows = []
        # Reescribir permite convivir con CSV antiguos que aún tenían 'precision'.
        with self.summary_path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(existing_rows)
            writer.writerow(summary)
