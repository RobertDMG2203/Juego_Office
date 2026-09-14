from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QLineF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFrame, QGraphicsDropShadowEffect,
    QGridLayout, QHBoxLayout, QHeaderView, QInputDialog, QLabel, QLineEdit, QMessageBox,
    QPushButton, QScrollArea, QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from data_exchange import (
    clear_imported_results, export_local_results, import_result_packages, imported_dir,
    load_attempt_detail, load_combined_results,
)
from maintenance import app_data_dir, clean_cache, purge_records, reset_cycle_data, schedule_uninstall
from settings_store import TeacherSettings


ACCENT = QColor("#43e6ff")
GRID = QColor("#26374b")
TEXT = QColor("#e5f1ff")
MUTED = QColor("#8294ad")
CARD = QColor("#0f1824")


def _number(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _achieved(row: dict) -> int:
    value = row.get("logros", row.get("aciertos", 0))
    try:
        return max(0, int(float(value or 0)))
    except (TypeError, ValueError):
        return 0


def _not_achieved(row: dict) -> int:
    if str(row.get("no_logradas", "")).strip() != "":
        try:
            return max(0, int(float(row.get("no_logradas", 0) or 0)))
        except (TypeError, ValueError):
            pass
    total = int(_number(row.get("tareas_totales"), 0))
    if total:
        return max(0, total - _achieved(row))
    # Historiales antiguos pueden tener errores registrados.
    return max(0, int(_number(row.get("errores"), 0)))


def _completion(row: dict) -> float:
    if str(row.get("completado", "")).strip() != "":
        return _number(row.get("completado"))
    total = _number(row.get("tareas_totales"), 0)
    if total > 0:
        return _achieved(row) * 100.0 / total
    return _number(row.get("calificacion"), 0)


def _format_bytes(value: int) -> str:
    size = float(max(0, value))
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def _directory_size(path: Path) -> int:
    total = 0
    if not path.exists():
        return total
    for item in path.rglob("*"):
        if item.is_file():
            try:
                total += item.stat().st_size
            except OSError:
                pass
    return total


def _shadow(widget: QWidget, blur: int = 28, y: int = 8) -> None:
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setColor(QColor(0, 0, 0, 135))
    effect.setOffset(0, y)
    widget.setGraphicsEffect(effect)


class MetricCard(QFrame):
    def __init__(self, title: str, icon: str):
        super().__init__()
        self.setObjectName("metricCard")
        _shadow(self, 22, 5)
        box = QVBoxLayout(self)
        box.setContentsMargins(18, 15, 18, 15)
        top = QHBoxLayout()
        self.title = QLabel(title.upper())
        self.title.setObjectName("metricTitle")
        icon_label = QLabel(icon)
        icon_label.setObjectName("metricIcon")
        top.addWidget(self.title)
        top.addStretch()
        top.addWidget(icon_label)
        self.value = QLabel("—")
        self.value.setObjectName("metricValue")
        box.addLayout(top)
        box.addWidget(self.value)


class RoundedChart(QWidget):
    def _paint_background(self, painter: QPainter, title: str) -> QRectF:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(rect, 16, 16)
        painter.fillPath(path, CARD)
        painter.setPen(QPen(QColor("#273a50"), 1))
        painter.drawPath(path)
        painter.setPen(TEXT)
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        painter.drawText(16, 27, title)
        return QRectF(46, 48, max(20, self.width() - 64), max(30, self.height() - 80))


class LineChart(RoundedChart):
    def __init__(self, title: str):
        super().__init__()
        self.title = title
        self.values: list[float] = []
        self.setMinimumHeight(215)

    def set_values(self, values: list[float]):
        self.values = values[-15:]
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        r = self._paint_background(p, self.title)
        p.setPen(QPen(GRID, 1))
        for i in range(5):
            y = r.bottom() - r.height() * i / 4
            p.drawLine(QLineF(r.left(), y, r.right(), y))
            p.setPen(MUTED)
            p.drawText(7, int(y + 4), str(i * 25))
            p.setPen(QPen(GRID, 1))
        if not self.values:
            p.setPen(MUTED)
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, "Aún no hay sesiones registradas")
            return
        step = r.width() / max(1, len(self.values) - 1)
        points = []
        for i, val in enumerate(self.values):
            x = r.left() + step * i
            y = r.bottom() - r.height() * max(0, min(100, val)) / 100
            points.append((x, y))
        p.setPen(QPen(ACCENT, 3))
        for i in range(1, len(points)):
            p.drawLine(QLineF(points[i - 1][0], points[i - 1][1], points[i][0], points[i][1]))
        p.setBrush(ACCENT)
        p.setPen(Qt.PenStyle.NoPen)
        for x, y in points:
            p.drawEllipse(QRectF(x - 4, y - 4, 8, 8))


class BarChart(RoundedChart):
    def __init__(self, title: str):
        super().__init__()
        self.title = title
        self.items: list[tuple[str, float]] = []
        self.setMinimumHeight(215)

    def set_items(self, items: list[tuple[str, float]]):
        self.items = items[:8]
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        r = self._paint_background(p, self.title)
        if not self.items:
            p.setPen(MUTED)
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, "Sin datos por grupo")
            return
        bar_w = r.width() / max(1, len(self.items))
        for i, (label, value) in enumerate(self.items):
            x = r.left() + i * bar_w + bar_w * .18
            h = r.height() * max(0, min(100, value)) / 100
            rect = QRectF(x, r.bottom() - h, bar_w * .64, h)
            bar = QPainterPath()
            bar.addRoundedRect(rect, 6, 6)
            p.fillPath(bar, QColor("#17465d"))
            p.setPen(ACCENT)
            p.drawText(QRectF(x, rect.top() - 20, bar_w * .64, 18), Qt.AlignmentFlag.AlignCenter, f"{value:.0f}")
            p.setPen(MUTED)
            short = label if len(label) <= 10 else label[:9] + "…"
            p.drawText(QRectF(x - 5, r.bottom() + 6, bar_w * .74, 20), Qt.AlignmentFlag.AlignCenter, short)


class StudentComparisonChart(RoundedChart):
    """Compara la evolución de hasta cinco alumnos por gráfica."""

    def __init__(self, title: str, series: list[tuple[str, list[float]]]):
        super().__init__()
        self.title = title
        self.series = series
        self.setMinimumHeight(245)

    def paintEvent(self, event):
        p = QPainter(self)
        r = self._paint_background(p, self.title)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(QPen(GRID, 1))
        for i in range(5):
            y = r.bottom() - r.height() * i / 4
            p.drawLine(QLineF(r.left(), y, r.right(), y))
            p.setPen(MUTED)
            p.drawText(7, int(y + 4), str(i * 25))
            p.setPen(QPen(GRID, 1))
        if not self.series:
            p.setPen(MUTED)
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, "Sin alumnos para comparar")
            return

        max_points = max((len(values) for _, values in self.series), default=1)
        plot = QRectF(r.left(), r.top() + 24, r.width(), max(20, r.height() - 24))
        for idx, (label, values) in enumerate(self.series):
            hue = int((idx * 359 / max(1, len(self.series))) % 360)
            color = QColor.fromHsv(hue, 150, 245)
            step = plot.width() / max(1, max_points - 1)
            points = []
            for i, value in enumerate(values):
                x = plot.left() + step * i
                y = plot.bottom() - plot.height() * max(0, min(100, value)) / 100
                points.append((x, y))
            p.setPen(QPen(color, 2.5))
            for i in range(1, len(points)):
                p.drawLine(QLineF(points[i - 1][0], points[i - 1][1], points[i][0], points[i][1]))
            p.setBrush(color)
            p.setPen(Qt.PenStyle.NoPen)
            for x, y in points:
                p.drawEllipse(QRectF(x - 3, y - 3, 6, 6))

            legend_x = r.left() + (idx % 3) * (r.width() / 3)
            legend_y = r.top() - 17 + (idx // 3) * 15
            p.setBrush(color)
            p.drawEllipse(QRectF(legend_x, legend_y, 8, 8))
            p.setPen(TEXT)
            short = label if len(label) <= 22 else label[:21] + "…"
            p.drawText(QRectF(legend_x + 12, legend_y - 4, r.width() / 3 - 15, 16), Qt.AlignmentFlag.AlignLeft, short)



class StudentDetailDialog(QDialog):
    def __init__(self, matricula: str, rows: list[dict], parent=None):
        super().__init__(parent)
        self.matricula = matricula
        self.rows = [row for row in rows if str(row.get("matricula", "")).strip() == matricula]
        latest = self.rows[-1] if self.rows else {}
        self.setWindowTitle(f"Detalle del alumno · {latest.get('nombre', matricula)}")
        self.resize(960, 660)
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(14)

        title = QLabel(str(latest.get("nombre", "Alumno")))
        title.setObjectName("dashboardTitle")
        meta = QLabel(f"Matrícula: {matricula}   ·   Grupo: {latest.get('grupo', '')}")
        meta.setObjectName("mutedText")
        root.addWidget(title)
        root.addWidget(meta)

        sessions = len(self.rows)
        grades = [_number(row.get("calificacion")) for row in self.rows]
        avg_grade = sum(grades) / sessions if sessions else 0
        achieved_total = sum(_achieved(row) for row in self.rows)
        assessed_total = achieved_total + sum(_not_achieved(row) for row in self.rows)
        completion = achieved_total * 100 / assessed_total if assessed_total else 0
        cards = QHBoxLayout()
        for label, value in (
            ("Sesiones", str(sessions)),
            ("Promedio", f"{avg_grade:.1f}/100" if sessions else "—"),
            ("Misiones logradas", f"{completion:.1f}%" if sessions else "—"),
            ("Última calificación", f"{grades[-1]:.0f}/100" if grades else "—"),
        ):
            card = MetricCard(label, "•")
            card.value.setText(value)
            cards.addWidget(card)
        root.addLayout(cards)

        section = QLabel("Desempeño por nivel")
        section.setObjectName("sectionTitle")
        root.addWidget(section)
        detail = load_attempt_detail(matricula)
        level_table = QTableWidget(0, 5)
        level_table.setHorizontalHeaderLabels(["Nivel", "Evaluadas", "Logradas", "No logradas", "Cumplimiento"])
        level_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        level_table.verticalHeader().setVisible(False)
        level_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        level_table.setMaximumHeight(190)
        order = ["Teclado", "Word", "PowerPoint", "Excel"]
        names = [name for name in order if name in detail] + sorted(name for name in detail if name not in order)
        level_table.setRowCount(len(names))
        for r, name in enumerate(names):
            stats = detail[name]
            completion_level = round(stats["aciertos"] * 100 / stats["intentos"]) if stats["intentos"] else 0
            for c, value in enumerate((name, stats["intentos"], stats["aciertos"], stats["errores"], f"{completion_level}%")):
                item = QTableWidgetItem(str(value))
                if c:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                level_table.setItem(r, c, item)
        root.addWidget(level_table)
        if not names:
            no_detail = QLabel("No hay logs detallados disponibles para este alumno; se conserva el resumen de sesiones.")
            no_detail.setObjectName("mutedText")
            root.addWidget(no_detail)

        history_title = QLabel("Historial de sesiones")
        history_title.setObjectName("sectionTitle")
        root.addWidget(history_title)
        history = QTableWidget(0, 6)
        history.setHorizontalHeaderLabels(["Fecha y hora", "Nivel", "Logradas", "No logradas", "Calificación", "Origen"])
        history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        history.verticalHeader().setVisible(False)
        history.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        history.setRowCount(len(self.rows))
        for r, row in enumerate(reversed(self.rows)):
            started = row.get("inicio", "")
            try:
                started = datetime.fromisoformat(str(started)).strftime("%d/%m/%Y %H:%M:%S")
            except (ValueError, TypeError):
                pass
            values = (
                started, row.get("nivel_educativo", ""), _achieved(row), _not_achieved(row),
                row.get("calificacion", ""), row.get("origen", ""),
            )
            for c, value in enumerate(values):
                history.setItem(r, c, QTableWidgetItem(str(value)))
        root.addWidget(history, 1)

        close = QPushButton("Cerrar")
        close.setProperty("class", "secondary")
        close.clicked.connect(self.accept)
        root.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)


class TeacherDashboard(QDialog):
    def __init__(self, settings: TeacherSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.rows: list[dict] = []
        self.setWindowTitle("Panel del profesor · Misión Digital")
        self.resize(1200, 790)
        self.setMinimumSize(1000, 700)
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(14)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Panel del profesor")
        title.setObjectName("dashboardTitle")
        subtitle = QLabel("Resultados, configuración y mantenimiento del equipo")
        subtitle.setObjectName("mutedText")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()
        self.level_badge = QLabel()
        self.level_badge.setObjectName("teacherBadge")
        header.addWidget(self.level_badge)
        root.addLayout(header)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self._build_dashboard_tab(), "Dashboard")
        self.tabs.addTab(self._build_exchange_tab(), "Importar / Exportar")
        self.tabs.addTab(self._build_settings_tab(), "Configuración")
        self.tabs.addTab(self._build_maintenance_tab(), "Mantenimiento")
        root.addWidget(self.tabs, 1)
        self._sync_level_ui()
        self.reload_data()
        self._refresh_storage_info()

    def _build_dashboard_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 16, 10, 10)
        layout.setSpacing(14)
        controls = QHBoxLayout()
        label = QLabel("Resultados locales + paquetes importados")
        label.setObjectName("mutedText")
        controls.addWidget(label)
        controls.addStretch()
        controls.addWidget(QLabel("Vista:"))
        self.student_filter = QComboBox()
        self.student_filter.setMinimumWidth(250)
        self.student_filter.addItem("Todos los estudiantes", "")
        self.student_filter.currentIndexChanged.connect(self._render_dashboard)
        controls.addWidget(self.student_filter)
        refresh = QPushButton("↻  Actualizar")
        refresh.setProperty("class", "secondary")
        refresh.clicked.connect(self.reload_data)
        controls.addWidget(refresh)
        layout.addLayout(controls)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        self.card_sessions = MetricCard("Sesiones", "◫")
        self.card_students = MetricCard("Estudiantes", "♙")
        self.card_grade = MetricCard("Promedio", "★")
        self.card_completion = MetricCard("Misiones logradas", "◎")
        for card in (self.card_sessions, self.card_students, self.card_grade, self.card_completion):
            cards.addWidget(card)
        layout.addLayout(cards)

        charts = QHBoxLayout()
        charts.setSpacing(14)
        self.grade_chart = LineChart("Calificación · últimas 15 sesiones")
        self.group_chart = BarChart("Promedio por grupo")
        charts.addWidget(self.grade_chart, 1)
        charts.addWidget(self.group_chart, 1)
        layout.addLayout(charts)

        comparison_title = QLabel("Comparativa simultánea por alumno")
        comparison_title.setObjectName("sectionTitle")
        layout.addWidget(comparison_title)
        comparison_help = QLabel("Cada línea representa la calificación de un estudiante a lo largo de sus sesiones. Se crean varias gráficas automáticamente cuando hay muchos alumnos.")
        comparison_help.setObjectName("mutedText")
        comparison_help.setWordWrap(True)
        layout.addWidget(comparison_help)
        self.comparison_scroll = QScrollArea()
        self.comparison_scroll.setWidgetResizable(True)
        self.comparison_scroll.setMinimumHeight(265)
        self.comparison_scroll.setMaximumHeight(520)
        self.comparison_widget = QWidget()
        self.comparison_layout = QVBoxLayout(self.comparison_widget)
        self.comparison_layout.setContentsMargins(0, 0, 0, 0)
        self.comparison_layout.setSpacing(10)
        self.comparison_scroll.setWidget(self.comparison_widget)
        layout.addWidget(self.comparison_scroll)

        self.interpretation = QLabel()
        self.interpretation.setObjectName("interpretation")
        self.interpretation.setWordWrap(True)
        layout.addWidget(self.interpretation)

        detail_hint = QLabel("Doble clic sobre una sesión para abrir el detalle individual del alumno.")
        detail_hint.setObjectName("mutedText")
        layout.addWidget(detail_hint)
        self.table = QTableWidget(0, 9)
        self.table.setAlternatingRowColors(True)
        self.table.setHorizontalHeaderLabels([
            "Nombre", "Matrícula", "Grupo", "Nivel", "Fecha y hora", "Logradas",
            "No logradas", "Calificación", "Origen",
        ])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.doubleClicked.connect(self._open_student_from_selection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(310)
        layout.addWidget(self.table, 1)
        return self._scroll_page(page)

    def _scroll_page(self, content: QWidget) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        return page

    def _build_exchange_tab(self) -> QWidget:
        content = QWidget()
        outer = QVBoxLayout(content)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(16)

        intro = QFrame()
        intro.setObjectName("maintenanceHero")
        intro_layout = QVBoxLayout(intro)
        intro_layout.setContentsMargins(22, 20, 22, 20)
        title = QLabel("Consolidación de resultados")
        title.setObjectName("sectionTitle")
        desc = QLabel(
            "En cada computadora de alumno exporta sus resultados al Escritorio. Después copia esas carpetas a la computadora "
            "del profesor e impórtalas aquí. El dashboard podrá comparar a todos o filtrar una matrícula individual."
        )
        desc.setObjectName("mutedText")
        desc.setWordWrap(True)
        intro_layout.addWidget(title)
        intro_layout.addWidget(desc)
        outer.addWidget(intro)

        export_box = QFrame()
        export_box.setObjectName("settingsCard")
        export_layout = QHBoxLayout(export_box)
        export_layout.setContentsMargins(22, 20, 22, 20)
        export_copy = QVBoxLayout()
        export_title = QLabel("Exportar resultados de este equipo")
        export_title.setObjectName("sectionTitleSmall")
        export_desc = QLabel(
            "Crea Escritorio/Mision_Digital_Resultados y genera un paquete independiente por matrícula con el resumen de sesiones "
            "y los logs detallados disponibles. Puedes copiar esa carpeta a una USB, red o nube."
        )
        export_desc.setObjectName("mutedText")
        export_desc.setWordWrap(True)
        export_copy.addWidget(export_title)
        export_copy.addWidget(export_desc)
        export_btn = QPushButton("Exportar al Escritorio")
        export_btn.setProperty("class", "primary")
        export_btn.clicked.connect(self._export_results)
        export_layout.addLayout(export_copy, 1)
        export_layout.addWidget(export_btn)
        outer.addWidget(export_box)

        import_box = QFrame()
        import_box.setObjectName("settingsCard")
        import_layout = QHBoxLayout(import_box)
        import_layout.setContentsMargins(22, 20, 22, 20)
        import_copy = QVBoxLayout()
        import_title = QLabel("Importar resultados de alumnos")
        import_title.setObjectName("sectionTitleSmall")
        import_desc = QLabel(
            "Selecciona una carpeta que contenga uno o muchos paquetes exportados. Las sesiones ya importadas se detectan y no se duplican."
        )
        import_desc.setObjectName("mutedText")
        import_desc.setWordWrap(True)
        self.import_status = QLabel()
        self.import_status.setObjectName("storageBadge")
        import_copy.addWidget(import_title)
        import_copy.addWidget(import_desc)
        import_copy.addWidget(self.import_status, alignment=Qt.AlignmentFlag.AlignLeft)
        import_btn = QPushButton("Seleccionar carpeta e importar")
        import_btn.setProperty("class", "primary")
        import_btn.clicked.connect(self._import_results)
        import_layout.addLayout(import_copy, 1)
        import_layout.addWidget(import_btn)
        outer.addWidget(import_box)

        clear_box = QFrame()
        clear_box.setObjectName("settingsCard")
        clear_layout = QHBoxLayout(clear_box)
        clear_layout.setContentsMargins(22, 18, 22, 18)
        clear_copy = QVBoxLayout()
        clear_title = QLabel("Limpiar consolidado importado")
        clear_title.setObjectName("sectionTitleSmall")
        clear_desc = QLabel("Borra sólo las copias importadas en esta computadora. No elimina los resultados locales originales ni los paquetes del Escritorio.")
        clear_desc.setObjectName("mutedText")
        clear_desc.setWordWrap(True)
        clear_copy.addWidget(clear_title)
        clear_copy.addWidget(clear_desc)
        clear_btn = QPushButton("Borrar datos importados")
        clear_btn.setProperty("class", "dangerSoft")
        clear_btn.clicked.connect(self._clear_imported_results)
        clear_layout.addLayout(clear_copy, 1)
        clear_layout.addWidget(clear_btn)
        outer.addWidget(clear_box)

        outer.addStretch()
        return self._scroll_page(content)

    def _build_settings_tab(self) -> QWidget:
        content = QWidget()
        outer = QVBoxLayout(content)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(16)

        level_box = QFrame()
        level_box.setObjectName("settingsCard")
        level_layout = QVBoxLayout(level_box)
        level_layout.setContentsMargins(22, 20, 22, 20)
        title = QLabel("Nivel de estudios")
        title.setObjectName("sectionTitle")
        text = QLabel("El cambio se aplica a las nuevas sesiones. Los ejercicios de teclado son acumulativos según el nivel.")
        text.setObjectName("mutedText")
        text.setWordWrap(True)
        row = QHBoxLayout()
        self.level_combo = QComboBox()
        self.level_combo.addItem("Primaria", "primaria")
        self.level_combo.addItem("Secundaria", "secundaria")
        self.level_combo.addItem("Prepa", "preparatoria")
        save_level = QPushButton("Guardar nivel")
        save_level.setProperty("class", "primary")
        save_level.clicked.connect(self._save_level)
        row.addWidget(self.level_combo, 1)
        row.addWidget(save_level)
        level_layout.addWidget(title)
        level_layout.addWidget(text)
        level_layout.addSpacing(5)
        level_layout.addLayout(row)
        outer.addWidget(level_box)

        hints_box = QFrame()
        hints_box.setObjectName("settingsCard")
        hints_layout = QHBoxLayout(hints_box)
        hints_layout.setContentsMargins(22, 20, 22, 20)
        hints_copy = QVBoxLayout()
        hints_title = QLabel("Pistas durante las misiones")
        hints_title.setObjectName("sectionTitle")
        hints_desc = QLabel("Controla la pista que aparece arriba a la derecha con el atajo esperado o la indicación de usar la cinta.")
        hints_desc.setObjectName("mutedText")
        hints_desc.setWordWrap(True)
        hints_copy.addWidget(hints_title)
        hints_copy.addWidget(hints_desc)
        self.hints_checkbox = QCheckBox("Mostrar pistas a los estudiantes")
        self.hints_checkbox.setChecked(self.settings.get_show_hints())
        self.hints_checkbox.toggled.connect(self._save_hints)
        hints_layout.addLayout(hints_copy, 1)
        hints_layout.addWidget(self.hints_checkbox)
        outer.addWidget(hints_box)

        pass_box = QFrame()
        pass_box.setObjectName("settingsCard")
        pass_layout = QGridLayout(pass_box)
        pass_layout.setContentsMargins(22, 20, 22, 20)
        pass_layout.setHorizontalSpacing(18)
        pass_layout.setVerticalSpacing(12)
        ptitle = QLabel("Seguridad del profesor")
        ptitle.setObjectName("sectionTitle")
        phelp = QLabel("Cambia la contraseña que protege el panel, reinicios y salidas de la sesión.")
        phelp.setObjectName("mutedText")
        phelp.setWordWrap(True)
        pass_layout.addWidget(ptitle, 0, 0, 1, 2)
        pass_layout.addWidget(phelp, 1, 0, 1, 2)
        self.current_password = QLineEdit()
        self.new_password = QLineEdit()
        self.confirm_password = QLineEdit()
        for edit in (self.current_password, self.new_password, self.confirm_password):
            edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.current_password.setPlaceholderText("Contraseña actual")
        self.new_password.setPlaceholderText("Nueva contraseña (mínimo 8 caracteres)")
        self.confirm_password.setPlaceholderText("Confirmar nueva contraseña")
        pass_layout.addWidget(QLabel("Actual:"), 2, 0)
        pass_layout.addWidget(self.current_password, 2, 1)
        pass_layout.addWidget(QLabel("Nueva:"), 3, 0)
        pass_layout.addWidget(self.new_password, 3, 1)
        pass_layout.addWidget(QLabel("Confirmar:"), 4, 0)
        pass_layout.addWidget(self.confirm_password, 4, 1)
        change = QPushButton("Cambiar contraseña")
        change.setProperty("class", "primary")
        change.clicked.connect(self._change_password)
        pass_layout.addWidget(change, 5, 1, alignment=Qt.AlignmentFlag.AlignRight)
        outer.addWidget(pass_box)
        outer.addStretch()
        return self._scroll_page(content)

    def _build_maintenance_tab(self) -> QWidget:
        content = QWidget()
        outer = QVBoxLayout(content)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(16)

        overview = QFrame()
        overview.setObjectName("maintenanceHero")
        overview_layout = QHBoxLayout(overview)
        overview_layout.setContentsMargins(22, 20, 22, 20)
        copy = QVBoxLayout()
        title = QLabel("Mantenimiento del ciclo escolar")
        title.setObjectName("sectionTitle")
        desc = QLabel("Herramientas protegidas para liberar temporales, depurar históricos y dejar el equipo listo para el siguiente ciclo.")
        desc.setObjectName("mutedText")
        desc.setWordWrap(True)
        self.storage_label = QLabel()
        self.storage_label.setObjectName("storageBadge")
        copy.addWidget(title)
        copy.addWidget(desc)
        copy.addWidget(self.storage_label, alignment=Qt.AlignmentFlag.AlignLeft)
        overview_layout.addLayout(copy, 1)
        outer.addWidget(overview)

        cache_box = QFrame()
        cache_box.setObjectName("settingsCard")
        cache_layout = QHBoxLayout(cache_box)
        cache_layout.setContentsMargins(22, 18, 22, 18)
        cache_text = QVBoxLayout()
        cache_title = QLabel("Limpiar caché y temporales")
        cache_title.setObjectName("sectionTitleSmall")
        cache_desc = QLabel("Elimina caché de la aplicación, archivos .tmp y __pycache__. No borra calificaciones, progreso ni configuración.")
        cache_desc.setObjectName("mutedText")
        cache_desc.setWordWrap(True)
        cache_text.addWidget(cache_title)
        cache_text.addWidget(cache_desc)
        cache_btn = QPushButton("Limpiar caché")
        cache_btn.setProperty("class", "secondary")
        cache_btn.clicked.connect(self._clean_cache)
        cache_layout.addLayout(cache_text, 1)
        cache_layout.addWidget(cache_btn)
        outer.addWidget(cache_box)

        records_box = QFrame()
        records_box.setObjectName("settingsCard")
        records_layout = QVBoxLayout(records_box)
        records_layout.setContentsMargins(22, 18, 22, 18)
        records_title = QLabel("Eliminar registros anteriores")
        records_title.setObjectName("sectionTitleSmall")
        records_desc = QLabel("Depura el histórico del dashboard y los logs detallados. El progreso actual de cada matrícula se conserva.")
        records_desc.setObjectName("mutedText")
        records_desc.setWordWrap(True)
        record_row = QHBoxLayout()
        self.retention_combo = QComboBox()
        self.retention_combo.addItem("Más antiguos de 30 días", 30)
        self.retention_combo.addItem("Más antiguos de 90 días", 90)
        self.retention_combo.addItem("Más antiguos de 180 días", 180)
        self.retention_combo.addItem("Más antiguos de 1 año", 365)
        self.retention_combo.addItem("Todos los resultados", None)
        self.retention_combo.setCurrentIndex(2)
        delete_old = QPushButton("Eliminar seleccionados")
        delete_old.setProperty("class", "dangerSoft")
        delete_old.clicked.connect(self._purge_records)
        record_row.addWidget(self.retention_combo, 1)
        record_row.addWidget(delete_old)
        records_layout.addWidget(records_title)
        records_layout.addWidget(records_desc)
        records_layout.addLayout(record_row)
        outer.addWidget(records_box)

        cycle_box = QFrame()
        cycle_box.setObjectName("dangerCard")
        cycle_layout = QHBoxLayout(cycle_box)
        cycle_layout.setContentsMargins(22, 18, 22, 18)
        cycle_text = QVBoxLayout()
        cycle_title = QLabel("Cerrar ciclo escolar")
        cycle_title.setObjectName("sectionTitleSmall")
        cycle_desc = QLabel("Borra TODOS los resultados y progresos del alumnado. Conserva la contraseña del profesor y el nivel educativo configurado.")
        cycle_desc.setObjectName("mutedText")
        cycle_desc.setWordWrap(True)
        cycle_text.addWidget(cycle_title)
        cycle_text.addWidget(cycle_desc)
        cycle_btn = QPushButton("Borrar datos del ciclo")
        cycle_btn.setProperty("class", "danger")
        cycle_btn.clicked.connect(self._reset_cycle)
        cycle_layout.addLayout(cycle_text, 1)
        cycle_layout.addWidget(cycle_btn)
        outer.addWidget(cycle_box)

        uninstall_box = QFrame()
        uninstall_box.setObjectName("dangerCard")
        uninstall_layout = QHBoxLayout(uninstall_box)
        uninstall_layout.setContentsMargins(22, 18, 22, 18)
        uninstall_text = QVBoxLayout()
        uninstall_title = QLabel("Desinstalar Misión Digital")
        uninstall_title.setObjectName("sectionTitleSmall")
        uninstall_desc = QLabel("Cierra la aplicación y elimina sus datos locales. En el .exe elimina también el ejecutable actual; en modo código sólo elimina la carpeta si contiene el marcador de este proyecto.")
        uninstall_desc.setObjectName("mutedText")
        uninstall_desc.setWordWrap(True)
        uninstall_text.addWidget(uninstall_title)
        uninstall_text.addWidget(uninstall_desc)
        uninstall_btn = QPushButton("Desinstalar aplicación")
        uninstall_btn.setProperty("class", "danger")
        uninstall_btn.clicked.connect(self._uninstall)
        uninstall_layout.addLayout(uninstall_text, 1)
        uninstall_layout.addWidget(uninstall_btn)
        outer.addWidget(uninstall_box)

        note = QLabel("Importante: ocultar la carpeta de código sólo evita acceso casual. Para los equipos de estudiantes se recomienda distribuir únicamente MisionDigital.exe; el código fuente no es necesario para ejecutar el juego.")
        note.setObjectName("maintenanceNote")
        note.setWordWrap(True)
        outer.addWidget(note)
        outer.addStretch()
        return self._scroll_page(content)

    def _sync_level_ui(self):
        level = self.settings.get_education_level()
        index = self.level_combo.findData(level)
        if index >= 0:
            self.level_combo.setCurrentIndex(index)
        names = {"primaria": "Primaria", "secundaria": "Secundaria", "preparatoria": "Prepa"}
        self.level_badge.setText(f"Nivel actual  ·  {names.get(level, level.title())}")

    def _save_level(self):
        self.settings.set_education_level(str(self.level_combo.currentData()))
        self._sync_level_ui()
        QMessageBox.information(self, "Nivel actualizado", "El nivel educativo se aplicará a la siguiente sesión que se inicie.")

    def _save_hints(self, enabled: bool):
        self.settings.set_show_hints(enabled)

    def _refresh_import_status(self):
        if hasattr(self, "import_status"):
            imported_rows = [row for row in self.rows if row.get("origen") == "importado"] if hasattr(self, "rows") else []
            students = {str(row.get("matricula", "")).strip() for row in imported_rows if str(row.get("matricula", "")).strip()}
            self.import_status.setText(f"Consolidado: {len(students)} alumno(s) · {len(imported_rows)} sesión(es) importada(s)")

    def _export_results(self):
        try:
            result = export_local_results()
        except ValueError as exc:
            QMessageBox.information(self, "Sin resultados", str(exc))
            return
        except OSError as exc:
            QMessageBox.warning(self, "No se pudo exportar", f"Windows no permitió crear la exportación.\n\n{exc}")
            return
        QMessageBox.information(
            self, "Exportación terminada",
            f"Se exportaron {result['students']} alumno(s) y {result['sessions']} sesión(es).\n\nCarpeta:\n{result['destination']}",
        )

    def _import_results(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecciona la carpeta con resultados de Misión Digital")
        if not folder:
            return
        try:
            result = import_result_packages(Path(folder))
        except ValueError as exc:
            QMessageBox.warning(self, "Paquetes no encontrados", str(exc))
            return
        except OSError as exc:
            QMessageBox.warning(self, "No se pudo importar", f"No fue posible leer o copiar los paquetes.\n\n{exc}")
            return
        self.reload_data()
        QMessageBox.information(
            self, "Importación terminada",
            f"Paquetes reconocidos: {result['packages']}\nSesiones nuevas: {result['rows_added']}\n"
            f"Sesiones ya existentes: {result['duplicates']}\nLogs detallados nuevos: {result['logs_added']}",
        )

    def _clear_imported_results(self):
        answer = QMessageBox.question(
            self, "Borrar consolidado importado",
            "Se eliminarán únicamente las copias importadas en esta computadora. Los datos locales y las carpetas exportadas originales no se tocarán. ¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        result = clear_imported_results()
        self.reload_data()
        QMessageBox.information(self, "Consolidado limpiado", f"Archivos importados eliminados: {result['files_removed']}")

    def _change_password(self):
        current = self.current_password.text()
        new = self.new_password.text()
        confirm = self.confirm_password.text()
        if new != confirm:
            QMessageBox.warning(self, "No coincide", "La confirmación de la nueva contraseña no coincide.")
            return
        ok, message = self.settings.change_password(current, new)
        if not ok:
            QMessageBox.warning(self, "No se pudo cambiar", message)
            return
        for edit in (self.current_password, self.new_password, self.confirm_password):
            edit.clear()
        QMessageBox.information(self, "Contraseña actualizada", message)

    def _refresh_storage_info(self):
        size = _directory_size(app_data_dir())
        self.storage_label.setText(f"Datos locales usados  ·  {_format_bytes(size)}")

    def _clean_cache(self):
        project_root = Path(__file__).resolve().parent
        result = clean_cache(project_root=project_root)
        self._refresh_storage_info()
        QMessageBox.information(
            self, "Limpieza terminada",
            f"Se limpiaron {result['items']} elemento(s) temporal(es) y se liberaron aproximadamente {_format_bytes(result['bytes'])}.\n\nLos resultados y progresos no fueron modificados.",
        )

    def _purge_records(self):
        days = self.retention_combo.currentData()
        selection = self.retention_combo.currentText()
        answer = QMessageBox.question(
            self, "Confirmar eliminación",
            f"Se eliminarán {selection.lower()} del dashboard y sus logs detallados.\n\nEl progreso de los estudiantes NO se borrará. ¿Deseas continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        result = purge_records(days)
        self.reload_data()
        self._refresh_storage_info()
        QMessageBox.information(
            self, "Registros depurados",
            f"Filas eliminadas del histórico: {result['rows_deleted']}\nLogs detallados eliminados: {result['files_deleted']}",
        )

    def _typed_confirmation(self, expected: str, title: str, prompt: str) -> bool:
        value, ok = QInputDialog.getText(self, title, f"{prompt}\n\nEscribe {expected} para confirmar:")
        return bool(ok and value.strip().upper() == expected)

    def _reset_cycle(self):
        answer = QMessageBox.warning(
            self, "Borrar datos del ciclo",
            "Esta acción eliminará todas las calificaciones, logs y progresos de estudiantes de este equipo.\n\nLa contraseña docente y el nivel educativo se conservarán.",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Ok:
            return
        if not self._typed_confirmation("BORRAR CICLO", "Confirmación reforzada", "Esta operación no se puede deshacer."):
            QMessageBox.information(self, "Cancelado", "No se borró ningún dato del ciclo.")
            return
        result = reset_cycle_data()
        self.reload_data()
        self._refresh_storage_info()
        QMessageBox.information(
            self, "Ciclo reiniciado",
            f"Se eliminaron los datos del alumnado ({', '.join(result['removed']) or 'sin datos previos'}).\nNivel educativo y contraseña del profesor conservados.",
        )

    def _uninstall(self):
        answer = QMessageBox.warning(
            self, "Desinstalar Misión Digital",
            "La aplicación se cerrará. En la versión EXE se eliminarán únicamente MisionDigital.exe y los datos locales propios de la aplicación.\n\nNO se desinstala Python, NO se ejecuta pip uninstall y NO se modifican librerías ni entornos de otros proyectos. Si se ejecuta desde código fuente, el repositorio y su entorno virtual se conservan.\n\nUsa esta opción únicamente al retirar el juego del equipo.",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Ok:
            return
        if not self._typed_confirmation("DESINSTALAR", "Confirmación de desinstalación", "Última confirmación."):
            QMessageBox.information(self, "Cancelado", "La aplicación no fue desinstalada.")
            return
        result = schedule_uninstall(remove_source_code=True)
        if not result.get("scheduled"):
            QMessageBox.warning(
                self, "Sólo disponible en Windows",
                "Se preparó el procedimiento, pero la eliminación automática sólo se ejecuta en Windows.",
            )
            return
        QMessageBox.information(
            self, "Desinstalación programada",
            "Misión Digital se cerrará ahora. Un proceso externo esperará a que este ejecutable termine "
            "y reintentará su borrado hasta confirmarlo. Python, los entornos virtuales y las librerías "
            "de desarrollo del equipo se conservarán.\n\n"
            "Si Windows impidiera el borrado, el diagnóstico quedará en "
            "%TEMP%\\MisionDigital_desinstalacion.log.",
        )
        app = QApplication.instance()
        # Este panel se abrió con QDialog.exec(), que mantiene un bucle modal propio.
        # Cerrarlo explícitamente evita que el proceso siga vivo y mantenga bloqueado
        # MisionDigital.exe mientras el helper externo intenta borrarlo.
        self.accept()
        if app is not None:
            QTimer.singleShot(0, app.quit)

    def reload_data(self):
        selected = ""
        if hasattr(self, "student_filter"):
            selected = str(self.student_filter.currentData() or "")
        self.rows = load_combined_results()
        if hasattr(self, "student_filter"):
            students: dict[str, str] = {}
            for row in self.rows:
                matricula = str(row.get("matricula", "")).strip()
                if matricula:
                    students[matricula] = str(row.get("nombre", "") or matricula)
            self.student_filter.blockSignals(True)
            self.student_filter.clear()
            self.student_filter.addItem("Todos los estudiantes", "")
            for matricula, nombre in sorted(students.items(), key=lambda item: (item[1].lower(), item[0].lower())):
                self.student_filter.addItem(f"{nombre} · {matricula}", matricula)
            index = self.student_filter.findData(selected)
            self.student_filter.setCurrentIndex(index if index >= 0 else 0)
            self.student_filter.blockSignals(False)
        self._render_dashboard()
        self._refresh_import_status()
        if hasattr(self, "storage_label"):
            self._refresh_storage_info()

    def _visible_rows(self) -> list[dict]:
        if not hasattr(self, "student_filter"):
            return list(self.rows)
        matricula = str(self.student_filter.currentData() or "").strip()
        if not matricula:
            return list(self.rows)
        return [row for row in self.rows if str(row.get("matricula", "")).strip() == matricula]

    def _render_dashboard(self, *args):
        rows = self._visible_rows()
        sessions = len(rows)
        students = len({r.get("matricula", "").strip() for r in rows if r.get("matricula", "").strip()})
        grades = [_number(r.get("calificacion")) for r in rows]
        avg_grade = sum(grades) / sessions if sessions else 0
        achieved_total = sum(_achieved(r) for r in rows)
        assessed_total = achieved_total + sum(_not_achieved(r) for r in rows)
        completion = achieved_total * 100 / assessed_total if assessed_total else 0
        self.card_sessions.value.setText(str(sessions))
        self.card_students.value.setText(str(students))
        self.card_grade.value.setText(f"{avg_grade:.1f}/100" if sessions else "—")
        self.card_completion.value.setText(f"{completion:.1f}%" if sessions else "—")
        self.grade_chart.set_values(grades)
        self._render_student_comparison(rows)

        grouped: dict[str, list[float]] = defaultdict(list)
        for row in rows:
            grouped[row.get("grupo", "Sin grupo") or "Sin grupo"].append(_number(row.get("calificacion")))
        group_items = sorted(
            ((group, sum(vals) / len(vals)) for group, vals in grouped.items()),
            key=lambda item: (-item[1], item[0].lower()),
        )
        self.group_chart.set_items(group_items)
        self._fill_table(rows)
        self.interpretation.setText(self._interpret(rows, avg_grade, completion, group_items))

    def _render_student_comparison(self, rows: list[dict]):
        while self.comparison_layout.count():
            item = self.comparison_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        grouped: dict[str, dict] = {}
        for row in rows:
            matricula = str(row.get("matricula", "")).strip()
            key = matricula or f"{row.get('nombre', '')}|{row.get('grupo', '')}"
            entry = grouped.setdefault(key, {
                "label": f"{row.get('nombre', 'Alumno')} · {matricula or 'sin matrícula'}",
                "rows": [],
            })
            entry["rows"].append(row)

        series = []
        for entry in grouped.values():
            ordered = sorted(entry["rows"], key=lambda r: str(r.get("inicio", "")))
            series.append((entry["label"], [_number(r.get("calificacion")) for r in ordered]))
        series.sort(key=lambda item: item[0].lower())

        if not series:
            self.comparison_layout.addWidget(StudentComparisonChart("Comparativa de alumnos", []))
            return
        chunk_size = 5
        total_charts = (len(series) + chunk_size - 1) // chunk_size
        for start in range(0, len(series), chunk_size):
            part = series[start:start + chunk_size]
            number = start // chunk_size + 1
            title = "Comparativa por sesión" if total_charts == 1 else f"Comparativa por sesión · grupo visual {number}/{total_charts}"
            self.comparison_layout.addWidget(StudentComparisonChart(title, part))

    def _fill_table(self, rows: list[dict]):
        display_rows = list(reversed(rows[-150:]))
        self.table.setRowCount(len(display_rows))
        level_names = {"primaria": "Primaria", "secundaria": "Secundaria", "preparatoria": "Prepa"}
        for r, row in enumerate(display_rows):
            started = row.get("inicio", "")
            try:
                date_text = datetime.fromisoformat(str(started)).strftime("%d/%m/%Y %H:%M:%S")
            except (ValueError, TypeError):
                date_text = started
            raw_level = str(row.get("nivel_educativo", ""))
            values = [
                row.get("nombre", ""), row.get("matricula", ""), row.get("grupo", ""),
                level_names.get(raw_level, raw_level.title() if raw_level else ""), date_text,
                _achieved(row), _not_achieved(row), row.get("calificacion", ""),
                "Importado" if row.get("origen") == "importado" else "Local",
            ]
            for c, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if c >= 4:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, c, item)

    def _open_student_from_selection(self, *args):
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, 1)
        if not item or not item.text().strip():
            return
        StudentDetailDialog(item.text().strip(), self.rows, self).exec()

    def _interpret(self, rows, avg_grade: float, completion: float, groups) -> str:
        if not rows:
            return "Interpretación automática · Aún no hay sesiones finalizadas. Al terminar una sesión aparecerán aquí el desempeño general, tendencias y grupos que requieren atención."
        if avg_grade >= 85:
            grade_text = "El avance global es alto"
        elif avg_grade >= 70:
            grade_text = "El avance global es adecuado, aunque todavía hay margen de práctica"
        else:
            grade_text = "El promedio global indica que conviene reforzar los ejercicios"
        if completion >= 85:
            completion_text = "La mayoría de las misiones evaluadas están logradas."
        elif completion >= 65:
            completion_text = "Hay un avance intermedio; conviene reforzar las misiones que aún quedan pendientes."
        else:
            completion_text = "Todavía hay varias misiones no logradas; se recomienda práctica guiada antes de aumentar dificultad."
        group_text = ""
        if groups:
            best = groups[0]
            worst = min(groups, key=lambda item: item[1])
            if len(groups) > 1:
                group_text = f" Mejor promedio por grupo: {best[0]} ({best[1]:.0f}). Grupo a observar: {worst[0]} ({worst[1]:.0f})."
        return f"Interpretación automática · {grade_text} ({avg_grade:.1f}/100). {completion_text}{group_text}"
