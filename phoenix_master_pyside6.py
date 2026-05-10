# phoenix_master_pyside6.py
import csv
import json
import os
import sys
import textwrap
import threading
import urllib.error
import urllib.request
from typing import Callable

from PySide6.QtCore import Qt, QSettings, QTimer, QUrl, Signal
from PySide6.QtGui import (
    QAction,
    QColor,
    QDesktopServices,
    QGuiApplication,
    QIcon,
    QKeySequence,
    QPainter,
    QPalette,
    QPixmap,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from phoenix_master_backend import (
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
from inventory import (
    Inventory,
    Part,
    inventory_json_path,
    is_admin_password,
    load_inventory,
    save_inventory,
)
try:
    from assets import ICO_B64, PNG_B64
    import base64 as _base64
    from PySide6.QtCore import QByteArray
    _ICO_BYTES = QByteArray(_base64.b64decode(ICO_B64))
    _PNG_BYTES = QByteArray(_base64.b64decode(PNG_B64))
except ImportError:
    _ICO_BYTES = None
    _PNG_BYTES = None

# ── Phoenix Controls design system ────────────────────────────────────────────
# Dark navy theme only — see Phoenix_Tool_Design_V1/CLAUDE_STARTER_PROMPT.txt
# All colors, spacing, and component patterns are defined in phoenix_style.qss.
# Widget code uses objectName + dynamic properties (never inline setStyleSheet)
# so visual rules stay in one file.

QSS_FILENAME = "phoenix_style.qss"

# Minimal embedded fallback used when the .qss file isn't found at runtime
# (e.g. an auto-update that ships only the new exe). Keep this in sync with
# the most-load-bearing rules in phoenix_style.qss — the full file is the
# source of truth.
_EMBEDDED_QSS = """
QMainWindow, QDialog { background-color: #0a0e27; color: #ffffff; }
QWidget { color: #ffffff; font-family: "Segoe UI", sans-serif; font-size: 11pt; }
QMenuBar { background-color: #0a0e27; color: #ffffff; border-bottom: 1px solid #2d3748; }
QMenuBar::item:selected { background-color: #1f2937; color: #3b82f6; }
QMenu { background-color: #141829; color: #ffffff; border: 1px solid #2d3748; }
QMenu::item:selected { background-color: #1f2937; color: #3b82f6; }
QPushButton { background-color: #dc2626; color: #ffffff; border: none; border-radius: 6px;
              padding: 10px 16px; font-weight: 600; }
QPushButton:hover { background-color: #b91c1c; }
QPushButton#secondaryButton { background-color: #1e3a8a; }
QPushButton#secondaryButton:hover { background-color: #1e40af; }
QPushButton#tertiaryButton { background-color: transparent; border: 1px solid #4b5563; color: #3b82f6; }
QPushButton#tertiaryButton:hover { background-color: #1f2937; border: 1px solid #3b82f6; }
QLineEdit, QTextEdit, QPlainTextEdit { background-color: #141829; color: #ffffff;
              border: 1px solid #2d3748; border-radius: 6px; padding: 10px 12px; }
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus { border: 2px solid #3b82f6; }
QListWidget, QTableWidget { background-color: #141829; color: #ffffff;
              border: 1px solid #2d3748; border-radius: 6px;
              alternate-background-color: #0f1219; }
QHeaderView::section { background-color: #050810; color: #e5e7eb; padding: 10px 12px;
              border: none; border-right: 1px solid #2d3748; border-bottom: 1px solid #2d3748;
              font-weight: 600; }
QTabWidget::pane { background-color: #141829; border: 1px solid #2d3748; }
QTabBar::tab { background-color: #050810; color: #9ca3af; padding: 10px 16px;
              border: 1px solid #2d3748; border-bottom: none; }
QTabBar::tab:selected { background-color: #141829; color: #ffffff; border-bottom: 3px solid #dc2626; }
QStatusBar { background-color: #050810; color: #d1d5db; border-top: 1px solid #2d3748; }
QFrame { border: 1px solid #2d3748; background-color: #141829; border-radius: 6px; }
QFrame#SectionCard, QFrame#HeaderCard { background-color: #141829; border: 1px solid #2d3748;
              border-radius: 8px; }
QScrollBar:vertical { background-color: #0a0e27; width: 12px; border: none; }
QScrollBar::handle:vertical { background-color: #4b5563; border-radius: 6px; min-height: 20px; }
"""


def _resource_path(filename: str) -> str:
    """Resolve a bundled-asset path that works both in dev and in PyInstaller bundles."""
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, filename)


def load_phoenix_stylesheet(app: QApplication) -> None:
    """Load the Phoenix Controls QSS file, falling back to the embedded copy
    if the file isn't bundled with the installation (e.g. a partial update)."""
    app.setStyle("Fusion")
    qss_path = _resource_path(QSS_FILENAME)
    try:
        with open(qss_path, "r", encoding="utf-8") as fh:
            app.setStyleSheet(fh.read())
    except OSError:
        app.setStyleSheet(_EMBEDDED_QSS)


# ── Phoenix component helper classes ──────────────────────────────────────────
# Per the design system (CLAUDE_STARTER_PROMPT.txt section
# "COMPONENT HELPER CLASSES"): use these instead of raw QPushButton /
# QTableWidget so default min-height, cursor, and objectName are consistent.

class PrimaryButton(QPushButton):
    """Red primary-action button — the QSS default for QPushButton.

    Uses setFixedHeight so the button doesn't get vertically stretched by
    parent layouts that have extra space to distribute.
    """

    def __init__(self, text: str, parent: "QWidget | None" = None) -> None:
        super().__init__(text, parent)
        self.setFixedHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class SecondaryButton(QPushButton):
    """Blue secondary-action button (objectName='secondaryButton')."""

    def __init__(self, text: str, parent: "QWidget | None" = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("secondaryButton")
        self.setFixedHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class TertiaryButton(QPushButton):
    """Outline low-emphasis button (objectName='tertiaryButton')."""

    def __init__(self, text: str, parent: "QWidget | None" = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("tertiaryButton")
        self.setFixedHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class PhoenixTable(QTableWidget):
    """Read-only data table with the Phoenix-styling defaults applied."""

    def __init__(self, rows: int = 0, cols: int = 0, parent: "QWidget | None" = None) -> None:
        super().__init__(rows, cols, parent)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAlternatingRowColors(True)


# ──────────────────────────────────────────────────────────────────────────────

ICON_FILE = "Normal_red.ico"
BACKGROUND_FILE = "Transparent_red.png"

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
TABLE_MIN_HEIGHT = 190

# Debounce delay (ms) for live decode-as-you-type
LIVE_DECODE_DELAY_MS = 400

# Logical fields plus their config-map key suffix. Display labels are auto-derived
# from each product's <logical>_label entry below — keep this list in sync with
# the keys actually present in standard_product_configs.
_LOGICAL_FIELDS: tuple[tuple[str, str], ...] = (
    ("family",       "family_map"),
    ("construction", "construction_map"),
    ("bodies",       "bodies_map"),
    ("size",         "size_map"),
    ("pressure",     "pressure_map"),
    ("design",       "design_map"),
    ("control",      "control_map"),
    ("controller",   "controller_map"),
    ("orientation",  "orientation_map"),
    ("failsafe",     "failsafe_map"),
)


def _build_field_maps() -> tuple[dict[str, str], dict[str, str]]:
    """Derive (FIELD_TO_CONFIG_KEY, FIELD_TO_LOGICAL_FIELD) from the product configs.

    Each product line uses its own display label per logical field (e.g. "Construction"
    vs "Valve Construction" vs "Chemical Resistance"). We collect every distinct label
    from every product and route it back to the same logical field + config key, so
    adding a new product line never requires editing this file.
    """
    config_key: dict[str, str] = {}
    logical: dict[str, str] = {}

    for cfg in standard_product_configs.values():
        for logical_name, map_key in _LOGICAL_FIELDS:
            label = cfg.get(f"{logical_name}_label")
            if label:
                config_key[label] = map_key
                logical[label] = logical_name

    # Static, non-product-specific fields.
    config_key["Communication Protocol"] = "protocol_map"
    logical["Communication Protocol"]    = "protocol"
    config_key["Options"]                = "option_map"
    logical["Options"]                   = "options"

    return config_key, logical


FIELD_TO_CONFIG_KEY, FIELD_TO_LOGICAL_FIELD = _build_field_maps()

# "Valve Family" is informational only — never editable.
EDITABLE_FIELDS: set[str] = {
    key for key in FIELD_TO_CONFIG_KEY if key != "Valve Family"
}

# Logical-field name -> ParsedModel attribute name. Used by _set_parsed_field
# to apply a code change to the cloned model without a long if/elif chain.
LOGICAL_FIELD_TO_PARSED_ATTR: dict[str, str] = {
    "family":       "prefix",
    "construction": "construction",
    "bodies":       "qty_char",
    "size":         "size_code",
    "pressure":     "pressure",
    "design":       "design_char",
    "control":      "control_type",
    "controller":   "controller",
    "orientation":  "orientation",
    "failsafe":     "failsafe",
    "protocol":     "protocol",
}

VALID_TEST_MODELS = [
    # Celeris II
    "MAVA108M-AMEHZ-REI",
    "EXVA108M-ANHHO-PSL",
    # Theris (BACnet TP supply)
    "HSVA110M-AIAHZ",
    # Theris LonMark + WRE (LonMark-only option)
    "HEVA108L-SIEHZ-WRE",
    # Theris FLEX
    "FSVA108M-AHAHZ-PSL",
    # Traccel
    "TSVA110M-AIAHZ",
    # Venturian
    "VEVA108M-AHAHZ",
    # CSCP
    "PVEA110M-AMBHY-BMT-PSL",
    # Base Upgradeable Tiered (Q control)
    "BSVA110M-AQFHZ-PSL",
    # Constant Volume / BxV
    "CSVA110M-ACNHZ",
    # PBC (non-valve)
    "PBC500-ZBH",
    # FHD500
    "FHD500-DHV",
    # Sentry FHD130
    "FHD130-ENG-RD1",
    # ZPS
    "ZPS310",
    # Upgrade Kit (Celeris 2)
    "C2UX112L-XMEXO-BC1",
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
    """Pill-shaped status badge.

    Visuals are driven entirely by the QSS — pass an `object_name`
    that matches a selector (e.g. ``ModeBadge``, ``ProductBadge``,
    ``ValidationBadge``) and use ``set_state`` to swap the dynamic
    property the QSS keys off of.
    """

    def __init__(self, text: str, object_name: str, state: str = "") -> None:
        super().__init__(text)
        self.setObjectName(object_name)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(26)
        self._property_name = self._property_for(object_name)
        self.set_state(state)

    @staticmethod
    def _property_for(object_name: str) -> str:
        # Each badge keys off a different property name so the QSS rules can
        # be specific (mode badge -> [mode="..."], validation -> [state="..."]).
        if object_name == "ModeBadge":
            return "mode"
        return "state"

    def set_state(self, state: str) -> None:
        """Apply a dynamic property that the QSS uses to pick the variant."""
        self.setProperty(self._property_name, state or "")
        # Force the style engine to re-evaluate selectors — required for
        # QSS [property="value"] rules to update at runtime.
        self.style().unpolish(self)
        self.style().polish(self)


class SectionCard(QFrame):
    def __init__(self, title: str, *, expanding: bool = False) -> None:
        super().__init__()
        self.setObjectName("SectionCard")
        # Default Vertical Fixed forces the card to be exactly its sizeHint —
        # neither grow when there's extra space nor shrink when crowded.
        # Combined with fixed-height children, the card height is fully
        # deterministic regardless of decoded state.
        # `expanding=True` opts into a vertically-growing card (used by the
        # Notes panel so the QTextEdit can fill the right column).
        v_policy = QSizePolicy.Policy.Expanding if expanding else QSizePolicy.Policy.Fixed
        self.setSizePolicy(QSizePolicy.Policy.Preferred, v_policy)
        self._layout = QVBoxLayout(self)
        # 8px grid: tight inner padding, modest gap between rows.
        self._layout.setContentsMargins(12, 12, 12, 12)
        self._layout.setSpacing(8)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("SectionTitle")
        self.title_label.setFixedHeight(22)
        self._layout.addWidget(self.title_label)

    def add_widget(self, widget: QWidget, stretch: int = 0) -> None:
        self._layout.addWidget(widget, stretch)

    def add_layout(self, layout) -> None:
        self._layout.addLayout(layout)

    def add_spacing(self, spacing: int) -> None:
        self._layout.addSpacing(spacing)

    def add_stretch(self, factor: int = 1) -> None:
        self._layout.addStretch(factor)

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)


class SelfTestDialog(QDialog):
    """Runs the bundled regression-style smoke test and shows results.

    Despite the legacy `run_baseline_debug_benchmark` name in the backend,
    this is a correctness smoke test (decode + validate ~12 representative
    models), not a performance benchmark. Useful for verifying an install
    works end-to-end before relying on it.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Self-Test Results")
        self.resize(980, 680)

        layout = QVBoxLayout(self)
        text_box = QTextEdit()
        text_box.setReadOnly(True)
        text_box.setPlainText(run_baseline_debug_benchmark())
        layout.addWidget(text_box)

        close_row = QHBoxLayout()
        close_row.addStretch(1)
        close_btn = TertiaryButton("Close")
        close_btn.clicked.connect(self.accept)
        close_row.addWidget(close_btn)
        layout.addLayout(close_row)


def _filter_list_widget(list_widget: QListWidget, needle: str) -> None:
    """Hide items in a QListWidget that don't match a case-insensitive substring."""
    needle = needle.strip().lower()
    for i in range(list_widget.count()):
        item = list_widget.item(i)
        item.setHidden(bool(needle) and needle not in item.text().lower())


# Picker dialogs use the design-system palette; hard-code the two foreground
# colours for valid vs invalid items (the rest is QSS-driven).
_PICKER_VALID_FG   = QColor("#ffffff")
_PICKER_INVALID_FG = QColor("#6b7280")


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
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        header = QLabel(field_name)
        header.setObjectName("PickerHeader")
        layout.addWidget(header)

        sub = QLabel("White = valid now • Grey = not valid now (reason shown)")
        sub.setObjectName("PickerSubtitle")
        layout.addWidget(sub)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter by code, description, or part number...")
        self._search.setClearButtonEnabled(True)
        layout.addWidget(self._search)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("PickerList")
        self.list_widget.setWordWrap(True)
        self._search.textChanged.connect(lambda t: _filter_list_widget(self.list_widget, t))

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
            item.setForeground(_PICKER_VALID_FG if valid else _PICKER_INVALID_FG)
            self.list_widget.addItem(item)

        self.list_widget.itemDoubleClicked.connect(self._handle_pick)
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        apply_btn = PrimaryButton("Apply Selected")
        apply_btn.clicked.connect(self._apply_selected)
        close_btn = TertiaryButton("Close")
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
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        header = QLabel("Options")
        header.setObjectName("PickerHeader")
        layout.addWidget(header)

        sub = QLabel("Double-click an option to add/remove it. White = valid now / Grey = not valid now")
        sub.setObjectName("PickerSubtitle")
        layout.addWidget(sub)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter by code, description, or part number...")
        self._search.setClearButtonEnabled(True)
        layout.addWidget(self._search)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("PickerList")
        self.list_widget.setWordWrap(True)
        layout.addWidget(self.list_widget)

        self._refresh()
        self.list_widget.itemDoubleClicked.connect(self._toggle_item)
        self._search.textChanged.connect(lambda t: _filter_list_widget(self.list_widget, t))

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        apply_btn = PrimaryButton("Apply")
        apply_btn.clicked.connect(self._apply)
        close_btn = TertiaryButton("Close")
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
            item.setForeground(_PICKER_VALID_FG if valid else _PICKER_INVALID_FG)
            self.list_widget.addItem(item)

        # Preserve the current filter across toggles.
        _filter_list_widget(self.list_widget, self._search.text())

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
        edit_indicator = "  ✏" if self.editable else ""
        status = "✖" if self.invalid else "✔"
        code, description = self._split_code_value(self.field_value)
        title = f"{self.field_name} {code}" if code else self.field_name
        body = compact_text(description, width=CARD_TEXT_WRAP, max_lines=2)
        self.setText(f"{status}  {title}{edit_indicator}\n{body}")
        self.setToolTip(
            f"{self.field_name}\n\n{self.field_value}"
            + ("\n\n✏ Click to edit" if self.editable else "")
        )
        # Hand off to the QSS — selectors keyed off our object name and the
        # ``editable`` / ``invalid`` dynamic properties below.
        self.setProperty("editable", "true" if self.editable else "false")
        self.setProperty("invalid",  "true" if self.invalid  else "false")

    @staticmethod
    def _split_code_value(value: str) -> tuple[str, str]:
        # Backend formats single-value fields as "{code} -> {description}".
        # Multi-value fields (Options) use a comma-separated list of those —
        # don't split those, since pulling out the first code would mislead.
        if not value or "," in value or " -> " not in value:
            return "", value
        code, _, description = value.partition(" -> ")
        return code.strip(), description.strip()


class ValidationIssueRow(QFrame):
    """A styled row widget for a single validation issue in the Validation tab.
    Visuals come entirely from the QSS — see ``QFrame#ValidationIssueRow``."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__()
        self.setObjectName("ValidationIssueRow")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        field_label = QLabel(field)
        field_label.setObjectName("ValidationIssueField")
        layout.addWidget(field_label)

        msg_label = QLabel(message)
        msg_label.setObjectName("ValidationIssueMessage")
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
            notes_btn = TertiaryButton("What's new?")
            notes_btn.setFixedWidth(100)
            notes_btn.clicked.connect(lambda: QMessageBox.information(
                self,
                f"What's new in v{info.latest_version}",
                info.release_notes,
            ))
            layout.addWidget(notes_btn)

        # InstallBtn is special — its objectName drives a custom QSS rule
        # (green primary), per the design-system starter prompt.
        install_btn = QPushButton("Install & Restart")
        install_btn.setObjectName("InstallBtn")
        install_btn.setFixedWidth(140)
        install_btn.setMinimumHeight(36)
        install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        install_btn.clicked.connect(self.install_clicked)
        layout.addWidget(install_btn)

        dismiss_btn = TertiaryButton("✕")
        dismiss_btn.setFixedWidth(32)
        dismiss_btn.setToolTip("Dismiss")
        dismiss_btn.clicked.connect(self.hide)
        layout.addWidget(dismiss_btn)


class CfmCalculatorDialog(QDialog):
    """CFM / Face Velocity calculator.

    Equation:  CFM = (Length × Width / 144) × Face Velocity Setpoint
    Rearranged: Face Velocity = CFM × 144 / (Length × Width)
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("CFM / Face Velocity Calculator")
        self.setMinimumWidth(380)
        self.setMaximumWidth(460)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # ── Header ──────────────────────────────────────────────
        title = QLabel("CFM / Face Velocity Calculator")
        title.setObjectName("CalcHeader")
        layout.addWidget(title)

        sub = QLabel("CFM  =  (L \u00d7 W \u00f7 144) \u00d7 Face Velocity")
        sub.setObjectName("CalcSubtitle")
        layout.addWidget(sub)

        # ── Mode selector ────────────────────────────────────────
        mode_row = QHBoxLayout()
        mode_label = QLabel("Solve for:")
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["CFM", "Face Velocity Setpoint"])
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_row.addWidget(mode_label)
        mode_row.addWidget(self._mode_combo)
        mode_row.addStretch(1)
        layout.addLayout(mode_row)

        # ── Input grid ───────────────────────────────────────────
        grid = QGridLayout()
        grid.setVerticalSpacing(10)
        grid.setHorizontalSpacing(12)

        def _make_input() -> QLineEdit:
            w = QLineEdit()
            w.setPlaceholderText("0")
            w.setFixedHeight(32)
            return w

        grid.addWidget(QLabel("Length (in):"), 0, 0)
        self._length = _make_input()
        grid.addWidget(self._length, 0, 1)

        grid.addWidget(QLabel("Width (in):"), 1, 0)
        self._width = _make_input()
        grid.addWidget(self._width, 1, 1)

        self._fv_label = QLabel("Face Velocity (fpm):")
        self._fv_input = _make_input()
        grid.addWidget(self._fv_label, 2, 0)
        grid.addWidget(self._fv_input, 2, 1)

        self._cfm_label = QLabel("CFM:")
        self._cfm_input = _make_input()
        grid.addWidget(self._cfm_label, 3, 0)
        grid.addWidget(self._cfm_input, 3, 1)

        layout.addLayout(grid)

        # ── Calculate button ─────────────────────────────────────
        self._calc_btn = PrimaryButton("Calculate")
        self._calc_btn.clicked.connect(self._calculate)
        layout.addWidget(self._calc_btn)

        # ── Result display ───────────────────────────────────────
        # All visuals are QSS-driven; the [state] property selects the variant.
        self._result_label = QLabel("")
        self._result_label.setObjectName("CalcResult")
        self._result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._result_label.setMinimumHeight(52)
        layout.addWidget(self._result_label)

        # ── Close button ─────────────────────────────────────────
        close_row = QHBoxLayout()
        close_row.addStretch(1)
        close_btn = TertiaryButton("Close")
        close_btn.clicked.connect(self.reject)
        close_row.addWidget(close_btn)
        layout.addLayout(close_row)

        self._on_mode_changed(0)  # set initial visibility

    def _on_mode_changed(self, index: int) -> None:
        solving_cfm = (index == 0)
        self._fv_label.setVisible(solving_cfm)
        self._fv_input.setVisible(solving_cfm)
        self._cfm_label.setVisible(not solving_cfm)
        self._cfm_input.setVisible(not solving_cfm)
        self._result_label.setText("")

    def _calculate(self) -> None:
        try:
            length = float(self._length.text())
            width  = float(self._width.text())
        except ValueError:
            self._result_label.setText("Enter valid Length and Width values.")
            self._set_result_state("error")
            return

        area = (length * width) / 144.0
        if area <= 0:
            self._result_label.setText("Length and Width must be greater than 0.")
            self._set_result_state("error")
            return

        solving_cfm = (self._mode_combo.currentIndex() == 0)
        try:
            if solving_cfm:
                fv = float(self._fv_input.text())
                cfm = area * fv
                self._result_label.setText(f"CFM  =  {cfm:,.1f}")
            else:
                cfm = float(self._cfm_input.text())
                fv = cfm / area
                self._result_label.setText(f"Face Velocity  =  {fv:,.1f} fpm")
        except ValueError:
            name = "Face Velocity" if solving_cfm else "CFM"
            self._result_label.setText(f"Enter a valid {name} value.")
            self._set_result_state("error")
            return

        self._set_result_state("ok")

    def _set_result_state(self, state: str) -> None:
        """Drive the result-label QSS via the dynamic [state] property."""
        self._result_label.setProperty("state", state)
        self._result_label.style().unpolish(self._result_label)
        self._result_label.style().polish(self._result_label)


class TestModelsDialog(QDialog):
    """Fly-out dialog listing every Quick Test Model (valid + sample-invalid).

    Replaces the inline two-list panel that was crowding the bottom of the
    left panel. Search filter at the top; double-click any entry to load it
    into the model-number input and dismiss.
    """

    def __init__(self, parent: "QWidget | None", on_pick: Callable[[str], None]) -> None:
        super().__init__(parent)
        self.setWindowTitle("Test Models")
        self.resize(560, 600)
        self.on_pick = on_pick

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = QLabel("Test Models")
        header.setObjectName("PickerHeader")
        layout.addWidget(header)

        sub = QLabel("Double-click any entry to load it into the model-number input.")
        sub.setObjectName("PickerSubtitle")
        layout.addWidget(sub)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter by code or product line...")
        self._search.setClearButtonEnabled(True)
        layout.addWidget(self._search)

        self._list = QListWidget()
        self._list.setObjectName("PickerList")
        self._list.itemDoubleClicked.connect(self._handle_pick)
        self._search.textChanged.connect(lambda t: _filter_list_widget(self._list, t))
        layout.addWidget(self._list, 1)

        # Two grouped sections inside one list — non-selectable section
        # headers and selectable model rows.
        self._add_header("✔  Valid Models", "TestModelsValidLabel")
        for m in VALID_TEST_MODELS:
            self._add_row(m, valid=True)
        self._add_header("✖  Sample Invalid Models", "TestModelsFailingLabel")
        for m in FAILING_TEST_MODELS:
            self._add_row(m, valid=False)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        close_btn = TertiaryButton("Close")
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _add_header(self, text: str, object_name: str) -> None:
        item = QListWidgetItem(text)
        item.setObjectName = object_name  # purely informational; used in QSS via UserRole
        item.setData(Qt.ItemDataRole.UserRole, None)  # None marks this as a header
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        # Slight visual distinction so the section break is obvious.
        item.setForeground(QColor("#10b981" if "Valid" in text else "#ef4444"))
        self._list.addItem(item)

    def _add_row(self, model: str, valid: bool) -> None:
        item = QListWidgetItem(f"   {model}")
        item.setData(Qt.ItemDataRole.UserRole, model)
        self._list.addItem(item)

    def _handle_pick(self, item: QListWidgetItem) -> None:
        model = item.data(Qt.ItemDataRole.UserRole)
        if not model:
            return  # header row — ignore
        self.on_pick(str(model))
        self.accept()


class PartsListDialog(QDialog):
    """ATS Parts List / Inventory tool.

    Read-only by default. Click "Edit Mode" to unlock with the admin
    password — once unlocked, cells become editable, rows can be added /
    deleted, and Save writes the JSON back to SharePoint.
    """

    _COLUMNS = (
        ("ats_id",      "ATS ID"),
        ("manuf_part",  "Manuf. Part #"),
        ("description", "Description"),
        ("low_limit",   "Low Limit"),
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Parts List")
        self.resize(1100, 720)

        self._admin = False     # set True after a successful password unlock
        self._dirty = False
        self._offline = False   # True when the dialog is showing cached data

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── Header row ─────────────────────────────────────────────
        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        header = QLabel("Parts List")
        header.setObjectName("PartsListHeader")
        header_row.addWidget(header)
        header_row.addStretch(1)
        self._admin_badge = QLabel("ADMIN")
        self._admin_badge.setObjectName("PartsListAdminBadge")
        self._admin_badge.setVisible(False)
        header_row.addWidget(self._admin_badge)
        layout.addLayout(header_row)

        subtitle = QLabel("ATS parts catalog — synced from SharePoint.")
        subtitle.setObjectName("PartsListSubtitle")
        layout.addWidget(subtitle)

        self._meta_label = QLabel("")
        self._meta_label.setObjectName("PartsListMeta")
        layout.addWidget(self._meta_label)

        # ── Error banner (shown only when load fails) ──────────────
        self._error_banner = QLabel("")
        self._error_banner.setObjectName("PartsListErrorBanner")
        self._error_banner.setWordWrap(True)
        self._error_banner.setVisible(False)
        layout.addWidget(self._error_banner)

        # ── Filter ─────────────────────────────────────────────────
        self._filter = QLineEdit()
        self._filter.setPlaceholderText("Filter by ATS ID, Manuf. Part #, or Description...")
        self._filter.setClearButtonEnabled(True)
        self._filter.textChanged.connect(self._apply_filter)
        layout.addWidget(self._filter)

        # ── Table ──────────────────────────────────────────────────
        self._table = PhoenixTable(0, len(self._COLUMNS))
        self._table.setHorizontalHeaderLabels([label for _, label in self._COLUMNS])
        self._table.setSortingEnabled(True)
        # Selection enabled (we'll need it for Delete Row); still no edit
        # by default until admin unlocks.
        self._table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self._table.horizontalHeader()
        for col in range(len(self._COLUMNS) - 2):  # ATS ID, Manuf. Part #
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)        # Description
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Low Limit
        self._table.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self._table, 1)

        # ── Action row ─────────────────────────────────────────────
        actions = QHBoxLayout()
        actions.setSpacing(8)

        self._refresh_btn = SecondaryButton("Refresh")
        self._refresh_btn.clicked.connect(self._reload)
        actions.addWidget(self._refresh_btn)

        self._edit_btn = SecondaryButton("Edit Mode")
        self._edit_btn.clicked.connect(self._toggle_edit_mode)
        actions.addWidget(self._edit_btn)

        self._add_btn = SecondaryButton("Add Row")
        self._add_btn.clicked.connect(self._add_row)
        self._add_btn.setVisible(False)
        actions.addWidget(self._add_btn)

        self._delete_btn = SecondaryButton("Delete Selected")
        self._delete_btn.clicked.connect(self._delete_selected)
        self._delete_btn.setVisible(False)
        actions.addWidget(self._delete_btn)

        self._save_btn = PrimaryButton("Save")
        self._save_btn.clicked.connect(self._save)
        self._save_btn.setVisible(False)
        actions.addWidget(self._save_btn)

        actions.addStretch(1)

        close_btn = TertiaryButton("Close")
        close_btn.clicked.connect(self.reject)
        actions.addWidget(close_btn)

        layout.addLayout(actions)

        # Initial load
        self._reload()

    # ----------------------------------------------------------------
    # Loading / saving
    # ----------------------------------------------------------------

    def _reload(self) -> None:
        if self._dirty and not self._confirm_discard("Reload"):
            return
        inv, banner, status = load_inventory()
        self._populate_table(inv.parts)
        # Banner: hidden on "ok", amber on "warning" (cache fallback), red on "error".
        if banner:
            self._error_banner.setText(banner)
            self._error_banner.setProperty(
                "severity", "warning" if status == "warning" else "error"
            )
            self._error_banner.style().unpolish(self._error_banner)
            self._error_banner.style().polish(self._error_banner)
            self._error_banner.setVisible(True)
        else:
            self._error_banner.setVisible(False)

        if inv.parts or status == "warning":
            who = inv.updated_by or "unknown"
            when = inv.updated_at or "unknown"
            self._meta_label.setText(
                f"{len(inv.parts)} parts  •  Last updated {when} by {who}  •  {inventory_json_path()}"
            )
        else:
            self._meta_label.setText("")

        # Offline (cache) mode disables editing — the SharePoint copy is the
        # source of truth, so we don't want admins making local-only edits
        # that could be overwritten when sync comes back.
        self._offline = (status == "warning")
        if self._offline and self._admin:
            self._admin = False
            self._refresh_admin_ui()
        self._edit_btn.setEnabled(not self._offline and status != "error")
        if self._offline:
            self._edit_btn.setToolTip(
                "Editing is disabled while working from cache. Reconnect to "
                "SharePoint to make changes."
            )
        else:
            self._edit_btn.setToolTip("")

        self._dirty = False
        self._update_save_button_label()

    def _populate_table(self, parts: list[Part]) -> None:
        # Block the itemChanged signal while we rebuild rows.
        self._table.blockSignals(True)
        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)
        for part in parts:
            self._append_row(part)
        self._table.setSortingEnabled(True)
        self._table.blockSignals(False)
        self._apply_filter(self._filter.text())

    def _append_row(self, part: Part) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        for col, (key, _label) in enumerate(self._COLUMNS):
            value = getattr(part, key)
            text = "" if value is None else str(value)
            item = QTableWidgetItem(text)
            # Right-align numeric Low Limit for readability.
            if key == "low_limit":
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, col, item)
        self._apply_row_editability(row)

    def _save(self) -> None:
        if not self._admin:
            return
        parts = self._collect_parts()
        ok, msg = save_inventory(parts)
        if not ok:
            QMessageBox.critical(self, "Save Failed", msg)
            return
        self._dirty = False
        self._update_save_button_label()
        self._reload()  # refresh meta footer with new updated_at / updated_by
        if self.parent() is not None and hasattr(self.parent(), "statusBar"):
            self.parent().statusBar().showMessage(msg, 4000)

    def _collect_parts(self) -> list[Part]:
        """Read every (visible or hidden) row out of the table back into a list."""
        parts: list[Part] = []
        for row in range(self._table.rowCount()):
            ats_id     = self._cell_text(row, 0)
            manuf_part = self._cell_text(row, 1)
            descr      = self._cell_text(row, 2)
            low_text   = self._cell_text(row, 3)
            if not (ats_id or manuf_part or descr):
                continue  # skip fully-blank rows
            try:
                low = int(low_text) if low_text else None
            except ValueError:
                low = None
            parts.append(Part(
                ats_id=ats_id,
                manuf_part=manuf_part,
                description=descr,
                low_limit=low,
            ))
        return parts

    def _cell_text(self, row: int, col: int) -> str:
        item = self._table.item(row, col)
        return item.text().strip() if item is not None else ""

    # ----------------------------------------------------------------
    # Filtering
    # ----------------------------------------------------------------

    def _apply_filter(self, needle: str = "") -> None:
        needle = (needle or "").strip().lower()
        for row in range(self._table.rowCount()):
            if not needle:
                self._table.setRowHidden(row, False)
                continue
            match = False
            for col in range(self._table.columnCount()):
                if needle in self._cell_text(row, col).lower():
                    match = True
                    break
            self._table.setRowHidden(row, not match)

    # ----------------------------------------------------------------
    # Edit mode
    # ----------------------------------------------------------------

    def _toggle_edit_mode(self) -> None:
        if self._admin:
            # Switching OFF
            if self._dirty and not self._confirm_discard("Exit edit mode"):
                return
            self._admin = False
            self._reload()  # discard unsaved changes by reloading
        else:
            # Switching ON — prompt for password
            pw, ok = QInputDialog.getText(
                self,
                "Admin Password",
                "Enter the admin password to enable editing:",
                QLineEdit.EchoMode.Password,
            )
            if not ok:
                return
            if not is_admin_password(pw):
                QMessageBox.warning(self, "Incorrect Password", "That password is not correct.")
                return
            self._admin = True
        self._refresh_admin_ui()

    def _refresh_admin_ui(self) -> None:
        self._admin_badge.setVisible(self._admin)
        self._edit_btn.setText("Exit Edit Mode" if self._admin else "Edit Mode")
        self._add_btn.setVisible(self._admin)
        self._delete_btn.setVisible(self._admin)
        self._save_btn.setVisible(self._admin)
        # Re-apply edit triggers per row
        for row in range(self._table.rowCount()):
            self._apply_row_editability(row)
        if self._admin:
            self._table.setEditTriggers(
                QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.EditKeyPressed
            )
        else:
            self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._update_save_button_label()

    def _apply_row_editability(self, row: int) -> None:
        editable_flag = (
            (Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable)
            if self._admin
            else (Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        )
        for col in range(self._table.columnCount()):
            item = self._table.item(row, col)
            if item is not None:
                item.setFlags(editable_flag)

    def _add_row(self) -> None:
        if not self._admin:
            return
        self._append_row(Part())
        self._dirty = True
        self._update_save_button_label()
        # Scroll to and select the new row
        new_row = self._table.rowCount() - 1
        self._table.scrollToBottom()
        self._table.setCurrentCell(new_row, 0)

    def _delete_selected(self) -> None:
        if not self._admin:
            return
        rows = sorted({idx.row() for idx in self._table.selectedIndexes()}, reverse=True)
        if not rows:
            QMessageBox.information(self, "Nothing Selected", "Select one or more rows first.")
            return
        count = len(rows)
        confirm = QMessageBox.question(
            self,
            "Delete Rows?",
            f"Delete {count} row{'s' if count != 1 else ''}? This cannot be undone until you Save.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        for row in rows:
            self._table.removeRow(row)
        self._dirty = True
        self._update_save_button_label()

    def _on_item_changed(self, _item: QTableWidgetItem) -> None:
        if not self._admin:
            return
        self._dirty = True
        self._update_save_button_label()

    def _update_save_button_label(self) -> None:
        self._save_btn.setText("Save *" if self._dirty else "Save")

    def _confirm_discard(self, action_label: str) -> bool:
        confirm = QMessageBox.question(
            self,
            "Discard Unsaved Changes?",
            f"You have unsaved edits. {action_label} and discard them?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return confirm == QMessageBox.StandardButton.Yes

    # ----------------------------------------------------------------
    # Qt overrides
    # ----------------------------------------------------------------

    def reject(self) -> None:
        if self._dirty and not self._confirm_discard("Close"):
            return
        super().reject()


class WatermarkWidget(QWidget):
    """Full-window central widget — paints a centered watermark at 25% opacity.

    Mimics the Project Tracking Tool's ``_BackgroundWidget``: the logo is
    drawn directly via ``QPainter`` (no ``QGraphicsOpacityEffect``, no child
    ``QLabel``) and sized to 60% of the smaller window dimension. Layout
    containers stacked on top use ``WA_TranslucentBackground`` so the
    watermark peeks through the gutters between cards.
    """

    # 0.35 picked over PTT's 0.25 because Phoenix Master Tool's bg is darker
    # navy (#0a0e27 vs PTT's slate); the red logo blends into the bg too far
    # at 0.25 to be visually present.
    _OPACITY = 0.35
    _SCALE = 0.60

    def __init__(self) -> None:
        super().__init__()
        self.logo_pixmap_original: QPixmap | None = None

    def set_watermark_bytes(self, data) -> None:
        px = QPixmap()
        px.loadFromData(data)
        if not px.isNull():
            self.logo_pixmap_original = px
            self.update()

    def set_watermark(self, image_path: str) -> None:
        if os.path.exists(image_path):
            px = QPixmap(image_path)
            if not px.isNull():
                self.logo_pixmap_original = px
                self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self.logo_pixmap_original is None or self.logo_pixmap_original.isNull():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setOpacity(self._OPACITY)

        max_dim = int(min(self.width(), self.height()) * self._SCALE)
        scaled = self.logo_pixmap_original.scaled(
            max_dim,
            max_dim,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
        painter.end()


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
        self._pending_update_info: UpdateInfo | None = None
        self._update_banner: UpdateBanner | None = None

        self._field_card_specs: list[tuple[str, str, bool, bool]] = []
        self._field_columns_current: int = 0

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

        # Startup checks (after UI is built)
        self._check_sync_folder()
        threading.Thread(target=self._check_update_bg, daemon=True).start()

    # ------------------------------------------------------------------ #
    # Qt overrides                                                         #
    # ------------------------------------------------------------------ #

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        # Avoid the per-pixel rebuild storm during window drags: only rebuild
        # when the column count actually flips between 1/2/3.
        if not self._field_card_specs:
            return
        new_columns = self._field_column_count()
        if new_columns != self._field_columns_current:
            self._rebuild_field_cards()

    # ------------------------------------------------------------------ #
    # Initialisation helpers                                               #
    # ------------------------------------------------------------------ #

    def _load_window_icon(self) -> None:
        pixmap = QPixmap()
        if _ICO_BYTES is not None:
            pixmap.loadFromData(_ICO_BYTES)
        if pixmap.isNull():
            icon_path = os.path.join(BASE_DIR, ICON_FILE)
            if os.path.exists(icon_path):
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
            app = QApplication.instance()
            if isinstance(app, QApplication):
                app.setWindowIcon(icon)

    def _load_background_watermark(self) -> None:
        if _PNG_BYTES is not None:
            self.watermark_widget.set_watermark_bytes(_PNG_BYTES)
        else:
            bg_path = os.path.join(BASE_DIR, BACKGROUND_FILE)
            self.watermark_widget.set_watermark(bg_path)

    def _build_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)  # Ctrl+S
        save_action.triggered.connect(self.save_output)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)  # Ctrl+Shift+S
        save_as_action.triggered.connect(self.save_output_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        tools_menu = menubar.addMenu("Tools")
        benchmark_action = QAction("Run Self-Test", self)
        benchmark_action.setToolTip("Decode and validate a set of known good and bad models to verify the app is working correctly.")
        benchmark_action.triggered.connect(self.show_benchmark_results)
        tools_menu.addAction(benchmark_action)

        copy_action = QAction("Copy Summary", self)
        copy_action.setShortcut("Ctrl+Shift+C")
        copy_action.triggered.connect(self.copy_output)
        tools_menu.addAction(copy_action)

        cfm_action = QAction("CFM / FV Calculator", self)
        cfm_action.setShortcut("Ctrl+K")
        cfm_action.triggered.connect(self._open_cfm_calculator)
        tools_menu.addAction(cfm_action)

        decode_action = QAction("Decode Model", self)
        decode_action.setShortcut("F5")
        decode_action.triggered.connect(self.decode_and_display)
        tools_menu.addAction(decode_action)

        focus_input_action = QAction("Focus Model Input", self)
        focus_input_action.setShortcut("Ctrl+L")
        focus_input_action.triggered.connect(self._focus_model_input)
        tools_menu.addAction(focus_input_action)

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
        # Design system: 16px window padding, 16px between major sections.
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(16)
        root_layout.addWidget(self._build_header())

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setOpaqueResize(True)
        # Translucent so the centered watermark on the central widget shows
        # through gutters between cards (the splitter itself paints a fill
        # otherwise, blocking the watermark across the whole panel area).
        self.main_splitter.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        root_layout.addWidget(self.main_splitter, 1)

        self.main_splitter.addWidget(self._build_left_panel())
        self.main_splitter.addWidget(self._build_center_panel())
        self.main_splitter.addWidget(self._build_right_panel())

        self.main_splitter.setStretchFactor(0, 2)
        self.main_splitter.setStretchFactor(1, 7)
        self.main_splitter.setStretchFactor(2, 4)
        self.main_splitter.setSizes([380, 800, 380])

        # Left panel is locked at a fixed width so the input section and table
        # stay where the user expects. 380px lets the operating-range table
        # show "Celeris II Medium Pressure (M) + Conical Shaped Diffuser (A)"
        # without truncating the title or the Pressure Drop column.
        self.main_splitter.widget(0).setFixedWidth(380)
        self.main_splitter.widget(2).setMinimumWidth(280)
        # Disable the handle between left and center; keep handle 2 (between
        # center and right) functional.
        left_handle = self.main_splitter.handle(1)
        left_handle.setEnabled(False)
        left_handle.setCursor(Qt.CursorShape.ArrowCursor)

        # Restore previously-saved splitter layout, if any.
        saved_sizes = QSettings("ATSInc", "PhoenixMasterTool").value("mainSplitterSizes")
        if isinstance(saved_sizes, list):
            try:
                self.main_splitter.setSizes([int(s) for s in saved_sizes])
            except (TypeError, ValueError):
                pass
        self.main_splitter.splitterMoved.connect(self._save_splitter_sizes)

        # Update banner — hidden until a new version is detected
        self._update_banner = None

        status = QStatusBar()
        status.showMessage("Phoenix Master Tool | Guided model builder ready")
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

        self.mode_badge = BadgeLabel("Normal Mode", "ModeBadge")
        self.product_badge = BadgeLabel("Product: —", "ProductBadge")
        self.validation_badge = BadgeLabel("No validation run yet", "ValidationBadge")

        cfm_btn = SecondaryButton("CFM / FV Calc")
        cfm_btn.clicked.connect(self._open_cfm_calculator)

        parts_list_btn = SecondaryButton("Parts List")
        parts_list_btn.clicked.connect(self._open_parts_list)

        test_models_btn = SecondaryButton("Test Models")
        test_models_btn.clicked.connect(self._open_test_models)

        layout.addWidget(cfm_btn)
        layout.addWidget(parts_list_btn)
        layout.addWidget(test_models_btn)
        layout.addWidget(self.mode_badge)
        layout.addWidget(self.product_badge)
        layout.addWidget(self.validation_badge)
        return card

    def _build_left_panel(self) -> QWidget:
        self.left_panel_container = QWidget()
        # Translucent so the centered watermark on the central widget shows
        # through the gutter between cards (mimics PTT's _BackgroundWidget).
        self.left_panel_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QVBoxLayout(self.left_panel_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._build_input_card(), 0)
        layout.addWidget(self._build_table_card(), 0)
        # Test Models moved to a fly-out dialog (Test Models button in header).
        layout.addStretch(1)
        return self.left_panel_container

    def _build_input_card(self) -> SectionCard:
        self.input_card = SectionCard("Input")
        # Lock every child of the input card to a fixed height so the layout
        # doesn't redistribute extra space differently between the empty and
        # populated states. QLabel/QCheckBox default to Preferred vertical
        # size policy and would otherwise grow when the section has slack.
        model_label = QLabel("Model Number")
        model_label.setFixedHeight(20)
        self.input_card.add_widget(model_label)

        self.model_entry = QLineEdit()
        self.model_entry.setPlaceholderText("Enter a model number...")
        self.model_entry.setFixedHeight(40)
        self.model_entry.returnPressed.connect(self.decode_and_display)
        self.model_entry.textChanged.connect(self._on_model_text_changed)
        self.input_card.add_widget(self.model_entry)
        self.input_card.add_spacing(12)

        self.analog_checkbox = QCheckBox("Analog Mode")
        self.analog_checkbox.setFixedHeight(22)
        self.analog_checkbox.stateChanged.connect(self._on_analog_changed)
        self.input_card.add_widget(self.analog_checkbox)

        BTN_ROW_SPACING = 12  # vertical breathing room between action-button rows

        # Decode + Clear buttons removed — live decode (text-changed timer)
        # already updates the display on every keystroke, and Ctrl+L / Esc /
        # F5 keyboard shortcuts cover the explicit-action use cases.

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        self.copy_button = SecondaryButton("Copy Summary")
        self.copy_button.clicked.connect(self.copy_output)
        self.save_button = SecondaryButton("Save Summary")
        self.save_button.clicked.connect(self.save_output)
        row2.addWidget(self.copy_button)
        row2.addWidget(self.save_button)
        self.input_card.add_layout(row2)
        self.input_card.add_spacing(BTN_ROW_SPACING)

        row3 = QHBoxLayout()
        row3.setSpacing(8)
        self.export_parts_button = SecondaryButton("Export Parts List")
        self.export_parts_button.clicked.connect(self._export_parts_list)
        row3.addWidget(self.export_parts_button)
        self.input_card.add_layout(row3)

        return self.input_card

    def _build_table_card(self) -> SectionCard:
        self.table_card = SectionCard("Flow / Pressure Operating Table")
        self.table_widget = QTableWidget()
        # The Phoenix QSS gives table cells/headers generous padding (8/12 px),
        # so a tighter object-name lets us tighten this specific table without
        # affecting the rest of the app.
        self.table_widget.setObjectName("OperatingTable")
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(
            ["Size", "Single CFM", "Dual CFM", "Pressure Drop"]
        )
        header = self.table_widget.horizontalHeader()
        # Auto-size the three numeric columns to the content + header text;
        # let Pressure Drop (always the same value across rows) take the rest.
        for col in range(3):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
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

    def _build_center_panel(self) -> QWidget:
        container = QWidget()
        container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.decoded_card = SectionCard("Decoded Fields")

        self.cards_container = QWidget()
        self.cards_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setContentsMargins(2, 2, 2, 2)
        self.cards_layout.setHorizontalSpacing(8)
        self.cards_layout.setVerticalSpacing(8)

        self.decoded_card.add_widget(self.cards_container)
        layout.addWidget(self.decoded_card, 0, Qt.AlignmentFlag.AlignTop)
        layout.addStretch(1)
        return container

    def _build_right_panel(self) -> QWidget:
        # Notes-only panel wrapped in an expanding SectionCard so the visual
        # framing matches the other panels (no orphaned QTextEdit border
        # peeking out below the section title). Validation issues are
        # surfaced on the field cards themselves (red border + tooltip);
        # the header badge shows the issue count.
        container = QWidget()
        container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        notes_card = SectionCard("Notes", expanding=True)

        self.notes_text = QTextEdit()
        self.notes_text.setReadOnly(True)
        # The QTextEdit's own border defines the content frame; an extra
        # SectionCard inset of 12px keeps everything aligned with the rest
        # of the dashboard. Drop the QTextEdit's frame so we don't get a
        # double-border ring.
        self.notes_text.setFrameShape(QFrame.Shape.NoFrame)
        notes_card.add_widget(self.notes_text, 1)

        layout.addWidget(notes_card, 1)
        return container

    def _update_table_columns(self) -> None:
        # Column sizing is fully QHeaderView-driven now: cols 0-2 use
        # ResizeToContents, col 3 uses Stretch. Nothing to set explicitly.
        pass

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
            self.mode_badge.set_state("analog")
        else:
            self.mode_badge.setText("Normal Mode")
            self.mode_badge.set_state("")
        # Re-trigger live decode when analog mode toggles
        if self.model_entry.text().strip():
            self._decode_timer.start()

    def _on_model_text_changed(self, text: str) -> None:
        """Restart the debounce timer on every keystroke; reset display when empty."""
        if text.strip():
            self._decode_timer.start()
        else:
            self._decode_timer.stop()
            self._reset_display_state()

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
            self._field_columns_current = 0
            return

        self._clear_field_cards()
        columns = self._field_column_count()
        self._field_columns_current = columns

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
        self.model_entry.clear()  # triggers _on_model_text_changed → _reset_display_state
        self.current_save_path = None

    def _reset_display_state(self) -> None:
        """Reset all decoded state and display panels (does not touch the model entry)."""
        self.notes_text.clear()
        self.table_widget.setRowCount(0)
        self.table_widget.setFixedHeight(TABLE_MIN_HEIGHT)
        self.current_output_text = ""
        self.current_product_line = "UNKNOWN"
        self.current_data = {}
        self.current_notes = []
        self.current_validation_issues = []
        self.current_parsed_model = None
        self.current_operating_table = None
        self._field_card_specs = []

        self.product_badge.setText("Product: —")
        self.validation_badge.setText("No validation run yet")
        self.validation_badge.set_state("")
        self.table_card.set_title("Flow / Pressure Operating Table")
        self._clear_field_cards()

    def _update_badges(self, product_line: str, validation_issues: list[dict]) -> None:
        product_text = PRODUCT_DISPLAY_NAMES.get(product_line, product_line)
        self.product_badge.setText(f"Product: {product_text}")

        if validation_issues:
            count = len(validation_issues)
            self.validation_badge.setText(f"{count} validation issue{'s' if count != 1 else ''}")
            self.validation_badge.set_state("issues")
        else:
            self.validation_badge.setText("No validation issues")
            self.validation_badge.set_state("clean")

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
        logical = FIELD_TO_LOGICAL_FIELD.get(field_name)
        attr = LOGICAL_FIELD_TO_PARSED_ATTR.get(logical) if logical else None
        if attr is not None:
            setattr(parsed, attr, code)

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
                    # Subtle highlight on the (merged) Pressure-Drop cell.
                    item.setBackground(QColor("#1e3a8a"))
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
        self._build_field_cards(parsed, decoded_data, validation_issues)

        self.current_output_text = self._make_summary_text(model, product_line, validation_issues, notes)

        self._update_notes_panel(notes)
        self._fill_table_from_structured(operating_table)

    def _update_notes_panel(self, notes: list[str]) -> None:
        if not notes:
            self.notes_text.setPlainText("No notes.")
            return

        # Bold the note heading prefix for readability. Colors come from the
        # design-system palette (Bright Blue for headings on Navy).
        header_color = "#3b82f6"
        text_color   = "#e5e7eb"

        html_parts = []
        for note in notes:
            lines = note.strip().splitlines()
            if not lines:
                continue
            first = lines[0]
            rest = lines[1:]
            if first.startswith("Note") or first[0].isdigit():
                first_html = f"<b style='color:{header_color};'>{first}</b>"
            else:
                first_html = first
            body = "<br>".join([first_html] + [l.replace("  ", "&nbsp;&nbsp;") for l in rest])
            html_parts.append(f"<p style='margin:0 0 10px 0; line-height:1.5;'>{body}</p>")

        self.notes_text.setHtml(
            f"<div style='font-size:11pt; color:{text_color}; font-family:Consolas,monospace;'>"
            + "".join(html_parts)
            + "</div>"
        )

    # ------------------------------------------------------------------ #
    # Copy / save                                                          #
    # ------------------------------------------------------------------ #

    def copy_output(self) -> None:
        if not self.current_output_text.strip():
            QMessageBox.warning(self, "Nothing to Copy", "There is no summary to copy.")
            return
        QGuiApplication.clipboard().setText(self.current_output_text)
        self.statusBar().showMessage("Summary copied to clipboard", 3000)

    def save_output_as(self) -> None:
        if not self.current_output_text.strip():
            QMessageBox.warning(self, "Nothing to Save", "There is no summary to save.")
            return

        default_name = self.model_entry.text().strip().replace("/", "-").replace("\\", "-").replace(":", "-")
        if not default_name:
            default_name = "PhoenixMasterTool_Summary"

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
            self.statusBar().showMessage(f"Saved: {file_path}", 4000)
        except OSError as exc:
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
            self.statusBar().showMessage(f"Saved: {self.current_save_path}", 4000)
        except OSError as exc:
            QMessageBox.critical(self, "Save Error", f"Could not save file:\n{exc}")

    # ------------------------------------------------------------------ #
    # Misc actions                                                         #
    # ------------------------------------------------------------------ #

    # ------------------------------------------------------------------ #
    # Dark / light mode                                                    #
    # ------------------------------------------------------------------ #

    def _export_parts_list(self) -> None:
        if self.current_parsed_model is None:
            QMessageBox.information(self, "No Model", "Decode a model number first.")
            return

        seen: dict[str, dict] = {}
        for field_name in FIELD_TO_LOGICAL_FIELD:
            for part in self._extract_spare_parts_for_field(self.current_parsed_model, field_name):
                pn = part.get("part_number", "")
                if not pn:
                    continue
                if pn in seen:
                    seen[pn]["quantity"] = seen[pn].get("quantity", 1) + part.get("quantity", 1)
                else:
                    seen[pn] = dict(part)

        if self.current_parsed_model.options:
            for opt in self.current_parsed_model.options:
                for part in self._extract_spare_parts_for_option(self.current_parsed_model, opt):
                    pn = part.get("part_number", "")
                    if not pn:
                        continue
                    if pn in seen:
                        seen[pn]["quantity"] = seen[pn].get("quantity", 1) + part.get("quantity", 1)
                    else:
                        seen[pn] = dict(part)

        if not seen:
            QMessageBox.information(self, "No Parts", "No spare parts found for this model.")
            return

        model_str = self.model_entry.text().strip().upper()
        default_name = f"{model_str}_parts.csv" if model_str else "parts.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Export Parts List", default_name, "CSV Files (*.csv)")
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Part Number", "Description", "Quantity", "Notes"])
                for part in seen.values():
                    notes = "; ".join(part.get("notes", []) or [])
                    writer.writerow([
                        part.get("part_number", ""),
                        part.get("description", ""),
                        part.get("quantity", 1),
                        notes,
                    ])
            self.statusBar().showMessage(f"Parts list exported: {path}", 4000)
        except OSError as exc:
            QMessageBox.critical(self, "Export Error", f"Could not save file:\n{exc}")

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
        progress.setAutoClose(False)
        progress.setValue(0)
        progress.show()

        def on_progress(done: int, total: int) -> None:
            if total > 0:
                progress.setValue(int(done / total * 100))
            QApplication.processEvents()
            if progress.wasCanceled():
                raise RuntimeError("Update cancelled.")

        try:
            download_and_apply(info, progress_callback=on_progress)
        except Exception as exc:  # noqa: BLE001 — surface any failure to the user
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

            # Match per-component (case-insensitive) rather than substring on the
            # whole path. Substring matching produced false positives on benign
            # folders like "icloud-backup" and missed SharePoint / Teams entirely.
            components = [c.upper() for c in path.replace("\\", "/").split("/") if c]

            EXACT_MATCH = {
                "ONEDRIVE",        # OneDrive personal
                "DROPBOX",
                "ICLOUDDRIVE",
                "BOX",             # Box Drive (modern client)
                "GOOGLEDRIVE",
                "GOOGLE DRIVE",
                "MY DRIVE",        # Google Drive root inside the sync dir
            }

            def _is_synced(c: str) -> bool:
                if c in EXACT_MATCH:
                    return True
                # OneDrive Business / SharePoint use:
                #   "OneDrive - <Tenant>"            (personal-paid + business)
                #   "<Tenant>"                       (after navigating into a SharePoint sync)
                # so flag any component starting with "ONEDRIVE -".
                if c.startswith("ONEDRIVE -"):
                    return True
                # SharePoint sync clients sometimes use a "SharePoint" subfolder.
                if "SHAREPOINT" in c:
                    return True
                # Box Sync (legacy) folder name is "Box Sync".
                if c == "BOX SYNC":
                    return True
                return False

            if any(_is_synced(c) for c in components):
                QMessageBox.warning(
                    self,
                    "⚠ Cloud Sync Detected",
                    f"PhoenixMasterTool appears to be running from a cloud-synced folder:\n\n{path}\n\n"
                    "Running from OneDrive, SharePoint, Dropbox, or similar services can cause update failures "
                    "due to file locking.\n\n"
                    "For best results, move the app to a local folder (e.g. C:\\Tools\\PhoenixMasterTool).",
                )
        except (AttributeError, OSError):
            pass

    # ------------------------------------------------------------------ #
    # Help menu actions                                                    #
    # ------------------------------------------------------------------ #

    def show_version_history(self) -> None:
        """Fetch all releases from GitHub and display them in a scrollable dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Version History & Recent Updates")
        dialog.setModal(True)
        dialog.resize(560, 480)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel("Fetching release history from GitHub…")
        header.setObjectName("PickerHeader")
        layout.addWidget(header)

        text_area = QPlainTextEdit()
        text_area.setObjectName("VersionHistoryBody")
        text_area.setReadOnly(True)
        layout.addWidget(text_area, 1)

        close_btn = TertiaryButton("Close")
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
            url = "https://api.github.com/repos/JustinGlave/phoenix-master-tool/releases"
            req = urllib.request.Request(
                url,
                headers={"Accept": "application/vnd.github+json",
                         "User-Agent": "PhoenixMasterTool"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                releases = json.loads(resp.read().decode())

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
                "https://github.com/JustinGlave/phoenix-master-tool/releases"
            )
            header.setText("Version History")

        dialog.exec()

    def _open_cfm_calculator(self) -> None:
        dlg = CfmCalculatorDialog(self)
        dlg.exec()

    def _open_parts_list(self) -> None:
        dlg = PartsListDialog(self)
        dlg.exec()

    def _open_test_models(self) -> None:
        dlg = TestModelsDialog(self, on_pick=self.load_example_model)
        dlg.exec()

    def _focus_model_input(self) -> None:
        self.model_entry.setFocus()
        self.model_entry.selectAll()

    def _save_splitter_sizes(self, *_args) -> None:
        QSettings("ATSInc", "PhoenixMasterTool").setValue(
            "mainSplitterSizes", self.main_splitter.sizes()
        )

    @staticmethod
    def _email_support() -> None:
        QDesktopServices.openUrl(QUrl("mailto:justing@atsinc.org"))

    def show_about(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle(f"About {APP_NAME}")
        dlg.setModal(True)
        dlg.resize(420, 220)

        layout = QVBoxLayout(dlg)
        layout.setSpacing(12)

        body = QLabel(
            f"<div style='font-size:14pt; font-weight:700;'>{APP_NAME}</div>"
            f"<div style='margin-top:6px;'>Version {__version__}</div>"
            "<p style='margin-top:14px;'>Phoenix valve model decoder and guided model builder.</p>"
            "<p>"
            "<a href='https://github.com/JustinGlave/phoenix-master-tool'>"
            "GitHub repository</a><br>"
            "<a href='https://github.com/JustinGlave/phoenix-master-tool/releases'>"
            "Release history</a><br>"
            "<a href='mailto:justing@atsinc.org'>Email support</a>"
            "</p>"
        )
        body.setTextFormat(Qt.TextFormat.RichText)
        body.setOpenExternalLinks(True)
        body.setWordWrap(True)
        layout.addWidget(body)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        close_btn = TertiaryButton("Close")
        close_btn.setDefault(True)
        close_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        dlg.exec()

    def show_benchmark_results(self) -> None:
        dlg = SelfTestDialog(self)
        dlg.exec()


# ---------------------------------------------------------------------- #
# Entry point                                                              #
# ---------------------------------------------------------------------- #

def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("ATS Inc")

    # Load the Phoenix Controls design-system stylesheet (dark navy theme).
    load_phoenix_stylesheet(app)

    window = ValveMasterMainWindow()
    # Open maximized so the dashboard fills the screen on first launch.
    # Title bar / menu bar / taskbar stay visible (this is the conventional
    # Windows "maximize" state, not borderless fullscreen).
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()