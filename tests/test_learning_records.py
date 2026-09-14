from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from session_log import SessionLogger

ROOT = Path(__file__).resolve().parents[1]


def test_wrong_exploration_is_not_saved_as_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    logger = SessionLogger({"nombre": "Ana", "matricula": "A1", "grupo": "2B"}, 2)
    task = {"id": "word_negrita", "texto": "Negrita"}
    logger.attempt(1, "Word", task, "cinta:cursiva", False)
    logger.attempt(1, "Word", task, "teclado:Ctrl+B", True)
    logger.finish(1, "salida_anticipada_profesor", task_results=[
        {"level": 2, "level_name": "Word", "task_id": "word_negrita", "task_text": "Negrita", "achieved": True},
        {"level": 2, "level_name": "Word", "task_id": "word_cursiva", "task_text": "Cursiva", "achieved": False},
    ])

    events = [json.loads(line) for line in logger.jsonl_path.read_text(encoding="utf-8").splitlines()]
    assert not any(e.get("event") == "attempt" for e in events)
    assert len([e for e in events if e.get("event") == "achievement"]) == 1
    results = [e for e in events if e.get("event") == "task_result"]
    assert [e["achieved"] for e in results] == [True, False]

    with logger.summary_path.open("r", encoding="utf-8-sig", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["logros"] == "1"
    assert row["no_logradas"] == "1"
    assert row["errores"] == "0"
    assert "precision" not in row


def test_ribbon_and_hints_offer_both_paths():
    source = (ROOT / "widgets.py").read_text(encoding="utf-8")
    assert '"word": {' in source and '"powerpoint": {' in source and '"excel": {' in source
    assert '"Fuente"' in source and '"Párrafo"' in source and '"Ordenar y filtrar"' in source
    assert 'hint = f"Usa la cinta  ·  o  {shortcut_text}"' in source


def test_dashboard_compares_many_students_and_keeps_time():
    source = (ROOT / "teacher_dashboard.py").read_text(encoding="utf-8")
    assert "class StudentComparisonChart" in source
    assert "chunk_size = 5" in source
    assert 'strftime("%d/%m/%Y %H:%M:%S")' in source
    assert 'MetricCard("Misiones logradas"' in source
