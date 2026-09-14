import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from game_engine import TaskSequence, cumulative_shortcuts, normalize_shortcut, shortcut_matches


def test_shortcut_normalization():
    assert normalize_shortcut("shift + ctrl + s") == "CTRL+SHIFT+S"
    assert shortcut_matches("Ctrl+C", "CONTROL+c")
    assert not shortcut_matches("Ctrl+C", "Ctrl+V")


def test_cumulative_school_levels():
    groups = {
        "primaria": [{"id": "a"}],
        "secundaria": [{"id": "b"}],
        "preparatoria": [{"id": "c"}],
    }
    assert [x["id"] for x in cumulative_shortcuts("secundaria", groups)] == ["a", "b"]


def test_task_sequence_by_action_and_shortcut():
    seq = TaskSequence([
        {"id": "a", "accion": "negrita", "atajo": "Ctrl+B"},
        {"id": "b", "accion": "centrar", "atajo": "Ctrl+E"},
    ])
    assert not seq.attempt(action="cursiva")
    assert seq.attempt(shortcut="Ctrl+B")
    assert seq.index == 1
    assert seq.attempt(action="centrar")
    assert seq.complete


def test_localized_shortcut_alternative():
    seq = TaskSequence([
        {"id": "bold", "accion": "negrita", "atajo": "Ctrl+B", "alternativos": ["Ctrl+N"]}
    ])
    assert seq.attempt(shortcut="Ctrl+N")


def test_office_tasks_expand_by_school_level():
    import config
    primary = cumulative_shortcuts("primaria", config.TAREAS_EXCEL_POR_NIVEL)
    secondary = cumulative_shortcuts("secundaria", config.TAREAS_EXCEL_POR_NIVEL)
    prep = cumulative_shortcuts("preparatoria", config.TAREAS_EXCEL_POR_NIVEL)
    assert len(primary) < len(secondary) < len(prep)
    autosum = next(task for task in primary if task["id"] == "excel_autosuma")
    assert autosum["atajo"] is None
