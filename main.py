from __future__ import annotations

import argparse
import sys

from PySide6.QtCore import QEvent, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QFormLayout, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget,
)

import config
from game_engine import TaskSequence, cumulative_shortcuts
from kiosk import WindowsShortcutBlocker
from progress_store import ProgressStore
from session_log import SessionLogger
from settings_store import TeacherSettings
from teacher_dashboard import TeacherDashboard
from styles import APP_STYLE
from widgets import ExcelLevel, FinishScreen, KeyboardLevel, MissionPanel, PowerPointLevel, WordLevel


LEVEL_NAMES = ("Teclado", "Word", "PowerPoint", "Excel")


class StudentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Identificación del estudiante")
        self.setModal(True)
        self.setFixedWidth(440)
        layout = QVBoxLayout(self)
        title = QLabel("Datos de la sesión")
        title.setStyleSheet("font-size:20px;font-weight:700;color:white")
        help_text = QLabel("Captura los datos antes de comenzar. La matrícula identifica el progreso guardado.")
        help_text.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(help_text)
        form = QFormLayout()
        self.name = QLineEdit()
        self.name.setPlaceholderText("Nombre completo")
        self.student_id = QLineEdit()
        self.student_id.setPlaceholderText("Matrícula")
        self.group = QLineEdit()
        self.group.setPlaceholderText("Grupo")
        form.addRow("Nombre:", self.name)
        form.addRow("Matrícula:", self.student_id)
        form.addRow("Grupo:", self.group)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate(self):
        if not self.name.text().strip() or not self.student_id.text().strip() or not self.group.text().strip():
            QMessageBox.warning(self, "Datos incompletos", "Captura nombre, matrícula y grupo para iniciar.")
            return
        self.accept()

    def data(self) -> dict:
        return {
            "nombre": self.name.text().strip(),
            "matricula": self.student_id.text().strip(),
            "grupo": self.group.text().strip(),
        }


class PasswordDialog(QDialog):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedWidth(380)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Escribe la contraseña del profesor:"))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("Contraseña")
        self.password.returnPressed.connect(self.accept)
        layout.addWidget(self.password)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def value(self) -> str:
        return self.password.text()


class GameWindow(QMainWindow):
    session_finished = Signal()
    def __init__(self, student: dict, windowed: bool = False):
        super().__init__()
        self.student = student
        self.windowed = windowed
        self.authorized_close = False
        self.session_closed = False
        self.shortcut_blocker = WindowsShortcutBlocker()
        self.teacher_settings = TeacherSettings()
        self.education_level = self.teacher_settings.get_education_level()
        self.show_hints = self.teacher_settings.get_show_hints()

        self.level_tasks = [
            cumulative_shortcuts(self.education_level, config.ATAJOS_POR_NIVEL),
            cumulative_shortcuts(self.education_level, config.TAREAS_WORD_POR_NIVEL),
            cumulative_shortcuts(self.education_level, config.TAREAS_POWERPOINT_POR_NIVEL),
            cumulative_shortcuts(self.education_level, config.TAREAS_EXCEL_POR_NIVEL),
        ]
        self.total_tasks = sum(len(tasks) for tasks in self.level_tasks)
        self.store = ProgressStore(config.GUARDAR_PROGRESO, student.get("matricula", "general"))
        self.saved = self.store.load()
        self.sequences = [TaskSequence(list(tasks)) for tasks in self.level_tasks]
        for index, sequence in enumerate(self.sequences):
            sequence.index = max(0, min(int(self.saved["levels"][index]), len(sequence.tasks)))
        self.level_index = max(0, min(int(self.saved.get("last_level", 0)), 3))
        self.logger = SessionLogger({**student, "nivel_educativo": self.education_level}, self.total_tasks)

        self.setWindowTitle(config.APP_TITLE)
        self.setMinimumSize(1024, 700)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, not windowed)
        self._build_ui()
        QApplication.instance().installEventFilter(self)
        self._open_current_level()

        if config.MODO_QUIOSCO_ESTRICTO and not windowed:
            self.shortcut_blocker.install()

    @property
    def sequence(self) -> TaskSequence:
        return self.sequences[self.level_index]

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        topbar = QFrame()
        topbar.setObjectName("topbar")
        top = QHBoxLayout(topbar)
        top.setContentsMargins(16, 9, 16, 9)
        brand = QLabel("⌨  MISIÓN DIGITAL")
        brand.setObjectName("brand")
        top.addWidget(brand)
        level_name = {'primaria': 'Primaria', 'secundaria': 'Secundaria', 'preparatoria': 'Prepa'}.get(self.education_level, self.education_level.title())
        self.student_pill = QLabel(f"{self.student['nombre']} · {self.student['grupo']} · {level_name}")
        self.student_pill.setObjectName("studentPill")
        top.addWidget(self.student_pill)
        top.addStretch()

        self.level_buttons: list[QPushButton] = []
        for i, name in enumerate(LEVEL_NAMES):
            button = QPushButton(str(i + 1) + " " + name)
            button.setProperty("class", "levelNav")
            button.clicked.connect(lambda checked=False, idx=i: self.switch_level(idx))
            self.level_buttons.append(button)
            top.addWidget(button)

        self.level_pill = QLabel()
        self.level_pill.setObjectName("levelPill")
        top.addWidget(self.level_pill)
        self.progress = QProgressBar()
        self.progress.setFixedWidth(145)
        self.progress.setTextVisible(False)
        top.addWidget(self.progress)
        reset = QPushButton("Reiniciar")
        reset.setObjectName("exitButton")
        reset.clicked.connect(self.request_reset)
        top.addWidget(reset)
        exit_button = QPushButton("Salida profesor")
        exit_button.setObjectName("exitButton")
        exit_button.clicked.connect(self.request_teacher_exit)
        top.addWidget(exit_button)
        root_layout.addWidget(topbar)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(22, 18, 22, 18)
        body_layout.setSpacing(12)
        self.mission = MissionPanel()
        self.mission.set_hints_enabled(self.show_hints)
        body_layout.addWidget(self.mission)
        self.feedback = QLabel()
        self.feedback.hide()
        body_layout.addWidget(self.feedback)
        self.stack = QStackedWidget()
        self.keyboard_level = KeyboardLevel()
        self.word_level = WordLevel(self.education_level)
        self.powerpoint_level = PowerPointLevel(self.education_level)
        self.excel_level = ExcelLevel(self.education_level)
        self.finish = FinishScreen()
        for page in (self.keyboard_level, self.word_level, self.powerpoint_level, self.excel_level, self.finish):
            self.stack.addWidget(page)
        self.keyboard_level.shortcut_pressed.connect(self.attempt_shortcut)
        self.word_level.action_requested.connect(self.attempt_action)
        self.powerpoint_level.action_requested.connect(self.attempt_action)
        self.excel_level.action_requested.connect(self.attempt_action)
        self.finish.restart_requested.connect(self.request_reset)
        self.finish.finish_requested.connect(self.request_normal_exit)
        body_layout.addWidget(self.stack, 1)
        root_layout.addWidget(body, 1)
        self.setCentralWidget(root)

    def _completed_count(self) -> int:
        return sum(min(seq.index, len(seq.tasks)) for seq in self.sequences)

    def _all_complete(self) -> bool:
        return all(seq.complete for seq in self.sequences)

    def _save_progress(self):
        levels = [seq.index for seq in self.sequences]
        self.store.save(levels, self.level_index, completed=self._all_complete())

    def _refresh_topbar(self):
        for i, button in enumerate(self.level_buttons):
            button.setProperty("active", i == self.level_index and self.stack.currentIndex() != 4)
            button.setText(f"{i + 1} {LEVEL_NAMES[i]}" + (" ✓" if self.sequences[i].complete else ""))
            button.style().unpolish(button)
            button.style().polish(button)
        self.progress.setValue(round(self._completed_count() * 100 / max(1, self.total_tasks)))

    def _open_current_level(self):
        if self._all_complete():
            self.show_finish_screen()
            return
        self.mission.show()
        self.stack.setCurrentIndex(self.level_index)
        self._refresh_task()

    def _refresh_task(self):
        sequence = self.sequence
        self.level_pill.setText(f"Nivel {self.level_index + 1} · {LEVEL_NAMES[self.level_index]}")
        if sequence.complete:
            self.mission.set_completed(LEVEL_NAMES[self.level_index], len(sequence.tasks))
        else:
            self.mission.set_task(sequence.current, sequence.index, len(sequence.tasks))
        self._refresh_topbar()

    def switch_level(self, index: int):
        if not 0 <= index < 4:
            return
        self.level_index = index
        self._save_progress()
        self.mission.show()
        self.stack.setCurrentIndex(index)
        self.feedback.hide()
        self._refresh_task()

    def attempt_action(self, action: str):
        sequence = self.sequence
        if sequence.complete:
            return
        task_before = sequence.current
        ok = sequence.attempt(action=action)
        if ok:
            # Sólo se registra un logro. Explorar otros botones de la cinta no es error.
            self.logger.attempt(self.level_index, LEVEL_NAMES[self.level_index], task_before, f"cinta:{action}", True)
            self._correct()

    def attempt_shortcut(self, shortcut: str) -> bool:
        sequence = self.sequence
        if sequence.complete:
            return False
        task_before = sequence.current
        ok = sequence.attempt(shortcut=shortcut)
        if ok:
            self.logger.attempt(self.level_index, LEVEL_NAMES[self.level_index], task_before, f"teclado:{shortcut}", True)
            if self.level_index in (1, 2, 3) and task_before:
                self.stack.widget(self.level_index).apply_visual(task_before.get("accion", ""))
            self._correct()
            return True
        # Una combinación distinta no se contabiliza ni afecta la evaluación.
        return False

    def _correct(self):
        self.feedback.setObjectName("feedbackGood")
        self.feedback.setText("✓ ¡Correcto! Avance guardado.")
        self._show_feedback()
        self._save_progress()
        QTimer.singleShot(config.DURACION_MENSAJE_MS, self._after_correct)

    def _wrong(self, message: str):
        self.feedback.setObjectName("feedbackBad")
        self.feedback.setText(f"Intenta de nuevo. {message}")
        self._show_feedback()
        QTimer.singleShot(1800, self.feedback.hide)

    def _show_feedback(self):
        self.feedback.style().unpolish(self.feedback)
        self.feedback.style().polish(self.feedback)
        self.feedback.show()

    def _after_correct(self):
        self.feedback.hide()
        if self.sequence.complete:
            self.logger.level_completed(self.level_index, LEVEL_NAMES[self.level_index])
            self._save_progress()
            if self._all_complete():
                self.show_finish_screen()
                return
            # Avanza visualmente al siguiente nivel pendiente, sin bloquear la navegación libre.
            for step in range(1, 5):
                candidate = (self.level_index + step) % 4
                if not self.sequences[candidate].complete:
                    self.level_index = candidate
                    break
            self._save_progress()
            self.stack.setCurrentIndex(self.level_index)
        self._refresh_task()

    def show_finish_screen(self):
        self._save_progress()
        self.stack.setCurrentIndex(4)
        self.mission.hide()
        self.level_pill.setText("Sesión completada")
        grade = self.logger.final_grade(self._completed_count())
        self.finish.set_summary(grade, self.logger.attempts, self.logger.correct)
        self.progress.setValue(100)
        self._refresh_topbar()

    def _shortcut_from_event(self, event) -> str:
        sequence = QKeySequence(event.keyCombination()).toString(QKeySequence.SequenceFormat.PortableText)
        return sequence.replace("Meta", "META").replace("Esc", "ESC")

    def _physical_code(self, event) -> str:
        key = event.key()
        special = {
            Qt.Key.Key_Control: "CTRL", Qt.Key.Key_Alt: "ALT", Qt.Key.Key_Shift: "SHIFT",
            Qt.Key.Key_Meta: "META", Qt.Key.Key_Escape: "ESC", Qt.Key.Key_Return: "ENTER",
            Qt.Key.Key_Enter: "ENTER", Qt.Key.Key_Backspace: "BACKSPACE", Qt.Key.Key_Space: "SPACE",
            Qt.Key.Key_Tab: "TAB", Qt.Key.Key_Delete: "DELETE", Qt.Key.Key_Insert: "INSERT",
            Qt.Key.Key_Home: "HOME", Qt.Key.Key_End: "END", Qt.Key.Key_PageUp: "PAGEUP",
            Qt.Key.Key_PageDown: "PAGEDOWN", Qt.Key.Key_Left: "LEFT", Qt.Key.Key_Right: "RIGHT",
            Qt.Key.Key_Up: "UP", Qt.Key.Key_Down: "DOWN",
        }
        if key in special:
            return special[key]
        if Qt.Key.Key_F1 <= key <= Qt.Key.Key_F12:
            return f"F{key - Qt.Key.Key_F1 + 1}"
        text = event.text().upper()
        if text and text.isprintable() and not text.isspace():
            return {"+": "PLUS", "-": "MINUS"}.get(text, text)
        return ""

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.KeyPress and not event.isAutoRepeat():
            physical = self._physical_code(event)
            if physical:
                self.keyboard_level.keyboard.flash(physical)
            if event.key() == Qt.Key.Key_Escape:
                self.request_teacher_exit()
                return True
            if event.key() in (Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_Shift, Qt.Key.Key_Meta):
                return super().eventFilter(watched, event)
            shortcut = self._shortcut_from_event(event)
            if shortcut:
                self.keyboard_level.keyboard.animate_shortcut(shortcut)
                if self.attempt_shortcut(shortcut):
                    return True
        return super().eventFilter(watched, event)

    def _ask_password(self, title: str) -> bool:
        dialog = PasswordDialog(title, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return False
        if self.teacher_settings.verify_password(dialog.value()):
            return True
        QMessageBox.warning(self, "Contraseña incorrecta", "La contraseña no es correcta.")
        return False

    def request_normal_exit(self):
        if not self._all_complete():
            QMessageBox.information(self, "Sesión en curso", "La salida normal se habilita al completar los cuatro niveles. El profesor puede usar 'Salida profesor'.")
            return
        if self._ask_password("Finalizar sesión"):
            self._finish_and_close("sesion_completada")

    def request_teacher_exit(self):
        if self._ask_password("Salida anticipada del profesor"):
            self._finish_and_close("salida_anticipada_profesor")

    def _finish_and_close(self, reason: str):
        if not self.session_closed:
            self._save_progress()
            task_results = []
            for level_idx, sequence in enumerate(self.sequences):
                for task_idx, task in enumerate(sequence.tasks):
                    task_results.append({
                        "level": level_idx + 1,
                        "level_name": LEVEL_NAMES[level_idx],
                        "task_id": task.get("id"),
                        "task_text": task.get("texto"),
                        "achieved": task_idx < sequence.index,
                    })
            self.logger.finish(self._completed_count(), reason, task_results=task_results)
            self.session_closed = True
        self.authorized_close = True
        self.shortcut_blocker.uninstall()
        self.session_finished.emit()
        self.close()

    def request_reset(self):
        if not self._ask_password("Reiniciar progreso"):
            return
        self.store.reset()
        self.level_index = 0
        self.sequences = [TaskSequence(list(tasks)) for tasks in self.level_tasks]
        self._save_progress()
        self.stack.setCurrentIndex(0)
        self.mission.show()
        self._refresh_task()

    def closeEvent(self, event):
        if self.authorized_close:
            self.shortcut_blocker.uninstall()
            event.accept()
        else:
            event.ignore()
            QTimer.singleShot(0, self.request_teacher_exit)


def parse_args():
    parser = argparse.ArgumentParser(description=config.APP_TITLE)
    parser.add_argument("--windowed", action="store_true", help="Modo ventana para desarrollo")
    return parser.parse_args()


class StartWindow(QMainWindow):
    def __init__(self, windowed: bool = False):
        super().__init__()
        self.windowed = windowed
        self.settings = TeacherSettings()
        self.game_window = None
        self.setWindowTitle(config.APP_TITLE)
        # La pantalla inicial tiene una composición centrada de tamaño controlado.
        # Esto evita que tarjetas, botones y el icono cambien de proporción al redimensionar.
        self.setMinimumSize(860, 660)
        self.resize(980, 720)
        self._build_ui()

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("startRoot")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 26, 28, 22)
        layout.setSpacing(16)
        layout.addStretch()

        card = QFrame()
        card.setObjectName("startCard")
        card.setMinimumWidth(700)
        card.setMaximumWidth(820)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(48)
        shadow.setColor(QColor(0, 0, 0, 175))
        shadow.setOffset(0, 14)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(46, 34, 46, 34)
        card_layout.setSpacing(13)

        top = QHBoxLayout()
        top.addStretch()
        icon = QLabel("⌨")
        icon.setObjectName("startIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFixedSize(108, 76)
        top.addWidget(icon)
        top.addStretch()
        card_layout.addLayout(top)

        eyebrow = QLabel("ENTRENAMIENTO DIGITAL PARA AULA")
        eyebrow.setObjectName("startEyebrow")
        eyebrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("MISIÓN DIGITAL")
        title.setObjectName("startTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Aprende atajos y herramientas esenciales en una simulación segura de teclado, Word, PowerPoint y Excel.")
        subtitle.setObjectName("startSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        self.level_label = QLabel()
        self.level_label.setObjectName("startLevel")
        self.level_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(eyebrow)
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(4)
        card_layout.addWidget(self.level_label)

        chips = QHBoxLayout()
        chips.setSpacing(8)
        for text in ("4 niveles", "Progreso por matrícula", "Dashboard docente"):
            chip = QLabel(text)
            chip.setObjectName("featureChip")
            chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chip.setMinimumHeight(34)
            chips.addWidget(chip, 1)
        card_layout.addLayout(chips)
        card_layout.addSpacing(10)

        start_button = QPushButton("▶   Iniciar sesión del estudiante")
        start_button.setObjectName("startPrimary")
        start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        start_button.setMinimumHeight(50)
        start_button.clicked.connect(self.start_student_session)
        teacher_button = QPushButton("⚙   Panel del profesor")
        teacher_button.setObjectName("startTeacher")
        teacher_button.setCursor(Qt.CursorShape.PointingHandCursor)
        teacher_button.setMinimumHeight(48)
        teacher_button.clicked.connect(self.open_teacher_panel)
        card_layout.addWidget(start_button)
        card_layout.addWidget(teacher_button)

        layout.addWidget(card, 0, Qt.AlignmentFlag.AlignHCenter)
        footer = QLabel("Windows 10/11  ·  Los datos del alumnado se guardan sólo en este equipo")
        footer.setObjectName("startFooter")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)
        layout.addStretch()
        self.setCentralWidget(root)
        self._refresh_level()

    def _refresh_level(self):
        level = self.settings.get_education_level()
        names = {"primaria": "Primaria", "secundaria": "Secundaria", "preparatoria": "Prepa"}
        self.level_label.setText(f"Nivel configurado: {names.get(level, level.title())}")

    def _verify_teacher(self, title: str) -> bool:
        dialog = PasswordDialog(title, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return False
        if self.settings.verify_password(dialog.value()):
            return True
        QMessageBox.warning(self, "Contraseña incorrecta", "La contraseña del profesor no es correcta.")
        return False

    def open_teacher_panel(self):
        if not self._verify_teacher("Acceso al panel del profesor"):
            return
        panel = TeacherDashboard(self.settings, self)
        panel.exec()
        self._refresh_level()

    def start_student_session(self):
        student_dialog = StudentDialog(self)
        if student_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.game_window = GameWindow(student_dialog.data(), windowed=self.windowed)
        self.game_window.session_finished.connect(self._return_from_session)
        self.setEnabled(False)
        if self.windowed:
            self.game_window.resize(1280, 800)
            self.game_window.show()
        else:
            self.game_window.showFullScreen()
            self.game_window.raise_()
            self.game_window.activateWindow()

    def _return_from_session(self):
        QTimer.singleShot(0, self._show_after_session)

    def _show_after_session(self):
        self._refresh_level()
        self.setEnabled(True)
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.game_window = None


def main():
    args = parse_args()
    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_TITLE)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLE)

    window = StartWindow(windowed=args.windowed)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
