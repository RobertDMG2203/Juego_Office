APP_STYLE = r"""
/* ---------- Base ---------- */
QWidget {
    font-family: 'Segoe UI Variable', 'Segoe UI';
    color: #dfeaff;
    background: transparent;
    font-size: 13px;
}
QMainWindow, QWidget#root, QWidget#startRoot, QDialog {
    background: qradialgradient(cx:0.14, cy:0.05, radius:1.25,
        fx:0.14, fy:0.05, stop:0 #112638, stop:0.35 #0a1420, stop:1 #060a10);
}
QFrame#topbar {
    background: rgba(10, 18, 29, 235);
    border-bottom: 1px solid #20344b;
}
QLabel#brand { color: #f4f9ff; font-size: 20px; font-weight: 800; letter-spacing: 1px; }
QLabel#studentPill, QLabel#levelPill, QLabel#teacherBadge {
    color: #bcefff;
    background: #102638;
    border: 1px solid #24536e;
    border-radius: 15px;
    padding: 6px 13px;
    font-weight: 650;
}

/* ---------- Navegación del juego ---------- */
QPushButton#exitButton {
    background: #111d2b; color: #dce8f8; border: 1px solid #2b425d;
    border-radius: 11px; padding: 9px 14px; font-weight: 650;
}
QPushButton#exitButton:hover { background: #172a3d; border-color: #47749b; }
QPushButton.levelNav {
    background: #0f1a27; color: #aebfd3; border: 1px solid #253b55;
    border-radius: 11px; padding: 8px 11px; font-weight: 650;
}
QPushButton.levelNav:hover { background: #162a3d; color: #ecfbff; border-color: #347b9e; }
QPushButton.levelNav[active='true'] {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0d536c, stop:1 #0b3549);
    color: #c4f9ff; border: 1px solid #35d9f5;
}
QFrame#mission {
    background: rgba(13, 24, 37, 238); border: 1px solid #2a4058;
    border-radius: 18px;
}
QLabel#eyebrow { color: #7892ae; font-size: 11px; font-weight: 800; letter-spacing: 1px; }
QLabel#instruction { color: #f1f8ff; font-size: 22px; font-weight: 750; }
QLabel#shortcutBadge {
    color: #a2f5ff; background: #0b3041; border: 1px solid #18718d;
    border-radius: 11px; padding: 8px 13px; font-weight: 750;
}
QProgressBar { height: 9px; background: #111d2a; border: 1px solid #243951; border-radius: 5px; }
QProgressBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #1fbad7, stop:1 #69efff);
    border-radius: 4px;
}

/* ---------- Teclado gamer 3D ---------- */
QWidget#spanishKeyboard {
    background: transparent;
}
QFrame#keyboardFunctionBlock, QFrame#keyboardMainBlock,
QFrame#keyboardNavBlock, QFrame#keyboardNumBlock {
    background: rgba(5, 10, 16, 232);
    border: 1px solid #1d4052;
    border-radius: 16px;
}
QPushButton.key {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #2a394b, stop:0.11 #1c2938, stop:0.45 #101925, stop:0.82 #080d14, stop:1 #05080c);
    color: #f1fcff;
    border: 1px solid #34718a;
    border-top: 1px solid #4b8198;
    border-bottom: 6px solid #020407;
    border-right: 3px solid #03070b;
    border-radius: 11px;
    padding: 6px 5px 8px 5px;
    font-weight: 850;
    min-height: 39px;
    font-size: 12px;
}
QPushButton.key[compact='true'] { font-size: 11px; padding-left: 3px; padding-right: 3px; }
QPushButton.key:hover {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #31536a, stop:0.25 #17394b, stop:0.75 #0b1c29, stop:1 #07111a);
    color: #ffffff;
    border-color: #46e9ff;
    border-bottom: 6px solid #073044;
}
QPushButton.key:pressed, QPushButton.key[active='true'], QPushButton.key[physical='true'] {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #2186a1, stop:0.34 #15546d, stop:1 #0a2635);
    color: #d5fcff;
    border: 2px solid #6af0ff;
    border-bottom: 2px solid #1dd0ea;
    padding-top: 10px;
    padding-bottom: 5px;
}

/* ---------- Office simulado ---------- */
QTabWidget::pane {
    border: 1px solid #273b52; background: #0b131d; border-radius: 14px;
    top: -1px;
}
QTabBar::tab {
    background: #101b28; color: #91a6bd; border: 1px solid #263b52;
    border-bottom: 0; padding: 10px 19px; margin-right: 3px;
    border-top-left-radius: 10px; border-top-right-radius: 10px;
}
QTabBar::tab:hover { color: #dff8ff; background: #14283a; }
QTabBar::tab:selected { color: #8ef3ff; background: #0f2d40; border-color: #287b98; font-weight: 750; }
QToolButton {
    color: #cbd8e8; background: #101925; border: 1px solid #243951;
    border-radius: 11px; padding: 8px; min-width: 58px;
}
QToolButton:hover { background: #153047; border-color: #31bdda; color: white; }
QToolButton:pressed { background: #0d4459; }
QLabel#feedbackGood { color: #b9ffe8; background: #0a3328; border: 1px solid #197458; border-radius: 12px; padding: 9px 14px; font-weight: 750; }
QLabel#feedbackBad { color: #ffd7ce; background: #3b1918; border: 1px solid #7d3932; border-radius: 12px; padding: 9px 14px; font-weight: 750; }

/* ---------- Botones ---------- */
QPushButton.primary, QPushButton#startPrimary {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #087b9d, stop:1 #0ba6bd);
    color: white; border: 1px solid #38d7ec;
    border-radius: 14px; padding: 12px 21px; font-weight: 780;
}
QPushButton.primary:hover, QPushButton#startPrimary:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0a91b7, stop:1 #0fc0d3);
    border-color: #7ff4ff;
}
QPushButton.primary:pressed, QPushButton#startPrimary:pressed { padding-top: 14px; padding-bottom: 10px; }
QPushButton.secondary, QPushButton#startTeacher {
    background: #121f2e; color: #dce8f8; border: 1px solid #34516e;
    border-radius: 14px; padding: 11px 18px; font-weight: 680;
}
QPushButton.secondary:hover, QPushButton#startTeacher:hover { background: #1a3046; border-color: #4e86ad; }
QPushButton.danger {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #5a2523, stop:1 #7a2e2a);
    color: #ffe4df; border: 1px solid #a94d45; border-radius: 13px; padding: 11px 17px; font-weight: 750;
}
QPushButton.danger:hover { background: #87342f; border-color: #d66b60; }
QPushButton.dangerSoft {
    background: #321d1d; color: #ffd8d3; border: 1px solid #74423d;
    border-radius: 13px; padding: 10px 16px; font-weight: 700;
}
QPushButton.dangerSoft:hover { background: #482222; border-color: #a25249; }

/* ---------- Diálogos y controles ---------- */
QDialog { color: #e8f2ff; }
QDialog QLabel { color: #dfeaff; }
QLineEdit, QComboBox {
    background: #09121c; color: #f2f8ff; border: 1px solid #324b67;
    border-radius: 11px; padding: 9px 11px; selection-background-color: #087d9b;
    min-height: 20px;
}
QLineEdit:hover, QComboBox:hover { border-color: #416889; }
QLineEdit:focus, QComboBox:focus { border: 1px solid #39d7ef; background: #0b1723; }
QComboBox::drop-down { border: 0; width: 28px; }
QComboBox QAbstractItemView {
    background: #0d1722; color: #e4edf8; border: 1px solid #30465f;
    border-radius: 8px; selection-background-color: #17485f; outline: 0;
}
QMessageBox { background: #08111a; }
QMessageBox QLabel { color: #eef7ff; min-width: 260px; }
QMessageBox QPushButton {
    background: #142337; color: white; border: 1px solid #3d5775;
    border-radius: 10px; padding: 8px 15px; min-width: 76px;
}
QMessageBox QPushButton:hover { background: #1c3550; border-color: #54a0ce; }
QInputDialog { background: #08111a; }

/* ---------- Tablas ---------- */
QTableWidget {
    background: #09111a; alternate-background-color: #0c1621; color: #dce8f8;
    gridline-color: #1d3044; border: 1px solid #273d54; border-radius: 13px;
    selection-background-color: #164b65;
}
QTableWidget::item { padding: 6px; border: 0; }
QTableWidget::item:selected { background: #164b65; color: white; }
QHeaderView::section {
    background: #101e2d; color: #b4c8dd; border: 0;
    border-right: 1px solid #23384e; border-bottom: 1px solid #23384e;
    padding: 8px; font-weight: 750;
}
QTextEdit {
    background: #09121c; color: #e4edf8; border: 1px solid #2e465f;
    border-radius: 12px; selection-background-color: #164b64;
}
QScrollArea { background: transparent; border: 0; }
QScrollBar:vertical { background: #09121b; width: 10px; margin: 2px; border-radius: 5px; }
QScrollBar::handle:vertical { background: #2e526c; min-height: 32px; border-radius: 5px; }
QScrollBar::handle:vertical:hover { background: #3f7595; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

/* ---------- Pantalla de inicio ---------- */
QFrame#startCard {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 rgba(18,31,46,248), stop:1 rgba(8,18,28,248));
    border: 1px solid #2c4d68;
    border-radius: 30px;
}
QLabel#startIcon {
    font-size: 45px; color: #7cf2ff; background: #0b2635;
    border: 1px solid #286c82; border-radius: 22px; padding: 0;
}
QLabel#startEyebrow { color: #59dff1; font-size: 11px; font-weight: 850; letter-spacing: 2px; }
QLabel#startTitle { font-size: 37px; font-weight: 900; color: #f4f9ff; letter-spacing: 2px; }
QLabel#startSubtitle { font-size: 16px; color: #8fa4bb; }
QLabel#startLevel {
    color: #aaf5ff; background: #0d2c3c; border: 1px solid #20647d;
    border-radius: 13px; padding: 9px 13px; font-weight: 750;
}
QLabel#featureChip {
    color: #aebfd2; background: #0b1622; border: 1px solid #273e56;
    border-radius: 12px; padding: 7px 10px; font-size: 12px;
}
QLabel#startFooter { color: #60778f; font-size: 11px; }
QPushButton#startPrimary, QPushButton#startTeacher { min-height: 46px; max-height: 54px; font-size: 15px; }

/* ---------- Dashboard ---------- */
QLabel#dashboardTitle { color: #f4f9ff; font-size: 28px; font-weight: 870; }
QFrame#metricCard, QFrame#settingsCard {
    background: rgba(14, 24, 36, 245); border: 1px solid #2a4057; border-radius: 18px;
}
QFrame#maintenanceHero {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0d2a3b, stop:1 #101c2b);
    border: 1px solid #28647c; border-radius: 19px;
}
QFrame#dangerCard { background: #211516; border: 1px solid #5c3030; border-radius: 18px; }
QLabel#metricTitle { color: #7992ae; font-size: 10px; font-weight: 800; letter-spacing: 1px; }
QLabel#metricIcon { color: #4fe7fa; font-size: 20px; font-weight: 850; }
QLabel#metricValue { color: #82f3ff; font-size: 27px; font-weight: 880; }
QLabel#mutedText { color: #8397ae; }
QLabel#sectionTitle { color: #f0f7ff; font-size: 19px; font-weight: 780; }
QLabel#sectionTitleSmall { color: #edf6ff; font-size: 16px; font-weight: 760; }
QLabel#interpretation {
    color: #c9edf3; background: #0a2938; border: 1px solid #1d667d;
    border-radius: 14px; padding: 12px 15px;
}
QLabel#storageBadge {
    color: #b8f6ff; background: #0a2230; border: 1px solid #1c6078;
    border-radius: 11px; padding: 7px 10px; font-weight: 700;
}
QLabel#maintenanceNote {
    color: #9bb0c6; background: #0b1520; border: 1px solid #293d52;
    border-radius: 14px; padding: 12px 14px;
}
"""

# Nota: el bloque anterior define el tema completo. Estas reglas finales refinan
# controles añadidos al panel del profesor y mantienen la estética oscura.
APP_STYLE += r"""
QCheckBox {
    color: #dce8f6;
    spacing: 10px;
    font-weight: 650;
    padding: 7px 4px;
}
QCheckBox::indicator {
    width: 22px; height: 22px;
    border-radius: 7px;
    border: 1px solid #35516e;
    background: #09131e;
}
QCheckBox::indicator:hover { border-color: #47dff2; background: #0d2230; }
QCheckBox::indicator:checked {
    background: #0b8aa7;
    border: 2px solid #68efff;
}
"""

# Cinta de Office emulada: mantiene el tema oscuro general, pero organiza las
# herramientas con la jerarquía visual de las cintas de Word/PowerPoint/Excel.
APP_STYLE += r"""
QWidget#officeRibbon { background: transparent; }
QTabWidget#officeRibbonTabs::pane {
    border: 1px solid #2b4055;
    background: #111820;
    border-radius: 0 10px 10px 10px;
    top: -1px;
}
QTabWidget#officeRibbonTabs QTabBar::tab {
    background: #0d131a;
    color: #c4ccd7;
    border: 0;
    border-bottom: 2px solid transparent;
    padding: 8px 15px;
    margin-right: 1px;
    border-radius: 0;
}
QTabWidget#officeRibbonTabs QTabBar::tab:hover {
    background: #17212b;
    color: white;
}
QTabWidget#officeRibbonTabs QTabBar::tab:selected {
    background: #151e28;
    color: #ffffff;
    border-bottom: 2px solid #62dff1;
    font-weight: 750;
}
QFrame#officeRibbonPage { background: #111820; }
QFrame#ribbonGroup {
    background: #151d26;
    border: 0;
    border-right: 1px solid #34404c;
    border-radius: 5px;
}
QLabel#ribbonGroupLabel {
    color: #8d99a7;
    background: transparent;
    font-size: 10px;
    padding: 1px 5px 0 5px;
}
QToolButton#ribbonTool {
    color: #e7ebf0;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 5px;
    padding: 5px 6px;
    min-width: 52px;
    font-size: 11px;
    font-weight: 600;
}
QToolButton#ribbonTool[large='true'] {
    font-size: 12px;
    font-weight: 650;
    min-width: 68px;
}
QToolButton#ribbonTool:hover {
    background: #25313d;
    border-color: #435363;
    color: white;
}
QToolButton#ribbonTool:pressed {
    background: #334353;
    border-color: #5c7388;
}
"""
