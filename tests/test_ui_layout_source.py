from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _class_assignments(path: Path, class_name: str) -> dict[str, object]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            values = {}
            for child in node.body:
                if isinstance(child, ast.Assign) and len(child.targets) == 1 and isinstance(child.targets[0], ast.Name):
                    try:
                        values[child.targets[0].id] = ast.literal_eval(child.value)
                    except (ValueError, TypeError):
                        pass
            return values
    raise AssertionError(f"No se encontró {class_name}")


def test_keyboard_main_rows_keep_same_logical_width():
    values = _class_assignments(ROOT / "widgets.py", "SpanishKeyboard")
    rows = values["MAIN_ROWS"]
    widths = [round(sum(float(item[2]) for item in row), 2) for row in rows]
    assert widths == [15.0, 15.0, 15.0, 15.0, 15.0]


def test_keyboard_has_separate_navigation_and_numpad_blocks():
    source = (ROOT / "widgets.py").read_text(encoding="utf-8")
    assert 'setObjectName("keyboardMainBlock")' in source
    assert 'setObjectName("keyboardNavBlock")' in source
    assert 'setObjectName("keyboardNumBlock")' in source
    assert 'num.addWidget(self._make_key("+", "NUMPLUS", compact=True), 1, 3, 2, 1)' in source
    assert 'num.addWidget(self._make_key("0", "NUM0", compact=True), 4, 0, 1, 2)' in source


def test_start_window_uses_bounded_card_and_fixed_icon():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "card.setMinimumWidth(700)" in source
    assert "card.setMaximumWidth(820)" in source
    assert "icon.setFixedSize(108, 76)" in source
    assert "self.setMinimumSize(860, 660)" in source


def test_teacher_uninstall_closes_modal_dialog_before_quitting_app():
    source = (ROOT / "teacher_dashboard.py").read_text(encoding="utf-8")
    uninstall_block = source[source.index("    def _uninstall(self):"):source.index("    def reload_data(self):")]
    assert "self.accept()" in uninstall_block
    assert "QTimer.singleShot(0, app.quit)" in uninstall_block
