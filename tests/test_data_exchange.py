from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_exchange import export_local_results, import_result_packages, load_combined_results
from session_log import logs_dir


def _write_summary(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_export_import_and_deduplicate(tmp_path, monkeypatch):
    student_root = tmp_path / "student"
    monkeypatch.setenv("LOCALAPPDATA", str(student_root))
    rows = [{
        "nombre": "Ana", "matricula": "A-01", "grupo": "2B", "nivel_educativo": "secundaria",
        "inicio": "2026-09-01T10:00:00", "fin": "2026-09-01T10:30:00", "motivo_salida": "sesion_completada",
        "intentos": "10", "aciertos": "9", "errores": "1", "logros": "9", "tareas_totales": "10",
        "calificacion": "90", "precision": "90",
    }]
    _write_summary(logs_dir() / "resumen_sesiones.csv", rows)
    log = logs_dir() / "A-01_20260901_100000.jsonl"
    log.write_text(json.dumps({
        "timestamp": "2026-09-01T10:01:00", "event": "attempt",
        "student": {"nombre": "Ana", "matricula": "A-01", "grupo": "2B"},
        "level_name": "Word", "correct": True,
    }) + "\n", encoding="utf-8")

    export_root = tmp_path / "exports"
    exported = export_local_results(export_root)
    assert exported["students"] == 1
    package = exported["packages"][0]
    assert (package / "manifest.json").exists()
    assert (package / "resultados.csv").exists()

    teacher_root = tmp_path / "teacher"
    monkeypatch.setenv("LOCALAPPDATA", str(teacher_root))
    first = import_result_packages(export_root)
    second = import_result_packages(export_root)
    assert first["rows_added"] == 1
    assert second["rows_added"] == 0
    assert second["duplicates"] == 1
    combined = load_combined_results()
    assert len(combined) == 1
    assert combined[0]["matricula"] == "A-01"
    assert combined[0]["origen"] == "importado"
