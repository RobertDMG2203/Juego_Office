from __future__ import annotations

from functools import partial

import config
from game_engine import cumulative_shortcuts

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextListFormat
from PySide6.QtWidgets import (
    QAbstractItemView, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel,
    QGraphicsDropShadowEffect, QPushButton, QSizePolicy, QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit,
    QToolButton, QVBoxLayout, QWidget,
)


class MissionPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.hints_enabled = True
        self.setObjectName("mission")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 16, 22, 16)
        top = QHBoxLayout()
        self.eyebrow = QLabel("MISIÓN ACTUAL")
        self.eyebrow.setObjectName("eyebrow")
        self.counter = QLabel()
        self.counter.setObjectName("eyebrow")
        top.addWidget(self.eyebrow)
        top.addStretch()
        top.addWidget(self.counter)
        layout.addLayout(top)
        row = QHBoxLayout()
        self.instruction = QLabel()
        self.instruction.setObjectName("instruction")
        self.instruction.setWordWrap(True)
        self.badge = QLabel()
        self.badge.setObjectName("shortcutBadge")
        row.addWidget(self.instruction, 1)
        row.addWidget(self.badge)
        layout.addLayout(row)

    def set_hints_enabled(self, enabled: bool):
        self.hints_enabled = bool(enabled)
        if not self.hints_enabled:
            self.badge.hide()

    def set_task(self, task: dict, index: int, total: int):
        self.eyebrow.setText("MISIÓN ACTUAL")
        self.instruction.setText(task["texto"])
        self.counter.setText(f"{index + 1} de {total}")
        shortcut = task.get("atajo")
        shortcuts = [value for value in [shortcut, *task.get("alternativos", [])] if value]
        shortcut_text = " / ".join(shortcuts)
        has_ribbon = bool(task.get("accion"))
        if has_ribbon and shortcut_text:
            hint = f"Usa la cinta  ·  o  {shortcut_text}"
        elif has_ribbon:
            hint = "Usa la cinta"
        elif shortcut_text:
            hint = f"Usa {shortcut_text}"
        else:
            hint = "Explora las herramientas"
        self.badge.setText(hint)
        self.badge.setVisible(self.hints_enabled)

    def set_completed(self, level_name: str, total: int):
        self.eyebrow.setText("NIVEL COMPLETADO")
        self.instruction.setText(f"Ya completaste {level_name}. Puedes practicar otro nivel desde la barra superior.")
        self.counter.setText(f"{total} de {total}")
        self.badge.setText("✓ Logro obtenido")
        self.badge.setVisible(True)


class SpanishKeyboard(QWidget):
    shortcut_pressed = Signal(str)

    # Distribución latinoamericana organizada como un teclado físico completo.
    # El bloque alfanumérico, navegación/flechas y numérico son independientes;
    # así nunca terminan debajo de la barra espaciadora al redimensionar la ventana.
    FUNCTION_ROW = [
        ("Esc", "ESC", 1.15), ("F1", "F1", 1), ("F2", "F2", 1), ("F3", "F3", 1),
        ("F4", "F4", 1), ("F5", "F5", 1), ("F6", "F6", 1), ("F7", "F7", 1),
        ("F8", "F8", 1), ("F9", "F9", 1), ("F10", "F10", 1), ("F11", "F11", 1),
        ("F12", "F12", 1), ("Impr\nPant", "PRINTSCREEN", 1.25),
        ("Bloq\nDespl", "SCROLLLOCK", 1.25), ("Pausa", "PAUSE", 1.15),
    ]

    MAIN_ROWS = [
        [("°\n|", "GRAVE", 1), ("1\n!", "1", 1), ("2\n\"", "2", 1), ("3\n#", "3", 1),
         ("4\n$", "4", 1), ("5\n%", "5", 1), ("6\n&", "6", 1), ("7\n/", "7", 1),
         ("8\n(", "8", 1), ("9\n)", "9", 1), ("0\n=", "0", 1), ("'\n?", "APOSTROPHE", 1),
         ("¿\n¡", "QUESTION", 1), ("Retroceso", "BACKSPACE", 2)],
        [("Tab", "TAB", 1.5), ("Q", "Q", 1), ("W", "W", 1), ("E", "E", 1), ("R", "R", 1),
         ("T", "T", 1), ("Y", "Y", 1), ("U", "U", 1), ("I", "I", 1), ("O", "O", 1),
         ("P", "P", 1), ("´\n¨", "ACUTE", 1), ("+\n*", "PLUS", 1), ("Enter", "ENTER", 1.5)],
        [("Bloq\nMayús", "CAPSLOCK", 1.7), ("A", "A", 1), ("S", "S", 1), ("D", "D", 1),
         ("F", "F", 1), ("G", "G", 1), ("H", "H", 1), ("J", "J", 1), ("K", "K", 1),
         ("L", "L", 1), ("Ñ", "Ñ", 1), ("{\n[", "BRACKETLEFT", 1), ("}\n]", "BRACKETRIGHT", 1),
         ("Enter", "ENTER", 1.3)],
        [("Shift", "SHIFT", 2), ("<\n>", "LESS", 1), ("Z", "Z", 1), ("X", "X", 1),
         ("C", "C", 1), ("V", "V", 1), ("B", "B", 1), ("N", "N", 1), ("M", "M", 1),
         (",\n;", "COMMA", 1), (".\n:", "PERIOD", 1), ("-\n_", "MINUS", 1), ("Shift", "SHIFT", 2)],
        [("Ctrl", "CTRL", 1.4), ("Win", "META", 1.2), ("Alt", "ALT", 1.2),
         ("Espacio", "SPACE", 7.3), ("Alt Gr", "ALTGR", 1.3), ("Menú", "MENU", 1.2),
         ("Ctrl", "CTRL", 1.4)],
    ]

    def __init__(self):
        super().__init__()
        self.active_modifiers: set[str] = set()
        self.buttons: dict[str, list[QPushButton]] = {}
        self.effects: dict[QPushButton, QGraphicsDropShadowEffect] = {}
        self.setObjectName("spanishKeyboard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(350)
        self.setMaximumHeight(430)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 12)
        outer.setSpacing(10)

        function_frame = QFrame()
        function_frame.setObjectName("keyboardFunctionBlock")
        function_layout = QHBoxLayout(function_frame)
        function_layout.setContentsMargins(6, 6, 6, 6)
        function_layout.setSpacing(5)
        for index, (label, code, width) in enumerate(self.FUNCTION_ROW):
            # pequeños huecos visuales como en un teclado real: Esc | F1-F4 | F5-F8 | F9-F12 | sistema
            if index in (1, 5, 9, 13):
                function_layout.addSpacing(8)
            button = self._make_key(label, code, compact=True)
            function_layout.addWidget(button, max(10, int(width * 10)))
        outer.addWidget(function_frame)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(12)

        main_frame = QFrame()
        main_frame.setObjectName("keyboardMainBlock")
        main_grid = QGridLayout(main_frame)
        main_grid.setContentsMargins(7, 7, 7, 7)
        main_grid.setHorizontalSpacing(5)
        main_grid.setVerticalSpacing(6)
        unit = 10
        max_columns = 150
        for row_index, row_data in enumerate(self.MAIN_ROWS):
            column = 0
            for label, code, width in row_data:
                span = max(1, int(round(width * unit)))
                button = self._make_key(label, code)
                main_grid.addWidget(button, row_index, column, 1, span)
                column += span
            if column < max_columns:
                # Mantiene todas las filas con la misma anchura lógica sin deformar las teclas.
                spacer = QWidget()
                spacer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                main_grid.addWidget(spacer, row_index, column, 1, max_columns - column)
        for col in range(max_columns):
            main_grid.setColumnStretch(col, 1)
        for row in range(len(self.MAIN_ROWS)):
            main_grid.setRowStretch(row, 1)
        body.addWidget(main_frame, 15)

        nav_frame = QFrame()
        nav_frame.setObjectName("keyboardNavBlock")
        nav = QGridLayout(nav_frame)
        nav.setContentsMargins(7, 7, 7, 7)
        nav.setHorizontalSpacing(5)
        nav.setVerticalSpacing(6)
        nav_items = [
            ("Insert", "INSERT", 0, 0), ("Inicio", "HOME", 0, 1), ("Re Pág", "PAGEUP", 0, 2),
            ("Supr", "DELETE", 1, 0), ("Fin", "END", 1, 1), ("Av Pág", "PAGEDOWN", 1, 2),
            ("↑", "UP", 3, 1), ("←", "LEFT", 4, 0), ("↓", "DOWN", 4, 1), ("→", "RIGHT", 4, 2),
        ]
        for label, code, row, col in nav_items:
            nav.addWidget(self._make_key(label, code, compact=True), row, col)
        # La fila vacía separa navegación y cursores igual que en un teclado físico.
        nav.setRowMinimumHeight(2, 9)
        for col in range(3):
            nav.setColumnStretch(col, 1)
        for row in (0, 1, 3, 4):
            nav.setRowStretch(row, 1)
        body.addWidget(nav_frame, 3)

        num_frame = QFrame()
        num_frame.setObjectName("keyboardNumBlock")
        num = QGridLayout(num_frame)
        num.setContentsMargins(7, 7, 7, 7)
        num.setHorizontalSpacing(5)
        num.setVerticalSpacing(6)
        num.addWidget(self._make_key("Bloq\nNum", "NUMLOCK", compact=True), 0, 0)
        num.addWidget(self._make_key("/", "NUMDIV", compact=True), 0, 1)
        num.addWidget(self._make_key("*", "NUMMUL", compact=True), 0, 2)
        num.addWidget(self._make_key("-", "NUMMINUS", compact=True), 0, 3)
        num.addWidget(self._make_key("7", "NUM7", compact=True), 1, 0)
        num.addWidget(self._make_key("8", "NUM8", compact=True), 1, 1)
        num.addWidget(self._make_key("9", "NUM9", compact=True), 1, 2)
        num.addWidget(self._make_key("+", "NUMPLUS", compact=True), 1, 3, 2, 1)
        num.addWidget(self._make_key("4", "NUM4", compact=True), 2, 0)
        num.addWidget(self._make_key("5", "NUM5", compact=True), 2, 1)
        num.addWidget(self._make_key("6", "NUM6", compact=True), 2, 2)
        num.addWidget(self._make_key("1", "NUM1", compact=True), 3, 0)
        num.addWidget(self._make_key("2", "NUM2", compact=True), 3, 1)
        num.addWidget(self._make_key("3", "NUM3", compact=True), 3, 2)
        num.addWidget(self._make_key("Enter", "NUMENTER", compact=True), 3, 3, 2, 1)
        num.addWidget(self._make_key("0", "NUM0", compact=True), 4, 0, 1, 2)
        num.addWidget(self._make_key(".", "NUMDECIMAL", compact=True), 4, 2)
        for col in range(4):
            num.setColumnStretch(col, 1)
        for row in range(5):
            num.setRowStretch(row, 1)
        body.addWidget(num_frame, 4)

        outer.addLayout(body)

    def _make_key(self, label: str, code: str, compact: bool = False) -> QPushButton:
        button = QPushButton(label)
        button.setProperty("class", "key")
        button.setProperty("compact", compact)
        button.setObjectName("keyboardKey")
        button.setMinimumHeight(42 if compact else 46)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        glow = QGraphicsDropShadowEffect(button)
        glow.setBlurRadius(18)
        glow.setColor(QColor("#0a9fbe"))
        glow.setOffset(0, 4)
        button.setGraphicsEffect(glow)
        self.effects[button] = glow
        button.clicked.connect(partial(self._click, code))
        self.buttons.setdefault(code, []).append(button)
        return button

    def _click(self, code: str):
        if code in {"CTRL", "ALT", "SHIFT", "META"}:
            if code in self.active_modifiers:
                self.active_modifiers.remove(code)
            else:
                self.active_modifiers.add(code)
            self._refresh_modifiers()
            return
        if code == "ALTGR":
            self.active_modifiers.update({"CTRL", "ALT"})
            self._refresh_modifiers()
            return
        names = [name for name in ("CTRL", "ALT", "SHIFT", "META") if name in self.active_modifiers]
        visible_code = {"BACKSPACE": "BACKSPACE", "SPACE": "SPACE", "PLUS": "+", "MINUS": "-"}.get(code, code)
        chord = "+".join(names + [visible_code])
        self.shortcut_pressed.emit(chord)
        self.flash(code)
        self.active_modifiers.clear()
        self._refresh_modifiers()

    def _refresh_modifiers(self):
        for code in ("CTRL", "ALT", "SHIFT", "META"):
            for button in self.buttons.get(code, []):
                button.setProperty("active", code in self.active_modifiers)
                button.style().unpolish(button)
                button.style().polish(button)

    def flash(self, code: str, duration_ms: int = 150):
        code = code.upper()
        for button in self.buttons.get(code, []):
            button.setProperty("physical", True)
            button.style().unpolish(button)
            button.style().polish(button)
            effect = self.effects.get(button)
            if effect:
                effect.setBlurRadius(40)
                effect.setColor(QColor("#68f3ff"))
                effect.setOffset(0, 1)
            QTimer.singleShot(duration_ms, lambda b=button: self._clear_flash(b))

    def _clear_flash(self, button: QPushButton):
        button.setProperty("physical", False)
        button.style().unpolish(button)
        button.style().polish(button)
        effect = self.effects.get(button)
        if effect:
            effect.setBlurRadius(18)
            effect.setColor(QColor("#0a9fbe"))
            effect.setOffset(0, 4)

    def animate_shortcut(self, shortcut: str):
        aliases = {
            "CONTROL": "CTRL", "META": "META", "ESC": "ESC", "ESCAPE": "ESC",
            "RETURN": "ENTER", "ENTER": "ENTER", "BACKSPACE": "BACKSPACE",
            "SPACE": "SPACE", "+": "PLUS", "-": "MINUS",
        }
        parts = [p.strip().upper() for p in shortcut.replace("Meta", "META").split("+") if p.strip()]
        for part in parts:
            self.flash(aliases.get(part, part))


class KeyboardLevel(QWidget):
    shortcut_pressed = Signal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 12)
        title = QLabel("Teclado latinoamericano")
        title.setStyleSheet("font-size:18px;font-weight:700;color:#eaf6ff")
        subtitle = QLabel("Forma el atajo con el teclado físico o selecciona los modificadores y la tecla en pantalla.")
        subtitle.setStyleSheet("color:#7f91a8")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        self.keyboard = SpanishKeyboard()
        self.keyboard.shortcut_pressed.connect(self.shortcut_pressed)
        layout.addStretch(1)
        layout.addWidget(self.keyboard)
        layout.addStretch(1)


class Ribbon(QWidget):
    """Cinta visual inspirada en Office.

    La meta es que el alumnado se familiarice con la ubicación típica de las
    herramientas en Word, PowerPoint y Excel. Muchas acciones son visuales o
    dummy, pero la distribución de pestañas, grupos y jerarquía se mantiene
    cercana a Office para favorecer el reconocimiento espacial.
    """

    action_requested = Signal(str)

    def __init__(self, tabs: dict[str, list[dict]], accent: str, app_kind: str):
        super().__init__()
        self.setObjectName("officeRibbon")
        self.setProperty("officeApp", app_kind)
        self.setProperty("accent", accent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        chrome = QFrame()
        chrome.setObjectName("officeChrome")
        chrome_layout = QHBoxLayout(chrome)
        chrome_layout.setContentsMargins(10, 5, 10, 5)
        chrome_layout.setSpacing(6)
        for symbol, label in (("💾", "Guardar"), ("↶", "Deshacer"), ("↷", "Rehacer")):
            btn = QToolButton()
            btn.setObjectName("quickAccessTool")
            btn.setText(symbol)
            btn.setToolTip(label)
            btn.setEnabled(False)
            chrome_layout.addWidget(btn)
        chrome_layout.addSpacing(10)
        title = QLabel("Cinta de opciones")
        title.setObjectName("officeChromeTitle")
        chrome_layout.addWidget(title)
        chrome_layout.addStretch(1)
        layout.addWidget(chrome)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("officeRibbonTabs")
        self.tabs.setDocumentMode(True)
        self.tabs.setUsesScrollButtons(True)

        for tab_name, groups in tabs.items():
            page = QFrame()
            page.setObjectName("officeRibbonPage")
            page_layout = QHBoxLayout(page)
            page_layout.setContentsMargins(8, 6, 8, 5)
            page_layout.setSpacing(0)

            for group_index, group in enumerate(groups):
                frame = self._build_group(group)
                page_layout.addWidget(frame)
                if group_index < len(groups) - 1:
                    separator = QFrame()
                    separator.setObjectName("ribbonSeparator")
                    separator.setFrameShape(QFrame.Shape.VLine)
                    page_layout.addWidget(separator)

            page_layout.addStretch(1)
            self.tabs.addTab(page, tab_name)

        for index in range(self.tabs.count()):
            if self.tabs.tabText(index) == "Inicio":
                self.tabs.setCurrentIndex(index)
                break

        layout.addWidget(self.tabs)

    def _build_group(self, group: dict) -> QFrame:
        frame = QFrame()
        frame.setObjectName("ribbonGroup")
        group_layout = QVBoxLayout(frame)
        group_layout.setContentsMargins(7, 5, 7, 3)
        group_layout.setSpacing(3)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(4)
        grid.setVerticalSpacing(3)

        row_cursor = 0
        column = 0
        for item in group.get("items", []):
            size = item.get("size", "small")
            button = self._make_button(item)
            if size == "large":
                if row_cursor != 0:
                    column += 1
                    row_cursor = 0
                grid.addWidget(button, 0, column, 3, 1)
                column += 1
            else:
                grid.addWidget(button, row_cursor, column, 1, 1)
                row_cursor += 1
                if row_cursor >= 3:
                    row_cursor = 0
                    column += 1

        for col in range(max(1, column + 1)):
            grid.setColumnMinimumWidth(col, 64)
        group_layout.addLayout(grid)

        group_label = QLabel(group["name"])
        group_label.setObjectName("ribbonGroupLabel")
        group_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        group_layout.addWidget(group_label)
        return frame

    def _make_button(self, item: dict) -> QToolButton:
        btn = QToolButton()
        btn.setObjectName("ribbonTool")
        size = item.get("size", "small")
        btn.setProperty("size", size)
        btn.setProperty("dummy", not bool(item.get("action")))
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        btn.setAutoRaise(False)
        btn.setCheckable(False)
        symbol = item.get("symbol", "□")
        label = item.get("label", "Herramienta")
        if size == "large":
            btn.setText(f"{symbol}\n{label.replace(' ', '\n', 1)}")
            btn.setMinimumSize(74, 88)
            btn.setMaximumSize(90, 110)
        else:
            compact_label = label if len(label) <= 12 else label.replace(' ', '\n', 1)
            btn.setText(f"{symbol} {compact_label}")
            btn.setMinimumSize(66, 26)
            btn.setMaximumHeight(28)
        tooltip = label
        if item.get("shortcut"):
            tooltip += f" ({item['shortcut']})"
        if not item.get("action"):
            tooltip += " · visual"
        btn.setToolTip(tooltip)
        action = item.get("action")
        if action:
            btn.clicked.connect(partial(self.action_requested.emit, action))
        else:
            btn.clicked.connect(lambda checked=False: None)
        return btn


class OfficeLevel(QWidget):
    action_requested = Signal(str)

    def __init__(self, accent: str, app_kind: str, tabs: dict[str, list[dict]]):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 8)
        layout.setSpacing(0)
        self.appbar = QLabel()
        self.appbar.setObjectName("officeAppBar")
        self.appbar.setProperty("officeApp", app_kind)
        self.appbar.setStyleSheet(
            f"background:{accent};color:white;padding:8px 14px;font-weight:700;"
            "border-top-left-radius:8px;border-top-right-radius:8px"
        )
        layout.addWidget(self.appbar)
        self.ribbon = Ribbon(tabs, accent, app_kind)
        self.ribbon.action_requested.connect(self._perform)
        layout.addWidget(self.ribbon)
        self.workspace = QWidget()
        self.workspace.setObjectName("officeWorkspace")
        layout.addWidget(self.workspace, 1)

    def _perform(self, action: str):
        self.apply_visual(action)
        self.action_requested.emit(action)

    def apply_visual(self, action: str):
        pass


def _allowed_actions(level: str, groups: dict[str, list[dict]]) -> set[str]:
    return {str(task.get("accion", "")) for task in cumulative_shortcuts(level, groups) if task.get("accion")}


def _filter_tabs(tabs: dict[str, list[tuple[str, str, str]]], allowed: set[str]) -> dict[str, list[tuple[str, str, str]]]:
    filtered: dict[str, list[tuple[str, str, str]]] = {}
    for name, tools in tabs.items():
        kept = [tool for tool in tools if tool[2] in allowed]
        if kept:
            filtered[name] = kept
    return filtered


def _btn(symbol: str, label: str, action: str | None = None, size: str = "small", shortcut: str | None = None) -> dict:
    return {"symbol": symbol, "label": label, "action": action, "size": size, "shortcut": shortcut}


def _word_ribbon_tabs() -> dict[str, list[dict]]:
    return {
        "Archivo": [
            {"name": "Documento", "items": [
                _btn("＋", "Nuevo", None, "large", "Ctrl+N"),
                _btn("⇪", "Abrir", None, "small", "Ctrl+O"),
                _btn("💾", "Guardar", None, "small", "Ctrl+S"),
                _btn("💾", "Guardar como", None, "small", "Ctrl+Shift+S"),
                _btn("🖨", "Imprimir", "imprimir", "large", "Ctrl+P"),
                _btn("✕", "Cerrar", None, "small", "Ctrl+W"),
            ]},
        ],
        "Inicio": [
            {"name": "Portapapeles", "items": [
                _btn("📋", "Pegar", None, "large", "Ctrl+V"),
                _btn("✂", "Cortar", None, "small", "Ctrl+X"),
                _btn("⎘", "Copiar", None, "small", "Ctrl+C"),
                _btn("🖌", "Copiar formato", None, "small"),
            ]},
            {"name": "Fuente", "items": [
                _btn("Aa", "Fuente", None, "small"),
                _btn("12", "Tamaño", None, "small"),
                _btn("A↑", "Aumentar fuente", "aumentar_fuente", "small", "Ctrl+Shift+>"),
                _btn("A↓", "Disminuir fuente", None, "small"),
                _btn("B", "Negrita", "negrita", "small", "Ctrl+B / Ctrl+N"),
                _btn("I", "Cursiva", "cursiva", "small", "Ctrl+I / Ctrl+K"),
                _btn("U", "Subrayado", "subrayado", "small", "Ctrl+U / Ctrl+S"),
                _btn("ab", "Tachado", None, "small"),
                _btn("A▾", "Color de fuente", "color_fuente", "small"),
                _btn("🖍", "Resaltar", "resaltar", "small"),
            ]},
            {"name": "Párrafo", "items": [
                _btn("•", "Viñetas", "vinetas", "small"),
                _btn("1.", "Numeración", None, "small"),
                _btn("≣", "Lista multinivel", None, "small"),
                _btn("←", "Disminuir sangría", None, "small"),
                _btn("→", "Aumentar sangría", None, "small"),
                _btn("⇤", "Alinear izquierda", "izquierda", "small", "Ctrl+L / Ctrl+Q"),
                _btn("↔", "Centrar", "centrar", "small", "Ctrl+E / Ctrl+T"),
                _btn("⇥", "Alinear derecha", None, "small"),
                _btn("☰", "Justificar", "justificar", "small", "Ctrl+J"),
                _btn("↕", "Interlineado", "interlineado", "small"),
                _btn("▦", "Bordes", None, "small"),
                _btn("░", "Sombreado", None, "small"),
            ]},
            {"name": "Estilos", "items": [
                _btn("N", "Normal", None, "large"),
                _btn("T1", "Título 1", None, "small"),
                _btn("T2", "Título 2", None, "small"),
                _btn("É", "Énfasis", None, "small"),
            ]},
            {"name": "Edición", "items": [
                _btn("🔎", "Buscar", None, "large", "Ctrl+F"),
                _btn("⇄", "Reemplazar", None, "small", "Ctrl+H"),
                _btn("☑", "Seleccionar", None, "small"),
            ]},
        ],
        "Insertar": [
            {"name": "Páginas", "items": [
                _btn("▤", "Portada", None, "large"),
                _btn("📄", "Página en blanco", None, "small"),
                _btn("↵", "Salto de página", None, "small"),
            ]},
            {"name": "Tablas", "items": [
                _btn("▦", "Tabla", "tabla", "large"),
            ]},
            {"name": "Ilustraciones", "items": [
                _btn("🖼", "Imágenes", None, "large"),
                _btn("○", "Formas", None, "small"),
                _btn("◆", "Iconos", None, "small"),
            ]},
            {"name": "Vínculos", "items": [
                _btn("↗", "Hipervínculo", "hipervinculo", "large", "Ctrl+K"),
                _btn("🔖", "Marcador", None, "small"),
                _btn("⇢", "Referencia cruzada", None, "small"),
            ]},
            {"name": "Encabezado y pie", "items": [
                _btn("▤", "Encabezado", "encabezado", "large"),
                _btn("▁", "Pie de página", None, "small"),
                _btn("#", "Número de página", None, "small"),
            ]},
            {"name": "Texto", "items": [
                _btn("T", "Cuadro de texto", None, "small"),
                _btn("A", "WordArt", None, "small"),
                _btn("L", "Letra capital", None, "small"),
            ]},
        ],
        "Disposición": [
            {"name": "Configurar página", "items": [
                _btn("▭", "Márgenes", None, "small"),
                _btn("↕", "Orientación", None, "small"),
                _btn("A4", "Tamaño", None, "small"),
                _btn("▥", "Columnas", "columnas", "large"),
                _btn("⏎", "Saltos", None, "small"),
            ]},
            {"name": "Párrafo", "items": [
                _btn("↔", "Sangría", None, "small"),
                _btn("↕", "Espaciado", None, "small"),
            ]},
            {"name": "Organizar", "items": [
                _btn("⇅", "Posición", None, "small"),
                _btn("⇆", "Ajustar texto", None, "small"),
                _btn("⤒", "Traer adelante", None, "small"),
                _btn("⤓", "Enviar atrás", None, "small"),
            ]},
        ],
        "Referencias": [
            {"name": "Tabla de contenido", "items": [
                _btn("≡", "Tabla de contenido", None, "large"),
                _btn("✚", "Agregar texto", None, "small"),
                _btn("↻", "Actualizar tabla", None, "small"),
            ]},
            {"name": "Notas al pie", "items": [
                _btn("¹", "Insertar nota al pie", None, "small"),
                _btn("²", "Insertar nota al final", None, "small"),
            ]},
        ],
        "Revisar": [
            {"name": "Revisión", "items": [
                _btn("ABC", "Ortografía", None, "large"),
                _btn("💬", "Comentarios", None, "small"),
                _btn("✓", "Control de cambios", None, "small"),
            ]},
        ],
        "Vista": [
            {"name": "Vistas", "items": [
                _btn("📖", "Modo lectura", None, "small"),
                _btn("📝", "Diseño de impresión", None, "small"),
                _btn("🌐", "Diseño web", None, "small"),
            ]},
            {"name": "Mostrar", "items": [
                _btn("☑", "Regla", None, "small"),
                _btn("☑", "Panel de navegación", None, "small"),
            ]},
        ],
    }


def _powerpoint_ribbon_tabs() -> dict[str, list[dict]]:
    return {
        "Archivo": [
            {"name": "Presentación", "items": [
                _btn("＋", "Nuevo", None, "large", "Ctrl+N"),
                _btn("⇪", "Abrir", None, "small", "Ctrl+O"),
                _btn("💾", "Guardar", None, "small", "Ctrl+S"),
                _btn("🖨", "Imprimir", None, "large", "Ctrl+P"),
            ]},
        ],
        "Inicio": [
            {"name": "Portapapeles", "items": [
                _btn("📋", "Pegar", None, "large"),
                _btn("✂", "Cortar", None, "small"),
                _btn("⎘", "Copiar", None, "small"),
                _btn("🖌", "Copiar formato", None, "small"),
            ]},
            {"name": "Diapositivas", "items": [
                _btn("＋", "Nueva diapositiva", "nueva_diapositiva", "large", "Ctrl+M"),
                _btn("▤", "Diseño", "diseno", "small"),
                _btn("⟲", "Restablecer", None, "small"),
                _btn("⧉", "Duplicar", "duplicar", "small", "Ctrl+Shift+D"),
            ]},
            {"name": "Fuente", "items": [
                _btn("Aa", "Fuente", None, "small"),
                _btn("12", "Tamaño", None, "small"),
                _btn("B", "Negrita", "negrita", "small", "Ctrl+B / Ctrl+N"),
                _btn("I", "Cursiva", None, "small"),
                _btn("U", "Subrayado", None, "small"),
                _btn("A▾", "Color", None, "small"),
            ]},
            {"name": "Párrafo", "items": [
                _btn("•", "Viñetas", None, "small"),
                _btn("1.", "Numeración", None, "small"),
                _btn("↔", "Centrar", "centrar", "small", "Ctrl+E / Ctrl+T"),
                _btn("☰", "Justificar", None, "small"),
                _btn("↕", "Interlineado", None, "small"),
            ]},
            {"name": "Dibujo", "items": [
                _btn("○", "Formas", "insertar_forma", "large"),
                _btn("⇔", "Alinear", "alinear_objetos", "small"),
                _btn("⤓", "Enviar al fondo", "enviar_fondo", "small"),
            ]},
            {"name": "Edición", "items": [
                _btn("🔎", "Buscar", None, "large"),
                _btn("⇄", "Reemplazar", None, "small"),
            ]},
        ],
        "Insertar": [
            {"name": "Tablas", "items": [
                _btn("▦", "Tabla", None, "large"),
            ]},
            {"name": "Imágenes", "items": [
                _btn("🖼", "Imágenes", "imagen", "large"),
                _btn("🗂", "Álbum", None, "small"),
                _btn("◆", "Iconos", None, "small"),
            ]},
            {"name": "Ilustraciones", "items": [
                _btn("○", "Formas", "insertar_forma", "large"),
                _btn("▨", "SmartArt", None, "small"),
                _btn("▥", "Gráfico", None, "small"),
            ]},
            {"name": "Texto", "items": [
                _btn("T", "Cuadro de texto", None, "large"),
                _btn("A", "WordArt", None, "small"),
                _btn("#", "Encabezado y pie", None, "small"),
            ]},
            {"name": "Multimedia", "items": [
                _btn("🎞", "Video", None, "small"),
                _btn("🔊", "Audio", None, "small"),
                _btn("🖥", "Grabación", None, "small"),
            ]},
        ],
        "Diseño": [
            {"name": "Temas", "items": [
                _btn("▧", "Temas", None, "large"),
                _btn("◫", "Variantes", None, "small"),
                _btn("▣", "Tamaño de diapositiva", None, "small"),
                _btn("🎨", "Formato del fondo", None, "small"),
            ]},
        ],
        "Transiciones": [
            {"name": "Vista previa", "items": [
                _btn("▶", "Vista previa", None, "large"),
            ]},
            {"name": "Transición a esta diapositiva", "items": [
                _btn("↝", "Transición", "transicion", "large"),
                _btn("⋯", "Opciones", None, "small"),
            ]},
            {"name": "Intervalos", "items": [
                _btn("🖱", "Al hacer clic", None, "small"),
                _btn("⏱", "Después de", None, "small"),
            ]},
        ],
        "Animaciones": [
            {"name": "Vista previa", "items": [
                _btn("▶", "Vista previa", None, "large"),
            ]},
            {"name": "Animación", "items": [
                _btn("✦", "Agregar animación", "animacion", "large"),
                _btn("☷", "Panel de animación", None, "small"),
                _btn("↻", "Reordenar", None, "small"),
            ]},
            {"name": "Intervalos", "items": [
                _btn("▷", "Iniciar", None, "small"),
                _btn("⏲", "Duración", None, "small"),
                _btn("↺", "Repetir", None, "small"),
            ]},
        ],
        "Presentación": [
            {"name": "Iniciar presentación", "items": [
                _btn("▶", "Desde el principio", "presentar", "large", "F5"),
                _btn("▷", "Desde la actual", "presentar_actual", "large", "Shift+F5"),
            ]},
            {"name": "Configurar", "items": [
                _btn("⚙", "Configurar presentación", None, "small"),
                _btn("⌲", "Ensayar intervalos", None, "small"),
                _btn("🖥", "Monitores", None, "small"),
            ]},
        ],
        "Vista": [
            {"name": "Vistas de presentación", "items": [
                _btn("▤", "Normal", None, "small"),
                _btn("☰", "Clasificador", None, "small"),
                _btn("📖", "Página de notas", "notas", "small"),
            ]},
            {"name": "Mostrar", "items": [
                _btn("☑", "Regla", None, "small"),
                _btn("☑", "Guías", None, "small"),
                _btn("☑", "Cuadrícula", None, "small"),
            ]},
        ],
    }


def _excel_ribbon_tabs() -> dict[str, list[dict]]:
    return {
        "Archivo": [
            {"name": "Libro", "items": [
                _btn("＋", "Nuevo", None, "large", "Ctrl+N"),
                _btn("⇪", "Abrir", None, "small", "Ctrl+O"),
                _btn("💾", "Guardar", None, "small", "Ctrl+S"),
                _btn("🖨", "Imprimir", None, "large", "Ctrl+P"),
            ]},
        ],
        "Inicio": [
            {"name": "Portapapeles", "items": [
                _btn("📋", "Pegar", None, "large"),
                _btn("✂", "Cortar", None, "small"),
                _btn("⎘", "Copiar", None, "small"),
                _btn("🖌", "Copiar formato", None, "small"),
            ]},
            {"name": "Fuente", "items": [
                _btn("Aa", "Fuente", None, "small"),
                _btn("12", "Tamaño", None, "small"),
                _btn("B", "Negrita", "negrita", "small", "Ctrl+B / Ctrl+N"),
                _btn("I", "Cursiva", None, "small"),
                _btn("U", "Subrayado", None, "small"),
                _btn("▦", "Bordes", "bordes", "small"),
                _btn("🪣", "Relleno", None, "small"),
                _btn("A▾", "Color fuente", None, "small"),
            ]},
            {"name": "Alineación", "items": [
                _btn("⇔", "Combinar y centrar", "combinar", "large"),
                _btn("↤", "Izquierda", None, "small"),
                _btn("↔", "Centrar", None, "small"),
                _btn("↦", "Derecha", None, "small"),
                _btn("↕", "Orientación", None, "small"),
                _btn("⇥", "Ajustar texto", None, "small"),
            ]},
            {"name": "Número", "items": [
                _btn("$", "Moneda", "moneda", "small", "Ctrl+Shift+4"),
                _btn("%", "Porcentaje", "porcentaje", "small", "Ctrl+Shift+5"),
                _btn("◴", "Fecha", "fecha", "small"),
                _btn("0.0", "Formato", None, "small"),
                _btn("➕", "Aumentar decimales", None, "small"),
                _btn("➖", "Disminuir decimales", None, "small"),
            ]},
            {"name": "Estilos", "items": [
                _btn("◩", "Formato condicional", "formato_condicional", "large"),
                _btn("▣", "Formato como tabla", "tabla_excel", "small", "Ctrl+T"),
                _btn("✓", "Estilos de celda", None, "small"),
            ]},
            {"name": "Celdas", "items": [
                _btn("＋", "Insertar", None, "small"),
                _btn("－", "Eliminar", None, "small"),
                _btn("▤", "Formato", None, "small"),
            ]},
            {"name": "Edición", "items": [
                _btn("Σ", "Autosuma", "autosuma", "large"),
                _btn("x̄", "Promedio", "promedio", "small"),
                _btn("A↓Z", "Ordenar", "ordenar", "small"),
                _btn("▽", "Filtro", "filtro", "small", "Ctrl+Shift+L"),
                _btn("🔎", "Buscar", None, "small"),
            ]},
        ],
        "Insertar": [
            {"name": "Tablas", "items": [
                _btn("▦", "Tabla", "tabla_excel", "large", "Ctrl+T"),
                _btn("◫", "Tabla dinámica", None, "small"),
            ]},
            {"name": "Ilustraciones", "items": [
                _btn("🖼", "Imágenes", None, "large"),
                _btn("○", "Formas", None, "small"),
                _btn("◆", "Iconos", None, "small"),
            ]},
            {"name": "Gráficos", "items": [
                _btn("▥", "Gráfico recomendado", "grafico", "large"),
                _btn("▤", "Columnas", None, "small"),
                _btn("◔", "Circular", None, "small"),
                _btn("╱", "Líneas", None, "small"),
            ]},
            {"name": "Minigráficos", "items": [
                _btn("╱", "Líneas", None, "small"),
                _btn("▮", "Columnas", None, "small"),
            ]},
        ],
        "Diseño de página": [
            {"name": "Temas", "items": [
                _btn("🎨", "Temas", None, "large"),
                _btn("A", "Fuentes", None, "small"),
                _btn("🌈", "Colores", None, "small"),
            ]},
            {"name": "Configurar página", "items": [
                _btn("▭", "Márgenes", None, "small"),
                _btn("↕", "Orientación", None, "small"),
                _btn("A4", "Tamaño", None, "small"),
                _btn("🖨", "Área de impresión", None, "small"),
                _btn("↘", "Saltos", None, "small"),
            ]},
        ],
        "Fórmulas": [
            {"name": "Biblioteca de funciones", "items": [
                _btn("Σ", "Autosuma", "autosuma", "large"),
                _btn("fx", "Insertar función", None, "small"),
                _btn("💰", "Financieras", None, "small"),
                _btn("∑", "Matemáticas", None, "small"),
                _btn("📅", "Fecha y hora", None, "small"),
            ]},
            {"name": "Nombres definidos", "items": [
                _btn("🏷", "Asignar nombre", None, "small"),
                _btn("☰", "Administrador", None, "small"),
            ]},
            {"name": "Auditoría de fórmulas", "items": [
                _btn("→", "Rastrear precedentes", None, "small"),
                _btn("←", "Rastrear dependientes", None, "small"),
                _btn("👁", "Evaluar fórmula", None, "small"),
            ]},
        ],
        "Datos": [
            {"name": "Obtener y transformar", "items": [
                _btn("⬇", "Obtener datos", None, "large"),
                _btn("↻", "Actualizar todo", None, "small"),
            ]},
            {"name": "Ordenar y filtrar", "items": [
                _btn("A↓Z", "Ordenar A-Z", "ordenar", "small"),
                _btn("Z↓A", "Ordenar Z-A", None, "small"),
                _btn("▽", "Filtro", "filtro", "small", "Ctrl+Shift+L"),
            ]},
            {"name": "Herramientas de datos", "items": [
                _btn("☰", "Texto en columnas", None, "small"),
                _btn("≠", "Quitar duplicados", None, "small"),
                _btn("✓", "Validación de datos", "validacion", "small"),
            ]},
            {"name": "Previsión", "items": [
                _btn("📈", "Hoja de previsión", None, "small"),
            ]},
        ],
        "Vista": [
            {"name": "Vistas del libro", "items": [
                _btn("▤", "Normal", None, "small"),
                _btn("📄", "Diseño de página", None, "small"),
                _btn("↘", "Saltos de página", None, "small"),
            ]},
            {"name": "Ventana", "items": [
                _btn("📌", "Inmovilizar", "inmovilizar", "large"),
                _btn("▥", "Dividir", None, "small"),
                _btn("▣", "Nueva ventana", None, "small"),
            ]},
            {"name": "Mostrar", "items": [
                _btn("☑", "Líneas de cuadrícula", None, "small"),
                _btn("☑", "Encabezados", None, "small"),
                _btn("☑", "Barra de fórmulas", None, "small"),
            ]},
        ],
    }


class WordLevel(OfficeLevel):
    def __init__(self, education_level: str = "primaria"):
        super().__init__("#185abd", "word", _word_ribbon_tabs())
        self.appbar.setText("W   Documento de práctica — Word")
        outer = QVBoxLayout(self.workspace)
        self.editor = QTextEdit()
        self.editor.setObjectName("wordSheet")
        self.editor.setPlainText("La tecnología es una herramienta para aprender, crear y comunicar.")
        self.editor.selectAll()
        self.editor.setStyleSheet(
            "QTextEdit#wordSheet{background:#ffffff;color:#15181d;border:1px solid #d9dde3;"
            "border-radius:4px;padding:48px;font-size:18px;selection-background-color:#b9ddff;selection-color:#111;}"
        )
        outer.setContentsMargins(90, 16, 90, 10)
        outer.addWidget(self.editor)

    def apply_visual(self, action: str):
        cursor = self.editor.textCursor()
        if action in {"negrita", "cursiva", "subrayado", "color_fuente", "resaltar", "aumentar_fuente", "hipervinculo"}:
            if not cursor.hasSelection():
                cursor.select(QTextCursor.SelectionType.Document)
            fmt = QTextCharFormat()
            if action == "negrita":
                fmt.setFontWeight(QFont.Weight.Bold)
            elif action == "cursiva":
                fmt.setFontItalic(True)
            elif action == "subrayado":
                fmt.setFontUnderline(True)
            elif action == "color_fuente":
                fmt.setForeground(QColor("#185abd"))
            elif action == "resaltar":
                fmt.setBackground(QColor("#fff59d"))
            elif action == "aumentar_fuente":
                current = cursor.charFormat().fontPointSize() or 18
                fmt.setFontPointSize(current + 2)
            elif action == "hipervinculo":
                fmt.setForeground(QColor("#0563c1"))
                fmt.setFontUnderline(True)
            cursor.mergeCharFormat(fmt)
        elif action in {"centrar", "izquierda", "justificar", "interlineado", "vinetas"}:
            block_fmt = QTextBlockFormat()
            if action == "centrar":
                block_fmt.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cursor.mergeBlockFormat(block_fmt)
            elif action == "izquierda":
                block_fmt.setAlignment(Qt.AlignmentFlag.AlignLeft)
                cursor.mergeBlockFormat(block_fmt)
            elif action == "justificar":
                block_fmt.setAlignment(Qt.AlignmentFlag.AlignJustify)
                cursor.mergeBlockFormat(block_fmt)
            elif action == "interlineado":
                block_fmt.setLineHeight(170, QTextBlockFormat.LineHeightTypes.ProportionalHeight)
                cursor.mergeBlockFormat(block_fmt)
            elif action == "vinetas":
                if not cursor.hasSelection():
                    cursor.select(QTextCursor.SelectionType.Document)
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                cursor.beginEditBlock()
                cursor.setPosition(start)
                list_format = QTextListFormat()
                list_format.setStyle(QTextListFormat.Style.ListDisc)
                while True:
                    block_cursor = QTextCursor(cursor.block())
                    block_cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                    if not block_cursor.currentList():
                        block_cursor.createList(list_format)
                    if cursor.position() >= end or not cursor.movePosition(QTextCursor.MoveOperation.NextBlock):
                        break
                cursor.endEditBlock()
        elif action == "imprimir":
            self.editor.setToolTip("Vista previa de impresión abierta")
        elif action == "tabla":
            self.editor.append("\n\n| Columna 1 | Columna 2 |\n|-----------|-----------|\n| Dato A    | Dato B    |")
        elif action == "encabezado":
            self.editor.setPlainText("Encabezado del documento\n\n" + self.editor.toPlainText())
        elif action == "columnas":
            self.editor.setViewportMargins(18, 0, 18, 0)
            self.editor.setToolTip("Diseño aplicado: dos columnas")
        self.editor.setTextCursor(cursor)


class PowerPointLevel(OfficeLevel):
    def __init__(self, education_level: str = "primaria"):
        super().__init__("#b7472a", "powerpoint", _powerpoint_ribbon_tabs())
        self.appbar.setText("P   Presentación de práctica — PowerPoint")
        outer = QHBoxLayout(self.workspace)
        self.thumbs = QVBoxLayout()
        for number in range(1, 3):
            thumb = QLabel(str(number))
            thumb.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            thumb.setFixedSize(120, 72)
            thumb.setStyleSheet("background:#ffffff;color:#222;border:2px solid #c7cbd1;border-radius:4px;padding:5px")
            self.thumbs.addWidget(thumb)
        self.thumbs.addStretch()
        outer.addLayout(self.thumbs)
        self.slide = QFrame()
        self.slide.setObjectName("powerPointSheet")
        self.slide.setStyleSheet("QFrame#powerPointSheet{background:#ffffff;border:1px solid #cfd3d9;border-radius:4px}")
        slide_layout = QVBoxLayout(self.slide)
        self.title = QLabel("Mi presentación")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size:30px;color:#1b1d21;background:transparent")
        self.subtitle = QLabel("Haz clic para agregar un subtítulo")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setStyleSheet("font-size:16px;color:#68707a;background:transparent")
        slide_layout.addStretch()
        slide_layout.addWidget(self.title)
        slide_layout.addWidget(self.subtitle)
        slide_layout.addStretch()
        outer.addWidget(self.slide, 1)

    def _add_thumb(self):
        number = max(1, self.thumbs.count())
        thumb = QLabel(str(number))
        thumb.setFixedSize(120, 72)
        thumb.setStyleSheet("background:#ffffff;color:#222;border:2px solid #b7472a;border-radius:4px;padding:5px")
        self.thumbs.insertWidget(max(0, self.thumbs.count() - 1), thumb)

    def apply_visual(self, action: str):
        if action in {"nueva_diapositiva", "duplicar"}:
            self._add_thumb()
            if action == "duplicar":
                self.subtitle.setText("Diapositiva duplicada")
        elif action == "diseno":
            self.subtitle.setText("Diseño: Título y contenido")
        elif action == "negrita":
            self.title.setStyleSheet("font-size:30px;color:#1b1d21;background:transparent;font-weight:700")
        elif action == "centrar":
            self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif action == "insertar_forma":
            self.subtitle.setText("●  Forma insertada")
            self.subtitle.setStyleSheet("font-size:22px;color:#b7472a;background:transparent")
        elif action == "imagen":
            self.subtitle.setText("▧  Imagen insertada")
        elif action == "transicion":
            self.slide.setStyleSheet("QFrame#powerPointSheet{background:#ffffff;border:4px solid #e68a72;border-radius:8px}")
        elif action == "alinear_objetos":
            self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.subtitle.setText("Objetos alineados al centro")
        elif action == "animacion":
            self.subtitle.setText("✦ Animación aplicada")
        elif action == "notas":
            self.subtitle.setText("Notas del presentador agregadas")
        elif action == "enviar_fondo":
            self.subtitle.setText("Objeto enviado al fondo")
        elif action in {"presentar", "presentar_actual"}:
            self.slide.setStyleSheet("QFrame#powerPointSheet{background:#ffffff;border:5px solid #b7472a;border-radius:4px}")
            self.title.setStyleSheet("font-size:34px;color:#111;background:transparent;font-weight:700")


class ExcelLevel(OfficeLevel):
    def __init__(self, education_level: str = "primaria"):
        super().__init__("#107c41", "excel", _excel_ribbon_tabs())
        self.appbar.setText("X   Libro de práctica — Excel")
        outer = QVBoxLayout(self.workspace)
        formula = QHBoxLayout()
        formula.addWidget(QLabel("A1"))
        formula.addWidget(QLabel("fx"))
        self.formula_value = QLabel("1250")
        self.formula_value.setStyleSheet("background:#0d141e;color:#e8f1fb;border:1px solid #33455c;border-radius:6px;padding:6px")
        formula.addWidget(self.formula_value, 1)
        outer.addLayout(formula)
        self.table = QTableWidget(12, 8)
        self.table.setObjectName("excelSheet")
        self.table.setHorizontalHeaderLabels(list("ABCDEFGH"))
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setStyleSheet(
            "QTableWidget#excelSheet{background:#fff;alternate-background-color:#fff;color:#15181d;gridline-color:#d9dde2;"
            "border:1px solid #cfd4da;border-radius:4px;selection-background-color:#b7daf7;selection-color:#111;}"
            "QTableWidget#excelSheet::item{background:#fff;color:#15181d;padding:5px;}"
            "QTableWidget#excelSheet::item:selected{background:#b7daf7;color:#111;}"
            "QTableWidget#excelSheet QHeaderView::section{background:#f2f3f5;color:#31363d;border:0;border-right:1px solid #d3d7dc;"
            "border-bottom:1px solid #c8cdd3;padding:6px;font-weight:650;}"
        )
        values = [["Producto", "Cantidad", "Precio"], ["Cuadernos", "10", "45"],
                  ["Lápices", "25", "8"], ["Mochilas", "4", "520"]]
        for r, row in enumerate(values):
            for c, value in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(value))
        self.table.setCurrentCell(1, 2)
        outer.addWidget(self.table)

    def apply_visual(self, action: str):
        item = self.table.currentItem() or self.table.item(1, 2)
        if not item:
            return
        if action == "negrita":
            font = item.font(); font.setBold(True); item.setFont(font)
        elif action == "bordes":
            item.setBackground(QColor("#e9f5ee"))
        elif action == "moneda":
            if not item.text().startswith("$"): item.setText(f"$ {item.text()}")
        elif action == "porcentaje":
            if not item.text().endswith("%"): item.setText(f"{item.text()} %")
        elif action == "combinar":
            self.table.setSpan(item.row(), item.column(), 1, 2)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        elif action == "autosuma":
            self.formula_value.setText("=SUMA(C2:C4)")
            self.table.setItem(4, 2, QTableWidgetItem("=SUMA(C2:C4)"))
        elif action == "ordenar":
            self.table.sortItems(0, Qt.SortOrder.AscendingOrder)
        elif action == "filtro":
            self.table.setSortingEnabled(True)
            self.table.setHorizontalHeaderLabels(["Producto ▼", "Cantidad ▼", "Precio ▼", "D", "E", "F", "G", "H"])
        elif action == "grafico":
            self.formula_value.setText("Gráfico de columnas insertado ✓")
        elif action == "promedio":
            self.formula_value.setText("=PROMEDIO(C2:C4)")
            self.table.setItem(5, 2, QTableWidgetItem("=PROMEDIO(C2:C4)"))
        elif action == "fecha":
            item.setText("14/09/2026")
        elif action == "formato_condicional":
            item.setBackground(QColor("#c9f2d6"))
            item.setForeground(QColor("#14532d"))
        elif action == "inmovilizar":
            self.table.horizontalHeader().setToolTip("Fila superior inmovilizada")
            self.formula_value.setText("Fila superior inmovilizada ✓")
        elif action == "validacion":
            item.setToolTip("Validación: sólo valores válidos")
            self.formula_value.setText("Validación de datos aplicada ✓")
        elif action == "tabla_excel":
            for c in range(min(3, self.table.columnCount())):
                header_item = self.table.item(0, c)
                if header_item:
                    header_item.setBackground(QColor("#dbeafe"))
                    font = header_item.font(); font.setBold(True); header_item.setFont(font)


class FinishScreen(QWidget):
    restart_requested = Signal()
    finish_requested = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        trophy = QLabel("★")
        trophy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        trophy.setStyleSheet("font-size:100px;color:#f4b942")
        title = QLabel("¡Misión completada!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:36px;font-weight:800;color:#f2f8ff")
        text = QLabel("Dominaste el teclado y las herramientas esenciales de Word, PowerPoint y Excel.")
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text.setStyleSheet("font-size:17px;color:#8190a8")
        self.summary = QLabel()
        self.summary.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.summary.setStyleSheet("font-size:16px;color:#d9e7f5;font-weight:700")
        button = QPushButton("Volver a practicar")
        button.setProperty("class", "secondary")
        button.clicked.connect(self.restart_requested)
        finish_button = QPushButton("Finalizar sesión")
        finish_button.setProperty("class", "primary")
        finish_button.clicked.connect(self.finish_requested)
        layout.addWidget(trophy)
        layout.addWidget(title)
        layout.addWidget(text)
        layout.addWidget(self.summary)
        layout.addSpacing(22)
        layout.addWidget(finish_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_summary(self, grade: int, attempts: int, correct: int):
        self.summary.setText(f"Calificación: {grade}/100   ·   Logros registrados en esta sesión: {correct}")
