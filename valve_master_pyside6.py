# valve_master_pyside6.py
import os
import sys
import textwrap
import threading
import urllib.error
import urllib.request
from typing import Callable

from PySide6.QtCore import Qt, QSettings, QSize, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QColor, QDesktopServices, QGuiApplication, QIcon, QPalette, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressDialog,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from valve_master_backend import (
    APP_NAME,
    PRODUCT_DISPLAY_NAMES,
    ParsedModel,
    OperatingTable,
    get_field_popup_details,
    process_model_structured,
    run_baseline_debug_benchmark,
    standard_product_configs,
)
try:
    from version import __version__
except ImportError:
    __version__ = "0.0.0"
from updater import UpdateInfo, check_for_update, download_and_apply

# ── Theme ─────────────────────────────────────────────────────────────────────
_DARK_MODE: bool = True  # default dark; overridden by QSettings at startup


def apply_light_theme(app: QApplication) -> None:
    global _DARK_MODE
    _DARK_MODE = False
    app.setStyle("Fusion")
    palette = QPalette()
    for role, color in [
        (QPalette.ColorRole.Window,          QColor(210, 212, 218)),
        (QPalette.ColorRole.WindowText,      QColor(25, 25, 25)),
        (QPalette.ColorRole.Base,            QColor(225, 227, 232)),
        (QPalette.ColorRole.AlternateBase,   QColor(200, 202, 208)),
        (QPalette.ColorRole.ToolTipBase,     QColor(255, 255, 220)),
        (QPalette.ColorRole.ToolTipText,     QColor(20, 20, 20)),
        (QPalette.ColorRole.Text,            QColor(25, 25, 25)),
        (QPalette.ColorRole.Button,          QColor(195, 198, 206)),
        (QPalette.ColorRole.ButtonText,      QColor(25, 25, 25)),
        (QPalette.ColorRole.BrightText,      QColor(180, 0, 0)),
        (QPalette.ColorRole.Highlight,       QColor(72, 124, 255)),
        (QPalette.ColorRole.HighlightedText, QColor(255, 255, 255)),
        (QPalette.ColorRole.Link,            QColor(0, 90, 200)),
    ]:
        palette.setColor(role, color)
    app.setPalette(palette)


def apply_dark_theme(app: QApplication) -> None:
    global _DARK_MODE
    _DARK_MODE = True
    app.setStyle("Fusion")
    palette = QPalette()
    for role, color in [
        (QPalette.ColorRole.Window,          QColor(28, 28, 28)),
        (QPalette.ColorRole.WindowText,      QColor(230, 230, 230)),
        (QPalette.ColorRole.Base,            QColor(18, 18, 18)),
        (QPalette.ColorRole.AlternateBase,   QColor(35, 35, 35)),
        (QPalette.ColorRole.ToolTipBase,     QColor(240, 240, 240)),
        (QPalette.ColorRole.ToolTipText,     QColor(20, 20, 20)),
        (QPalette.ColorRole.Text,            QColor(230, 230, 230)),
        (QPalette.ColorRole.Button,          QColor(45, 45, 45)),
        (QPalette.ColorRole.ButtonText,      QColor(235, 235, 235)),
        (QPalette.ColorRole.BrightText,      QColor(255, 90, 90)),
        (QPalette.ColorRole.Highlight,       QColor(72, 124, 255)),
        (QPalette.ColorRole.HighlightedText, QColor(255, 255, 255)),
        (QPalette.ColorRole.Link,            QColor(102, 169, 255)),
    ]:
        palette.setColor(role, color)
    app.setPalette(palette)

# ──────────────────────────────────────────────────────────────────────────────

ICON_FILE = "valve_master.ico"
BACKGROUND_FILE = "vmt_logo_transparent.png"

# Resolve the directory containing assets (the .ico and .png).
# When running as a PyInstaller --onefile bundle, files are extracted to a
# temporary folder referenced by sys._MEIPASS.  When running as a plain
# script, use the directory of this .py file.
if getattr(sys, "frozen", False):
    BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WINDOW_MIN_W = 1180
WINDOW_MIN_H = 780

CARD_MIN_HEIGHT = 68
CARD_MAX_HEIGHT = 86
CARD_TEXT_WRAP = 34

ACTION_BUTTON_HEIGHT = 28
MODEL_LIST_ROW_HEIGHT = 24
MODEL_LIST_HEIGHT = 90

TABLE_MIN_HEIGHT = 190

# Debounce delay (ms) for live decode-as-you-type
LIVE_DECODE_DELAY_MS = 400

FIELD_TO_CONFIG_KEY = {
    "Valve Family": "family_map",
    "Construction": "construction_map",
    "Valve Construction": "construction_map",
    "Chemical Resistance": "construction_map",
    "Bodies": "bodies_map",
    "Valve Bodies": "bodies_map",
    "Size": "size_map",
    "Valve Size": "size_map",
    "Pressure": "pressure_map",
    "Pressure Rating": "pressure_map",
    "Flow/Pressure Operating": "pressure_map",
    "Valve Design": "design_map",
    "Body Design": "design_map",
    "Control Type": "control_map",
    "Actuator Type": "control_map",
    "Controller": "controller_map",
    "Valve Controller Designation": "controller_map",
    "Controller Type": "controller_map",
    "Orientation": "orientation_map",
    "Valve Orientation": "orientation_map",
    "Fail-Safe": "failsafe_map",
    "Failsafe Position": "failsafe_map",
    "Fail-Safe Module": "failsafe_map",
    "Communication Protocol": "protocol_map",
    "Options": "option_map",
}

FIELD_TO_LOGICAL_FIELD: dict[str, str] = {
    "Construction": "construction",
    "Valve Construction": "construction",
    "Chemical Resistance": "construction",
    "Bodies": "bodies",
    "Valve Bodies": "bodies",
    "Size": "size",
    "Valve Size": "size",
    "Pressure": "pressure",
    "Pressure Rating": "pressure",
    "Flow/Pressure Operating": "pressure",
    "Valve Design": "design",
    "Body Design": "design",
    "Control Type": "control",
    "Actuator Type": "control",
    "Controller": "controller",
    "Valve Controller Designation": "controller",
    "Controller Type": "controller",
    "Orientation": "orientation",
    "Valve Orientation": "orientation",
    "Fail-Safe": "failsafe",
    "Failsafe Position": "failsafe",
    "Fail-Safe Module": "failsafe",
    "Communication Protocol": "protocol",
    "Options": "options",
    "Valve Family": "family",
}

# EDITABLE_FIELDS is derived from FIELD_TO_CONFIG_KEY to avoid the two drifting
# out of sync. "Valve Family" is intentionally excluded — it is informational only.
EDITABLE_FIELDS: set[str] = {
    key for key in FIELD_TO_CONFIG_KEY if key != "Valve Family"
}

# Fixed: corrected the 3 valid models that previously had invalid orientation/failsafe codes
VALID_TEST_MODELS = [
    "MAVA108M-AMEHZ-REI",
    "EXVA108M-ANHHO-P",
    "HEVA108L-SIAHZ-WRE",
]

FAILING_TEST_MODELS = [
    "MAVA114L-ALHHZ",
    "MAVD208M-AAEHN-SFB",
    "BEVA108L-LQFHZ",
]


def compact_text(value: str, width: int = CARD_TEXT_WRAP, max_lines: int = 2) -> str:
    wrapped = textwrap.wrap(value, width=width) or [value]
    if len(wrapped) <= max_lines:
        return "\n".join(wrapped)
    visible = wrapped[:max_lines]
    last = visible[-1]
    if len(last) > max(3, width - 3):
        last = last[: width - 3]
    visible[-1] = last.rstrip() + "..."
    return "\n".join(visible)


def format_spare_parts_lines(spare_parts: list[dict]) -> list[str]:
    """Format a list of spare part dicts into display lines for picker dialogs."""
    lines: list[str] = []
    for spare in spare_parts:
        qty = spare.get("quantity", 1)
        prefix = f"Qty {qty} x " if qty and qty != 1 else ""
        lines.append(f"{prefix}{spare.get('part_number', '')} — {spare.get('description', '')}")
        for note in spare.get("notes", []) or []:
            lines.append(f"    Note: {note}")
    return lines


class BadgeLabel(QLabel):
    def __init__(self, text: str = "", kind: str = "neutral") -> None:
        super().__init__(text)
        self._kind = kind
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(26)
        self.set_kind(kind)

    @property
    def kind(self) -> str:
        return self._kind

    def set_kind(self, kind: str) -> None:
        self._kind = kind
        if _DARK_MODE:
            styles = {
                "neutral": ("#e8e8e8", "#383838", "#505050"),
                "blue":    ("#93c5fd", "#1e3a5f", "#2563eb"),
                "green":   ("#4ade80", "#14301f", "#16a34a"),
                "red":     ("#f87171", "#3b1010", "#dc2626"),
                "gold":    ("#fbbf24", "#3b2500", "#f59e0b"),
            }
        else:
            styles = {
                "neutral": ("#191919", "#c3c6ce", "#a8acb8"),
                "blue":    ("#ffffff", "#487cff", "#3068ee"),
                "green":   ("#ffffff", "#22c55e", "#16a34a"),
                "red":     ("#ffffff", "#ef4444", "#dc2626"),
                "gold":    ("#ffffff", "#f59e0b", "#d97706"),
            }
        fg, bg, border = styles.get(kind, styles["neutral"])
        self.setStyleSheet(
            f"""
            QLabel {{
                color: {fg};
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 12px;
                padding: 3px 10px;
                font-weight: 600;
                font-size: 12px;
            }}
            """
        )


class SectionCard(QFrame):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("SectionCard")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(10, 6, 10, 10)
        self._layout.setSpacing(6)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("SectionTitle")
        self._layout.addWidget(self.title_label)

    def add_widget(self, widget: QWidget) -> None:
        self._layout.addWidget(widget)

    def add_layout(self, layout) -> None:
        self._layout.addLayout(layout)

    def add_spacing(self, spacing: int) -> None:
        self._layout.addSpacing(spacing)

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)


class BenchmarkDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Benchmark Results")
        self.resize(980, 680)

        layout = QVBoxLayout(self)
        text_box = QTextEdit()
        text_box.setReadOnly(True)
        text_box.setPlainText(run_baseline_debug_benchmark())
        layout.addWidget(text_box)


class OptionPickerDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        title: str,
        field_name: str,
        entries: list[dict],
        on_pick: Callable[[str], None],
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(820, 560)
        self.on_pick = on_pick

        layout = QVBoxLayout(self)

        header = QLabel(field_name)
        header.setStyleSheet("font-size: 13pt; font-weight: 700; color: #487cff;")
        layout.addWidget(header)

        sub_color = "#999999" if _DARK_MODE else "#555b66"
        sub = QLabel("Dark = valid now • Grey = not valid now (reason shown)")
        sub.setStyleSheet(f"color: {sub_color}; font-size: 10pt;")
        layout.addWidget(sub)

        list_bg     = "#121212"  if _DARK_MODE else "#e1e3e8"
        list_border = "#404040"  if _DARK_MODE else "#b0b4be"
        item_sep    = "#2a2a2a"  if _DARK_MODE else "#c8cad0"
        list_text   = "#ececec"  if _DARK_MODE else "#191919"

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            f"""
            QListWidget {{
                background: {list_bg}; color: {list_text};
                border: 1px solid {list_border}; border-radius: 10px; padding: 6px;
            }}
            QListWidget::item {{
                padding: 10px; border-bottom: 1px solid {item_sep};
            }}
            """
        )

        valid_fg   = QColor("#ececec") if _DARK_MODE else QColor("#191919")
        invalid_fg = QColor("#6b7280") if _DARK_MODE else QColor("#9ca3af")

        for entry in entries:
            code = entry["code"]
            desc = entry["desc"]
            valid = entry["valid"]
            reason = entry["reason"]
            spare_parts = entry.get("spare_parts", [])

            text = f"{code}  —  {desc}"
            if not valid and reason:
                text += f"\n    \u26a0 Not valid now: {reason}"
            for line in format_spare_parts_lines(spare_parts):
                text += f"\n    \U0001f527 {line}"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, code)
            item.setForeground(valid_fg if valid else invalid_fg)
            self.list_widget.addItem(item)

        self.list_widget.itemDoubleClicked.connect(self._handle_pick)
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        apply_btn = QPushButton("Apply Selected")
        apply_btn.clicked.connect(self._apply_selected)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)

        btn_row.addStretch(1)
        btn_row.addWidget(apply_btn)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _apply_selected(self) -> None:
        item = self.list_widget.currentItem()
        if item is None:
            return
        self._handle_pick(item)

    def _handle_pick(self, item: QListWidgetItem) -> None:
        code = item.data(Qt.ItemDataRole.UserRole)
        if code is None:
            return
        self.on_pick(str(code))
        self.accept()


class OptionsEditorDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        current_options: list[str],
        entries: list[dict],
        on_done: Callable[[list[str]], None],
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Options")
        self.resize(900, 600)
        self.on_done = on_done
        self.working_options = list(current_options)
        self.entries = entries

        layout = QVBoxLayout(self)

        header = QLabel("Options")
        header.setStyleSheet("font-size: 13pt; font-weight: 700; color: #487cff;")
        layout.addWidget(header)

        sub_color = "#999999" if _DARK_MODE else "#555b66"
        sub = QLabel("Double-click an option to add/remove it. Dark = valid now • Grey = not valid now")
        sub.setStyleSheet(f"color: {sub_color}; font-size: 10pt;")
        layout.addWidget(sub)

        list_bg     = "#121212"  if _DARK_MODE else "#e1e3e8"
        list_border = "#404040"  if _DARK_MODE else "#b0b4be"
        item_sep    = "#2a2a2a"  if _DARK_MODE else "#c8cad0"
        list_text   = "#ececec"  if _DARK_MODE else "#191919"

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            f"""
            QListWidget {{
                background: {list_bg}; color: {list_text};
                border: 1px solid {list_border}; border-radius: 10px; padding: 6px;
            }}
            QListWidget::item {{
                padding: 10px; border-bottom: 1px solid {item_sep};
            }}
            """
        )
        layout.addWidget(self.list_widget)

        self._refresh()
        self.list_widget.itemDoubleClicked.connect(self._toggle_item)

        btn_row = QHBoxLayout()
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._apply)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        btn_row.addStretch(1)
        btn_row.addWidget(apply_btn)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _refresh(self) -> None:
        self.list_widget.clear()
        selected = set(self.working_options)

        for entry in self.entries:
            code = entry["code"]
            desc = entry["desc"]
            valid = entry["valid"]
            reason = entry["reason"]
            spare_parts = entry.get("spare_parts", [])
            included = code in selected

            state = "[X]" if included else "[ ]"
            text = f"{state} {code}  —  {desc}"
            if not valid and reason:
                text += f"\n    \u26a0 Not valid now: {reason}"
            for line in format_spare_parts_lines(spare_parts):
                text += f"\n    \U0001f527 {line}"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, code)
            valid_fg   = QColor("#ececec") if _DARK_MODE else QColor("#191919")
            invalid_fg = QColor("#6b7280") if _DARK_MODE else QColor("#9ca3af")
            item.setForeground(valid_fg if valid else invalid_fg)
            self.list_widget.addItem(item)

    def _toggle_item(self, item: QListWidgetItem) -> None:
        code = str(item.data(Qt.ItemDataRole.UserRole))
        if code in self.working_options:
            self.working_options.remove(code)
        else:
            self.working_options.append(code)
        self.working_options = sorted(dict.fromkeys(self.working_options))
        self._refresh()

    def _apply(self) -> None:
        self.on_done(self.working_options)
        self.accept()


class ClickableFieldCard(QPushButton):
    def __init__(self, field_name: str, field_value: str, invalid: bool = False, editable: bool = False) -> None:
        super().__init__()
        self.field_name = field_name
        self.field_value = field_value
        self.invalid = invalid
        self.editable = editable

        self.setObjectName("FieldCardButton")
        self.setCursor(
            Qt.CursorShape.PointingHandCursor if editable
            else Qt.CursorShape.ArrowCursor
        )
        self.setFlat(True)
        self.setMinimumHeight(CARD_MIN_HEIGHT)
        self.setMaximumHeight(CARD_MAX_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._build_ui()

    def _build_ui(self) -> None:
        # FIX: replace "(click to edit)" text with a ✏ icon indicator
        # This removes noisy helper text and gives cleaner card height
        edit_indicator = "  ✏" if self.editable else ""
        status = "✖" if self.invalid else "✔"
        compact_value = compact_text(self.field_value, width=CARD_TEXT_WRAP, max_lines=2)
        self.setText(f"{status}  {self.field_name}{edit_indicator}\n{compact_value}")
        self.setToolTip(
            f"{self.field_name}\n\n{self.field_value}"
            + ("\n\n✏ Click to edit" if self.editable else "")
        )
        self.setStyleSheet(self._style())

    def _style(self) -> str:
        if _DARK_MODE:
            if self.invalid:
                return """
                QPushButton#FieldCardButton {
                    text-align: left; padding: 8px 8px 8px 12px;
                    background: #251417; color: #fca5a5;
                    border: 1px solid #7f1d1d; border-left: 3px solid #ef4444;
                    border-radius: 10px; font-weight: 600; font-size: 10pt;
                }
                QPushButton#FieldCardButton:hover {
                    background: #31191d; border: 1px solid #ef4444;
                    border-left: 3px solid #f87171;
                }
                """
            if self.editable:
                return """
                QPushButton#FieldCardButton {
                    text-align: left; padding: 8px 8px 8px 12px;
                    background: #0b1220; color: #e5e7eb;
                    border: 1px solid #243244; border-left: 3px solid #22c55e;
                    border-radius: 10px; font-weight: 600; font-size: 10pt;
                }
                QPushButton#FieldCardButton:hover {
                    background: #111a2b; border: 1px solid #22c55e;
                    border-left: 3px solid #4ade80;
                }
                """
            return """
            QPushButton#FieldCardButton {
                text-align: left; padding: 8px 8px 8px 12px;
                background: #0b1220; color: #cbd5e1;
                border: 1px solid #243244; border-left: 3px solid #334155;
                border-radius: 10px; font-weight: 600; font-size: 10pt;
            }
            QPushButton#FieldCardButton:hover {
                background: #111a2b; border: 1px solid #334155;
                border-left: 3px solid #475569;
            }
            """
        else:
            if self.invalid:
                return """
                QPushButton#FieldCardButton {
                    text-align: left; padding: 8px 8px 8px 12px;
                    background: rgba(255, 220, 220, 220); color: #7f1d1d;
                    border: 1px solid #fca5a5; border-left: 3px solid #ef4444;
                    border-radius: 10px; font-weight: 600; font-size: 10pt;
                }
                QPushButton#FieldCardButton:hover {
                    background: rgba(255, 200, 200, 220); border: 1px solid #ef4444;
                    border-left: 3px solid #dc2626;
                }
                """
            if self.editable:
                return """
                QPushButton#FieldCardButton {
                    text-align: left; padding: 8px 8px 8px 12px;
                    background: rgba(220, 222, 228, 220); color: #191919;
                    border: 1px solid #b0b4be; border-left: 3px solid #22c55e;
                    border-radius: 10px; font-weight: 600; font-size: 10pt;
                }
                QPushButton#FieldCardButton:hover {
                    background: rgba(200, 202, 210, 220); border: 1px solid #22c55e;
                    border-left: 3px solid #16a34a;
                }
                """
            return """
            QPushButton#FieldCardButton {
                text-align: left; padding: 8px 8px 8px 12px;
                background: rgba(220, 222, 228, 220); color: #191919;
                border: 1px solid #b0b4be; border-left: 3px solid #a8acb8;
                border-radius: 10px; font-weight: 600; font-size: 10pt;
            }
            QPushButton#FieldCardButton:hover {
                background: rgba(200, 202, 210, 220); border: 1px solid #9098a8;
                border-left: 3px solid #487cff;
            }
            """


class ValidationIssueRow(QFrame):
    """A styled row widget for a single validation issue in the Validation tab."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__()
        self.setObjectName("ValidationIssueRow")
        if _DARK_MODE:
            frame_style = """
                QFrame#ValidationIssueRow {
                    background: #2a0f0f; border: 1px solid #7f1d1d;
                    border-left: 3px solid #ef4444; border-radius: 8px; margin: 2px 0px;
                }"""
            field_color = "color: #fca5a5;"
            msg_color   = "color: #e5e7eb;"
        else:
            frame_style = """
                QFrame#ValidationIssueRow {
                    background: rgba(255, 220, 220, 180); border: 1px solid #fca5a5;
                    border-left: 3px solid #ef4444; border-radius: 8px; margin: 2px 0px;
                }"""
            field_color = "color: #b91c1c;"
            msg_color   = "color: #191919;"

        self.setStyleSheet(frame_style)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(2)

        field_label = QLabel(field)
        field_label.setStyleSheet(f"{field_color} font-weight: 700; font-size: 10pt; background: transparent;")
        layout.addWidget(field_label)

        msg_label = QLabel(message)
        msg_label.setStyleSheet(f"{msg_color} font-size: 10pt; background: transparent;")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)


class UpdateBanner(QFrame):
    """
    Slim banner shown in the status bar when an update is available.
    Matches the style of the Project Tracking Tool updater.
    """

    install_clicked = Signal()

    def __init__(self, info: "UpdateInfo", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("UpdateBanner")
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)

        msg = QLabel(
            f"🆕  Update available — v{info.latest_version} is ready. "
            f"You're on v{info.current_version}."
        )
        msg.setObjectName("UpdateMsg")
        layout.addWidget(msg, 1)

        if info.release_notes:
            notes_btn = QPushButton("What's new?")
            notes_btn.setFixedWidth(100)
            notes_btn.clicked.connect(lambda: QMessageBox.information(
                self,
                f"What's new in v{info.latest_version}",
                info.release_notes,
            ))
            layout.addWidget(notes_btn)

        install_btn = QPushButton("Install & Restart")
        install_btn.setFixedWidth(140)
        install_btn.setObjectName("InstallBtn")
        install_btn.clicked.connect(self.install_clicked)
        layout.addWidget(install_btn)

        dismiss_btn = QPushButton("✕")
        dismiss_btn.setFixedWidth(32)
        dismiss_btn.setToolTip("Dismiss")
        dismiss_btn.clicked.connect(self.hide)
        layout.addWidget(dismiss_btn)


class WatermarkWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.logo_label = QLabel(self)
        self.logo_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.logo_label.setStyleSheet("background: transparent;")
        self.logo_pixmap_original: QPixmap | None = None

        opacity_effect = QGraphicsOpacityEffect(self.logo_label)
        opacity_effect.setOpacity(0.25)
        self.logo_label.setGraphicsEffect(opacity_effect)

    def set_watermark(self, image_path: str) -> None:
        if os.path.exists(image_path):
            self.logo_pixmap_original = QPixmap(image_path)
            self._update_watermark()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_watermark()

    def _update_watermark(self) -> None:
        if self.logo_pixmap_original is None or self.logo_pixmap_original.isNull():
            self.logo_label.hide()
            return

        max_w = max(220, int(self.width() * 0.38))
        max_h = max(220, int(self.height() * 0.38))

        scaled = self.logo_pixmap_original.scaled(
            max_w,
            max_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.logo_label.setPixmap(scaled)
        self.logo_label.adjustSize()

        x = self.width() - self.logo_label.width() - 24
        y = self.height() - self.logo_label.height() - 24
        self.logo_label.move(max(0, x), max(0, y))
        # Raise above all sibling widgets that were added after __init__
        self.logo_label.raise_()
        self.logo_label.show()


class ValveMasterMainWindow(QMainWindow):
    _update_ready = Signal()   # emitted from bg thread when a new version is found

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{__version__}")
        self.resize(1500, 940)
        self.setMinimumSize(WINDOW_MIN_W, WINDOW_MIN_H)

        self.current_save_path: str | None = None
        self.current_output_text: str = ""
        self.current_product_line: str = "UNKNOWN"
        self.current_data: dict[str, str] = {}
        self.current_notes: list[str] = []
        self.current_validation_issues: list[dict] = []
        self.current_parsed_model: ParsedModel | None = None
        self.current_operating_table: OperatingTable | None = None
        self.show_test_models: bool = True
        self._pending_update_info: UpdateInfo | None = None
        self._update_banner: UpdateBanner | None = None

        self._field_card_specs: list[tuple[str, str, bool, bool]] = []

        # debounce timer for live decode-as-you-type
        self._decode_timer = QTimer(self)
        self._decode_timer.setSingleShot(True)
        self._decode_timer.setInterval(LIVE_DECODE_DELAY_MS)
        self._decode_timer.timeout.connect(self._live_decode)

        # update signal — fired from background thread, handled on UI thread
        self._update_ready.connect(self._show_update_banner)

        self._load_window_icon()
        self._build_menu()
        self._build_ui()
        self._load_background_watermark()
        self._apply_styles()

        # Startup checks (after UI is built)
        self._check_sync_folder()
        threading.Thread(target=self._check_update_bg, daemon=True).start()

    # ------------------------------------------------------------------ #
    # Qt overrides                                                         #
    # ------------------------------------------------------------------ #

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._rebuild_field_cards()

    # ------------------------------------------------------------------ #
    # Initialisation helpers                                               #
    # ------------------------------------------------------------------ #

    def _load_window_icon(self) -> None:
        icon_path = os.path.join(BASE_DIR, ICON_FILE)
        if os.path.exists(icon_path):
            # Load the .ico as a pixmap scaled to 256x256 so the OS can
            # pick a large size for the title bar and taskbar
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                icon = QIcon()
                for size in (16, 32, 48, 64, 128, 256):
                    icon.addPixmap(
                        pixmap.scaled(size, size,
                                      Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)
                    )
                self.setWindowIcon(icon)
                # Also set on the application so taskbar picks it up
                app = QApplication.instance()
                if isinstance(app, QApplication):
                    app.setWindowIcon(icon)

    def _load_background_watermark(self) -> None:
        bg_path = os.path.join(BASE_DIR, BACKGROUND_FILE)
        self.watermark_widget.set_watermark(bg_path)
        # Force a raise after all child panels have been laid out
        self.watermark_widget.logo_label.raise_()

    def _build_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_output)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save As...", self)
        save_as_action.triggered.connect(self.save_output_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        tools_menu = menubar.addMenu("Tools")
        benchmark_action = QAction("Run Benchmark", self)
        benchmark_action.triggered.connect(self.show_benchmark_results)
        tools_menu.addAction(benchmark_action)

        copy_action = QAction("Copy Summary", self)
        copy_action.triggered.connect(self.copy_output)
        tools_menu.addAction(copy_action)

        view_menu = menubar.addMenu("View")
        self._dark_mode_action = QAction("Dark Mode", self, checkable=True)
        self._dark_mode_action.setChecked(_DARK_MODE)
        self._dark_mode_action.triggered.connect(self._toggle_dark_mode)
        view_menu.addAction(self._dark_mode_action)

        view_menu.addSeparator()

        self.toggle_debug_action = QAction("Show Debug Tab", self, checkable=True)
        self.toggle_debug_action.setChecked(True)
        self.toggle_debug_action.triggered.connect(self.toggle_debug_panel)
        view_menu.addAction(self.toggle_debug_action)

        self.toggle_tests_action = QAction("Show Test Models", self, checkable=True)
        self.toggle_tests_action.setChecked(True)
        self.toggle_tests_action.triggered.connect(self.toggle_test_models)
        view_menu.addAction(self.toggle_tests_action)

        help_menu = menubar.addMenu("Help")
        version_history_action = QAction("Version History && Recent Updates", self)
        version_history_action.triggered.connect(self.show_version_history)
        help_menu.addAction(version_history_action)

        help_menu.addSeparator()

        email_action = QAction("Email Support", self)
        email_action.triggered.connect(self._email_support)
        help_menu.addAction(email_action)

        help_menu.addSeparator()

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    # ------------------------------------------------------------------ #
    # UI construction                                                      #
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        self.watermark_widget = WatermarkWidget()
        self.setCentralWidget(self.watermark_widget)

        root_layout = QVBoxLayout(self.watermark_widget)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)
        root_layout.addWidget(self._build_header())

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setOpaqueResize(True)
        root_layout.addWidget(self.main_splitter, 1)

        self.main_splitter.addWidget(self._build_left_panel())
        self.main_splitter.addWidget(self._build_center_panel())
        self.main_splitter.addWidget(self._build_right_panel())

        self.main_splitter.setStretchFactor(0, 2)
        self.main_splitter.setStretchFactor(1, 7)
        self.main_splitter.setStretchFactor(2, 4)
        self.main_splitter.setSizes([320, 840, 380])

        # Update banner — hidden until a new version is detected
        self._update_banner = None

        status = QStatusBar()
        status.showMessage("Valve Master Tool | Guided model builder ready")
        self.setStatusBar(status)

    def _build_header(self) -> QWidget:
        card = QFrame()
        card.setObjectName("HeaderCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        title = QLabel(APP_NAME)
        title.setObjectName("AppTitle")
        subtitle = QLabel("Phoenix valve model decoder / guided model builder")
        subtitle.setObjectName("SubTitle")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        layout.addLayout(title_col, 1)

        self.mode_badge = BadgeLabel("Normal Mode", "gold")
        self.product_badge = BadgeLabel("Product: —", "blue")
        self.validation_badge = BadgeLabel("No validation run yet", "neutral")

        layout.addWidget(self.mode_badge)
        layout.addWidget(self.product_badge)
        layout.addWidget(self.validation_badge)
        return card

    def _build_left_panel(self) -> QWidget:
        self.left_panel_container = QWidget()
        layout = QVBoxLayout(self.left_panel_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._build_input_card(), 0)
        layout.addWidget(self._build_table_card(), 0)
        layout.addWidget(self._build_test_models_card(), 0)
        layout.addStretch(1)
        return self.left_panel_container

    def _build_input_card(self) -> SectionCard:
        self.input_card = SectionCard("Input")
        self.input_card.add_widget(QLabel("Model Number"))

        self.model_entry = QLineEdit()
        self.model_entry.setPlaceholderText("Enter a model number...")
        self.model_entry.returnPressed.connect(self.decode_and_display)
        # FIX: live decode-as-you-type via debounced timer
        self.model_entry.textChanged.connect(self._on_model_text_changed)
        self.input_card.add_widget(self.model_entry)

        self.analog_checkbox = QCheckBox("Analog Mode")
        self.analog_checkbox.stateChanged.connect(self._on_analog_changed)
        self.input_card.add_widget(self.analog_checkbox)

        row1 = QHBoxLayout()
        row1.setSpacing(8)
        self.decode_button = QPushButton("Decode")
        self.decode_button.setObjectName("PrimaryButton")
        self.decode_button.clicked.connect(self.decode_and_display)
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_output)
        row1.addWidget(self.decode_button)
        row1.addWidget(self.clear_button)
        self.input_card.add_layout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        self.copy_button = QPushButton("Copy Summary")
        self.copy_button.clicked.connect(self.copy_output)
        self.save_button = QPushButton("Save Summary")
        self.save_button.clicked.connect(self.save_output)
        row2.addWidget(self.copy_button)
        row2.addWidget(self.save_button)
        self.input_card.add_layout(row2)

        self._builder_helper = QLabel(
            "Builder Help:\n"
            "• Click ✏ field cards to change codes."
        )
        self._builder_helper.setWordWrap(True)
        self._apply_helper_style()
        self.input_card.add_widget(self._builder_helper)

        return self.input_card

    def _build_table_card(self) -> SectionCard:
        self.table_card = SectionCard("Flow / Pressure Operating Table")
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(
            ["Size", "Single CFM", "Dual CFM", "Pressure Drop"]
        )
        header = self.table_widget.horizontalHeader()
        for col in range(3):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setWordWrap(True)
        self.table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table_widget.setMinimumHeight(TABLE_MIN_HEIGHT)
        self.table_widget.setMaximumHeight(TABLE_MIN_HEIGHT)
        self.table_card.add_widget(self.table_widget)
        return self.table_card

    def _build_test_models_card(self) -> SectionCard:
        self.test_models_card = SectionCard("Quick Test Models")
        self.test_models_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Valid group
        valid_color = "#4ade80" if _DARK_MODE else "#16a34a"
        self._valid_label = QLabel("✔  Valid Models")
        self._valid_label.setStyleSheet(
            f"color: {valid_color}; font-weight: 700; font-size: 10pt; "
            "padding: 4px 0px 2px 0px; background: transparent;"
        )
        self.test_models_card.add_widget(self._valid_label)

        self.valid_models_list = QListWidget()
        self._configure_model_list(self.valid_models_list, VALID_TEST_MODELS, item_color=valid_color)
        self.valid_models_list.setFixedHeight(MODEL_LIST_HEIGHT)
        self.valid_models_list.itemDoubleClicked.connect(self._load_model_from_list)
        self.test_models_card.add_widget(self.valid_models_list)

        self.test_models_card.add_spacing(4)

        # Failing group
        failing_color = "#f87171" if _DARK_MODE else "#dc2626"
        self._failing_label = QLabel("✖  Failing Models")
        self._failing_label.setStyleSheet(
            f"color: {failing_color}; font-weight: 700; font-size: 10pt; "
            "padding: 8px 0px 2px 0px; background: transparent;"
        )
        self.test_models_card.add_widget(self._failing_label)

        self.failing_models_list = QListWidget()
        self._configure_model_list(self.failing_models_list, FAILING_TEST_MODELS, item_color=failing_color)
        self.failing_models_list.setFixedHeight(MODEL_LIST_HEIGHT)
        self.failing_models_list.itemDoubleClicked.connect(self._load_model_from_list)
        self.test_models_card.add_widget(self.failing_models_list)

        return self.test_models_card

    @staticmethod
    def _configure_model_list(widget: QListWidget, models: list[str], item_color: str = "#e5e7eb") -> None:
        widget.setUniformItemSizes(True)
        widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        widget.setSpacing(0)
        list_bg      = "#0b1220" if _DARK_MODE else "#e1e3e8"
        list_border  = "#1e293b" if _DARK_MODE else "#b0b4be"
        scroll_track = "#1c1c1c" if _DARK_MODE else "#d2d4da"
        scroll_thumb = "#334155" if _DARK_MODE else "#a8acb8"
        hover_bg     = "#151f35" if _DARK_MODE else "rgba(72, 124, 255, 60)"
        selected_bg  = "#1d4ed8" if _DARK_MODE else "#487cff"

        widget.setStyleSheet(
            f"""
            QListWidget {{
                background: {list_bg};
                border: 1px solid {list_border};
                border-radius: 8px;
                padding: 3px;
                font-size: 10pt;
                font-family: Consolas, monospace;
                outline: none;
            }}
            QListWidget::item {{
                color: {item_color};
                padding: 3px 8px;
                border-radius: 4px;
                min-height: {MODEL_LIST_ROW_HEIGHT}px;
            }}
            QListWidget::item:selected {{
                background: {selected_bg};
                color: #ffffff;
            }}
            QListWidget::item:hover:!selected {{
                background: {hover_bg};
            }}
            QScrollBar:vertical {{
                background: {scroll_track};
                width: 5px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {scroll_thumb};
                border-radius: 2px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            """
        )
        for model in models:
            item = QListWidgetItem(model)
            item.setSizeHint(QSize(0, MODEL_LIST_ROW_HEIGHT))
            item.setForeground(QColor(item_color))
            widget.addItem(item)

    def _load_model_from_list(self, item: QListWidgetItem) -> None:
        self.load_example_model(item.text())

    def _build_center_panel(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.decoded_card = SectionCard("Decoded Fields")

        self.cards_container = QWidget()
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setContentsMargins(2, 2, 2, 2)
        self.cards_layout.setHorizontalSpacing(8)
        self.cards_layout.setVerticalSpacing(8)

        self.decoded_card.add_widget(self.cards_container)
        layout.addWidget(self.decoded_card, 0, Qt.AlignmentFlag.AlignTop)
        layout.addStretch(1)
        return container

    def _build_right_panel(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.tabs = QTabWidget()

        self.notes_text = QTextEdit()
        self.notes_text.setReadOnly(True)

        # FIX: Validation tab uses a scrollable widget container for styled rows
        # instead of plain text, so each issue is a distinct colored card
        self._validation_scroll_widget = QWidget()
        self._validation_scroll_layout = QVBoxLayout(self._validation_scroll_widget)
        self._validation_scroll_layout.setContentsMargins(6, 6, 6, 6)
        self._validation_scroll_layout.setSpacing(4)
        self._validation_scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._validation_scroll = QScrollArea()
        self._validation_scroll.setWidgetResizable(True)
        self._validation_scroll.setWidget(self._validation_scroll_widget)
        self._apply_scroll_style()

        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)

        self.tabs.addTab(self.notes_text, "Notes")
        self.tabs.addTab(self._validation_scroll, "Validation")
        self.tabs.addTab(self.debug_text, "Debug")

        layout.addWidget(self.tabs)
        return container

    def _apply_helper_style(self) -> None:
        color = "#999999" if _DARK_MODE else "#555b66"
        self._builder_helper.setStyleSheet(f"color: {color}; font-size: 10pt;")

    def _apply_scroll_style(self) -> None:
        if _DARK_MODE:
            self._validation_scroll.setStyleSheet(
                "QScrollArea { background: #0b1220; border: 1px solid #334155; border-radius: 10px; }"
            )
        else:
            self._validation_scroll.setStyleSheet(
                "QScrollArea { background: #e1e3e8; border: 1px solid #b0b4be; border-radius: 10px; }"
            )

    def _apply_styles(self) -> None:
        if _DARK_MODE:
            qss = """
            QWidget { font-family: Segoe UI, Arial, sans-serif; font-size: 11pt; }
            QMainWindow, QMenuBar, QMenu, QStatusBar {
                background: #1c1c1c; color: #e8e8e8;
            }
            QMenuBar::item:selected, QMenu::item:selected { background: #487cff; color: white; }
            QMenu { border: 1px solid #3a3a3a; }
            QStatusBar { border-top: 1px solid #3a3a3a; font-size: 10pt; color: #999999; }
            QFrame#HeaderCard, QFrame#SectionCard {
                background: rgba(38, 38, 38, 200); border: 1px solid #3a3a3a; border-radius: 14px;
            }
            QLabel#AppTitle  { color: #e8e8e8; font-size: 18pt; font-weight: 700; }
            QLabel#SubTitle  { color: #999999; font-size: 10pt; }
            QLabel#SectionTitle { color: #e0e0e0; font-size: 12pt; font-weight: 600; }
            QLabel { color: #e8e8e8; background: transparent; }
            QLineEdit, QTextEdit {
                background: #121212; color: #ececec; border: 1px solid #404040;
                border-radius: 10px; padding: 6px 8px; selection-background-color: #487cff; font-size: 11pt;
            }
            QTabWidget::pane { background: rgba(38,38,38,200); border: 1px solid #3a3a3a; border-radius: 10px; }
            QListWidget {
                background: #121212; color: #ececec; border: 1px solid #404040;
                border-radius: 10px; padding: 4px; selection-background-color: #487cff; font-size: 11pt;
            }
            QListWidget::item { padding: 3px 6px; min-height: 18px; border-radius: 4px; }
            QListWidget::item:selected { background: #2d4c8f; color: #ffffff; }
            QPushButton {
                background: #383838; color: #e8e8e8; border: 1px solid #505050;
                border-radius: 10px; padding: 6px 14px; font-weight: 600; font-size: 10pt; min-height: 24px;
            }
            QPushButton:hover { background: #454545; border: 1px solid #606060; }
            QPushButton:pressed { background: #2a2a2a; }
            QPushButton#PrimaryButton { background: #487cff; border: 1px solid #3068ee; color: white; }
            QPushButton#PrimaryButton:hover { background: #3068ee; }
            QCheckBox { color: #e8e8e8; spacing: 6px; background: transparent; font-size: 11pt; }
            QTabBar::tab {
                background: #2d2d2d; color: #999999; padding: 6px 14px;
                border: 1px solid #3a3a3a; border-top-left-radius: 8px;
                border-top-right-radius: 8px; margin-right: 4px; font-size: 10pt;
            }
            QTabBar::tab:selected { background: rgba(38,38,38,200); color: #e8e8e8; border-bottom-color: transparent; }
            QTableWidget {
                background: transparent; color: #ececec; border: 1px solid #404040;
                border-radius: 10px; padding: 4px; selection-background-color: #487cff;
                gridline-color: #3a3a3a; alternate-background-color: rgba(35,35,35,140);
            }
            QTableWidget::item { background: rgba(25,25,25,140); border: none; padding: 4px 8px; }
            QTableWidget::item:selected { background: rgba(72,124,255,160); color: white; }
            QHeaderView::section {
                background: rgba(40,40,40,180); color: #e0e0e0; border: none;
                border-right: 1px solid #3a3a3a; border-bottom: 1px solid #3a3a3a;
                padding: 6px 4px; font-weight: 600; font-size: 10pt;
            }
            QScrollBar:vertical { background: #1c1c1c; width: 8px; margin: 2px; }
            QScrollBar::handle:vertical { background: #505050; border-radius: 4px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollArea { background: #121212; border: 1px solid #404040; border-radius: 10px; }
            #UpdateBanner { background: rgba(30,60,40,220); border-top: 1px solid #2d6a3f; }
            #UpdateBanner QLabel#UpdateMsg { color: #6ee7a0; font-weight: 600; font-size: 11pt; background: transparent; }
            #InstallBtn { background: #2d6a3f; border: 1px solid #3d8a52; color: white; font-weight: 700; }
            #InstallBtn:hover { background: #3d8a52; }
            """
        else:
            qss = """
            QWidget { font-family: Segoe UI, Arial, sans-serif; font-size: 11pt; }
            QMainWindow, QMenuBar, QMenu, QStatusBar {
                background: #d2d4da; color: #191919;
            }
            QMenuBar::item:selected, QMenu::item:selected { background: #487cff; color: white; }
            QMenu { border: 1px solid #b0b4be; }
            QStatusBar { border-top: 1px solid #b0b4be; font-size: 10pt; color: #555b66; }
            QFrame#HeaderCard, QFrame#SectionCard {
                background: rgba(220,222,228,200); border: 1px solid #b0b4be; border-radius: 14px;
            }
            QLabel#AppTitle  { color: #111111; font-size: 18pt; font-weight: 700; }
            QLabel#SubTitle  { color: #555b66; font-size: 10pt; }
            QLabel#SectionTitle { color: #191919; font-size: 12pt; font-weight: 600; }
            QLabel { color: #191919; background: transparent; }
            QLineEdit, QTextEdit {
                background: #e1e3e8; color: #191919; border: 1px solid #b0b4be;
                border-radius: 10px; padding: 6px 8px; selection-background-color: #487cff; font-size: 11pt;
            }
            QTabWidget::pane { background: rgba(220,222,228,200); border: 1px solid #b0b4be; border-radius: 10px; }
            QListWidget {
                background: #e1e3e8; color: #191919; border: 1px solid #b0b4be;
                border-radius: 10px; padding: 4px; selection-background-color: #487cff; font-size: 11pt;
            }
            QListWidget::item { padding: 3px 6px; min-height: 18px; border-radius: 4px; }
            QListWidget::item:selected { background: #487cff; color: #ffffff; }
            QPushButton {
                background: #c3c6ce; color: #191919; border: 1px solid #a8acb8;
                border-radius: 10px; padding: 6px 14px; font-weight: 600; font-size: 10pt; min-height: 24px;
            }
            QPushButton:hover { background: #b2b6c2; border: 1px solid #9098a8; }
            QPushButton:pressed { background: #a0a4b0; }
            QPushButton#PrimaryButton { background: #487cff; border: 1px solid #3068ee; color: white; }
            QPushButton#PrimaryButton:hover { background: #3068ee; }
            QCheckBox { color: #191919; spacing: 6px; background: transparent; font-size: 11pt; }
            QTabBar::tab {
                background: #c3c6ce; color: #555b66; padding: 6px 14px;
                border: 1px solid #b0b4be; border-top-left-radius: 8px;
                border-top-right-radius: 8px; margin-right: 4px; font-size: 10pt;
            }
            QTabBar::tab:selected { background: rgba(220,222,228,200); color: #191919; border-bottom-color: transparent; }
            QTableWidget {
                background: transparent; color: #191919; border: 1px solid #b0b4be;
                border-radius: 10px; padding: 4px; selection-background-color: #487cff;
                gridline-color: #b0b4be; alternate-background-color: rgba(200,202,208,180);
            }
            QTableWidget::item { background: rgba(215,217,223,180); border: none; padding: 4px 8px; }
            QTableWidget::item:selected { background: rgba(72,124,255,180); color: white; }
            QHeaderView::section {
                background: rgba(195,198,206,220); color: #191919; border: none;
                border-right: 1px solid #b0b4be; border-bottom: 1px solid #b0b4be;
                padding: 6px 4px; font-weight: 600; font-size: 10pt;
            }
            QScrollBar:vertical { background: #d2d4da; width: 8px; margin: 2px; }
            QScrollBar::handle:vertical { background: #a8acb8; border-radius: 4px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollArea { background: #e1e3e8; border: 1px solid #b0b4be; border-radius: 10px; }
            #UpdateBanner { background: rgba(200,240,215,220); border-top: 1px solid #86efac; }
            #UpdateBanner QLabel#UpdateMsg { color: #14532d; font-weight: 600; font-size: 11pt; background: transparent; }
            #InstallBtn { background: #22c55e; border: 1px solid #16a34a; color: white; font-weight: 700; }
            #InstallBtn:hover { background: #16a34a; }
            """

        self.setStyleSheet(qss)
        self._apply_scroll_style()

        self.model_entry.setMinimumHeight(32)
        self.table_widget.setMinimumHeight(TABLE_MIN_HEIGHT)
        self.table_widget.verticalHeader().setDefaultSectionSize(28)

        self.decode_button.setMaximumHeight(ACTION_BUTTON_HEIGHT + 6)
        self.clear_button.setMaximumHeight(ACTION_BUTTON_HEIGHT + 6)
        self.copy_button.setMaximumHeight(ACTION_BUTTON_HEIGHT + 6)
        self.save_button.setMaximumHeight(ACTION_BUTTON_HEIGHT + 6)

        self._update_table_columns()

    def _update_table_columns(self) -> None:
        self.table_widget.setColumnWidth(0, 52)
        self.table_widget.setColumnWidth(1, 95)
        self.table_widget.setColumnWidth(2, 95)
        # column 3 (Pressure Drop) is Stretch — no fixed width needed

    def _fit_table_height(self) -> None:
        """Shrink the table to exactly fit its header + rows, no blank space."""
        row_count = self.table_widget.rowCount()
        if row_count == 0:
            self.table_widget.setFixedHeight(TABLE_MIN_HEIGHT)
            return
        h = self.table_widget.horizontalHeader().height()
        for i in range(row_count):
            h += self.table_widget.rowHeight(i)
        h += 4  # border
        self.table_widget.setFixedHeight(h)

    # ------------------------------------------------------------------ #
    # Event / state handlers                                               #
    # ------------------------------------------------------------------ #

    def _on_analog_changed(self, state: int) -> None:
        if state == Qt.CheckState.Checked.value:
            self.mode_badge.setText("Analog Mode")
            self.mode_badge.set_kind("blue")
        else:
            self.mode_badge.setText("Normal Mode")
            self.mode_badge.set_kind("gold")
        # Re-trigger live decode when analog mode toggles
        if self.model_entry.text().strip():
            self._decode_timer.start()

    def _on_model_text_changed(self, text: str) -> None:
        """Restart the debounce timer on every keystroke."""
        if text.strip():
            self._decode_timer.start()
        else:
            self._decode_timer.stop()

    def _live_decode(self) -> None:
        """Called by the debounce timer — silently decodes without showing error dialogs."""
        model = self.model_entry.text().strip()
        if not model:
            return
        analog_active = self.analog_checkbox.isChecked()
        success, message, decoded_data, notes, validation_issues, parsed, operating_table = process_model_structured(
            model, analog_active
        )
        if not success:
            return  # Don't interrupt mid-typing with a dialog

        self._apply_decode_results(model, decoded_data, notes, validation_issues, parsed, operating_table)

    def toggle_test_models(self) -> None:
        self.show_test_models = self.toggle_tests_action.isChecked()
        self.test_models_card.setVisible(self.show_test_models)

    def load_example_model(self, model: str) -> None:
        self.model_entry.setText(model)
        self.decode_and_display()

    # ------------------------------------------------------------------ #
    # Field-card helpers                                                   #
    # ------------------------------------------------------------------ #

    def _clear_field_cards(self) -> None:
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _field_column_count(self) -> int:
        width = self.cards_container.width() or self.width()
        if width >= 1200:
            return 3
        if width >= 650:
            return 2
        return 1

    def _rebuild_field_cards(self) -> None:
        if not self._field_card_specs:
            self._clear_field_cards()
            return

        self._clear_field_cards()
        columns = self._field_column_count()

        for index, (field_name, field_value, invalid, editable) in enumerate(self._field_card_specs):
            row = index // columns
            col = index % columns
            card = ClickableFieldCard(field_name, field_value, invalid, editable)
            if editable:
                card.clicked.connect(lambda _, name=field_name: self._show_field_editor(name))
            self.cards_layout.addWidget(card, row, col)

        for col in range(columns):
            self.cards_layout.setColumnStretch(col, 1)

    # ------------------------------------------------------------------ #
    # Output helpers                                                       #
    # ------------------------------------------------------------------ #

    def clear_output(self) -> None:
        self._decode_timer.stop()
        self.model_entry.clear()
        self.notes_text.clear()
        self._clear_validation_rows()
        self.debug_text.clear()
        self.table_widget.setRowCount(0)
        self.table_widget.setFixedHeight(TABLE_MIN_HEIGHT)
        self.current_output_text = ""
        self.current_product_line = "UNKNOWN"
        self.current_data = {}
        self.current_notes = []
        self.current_validation_issues = []
        self.current_parsed_model = None
        self.current_operating_table = None
        self.current_save_path = None
        self._field_card_specs = []

        self.product_badge.setText("Product: —")
        self.product_badge.set_kind("blue")
        self.validation_badge.setText("No validation run yet")
        self.validation_badge.set_kind("neutral")
        self.table_card.set_title("Flow / Pressure Operating Table")
        self._clear_field_cards()

    def _clear_validation_rows(self) -> None:
        """Remove all issue row widgets from the validation scroll panel."""
        while self._validation_scroll_layout.count():
            item = self._validation_scroll_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _update_badges(self, product_line: str, validation_issues: list[dict]) -> None:
        product_text = PRODUCT_DISPLAY_NAMES.get(product_line, product_line)
        self.product_badge.setText(f"Product: {product_text}")

        if validation_issues:
            count = len(validation_issues)
            self.validation_badge.setText(f"{count} validation issue{'s' if count != 1 else ''}")
            self.validation_badge.set_kind("red")
        else:
            self.validation_badge.setText("No validation issues")
            self.validation_badge.set_kind("green")

    def _update_tab_labels(self, validation_issues: list[dict]) -> None:
        """FIX: show a count badge on the Validation tab so issues are visible
        without the user needing to switch tabs."""
        count = len(validation_issues)
        label = f"Validation ({count})" if count else "Validation"
        # FIX: find tab index by widget reference, not hardcoded integer,
        # so reordering tabs never silently breaks this.
        idx = self.tabs.indexOf(self._validation_scroll)
        if idx >= 0:
            self.tabs.setTabText(idx, label)

    def _make_summary_text(self, model: str, product_line: str, validation_issues: list[dict], notes: list[str]) -> str:
        lines = [
            f"Model: {model}",
            f"Product Line: {PRODUCT_DISPLAY_NAMES.get(product_line, product_line)}",
            f"Mode: {'Analog' if self.analog_checkbox.isChecked() else 'Normal'}",
            f"Validation Issues: {len(validation_issues)}",
        ]
        if validation_issues:
            lines.append("")
            lines.append("Validation Issues:")
            for issue in validation_issues:
                lines.append(f"- {issue['field']}: {issue['message']}")
        if notes:
            lines.append("")
            lines.append("Notes:")
            for note in notes:
                lines.append(note)
        return "\n".join(lines)

    @staticmethod
    def _parse_issue_reasons(issues: list[dict], field_name: str) -> list[str]:
        return [issue["message"] for issue in issues if issue["field"] == field_name]

    @staticmethod
    def _logical_field_for_display_name(field_name: str) -> str:
        return FIELD_TO_LOGICAL_FIELD.get(field_name, field_name.lower())

    def _extract_spare_parts_for_field(self, reparsed: ParsedModel | None, field_name: str) -> list[dict]:
        if reparsed is None:
            return []
        details = get_field_popup_details(reparsed, self._logical_field_for_display_name(field_name))
        return list(details.get("spare_parts", []))

    @staticmethod
    def _extract_spare_parts_for_option(reparsed: ParsedModel | None, option_code: str) -> list[dict]:
        if reparsed is None:
            return []
        details = get_field_popup_details(reparsed, "options")
        for item in details.get("selected_items", []):
            if item.get("code") == option_code:
                return list(item.get("spare_parts", []))
        return []

    # ------------------------------------------------------------------ #
    # ParsedModel manipulation                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _clone_parsed_model(parsed: ParsedModel) -> ParsedModel:
        return ParsedModel(
            full_model=parsed.full_model,
            product_line=parsed.product_line,
            base=parsed.base,
            suffix=parsed.suffix,
            prefix=parsed.prefix,
            construction=parsed.construction,
            qty_char=parsed.qty_char,
            size_code=parsed.size_code,
            pressure=parsed.pressure,
            design_char=parsed.design_char,
            control_type=parsed.control_type,
            controller=parsed.controller,
            orientation=parsed.orientation,
            failsafe=parsed.failsafe,
            protocol=parsed.protocol,
            options=list(parsed.options),
        )

    @staticmethod
    def _set_parsed_field(parsed: ParsedModel, field_name: str, code: str) -> None:
        if field_name in ("Construction", "Valve Construction", "Chemical Resistance"):
            parsed.construction = code
        elif field_name in ("Bodies", "Valve Bodies"):
            parsed.qty_char = code
        elif field_name in ("Size", "Valve Size"):
            parsed.size_code = code
        elif field_name in ("Pressure", "Pressure Rating", "Flow/Pressure Operating"):
            parsed.pressure = code
        elif field_name in ("Valve Design", "Body Design"):
            parsed.design_char = code
        elif field_name in ("Control Type", "Actuator Type"):
            parsed.control_type = code
        elif field_name in ("Controller", "Controller Type", "Valve Controller Designation"):
            parsed.controller = code
        elif field_name in ("Orientation", "Valve Orientation"):
            parsed.orientation = code
        elif field_name in ("Fail-Safe", "Failsafe Position", "Fail-Safe Module"):
            parsed.failsafe = code
        elif field_name == "Communication Protocol":
            parsed.protocol = code

    @staticmethod
    def _build_model_from_parsed(parsed: ParsedModel) -> str:
        base = f"{parsed.prefix}{parsed.construction}{parsed.qty_char}{parsed.size_code}{parsed.pressure}"
        suffix = f"{parsed.design_char}{parsed.control_type}{parsed.controller}{parsed.orientation}{parsed.failsafe}"
        parts = [base, suffix]
        if parsed.product_line == "CSCP" and parsed.protocol:
            parts.append(parsed.protocol)
        parts.extend(parsed.options)
        return "-".join([part for part in parts if part])

    def _simulate_with_replacement(self, replace_fn: Callable[[ParsedModel], None]) -> tuple[list[dict], ParsedModel | None]:
        parsed = self.current_parsed_model
        if parsed is None:
            return [], None

        new_parsed = self._clone_parsed_model(parsed)
        replace_fn(new_parsed)
        model_text = self._build_model_from_parsed(new_parsed)
        success, _, _, _, issues, reparsed, _ = process_model_structured(
            model_text, self.analog_checkbox.isChecked()
        )
        if not success:
            return [{"field": "Unknown", "message": "Could not parse simulated model."}], reparsed
        return issues, reparsed

    def _simulate_field_change(self, field_name: str, code: str) -> tuple[list[dict], ParsedModel | None]:
        def replace_fn(p: ParsedModel) -> None:
            self._set_parsed_field(p, field_name, code)
        return self._simulate_with_replacement(replace_fn)

    def _build_picker_entries(self, field_name: str, options_map: dict[str, str]) -> list[dict]:
        entries: list[dict] = []
        for code, desc in options_map.items():
            issues, reparsed = self._simulate_field_change(field_name, code)
            reasons = self._parse_issue_reasons(issues, field_name)
            valid = len(reasons) == 0
            spare_parts = self._extract_spare_parts_for_field(reparsed, field_name) if reparsed else []
            entries.append({
                "code": code,
                "desc": desc,
                "valid": valid,
                "reason": reasons[0] if reasons else "",
                "spare_parts": spare_parts,
            })
        return entries

    # ------------------------------------------------------------------ #
    # Field / options editor dialogs                                       #
    # ------------------------------------------------------------------ #

    def _show_field_editor(self, field_name: str) -> None:
        if self.current_product_line not in standard_product_configs:
            QMessageBox.information(self, "No Options", "No editable options available for this product line.")
            return

        if field_name not in EDITABLE_FIELDS:
            QMessageBox.information(self, "Not Editable", f"'{field_name}' is informational and not editable.")
            return

        cfg = standard_product_configs[self.current_product_line]
        config_key = FIELD_TO_CONFIG_KEY.get(field_name)

        if field_name == "Options":
            self._show_options_editor()
            return

        if not config_key:
            QMessageBox.information(self, "No Options", f"No option reference is configured for '{field_name}'.")
            return

        if field_name in ("Fail-Safe", "Failsafe Position", "Fail-Safe Module"):
            if self.current_product_line == "ANALOG":
                if self.current_parsed_model and self.current_parsed_model.prefix == "EXV":
                    options_map = cfg.get("failsafe_map_exv", {})
                elif self.current_parsed_model and self.current_parsed_model.prefix == "MAV":
                    options_map = cfg.get("failsafe_map_mav", {})
                else:
                    options_map = {}
            else:
                options_map = cfg.get("failsafe_map", {}) or {}
        else:
            options_map = cfg.get(config_key, {}) or {}

        if not options_map:
            QMessageBox.information(self, "No Options", f"No option reference is available for '{field_name}'.")
            return

        entries = self._build_picker_entries(field_name, options_map)

        def on_pick(code: str) -> None:
            self._apply_field_change(field_name, code)

        dlg = OptionPickerDialog(self, f"{field_name} Options", field_name, entries, on_pick)
        dlg.exec()

    def _simulate_option_toggle(self, code: str) -> tuple[list[dict], ParsedModel | None]:
        def replace_fn(p: ParsedModel) -> None:
            if code in p.options:
                p.options = [opt for opt in p.options if opt != code]
            else:
                p.options.append(code)
                p.options = sorted(dict.fromkeys(p.options))
        return self._simulate_with_replacement(replace_fn)

    def _show_options_editor(self) -> None:
        if self.current_product_line not in standard_product_configs:
            return

        cfg = standard_product_configs[self.current_product_line]
        options_map = cfg.get("option_map", {}) or {}
        current_options = list(self.current_parsed_model.options) if self.current_parsed_model else []

        entries = []
        for code, desc in options_map.items():
            issues, reparsed = self._simulate_option_toggle(code)
            option_reasons = self._parse_issue_reasons(issues, "Options")
            valid = len(option_reasons) == 0

            # Spare parts: use current parsed model if option is already selected,
            # otherwise use the reparsed model that has the option toggled on
            if code in current_options and self.current_parsed_model is not None:
                spare_parts = self._extract_spare_parts_for_option(self.current_parsed_model, code)
            else:
                spare_parts = self._extract_spare_parts_for_option(reparsed, code)

            entries.append({
                "code": code,
                "desc": desc,
                "valid": valid,
                "reason": option_reasons[0] if option_reasons else "",
                "spare_parts": spare_parts,
            })

        def on_done(new_options: list[str]) -> None:
            self._apply_options_change(new_options)

        dlg = OptionsEditorDialog(self, current_options, entries, on_done)
        dlg.exec()

    def _apply_options_change(self, new_options: list[str]) -> None:
        if self.current_parsed_model is None:
            return
        new_parsed = self._clone_parsed_model(self.current_parsed_model)
        new_parsed.options = sorted(dict.fromkeys(new_options))
        model_text = self._build_model_from_parsed(new_parsed)
        self.model_entry.setText(model_text)
        self.decode_and_display()

    def _apply_field_change(self, field_name: str, code: str) -> None:
        if self.current_parsed_model is None:
            return
        new_parsed = self._clone_parsed_model(self.current_parsed_model)
        self._set_parsed_field(new_parsed, field_name, code)
        model_text = self._build_model_from_parsed(new_parsed)
        self.model_entry.setText(model_text)
        self.decode_and_display()

    # ------------------------------------------------------------------ #
    # Decode + display                                                     #
    # ------------------------------------------------------------------ #

    def _build_field_cards(self, parsed: ParsedModel | None, decoded_data: dict[str, str], validation_issues: list[dict]) -> None:
        invalid_fields = {issue["field"] for issue in validation_issues}
        specs: list[tuple[str, str, bool, bool]] = []

        if parsed is not None:
            specs.append(("Base", parsed.base, "Base" in invalid_fields, False))
            specs.append(("Suffix", parsed.suffix, "Suffix" in invalid_fields, False))

        for key, value in decoded_data.items():
            if key == "Product Line":
                continue
            editable = key in EDITABLE_FIELDS
            specs.append((key, value, key in invalid_fields, editable))

        self._field_card_specs = specs
        self._rebuild_field_cards()

    def _fill_table_from_structured(self, operating_table: OperatingTable | None) -> None:
        self.table_widget.setRowCount(0)

        if operating_table is None or not operating_table.rows:
            self.table_card.set_title("Flow / Pressure Operating Table")
            return

        self.table_card.set_title(operating_table.title)
        self.table_widget.setRowCount(len(operating_table.rows))

        for row_index, row in enumerate(operating_table.rows):
            values = [
                row.get("size", ""),
                row.get("single_cfm", ""),
                row.get("dual_cfm", ""),
                row.get("pressure_drop", ""),
            ]
            for col_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col_index != 3:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                if col_index == 3 and value:
                    item.setBackground(QColor("#132238") if _DARK_MODE else QColor("#dbeafe"))
                self.table_widget.setItem(row_index, col_index, item)

        self._update_table_columns()
        self._fit_table_height()

    def decode_and_display(self) -> None:
        """Explicit decode triggered by button or Enter — shows error dialogs."""
        self._decode_timer.stop()
        model = self.model_entry.text().strip()
        if not model:
            QMessageBox.warning(self, "Input Required", "Please enter a model number.")
            return

        analog_active = self.analog_checkbox.isChecked()
        success, message, decoded_data, notes, validation_issues, parsed, operating_table = process_model_structured(
            model, analog_active
        )

        if not success:
            QMessageBox.critical(self, "Decode Error", message)
            return

        self._apply_decode_results(model, decoded_data, notes, validation_issues, parsed, operating_table)
        self.statusBar().showMessage(f"Decoded {model}")

    def _apply_decode_results(
        self,
        model: str,
        decoded_data: dict[str, str],
        notes: list[str],
        validation_issues: list[dict],
        parsed: ParsedModel | None,
        operating_table: OperatingTable | None,
    ) -> None:
        """Apply a complete decode result to all UI panels (shared by live and explicit decode)."""
        self.current_parsed_model = parsed
        self.current_operating_table = operating_table

        product_line = parsed.product_line if parsed else "UNKNOWN"
        self.current_product_line = product_line
        self.current_data = decoded_data
        self.current_notes = notes
        self.current_validation_issues = validation_issues

        self._update_badges(product_line, validation_issues)
        self._update_tab_labels(validation_issues)
        self._build_field_cards(parsed, decoded_data, validation_issues)

        self.current_output_text = self._make_summary_text(model, product_line, validation_issues, notes)

        self._update_notes_panel(notes)
        self._update_validation_panel(validation_issues)
        self._update_debug_panel(parsed, "Valid", validation_issues, operating_table)
        self._fill_table_from_structured(operating_table)

    def _update_notes_panel(self, notes: list[str]) -> None:
        if not notes:
            self.notes_text.setPlainText("No notes.")
            return

        # FIX: bold note number/header prefix for better readability
        html_parts = []
        for note in notes:
            lines = note.strip().splitlines()
            if not lines:
                continue
            first = lines[0]
            rest = lines[1:]
            # Bold the first line if it looks like a note heading
            if first.startswith("Note") or first[0].isdigit():
                first_html = f"<b style='color:#487cff;'>{first}</b>"
            else:
                first_html = first
            body = "<br>".join([first_html] + [l.replace("  ", "&nbsp;&nbsp;") for l in rest])
            html_parts.append(f"<p style='margin:0 0 10px 0; line-height:1.5;'>{body}</p>")

        text_color = "#e5e7eb" if _DARK_MODE else "#191919"
        self.notes_text.setHtml(
            f"<div style='font-size:11pt; color:{text_color}; font-family:Consolas,monospace;'>"
            + "".join(html_parts)
            + "</div>"
        )

    def _update_validation_panel(self, validation_issues: list[dict]) -> None:
        # FIX: replace plain text with styled ValidationIssueRow cards
        self._clear_validation_rows()

        if not validation_issues:
            ok_color = "#4ade80" if _DARK_MODE else "#16a34a"
            ok_label = QLabel("✔  No validation issues")
            ok_label.setStyleSheet(
                f"color: {ok_color}; font-weight: 700; font-size: 12pt; padding: 12px; background: transparent;"
            )
            self._validation_scroll_layout.addWidget(ok_label)
            return

        for issue in validation_issues:
            row = ValidationIssueRow(issue["field"], issue["message"])
            self._validation_scroll_layout.addWidget(row)

    def _update_debug_panel(
        self,
        parsed: ParsedModel | None,
        message: str,
        validation_issues: list[dict],
        operating_table: OperatingTable | None,
    ) -> None:
        if parsed is None:
            self.debug_text.setPlainText("No parsed model data available.")
            return

        debug_lines = [
            f"Full Model: {parsed.full_model}",
            f"Detected Product Line: {PRODUCT_DISPLAY_NAMES.get(parsed.product_line, parsed.product_line)}",
            f"Parse Message: {message}",
            f"Base: {parsed.base}",
            f"Suffix: {parsed.suffix}",
            f"Prefix={parsed.prefix} | Construction={parsed.construction} | Bodies={parsed.qty_char} | Size={parsed.size_code} | Pressure={parsed.pressure}",
            f"Design={parsed.design_char} | Control={parsed.control_type} | Controller={parsed.controller} | Orientation={parsed.orientation} | Fail-Safe={parsed.failsafe}",
            f"Protocol={parsed.protocol or 'None'}",
            f"Options={', '.join(parsed.options) if parsed.options else 'None'}",
            f"Validation Issues={len(validation_issues)}",
            f"Structured Table={'Yes' if operating_table else 'No'}",
        ]
        self.debug_text.setPlainText("\n".join(debug_lines))

    # ------------------------------------------------------------------ #
    # Copy / save                                                          #
    # ------------------------------------------------------------------ #

    def copy_output(self) -> None:
        if not self.current_output_text.strip():
            QMessageBox.warning(self, "Nothing to Copy", "There is no summary to copy.")
            return
        QGuiApplication.clipboard().setText(self.current_output_text)
        QMessageBox.information(self, "Copied", "Summary copied to clipboard.")

    def save_output_as(self) -> None:
        if not self.current_output_text.strip():
            QMessageBox.warning(self, "Nothing to Save", "There is no summary to save.")
            return

        default_name = self.model_entry.text().strip().replace("/", "-").replace("\\", "-").replace(":", "-")
        if not default_name:
            default_name = "ValveMasterTool_Summary"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Summary As",
            f"{default_name}.txt",
            "Text Files (*.txt);;All Files (*.*)",
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as handle:
                handle.write(self.current_output_text + "\n")
            self.current_save_path = file_path
            QMessageBox.information(self, "Saved", f"Summary saved to:\n{file_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", f"Could not save file:\n{exc}")

    def save_output(self) -> None:
        if not self.current_output_text.strip():
            QMessageBox.warning(self, "Nothing to Save", "There is no summary to save.")
            return

        if not self.current_save_path:
            self.save_output_as()
            return

        try:
            with open(self.current_save_path, "w", encoding="utf-8") as handle:
                handle.write(self.current_output_text + "\n")
            QMessageBox.information(self, "Saved", f"Summary saved to:\n{self.current_save_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", f"Could not save file:\n{exc}")

    # ------------------------------------------------------------------ #
    # Misc actions                                                         #
    # ------------------------------------------------------------------ #

    # ------------------------------------------------------------------ #
    # Dark / light mode                                                    #
    # ------------------------------------------------------------------ #

    def _toggle_dark_mode(self) -> None:
        app = QApplication.instance()
        assert isinstance(app, QApplication)
        dark = self._dark_mode_action.isChecked()
        if dark:
            apply_dark_theme(app)
        else:
            apply_light_theme(app)
        QSettings("ATSInc", "ValveMasterTool").setValue("darkMode", "true" if dark else "false")
        self._refresh_theme_dependent_styles()

    def _refresh_theme_dependent_styles(self) -> None:
        """Re-apply all theme-dependent styles after a dark/light mode switch."""
        self._apply_styles()

        # Badges
        self.mode_badge.set_kind(self.mode_badge.kind)
        self.product_badge.set_kind(self.product_badge.kind)
        self.validation_badge.set_kind(self.validation_badge.kind)

        # Helper label
        self._apply_helper_style()

        # Test model labels and list colours
        valid_color   = "#4ade80" if _DARK_MODE else "#16a34a"
        failing_color = "#f87171" if _DARK_MODE else "#dc2626"
        self._valid_label.setStyleSheet(
            f"color: {valid_color}; font-weight: 700; font-size: 10pt; "
            "padding: 4px 0px 2px 0px; background: transparent;"
        )
        self._failing_label.setStyleSheet(
            f"color: {failing_color}; font-weight: 700; font-size: 10pt; "
            "padding: 8px 0px 2px 0px; background: transparent;"
        )
        # Re-apply list widget stylesheets (items already populated)
        self._restyle_model_list(self.valid_models_list,   valid_color)
        self._restyle_model_list(self.failing_models_list, failing_color)

        # Rebuild field cards (ClickableFieldCard reads _DARK_MODE at construction)
        self._rebuild_field_cards()

        # Rebuild validation panel (ValidationIssueRow reads _DARK_MODE at construction)
        self._update_validation_panel(self.current_validation_issues)

        # Re-render notes HTML (text color depends on theme)
        if self.current_notes:
            self._update_notes_panel(self.current_notes)

        # Re-fill table to update pressure-drop cell highlight
        self._fill_table_from_structured(self.current_operating_table)

    @staticmethod
    def _restyle_model_list(widget: QListWidget, item_color: str) -> None:
        """Re-apply theme-aware stylesheet to an already-populated model list."""
        list_bg      = "#0b1220" if _DARK_MODE else "#e1e3e8"
        list_border  = "#1e293b" if _DARK_MODE else "#b0b4be"
        scroll_track = "#1c1c1c" if _DARK_MODE else "#d2d4da"
        scroll_thumb = "#334155" if _DARK_MODE else "#a8acb8"
        hover_bg     = "#151f35" if _DARK_MODE else "rgba(72, 124, 255, 60)"
        selected_bg  = "#1d4ed8" if _DARK_MODE else "#487cff"

        widget.setStyleSheet(
            f"""
            QListWidget {{
                background: {list_bg}; border: 1px solid {list_border};
                border-radius: 8px; padding: 3px;
                font-size: 10pt; font-family: Consolas, monospace; outline: none;
            }}
            QListWidget::item {{
                color: {item_color}; padding: 3px 8px;
                border-radius: 4px; min-height: {MODEL_LIST_ROW_HEIGHT}px;
            }}
            QListWidget::item:selected {{ background: {selected_bg}; color: #ffffff; }}
            QListWidget::item:hover:!selected {{ background: {hover_bg}; }}
            QScrollBar:vertical {{ background: {scroll_track}; width: 5px; margin: 2px; }}
            QScrollBar::handle:vertical {{ background: {scroll_thumb}; border-radius: 2px; min-height: 20px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            """
        )
        # Update foreground on each item
        fg = QColor(item_color)
        for i in range(widget.count()):
            widget.item(i).setForeground(fg)

    # ------------------------------------------------------------------ #
    # Auto-updater                                                         #
    # ------------------------------------------------------------------ #

    def _check_update_bg(self) -> None:
        """Runs in a daemon thread — checks GitHub, posts result to UI thread."""
        info = check_for_update()
        if info:
            self._pending_update_info = info
            self._update_ready.emit()

    def _show_update_banner(self) -> None:
        info = self._pending_update_info
        if info is None:
            return
        banner = UpdateBanner(info, self)
        banner.install_clicked.connect(lambda: self._do_install(info))
        self._update_banner = banner
        self.statusBar().addPermanentWidget(banner, 1)
        banner.show()
        self.statusBar().showMessage(f"Update available: v{info.latest_version}", 0)

    def _do_install(self, info: UpdateInfo) -> None:
        progress = QProgressDialog("Downloading update…", "Cancel", 0, 100, self)
        progress.setWindowTitle("Installing Update")
        progress.setModal(True)
        progress.setValue(0)
        progress.show()

        def on_progress(done: int, total: int) -> None:
            if total > 0:
                progress.setValue(int(done / total * 100))
            QApplication.processEvents()

        try:
            download_and_apply(info, progress_callback=on_progress)
        except RuntimeError as exc:
            progress.close()
            QMessageBox.critical(self, "Update Failed", str(exc))

    # ------------------------------------------------------------------ #
    # Startup checks                                                       #
    # ------------------------------------------------------------------ #

    def _check_sync_folder(self) -> None:
        """Warn the user if the app is running from a cloud-synced folder."""
        try:
            if getattr(sys, "frozen", False):
                path = os.path.abspath(sys.executable)
            else:
                path = os.path.abspath(__file__)

            path_upper = path.upper()
            sync_keywords = ["ONEDRIVE", "DROPBOX", "GOOGLE DRIVE", "GOOGLEDRIVE", "ICLOUD", "BOX SYNC"]
            for kw in sync_keywords:
                if kw in path_upper:
                    QMessageBox.warning(
                        self,
                        "⚠ Cloud Sync Detected",
                        f"ValveMasterTool appears to be running from a cloud-synced folder:\n\n{path}\n\n"
                        "Running from OneDrive, Dropbox, or similar services can cause update failures "
                        "due to file locking.\n\n"
                        "For best results, move the app to a local folder (e.g. C:\\Tools\\ValveMasterTool).",
                    )
                    break
        except (AttributeError, OSError):
            pass

    # ------------------------------------------------------------------ #
    # Help menu actions                                                    #
    # ------------------------------------------------------------------ #

    def show_version_history(self) -> None:
        """Fetch all releases from GitHub and display them in a scrollable dialog."""
        from PySide6.QtWidgets import QPlainTextEdit
        dialog = QDialog(self)
        dialog.setWindowTitle("Version History & Recent Updates")
        dialog.setModal(True)
        dialog.resize(560, 480)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)

        header = QLabel("Fetching release history from GitHub…")
        header.setStyleSheet("font-size: 13pt; font-weight: 700; color: #487cff;")
        layout.addWidget(header)

        text_area = QPlainTextEdit()
        text_area.setReadOnly(True)
        if _DARK_MODE:
            ta_style = ("background: #0e1016; color: #7a8599; border: 1px solid #252b36; "
                        "border-radius: 8px; padding: 8px; font-family: Consolas, monospace; font-size: 10pt;")
        else:
            ta_style = ("background: #e1e3e8; color: #555b66; border: 1px solid #b0b4be; "
                        "border-radius: 8px; padding: 8px; font-family: Consolas, monospace; font-size: 10pt;")
        text_area.setStyleSheet(ta_style)
        layout.addWidget(text_area, 1)

        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(dialog.accept)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        dialog.show()
        QApplication.processEvents()

        # Fetch releases in-place (dialog is already visible)
        try:
            import json as _json
            url = f"https://api.github.com/repos/JustinGlave/valve-master-tool/releases"
            req = urllib.request.Request(
                url,
                headers={"Accept": "application/vnd.github+json",
                         "User-Agent": "ValveMasterTool"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                releases = _json.loads(resp.read().decode())

            if not releases:
                text_area.setPlainText("No releases found on GitHub.")
                header.setText("Version History")
                dialog.exec()
                return

            lines = []
            for rel in releases:
                tag   = rel.get("tag_name", "").lstrip("vV")
                name  = rel.get("name", tag)
                date  = rel.get("published_at", "")[:10]
                notes = rel.get("body", "").strip() or "No release notes."
                lines.append(f"v{tag} — {name}  ({date})")
                lines.append("─" * 48)
                lines.append(notes)
                lines.append("")

            text_area.setPlainText("\n".join(lines))
            count = len(releases)
            header.setText(f"Version History  ({count} release{'s' if count != 1 else ''})")

        except (urllib.error.URLError, OSError) as exc:
            text_area.setPlainText(
                f"Could not fetch release history.\n\nError: {exc}\n\n"
                "You can view the full history at:\n"
                "https://github.com/JustinGlave/valve-master-tool/releases"
            )
            header.setText("Version History")

        dialog.exec()

    @staticmethod
    def _email_support() -> None:
        QDesktopServices.openUrl(QUrl("mailto:justinglave@gmail.com"))

    def show_about(self) -> None:
        QMessageBox.information(
            self,
            f"About {APP_NAME}",
            f"{APP_NAME}\nVersion: {__version__}\n\n"
            "Phoenix valve model decoder and guided model builder.\n\n"
            "GitHub: github.com/JustinGlave/valve-master-tool",
        )

    def show_benchmark_results(self) -> None:
        dlg = BenchmarkDialog(self)
        dlg.exec()

    def toggle_debug_panel(self) -> None:
        # FIX: look up tab index by widget reference, not hardcoded integer
        idx = self.tabs.indexOf(self.debug_text)
        if idx >= 0:
            self.tabs.setTabVisible(idx, self.toggle_debug_action.isChecked())


# ---------------------------------------------------------------------- #
# Entry point                                                              #
# ---------------------------------------------------------------------- #

def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    if QSettings("ATSInc", "ValveMasterTool").value("darkMode", "true") != "false":
        apply_dark_theme(app)
    else:
        apply_light_theme(app)

    window = ValveMasterMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()