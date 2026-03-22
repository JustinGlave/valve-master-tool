# valve_master_pyside6.py
import os
import sys
import textwrap
import threading
from typing import Callable

from PySide6.QtCore import Qt, QSize, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QGuiApplication, QIcon, QPixmap
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
from updater import check_for_update, fetch_all_release_notes, download_and_install

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

    def set_kind(self, kind: str) -> None:
        self._kind = kind
        # FIX: corrected color assignment — bg is the pill background (dark),
        # fg is the text color (light), border is the accent ring.
        styles = {
            "neutral": ("#94a3b8", "#1e293b", "#334155"),
            "blue":    ("#93c5fd", "#1e3a5f", "#2563eb"),
            "green":   ("#4ade80", "#14301f", "#16a34a"),
            "red":     ("#f87171", "#3b1010", "#dc2626"),
            "gold":    ("#fbbf24", "#3b2500", "#f59e0b"),
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
        header.setStyleSheet("font-size: 16px; font-weight: 700; color: #93c5fd;")
        layout.addWidget(header)

        sub = QLabel("White = valid now • Grey = not valid now (reason shown)")
        sub.setStyleSheet("color: #94a3b8;")
        layout.addWidget(sub)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            """
            QListWidget {
                background: #0b1220;
                color: #e5e7eb;
                border: 1px solid #334155;
                border-radius: 10px;
                padding: 6px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #1f2937;
            }
            """
        )

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
            item.setForeground(QColor("#f8fafc") if valid else QColor("#6b7280"))
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
        header.setStyleSheet("font-size: 16px; font-weight: 700; color: #93c5fd;")
        layout.addWidget(header)

        sub = QLabel("Double-click an option to add/remove it. White = valid now • Grey = not valid now")
        sub.setStyleSheet("color: #94a3b8;")
        layout.addWidget(sub)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            """
            QListWidget {
                background: #0b1220;
                color: #e5e7eb;
                border: 1px solid #334155;
                border-radius: 10px;
                padding: 6px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #1f2937;
            }
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
            item.setForeground(QColor("#f8fafc") if valid else QColor("#6b7280"))
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
        # FIX: added a colored left-border accent stripe for clearer valid/invalid
        # signalling that doesn't rely solely on background color
        if self.invalid:
            return """
            QPushButton#FieldCardButton {
                text-align: left;
                padding: 8px 8px 8px 12px;
                background: #251417;
                color: #fca5a5;
                border: 1px solid #7f1d1d;
                border-left: 3px solid #ef4444;
                border-radius: 10px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton#FieldCardButton:hover {
                background: #31191d;
                border: 1px solid #ef4444;
                border-left: 3px solid #f87171;
            }
            """
        if self.editable:
            return """
            QPushButton#FieldCardButton {
                text-align: left;
                padding: 8px 8px 8px 12px;
                background: #0b1220;
                color: #e5e7eb;
                border: 1px solid #243244;
                border-left: 3px solid #22c55e;
                border-radius: 10px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton#FieldCardButton:hover {
                background: #111a2b;
                border: 1px solid #22c55e;
                border-left: 3px solid #4ade80;
            }
            """
        return """
        QPushButton#FieldCardButton {
            text-align: left;
            padding: 8px 8px 8px 12px;
            background: #0b1220;
            color: #cbd5e1;
            border: 1px solid #243244;
            border-left: 3px solid #334155;
            border-radius: 10px;
            font-weight: 600;
            font-size: 12px;
        }
        QPushButton#FieldCardButton:hover {
            background: #111a2b;
            border: 1px solid #334155;
            border-left: 3px solid #475569;
        }
        """


class ValidationIssueRow(QFrame):
    """A styled row widget for a single validation issue in the Validation tab."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__()
        self.setObjectName("ValidationIssueRow")
        self.setStyleSheet(
            """
            QFrame#ValidationIssueRow {
                background: #2a0f0f;
                border: 1px solid #7f1d1d;
                border-left: 3px solid #ef4444;
                border-radius: 8px;
                margin: 2px 0px;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(2)

        field_label = QLabel(field)
        field_label.setStyleSheet("color: #fca5a5; font-weight: 700; font-size: 12px; background: transparent;")
        layout.addWidget(field_label)

        msg_label = QLabel(message)
        msg_label.setStyleSheet("color: #e5e7eb; font-size: 11px; background: transparent;")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)


class UpdateBanner(QFrame):
    """
    Green banner shown at the bottom of the window when an update is available.
    Hidden by default; shown by ValveMasterMainWindow._show_update_banner().
    """

    install_clicked  = Signal()
    dismiss_clicked  = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("UpdateBanner")
        self.setFixedHeight(40)
        self.setStyleSheet(
            """
            QFrame#UpdateBanner {
                background: #14532d;
                border-top: 1px solid #16a34a;
            }
            QLabel { color: #bbf7d0; font-weight: 600; font-size: 12px; background: transparent; }
            QPushButton {
                background: #16a34a; color: #ffffff; border: 1px solid #4ade80;
                border-radius: 6px; padding: 3px 12px; font-weight: 700; font-size: 12px;
            }
            QPushButton:hover { background: #15803d; }
            QPushButton#DismissBtn {
                background: transparent; color: #86efac; border: 1px solid #4ade80;
            }
            QPushButton#DismissBtn:hover { background: #166534; }
            """
        )

        row = QHBoxLayout(self)
        row.setContentsMargins(16, 4, 16, 4)
        row.setSpacing(12)

        self._label = QLabel("🚀 A new version is available!")
        row.addWidget(self._label)
        row.addStretch(1)

        install_btn = QPushButton("Install & Restart")
        install_btn.clicked.connect(self.install_clicked)
        row.addWidget(install_btn)

        dismiss_btn = QPushButton("Dismiss")
        dismiss_btn.setObjectName("DismissBtn")
        dismiss_btn.clicked.connect(self.dismiss_clicked)
        row.addWidget(dismiss_btn)

        self.hide()

    def set_version_text(self, new_version: str) -> None:
        self._label.setText(f"🚀 Update available: v{new_version} — click Install & Restart to upgrade.")


class WatermarkWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.logo_label = QLabel(self)
        self.logo_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.logo_label.setStyleSheet("background: transparent;")
        self.logo_pixmap_original: QPixmap | None = None

        opacity_effect = QGraphicsOpacityEffect(self.logo_label)
        opacity_effect.setOpacity(0.18)
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
    _update_ready = Signal(str, str)   # (new_version, download_url)

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
        self._pending_update_url: str = ""

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

        # Update banner sits below the splitter, hidden until an update is found
        self.update_banner = UpdateBanner()
        self.update_banner.install_clicked.connect(self._install_update)
        self.update_banner.dismiss_clicked.connect(self.update_banner.hide)
        root_layout.addWidget(self.update_banner)

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

        helper = QLabel(
            "Builder Help:\n"
            "• Click ✏ field cards to change codes."
        )
        helper.setStyleSheet("color: #94a3b8; line-height: 1.35;")
        helper.setWordWrap(True)
        self.input_card.add_widget(helper)

        return self.input_card

    def _build_table_card(self) -> SectionCard:
        self.table_card = SectionCard("Flow / Pressure Operating Table")
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(
            ["Size", "Single CFM", "Dual CFM", "Pressure Drop"]
        )
        header = self.table_widget.horizontalHeader()
        for col in range(4):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)

        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setWordWrap(True)
        self.table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table_widget.setMinimumHeight(TABLE_MIN_HEIGHT)
        self.table_card.add_widget(self.table_widget)
        return self.table_card

    def _build_test_models_card(self) -> SectionCard:
        self.test_models_card = SectionCard("Quick Test Models")
        self.test_models_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Valid group
        valid_label = QLabel("✔  Valid Models")
        valid_label.setStyleSheet(
            "color: #4ade80; font-weight: 700; font-size: 11px; "
            "padding: 4px 0px 2px 0px; background: transparent;"
        )
        self.test_models_card.add_widget(valid_label)

        self.valid_models_list = QListWidget()
        self._configure_model_list(self.valid_models_list, VALID_TEST_MODELS, item_color="#4ade80")
        self.valid_models_list.setFixedHeight(MODEL_LIST_HEIGHT)
        self.valid_models_list.itemDoubleClicked.connect(self._load_model_from_list)
        self.test_models_card.add_widget(self.valid_models_list)

        self.test_models_card.add_spacing(4)

        # Failing group
        failing_label = QLabel("✖  Failing Models")
        failing_label.setStyleSheet(
            "color: #f87171; font-weight: 700; font-size: 11px; "
            "padding: 8px 0px 2px 0px; background: transparent;"
        )
        self.test_models_card.add_widget(failing_label)

        self.failing_models_list = QListWidget()
        self._configure_model_list(self.failing_models_list, FAILING_TEST_MODELS, item_color="#f87171")
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
        widget.setStyleSheet(
            f"""
            QListWidget {{
                background: #0b1220;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 3px;
                font-size: 12px;
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
                background: #1d4ed8;
                color: #ffffff;
            }}
            QListWidget::item:hover:!selected {{
                background: #151f35;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 5px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: #334155;
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
        self._validation_scroll.setStyleSheet(
            "QScrollArea { background: #0b1220; border: 1px solid #334155; border-radius: 10px; }"
        )

        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)

        self.tabs.addTab(self.notes_text, "Notes")
        self.tabs.addTab(self._validation_scroll, "Validation")
        self.tabs.addTab(self.debug_text, "Debug")

        layout.addWidget(self.tabs)
        return container

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #0f172a;
                font-size: 12px;
            }
            QMenuBar {
                background: #111827;
                color: #e5e7eb;
                border-bottom: 1px solid #1f2937;
                font-size: 12px;
            }
            QMenuBar::item:selected {
                background: #1f2937;
            }
            QMenu {
                background: #111827;
                color: #e5e7eb;
                border: 1px solid #334155;
                font-size: 12px;
            }
            QMenu::item:selected {
                background: #1e3a8a;
            }
            QStatusBar {
                background: #111827;
                color: #94a3b8;
                border-top: 1px solid #1f2937;
                font-size: 11px;
            }
            QFrame#HeaderCard, QFrame#SectionCard {
                background: rgba(17, 24, 39, 230);
                border: 1px solid #1f2937;
                border-radius: 14px;
            }
            QLabel#AppTitle {
                color: #e5e7eb;
                font-size: 22px;
                font-weight: 700;
            }
            QLabel#SubTitle {
                color: #94a3b8;
                font-size: 11px;
            }
            QLabel#SectionTitle {
                color: #93c5fd;
                font-size: 13px;
                font-weight: 700;
            }
            QLabel {
                color: #e5e7eb;
                background: transparent;
            }
            QLineEdit, QTextEdit, QTableWidget, QTabWidget::pane, QListWidget {
                background: rgba(11, 18, 32, 235);
                color: #e5e7eb;
                border: 1px solid #334155;
                border-radius: 10px;
                padding: 6px;
                selection-background-color: #1d4ed8;
                font-size: 12px;
            }
            QPushButton {
                background: #1f2937;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 4px 8px;
                font-weight: 600;
                font-size: 12px;
                min-height: 24px;
            }
            QPushButton:hover {
                background: #273449;
                border: 1px solid #475569;
            }
            QPushButton#PrimaryButton {
                background: #2563eb;
                border: 1px solid #3b82f6;
                color: white;
            }
            QPushButton#PrimaryButton:hover {
                background: #1d4ed8;
            }
            QCheckBox {
                color: #e5e7eb;
                spacing: 6px;
                background: transparent;
                font-size: 12px;
            }
            QTabBar::tab {
                background: #111827;
                color: #94a3b8;
                padding: 6px 12px;
                border: 1px solid #1f2937;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                color: #e5e7eb;
                background: #1f2937;
                border-color: #334155;
            }
            QTableWidget {
                gridline-color: #334155;
                alternate-background-color: #0f172a;
            }
            QHeaderView::section {
                background: #111827;
                color: #93c5fd;
                border: 1px solid #1f2937;
                padding: 4px;
                font-weight: 600;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 1px 4px;
                min-height: 16px;
            }
            QListWidget::item:selected {
                background: #1d4ed8;
                color: #ffffff;
                border-radius: 4px;
            }
            """
        )

        self.model_entry.setMinimumHeight(28)
        self.table_widget.setMinimumHeight(TABLE_MIN_HEIGHT)
        self.table_widget.verticalHeader().setDefaultSectionSize(28)

        self.decode_button.setMaximumHeight(ACTION_BUTTON_HEIGHT)
        self.clear_button.setMaximumHeight(ACTION_BUTTON_HEIGHT)
        self.copy_button.setMaximumHeight(ACTION_BUTTON_HEIGHT)
        self.save_button.setMaximumHeight(ACTION_BUTTON_HEIGHT)

        self._update_table_columns()

    def _update_table_columns(self) -> None:
        self.table_widget.setColumnWidth(0, 52)
        self.table_widget.setColumnWidth(1, 95)
        self.table_widget.setColumnWidth(2, 95)
        self.table_widget.setColumnWidth(3, 110)

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
                    item.setBackground(QColor("#132238"))
                self.table_widget.setItem(row_index, col_index, item)

        self._update_table_columns()

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
                first_html = f"<b style='color:#93c5fd;'>{first}</b>"
            else:
                first_html = first
            body = "<br>".join([first_html] + [l.replace("  ", "&nbsp;&nbsp;") for l in rest])
            html_parts.append(f"<p style='margin:0 0 10px 0; line-height:1.5;'>{body}</p>")

        self.notes_text.setHtml(
            "<div style='font-size:12px; color:#e5e7eb; font-family:monospace;'>"
            + "".join(html_parts)
            + "</div>"
        )

    def _update_validation_panel(self, validation_issues: list[dict]) -> None:
        # FIX: replace plain text with styled ValidationIssueRow cards
        self._clear_validation_rows()

        if not validation_issues:
            ok_label = QLabel("✔  No validation issues")
            ok_label.setStyleSheet(
                "color: #4ade80; font-weight: 700; font-size: 13px; padding: 12px; background: transparent;"
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
    # Auto-updater                                                         #
    # ------------------------------------------------------------------ #

    def _check_update_bg(self) -> None:
        """Background thread — checks GitHub for a newer release."""
        try:
            available, new_version, download_url = check_for_update()
            if available and download_url:
                self._update_ready.emit(new_version, download_url)
        except (OSError, ValueError, RuntimeError):
            pass  # Never crash the app over an update check

    def _show_update_banner(self, new_version: str, download_url: str) -> None:
        """Called on the UI thread via Signal when an update is found."""
        self._pending_update_url = download_url
        self.update_banner.set_version_text(new_version)
        self.update_banner.show()
        self.statusBar().showMessage(f"Update available: v{new_version} — see banner below")

    def _install_update(self) -> None:
        if not self._pending_update_url:
            return
        reply = QMessageBox.question(
            self,
            "Install Update",
            "The app will download the update, close, install, and restart automatically.\n\nProceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            download_and_install(self._pending_update_url)
        except Exception as exc:
            QMessageBox.critical(self, "Update Failed", f"Could not install update:\n{exc}")

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
        dlg = QDialog(self)
        dlg.setWindowTitle("Version History & Recent Updates")
        dlg.resize(780, 560)

        layout = QVBoxLayout(dlg)

        header = QLabel("Version History")
        header.setStyleSheet("font-size: 16px; font-weight: 700; color: #93c5fd;")
        layout.addWidget(header)

        text_box = QTextEdit()
        text_box.setReadOnly(True)
        layout.addWidget(text_box)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        text_box.setPlainText("Fetching release notes from GitHub...")
        dlg.show()

        def _fetch() -> None:
            try:
                releases = fetch_all_release_notes()
                if not releases:
                    text_box.setPlainText("No releases found, or could not reach GitHub.")
                    return
                lines = []
                for r in releases:
                    tag   = r.get("tag", "")
                    name  = r.get("name", "") or tag
                    date  = r.get("published_at", "")
                    body  = r.get("body", "").strip()
                    lines.append(f"{'='*60}")
                    lines.append(f"{name}  ({tag})  —  {date}")
                    lines.append(f"{'='*60}")
                    if body:
                        lines.append(body)
                    lines.append("")
                text_box.setPlainText("\n".join(lines))
            except Exception as exc:
                text_box.setPlainText(f"Could not fetch release notes:\n{exc}")

        threading.Thread(target=_fetch, daemon=True).start()

        dlg.exec()

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

    window = ValveMasterMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
