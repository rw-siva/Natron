#!/usr/bin/env python3
"""Visual editor for Natron's Qt widget theme and custom-painted node style."""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = Path(__file__).with_name("theme.json")
STYLESHEET = ROOT / "Gui/Resources/Stylesheets/theme-editor.qss"
HEADER = ROOT / "Gui/ThemeValues.h"

DEFAULTS = {
    "panel": "#303030",
    "raised": "#474747",
    "sunken": "#1f1f1f",
    "text": "#c7c7c7",
    "accent": "#f28a00",
    "border": "#000000",
    "node_fill": "#b3b3b3",
    "node_border": "#000000",
    "panel_border_width": 1,
    "panel_radius": 0,
    "tab_radius": 5,
    "button_radius": 3,
    "dropdown_radius": 3,
    "dropdown_popup_radius": 3,
    "field_radius": 3,
    "group_radius": 0,
    "menu_radius": 3,
    "tooltip_radius": 5,
    "list_radius": 0,
    "node_radius": 5,
    "node_border_width": 1,
    "override_node_fill": False,
    "uppercase_labels": True,
    "uppercase_node_names": True,
    "font_family": "Droid Sans",
    "font_size": 11,
    "accent_underline_width": 2,
    "icons": {},
}

ICONS = (
    ("firstFrame.png", "First frame"),
    ("back1.png", "Previous frame"),
    ("rewind.png", "Rewind"),
    ("rewind_enabled.png", "Rewind enabled"),
    ("play.png", "Play"),
    ("play_enabled.png", "Play enabled"),
    ("stopDisabled.png", "Stop"),
    ("stopEnabled.png", "Stop enabled"),
    ("forward1.png", "Next frame"),
    ("lastFrame.png", "Last frame"),
)

VIEWER_BUTTONS = {
    "Viewer display": (
        "centerViewer.png", "cliptoprojectDisabled.png", "cliptoprojectEnabled.png",
        "fullFrameOff.png", "fullFrameOn.png", "viewer_roiDisabled.png",
        "viewer_roiEnabled.png", "renderScale.png", "renderScale_checked.png",
        "refresh.png", "refreshActive.png", "checkerboard_off.png",
        "checkerboard_on.png", "color_picker.png", "pauseDisabled.png",
        "pauseEnabled.png", "updateViewerDisabled.png", "updateViewerEnabled.png",
    ),
    "Playback and timeline": (
        "timelineIn.png", "firstFrame.png", "prevKF.png", "previousIncr.png",
        "back1.png", "rewind.png", "rewind_enabled.png", "play.png",
        "play_enabled.png", "stopDisabled.png", "stopEnabled.png",
        "forward1.png", "nextIncr.png", "nextKF.png", "lastFrame.png",
        "timelineOut.png", "loopmode.png", "bounce.png", "playOnce.png",
        "locked.png", "unlocked.png",
    ),
}


def resource_icons() -> tuple[str, ...]:
    """PNG icons compiled into Natron's GUI resource collection."""
    qrc = ET.parse(ROOT / "Gui/GuiResources.qrc")
    prefix = "Resources/Images/"
    return tuple(sorted({entry.text[len(prefix):] for entry in qrc.iter("file")
                         if entry.text and entry.text.startswith(prefix)
                         and entry.text.lower().endswith(".png")}))


RESOURCE_ICONS = resource_icons()

COLORS = (
    ("panel", "Panel background"),
    ("raised", "Raised controls"),
    ("sunken", "Sunken surfaces"),
    ("text", "Text"),
    ("accent", "Accent / focus"),
    ("node_fill", "Node fill"),
)
SIZES = (
    ("panel_radius", "Panel corner radius", 0, 20),
    ("tab_radius", "Tab corner radius", 0, 20),
    ("button_radius", "Button corner radius", 0, 20),
    ("dropdown_radius", "Dropdown / Viewer corner radius", 0, 20),
    ("dropdown_popup_radius", "Dropdown list radius", 0, 20),
    ("field_radius", "Input field radius", 0, 20),
    ("group_radius", "Group box radius", 0, 20),
    ("menu_radius", "Menu corner radius", 0, 20),
    ("tooltip_radius", "Tooltip corner radius", 0, 20),
    ("list_radius", "List/tree corner radius", 0, 20),
    ("node_radius", "Node corner radius", 0, 20),
)

# Each row maps one visible control family to its own width and color.
BORDER_STYLES = (
    ("Panel", "panel_border_width", "border"),
    ("Tabs", "tab_border_width", "tab_border"),
    ("Buttons", "button_border_width", "button_border"),
    ("Dropdowns", "dropdown_border_width", "dropdown_border"),
    ("Dropdown lists", "dropdown_popup_border_width", "dropdown_popup_border"),
    ("Input fields", "field_border_width", "field_border"),
    ("Group boxes", "group_border_width", "group_border"),
    ("Menus", "menu_border_width", "menu_border"),
    ("Tooltips", "tooltip_border_width", "tooltip_border"),
    ("Lists / trees", "list_border_width", "list_border"),
    ("Graph nodes", "node_border_width", "node_border"),
    ("Viewer layer", "viewer_layer_border_width", "viewer_layer_border"),
    ("Viewer alpha", "viewer_alpha_border_width", "viewer_alpha_border"),
    ("Viewer Channels", "viewer_channels_border_width", "viewer_channels_border"),
    ("Viewer Zoom", "viewer_zoom_border_width", "viewer_zoom_border"),
    ("Viewer render scale", "viewer_render_scale_border_width", "viewer_render_scale_border"),
    ("Viewer A", "viewer_a_border_width", "viewer_a_border"),
    ("Viewer composite", "viewer_composite_border_width", "viewer_composite_border"),
    ("Viewer B", "viewer_b_border_width", "viewer_b_border"),
)
for _label, _width_key, _color_key in BORDER_STYLES:
    DEFAULTS.setdefault(_width_key, 1)
    DEFAULTS.setdefault(_color_key, "#000000")


def validated(raw: dict) -> dict:
    theme = DEFAULTS.copy()
    for key in theme:
        if key not in raw:
            continue
        value = raw[key]
        if key == "font_family":
            if not isinstance(value, str) or not value.strip() or len(value) > 100 or any(c in value for c in '"\\\n\r'):
                raise ValueError("font_family must be a valid font name")
            theme[key] = value.strip()
            continue
        if key == "icons":
            if not isinstance(value, dict) or any(k not in RESOURCE_ICONS or not isinstance(v, str) for k, v in value.items()):
                raise ValueError("icons must map bundled icon names to file paths")
            theme[key] = value.copy()
            continue
        if key in ("font_size", "accent_underline_width"):
            maximum = 32 if key == "font_size" else 8
            minimum = 6 if key == "font_size" else 0
            if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
                raise ValueError(f"{key} must be from {minimum} to {maximum}")
            theme[key] = value
            continue
        if isinstance(theme[key], str):
            if not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
                raise ValueError(f"{key} must be a #RRGGBB color")
            theme[key] = value.lower()
        elif isinstance(theme[key], bool):
            if not isinstance(value, bool):
                raise ValueError(f"{key} must be true or false")
            theme[key] = value
        else:
            maximum = (6 if any(row[1] == key for row in BORDER_STYLES)
                       else next(row[3] for row in SIZES if row[0] == key))
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
                raise ValueError(f"{key} must be an integer from 0 to {maximum}")
            theme[key] = value
    return theme


def load_theme() -> dict:
    return validated(json.loads(CONFIG.read_text(encoding="utf-8")))


def color_channels(value: str) -> tuple[int, int, int]:
    return tuple(int(value[index:index + 2], 16) for index in (1, 3, 5))


def stylesheet(theme: dict) -> str:
    t = theme
    viewer_overrides = "".join(
        f'#{object_name} {{ qproperty-borderWidth: {t[f"viewer_{name}_border_width"]}; '
        f'qproperty-borderColor: {t[f"viewer_{name}_border"]}; }}\n'
        for name, object_name in (
            ("layer", "natronViewerLayer"),
            ("alpha", "natronViewerAlpha"),
            ("channels", "natronViewerChannels"),
            ("zoom", "natronViewerZoom"),
            ("render_scale", "natronViewerRenderScale"),
            ("a", "natronViewerA"),
            ("composite", "natronViewerComposite"),
            ("b", "natronViewerB"),
        )
    )
    return (
        "/* Generated by ui-design/theme_editor.py. Edit with that tool. */\n"
        f'QWidget {{ color: {t["text"]}; background-color: {t["panel"]}; font-family: "{t["font_family"]}"; font-size: {t["font_size"]}pt; }}\n'
        f'QTabWidget::pane {{ border: {t["panel_border_width"]}px solid {t["border"]}; border-radius: {t["panel_radius"]}px; }}\n'
        f'QTabBar::tab {{ background-color: {t["sunken"]}; color: {t["text"]}; '
        f'border: {t["tab_border_width"]}px solid {t["tab_border"]}; border-top-left-radius: {t["tab_radius"]}px; '
        f'border-top-right-radius: {t["tab_radius"]}px; }}\n'
        f'QTabBar::tab:selected {{ background-color: {t["panel"]}; color: {t["text"]}; border-bottom: {t["accent_underline_width"]}px solid {t["accent"]}; }}\n'
        f'QTabBar::tab:hover {{ background-color: {t["raised"]}; }}\n'
        f'QPushButton, QToolButton {{ background-color: {t["raised"]}; color: {t["text"]}; '
        f'border: {t["button_border_width"]}px solid {t["button_border"]}; border-radius: {t["button_radius"]}px; }}\n'
        f'QPushButton:hover, QToolButton:hover {{ border-color: {t["accent"]}; }}\n'
        f'QPushButton:pressed, QToolButton:pressed {{ background-color: {t["sunken"]}; }}\n'
        f'QComboBox {{ background-color: {t["raised"]}; color: {t["text"]}; '
        f'border: {t["dropdown_border_width"]}px solid {t["dropdown_border"]}; border-radius: {t["dropdown_radius"]}px; }}\n'
        f'ComboBox, Natron--ComboBox, ChannelsComboBox, Natron--ChannelsComboBox '
        f'{{ qproperty-cornerRadius: {t["dropdown_radius"]}; '
        f'qproperty-borderWidth: {t["dropdown_border_width"]}; '
        f'qproperty-borderColor: {t["dropdown_border"]}; }}\n' +
        viewer_overrides +
        f'QComboBox QAbstractItemView {{ background-color: {t["raised"]}; color: {t["text"]}; '
        f'border: {t["dropdown_popup_border_width"]}px solid {t["dropdown_popup_border"]}; border-radius: {t["dropdown_popup_radius"]}px; }}\n'
        f'QComboBox::drop-down {{ border: 0px; border-top-right-radius: {t["dropdown_radius"]}px; '
        f'border-bottom-right-radius: {t["dropdown_radius"]}px; }}\n'
        f'QLineEdit {{ background-color: {t["raised"]}; color: {t["text"]}; '
        f'border: {t["field_border_width"]}px solid {t["field_border"]}; border-radius: {t["field_radius"]}px; }}\n'
        f'QLineEdit:focus {{ border-color: {t["accent"]}; }}\n'
        f'QAbstractSpinBox, QTextEdit, QPlainTextEdit {{ background-color: {t["raised"]}; color: {t["text"]}; '
        f'border: {t["field_border_width"]}px solid {t["field_border"]}; border-radius: {t["field_radius"]}px; }}\n'
        f'QGroupBox {{ border: {t["group_border_width"]}px solid {t["group_border"]}; border-radius: {t["group_radius"]}px; margin-top: 5px; }}\n'
        f'QMenu {{ background-color: {t["panel"]}; color: {t["text"]}; '
        f'border: {t["menu_border_width"]}px solid {t["menu_border"]}; border-radius: {t["menu_radius"]}px; }}\n'
        f'QToolTip {{ background-color: {t["sunken"]}; color: {t["text"]}; '
        f'border: {t["tooltip_border_width"]}px solid {t["tooltip_border"]}; border-radius: {t["tooltip_radius"]}px; }}\n'
        f'QTreeView, QListView {{ border: {t["list_border_width"]}px solid {t["list_border"]}; border-radius: {t["list_radius"]}px; }}\n'
    )


def header(theme: dict) -> str:
    nr, ng, nb = color_channels(theme["node_border"])
    fr, fg, fb = color_channels(theme["node_fill"])
    return (
        "#ifndef GUI_THEMEVALUES_H\n#define GUI_THEMEVALUES_H\n\n"
        "// Generated by ui-design/theme_editor.py. These values affect custom-painted\n"
        "// node graph items; the stylesheet handles ordinary Qt widgets.\n"
        "namespace NatronTheme {\n"
        f'static const int NodeCornerRadius = {theme["node_radius"]};\n'
        f'static const int NodeBorderWidth = {theme["node_border_width"]};\n'
        f"static const int NodeBorderRed = {nr};\n"
        f"static const int NodeBorderGreen = {ng};\n"
        f"static const int NodeBorderBlue = {nb};\n"
        f'static const bool OverrideNodeFill = {str(theme["override_node_fill"]).lower()};\n'
        f'static const bool UppercaseLabels = {str(theme["uppercase_labels"]).lower()};\n'
        f'static const bool UppercaseNodeNames = {str(theme["uppercase_node_names"]).lower()};\n'
        f"static const int NodeFillRed = {fr};\n"
        f"static const int NodeFillGreen = {fg};\n"
        f"static const int NodeFillBlue = {fb};\n"
        "}\n\n#endif // GUI_THEMEVALUES_H\n"
    )


def apply_theme(theme: dict) -> None:
    theme = validated(theme)
    apply_icons(theme)
    CONFIG.write_text(json.dumps(theme, indent=2) + "\n", encoding="utf-8")
    STYLESHEET.write_text(stylesheet(theme), encoding="utf-8")
    HEADER.write_text(header(theme), encoding="utf-8")


def apply_icons(theme: dict) -> None:
    if not theme["icons"]:
        return
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    for name, source_name in theme["icons"].items():
        source = Path(source_name).expanduser().resolve()
        if not source.is_file() or source.suffix.lower() not in (".png", ".svg"):
            raise ValueError(f"Icon must be an existing PNG or SVG: {source}")
        target = ROOT / "Gui/Resources/Images" / name
        if source == target.resolve():
            continue
        if source.suffix.lower() == ".svg":
            renderer = QSvgRenderer(str(source))
            if not renderer.isValid():
                raise ValueError(f"Invalid SVG: {source}")
            size = renderer.defaultSize()
            if not size.isValid():
                size.setWidth(32)
                size.setHeight(32)
            image = QImage(size, QImage.Format_ARGB32)
            image.fill(Qt.transparent)
            painter = QPainter(image)
            renderer.render(painter)
            painter.end()
        else:
            image = QImage(str(source))
            if image.isNull():
                raise ValueError(f"Invalid PNG: {source}")
        if not image.save(str(target), "PNG"):
            raise OSError(f"Could not save {target}")


def check_theme(theme: dict) -> bool:
    return STYLESHEET.read_text(encoding="utf-8") == stylesheet(theme) and HEADER.read_text(encoding="utf-8") == header(theme)


def run_gui(theme: dict, smoke: bool = False, open_live: bool = False) -> int:
    from PySide6.QtCore import Qt, QSize, QProcess, QProcessEnvironment, QTimer
    from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QIntValidator, QLinearGradient, QPainter, QPen
    from PySide6.QtWidgets import (
        QAbstractButton, QApplication, QCheckBox, QColorDialog, QComboBox, QDoubleSpinBox,
        QFileDialog, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
        QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMenu, QMessageBox,
        QPushButton, QProgressBar, QRadioButton, QScrollArea, QSlider, QSpinBox,
        QTabBar, QTabWidget, QTextEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
    )

    class NodeSample(QWidget):
        def __init__(self):
            super().__init__()
            self.setMinimumHeight(165)

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.fillRect(self.rect(), QColor(theme["sunken"]))
            width, height = 170, 52
            x = (self.width() - width) / 2
            y = (self.height() - height) / 2
            fill = QColor(theme["node_fill"] if theme["override_node_fill"] else DEFAULTS["node_fill"])
            gradient = QLinearGradient(x, y, x, y + height)
            gradient.setColorAt(0.0, fill.lighter(130))
            gradient.setColorAt(1.0, fill.darker(120))
            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen if theme["node_border_width"] == 0 else QPen(QColor(theme["node_border"]), theme["node_border_width"]))
            painter.drawRoundedRect(x, y, width, height, theme["node_radius"], theme["node_radius"])
            painter.setPen(QColor("#000000"))
            painter.drawText(int(x), int(y), width, height, Qt.AlignCenter,
                             "BLUR1" if theme["uppercase_node_names"] else "Blur1")
            painter.end()

    class GraphSample(QWidget):
        def __init__(self, kind):
            super().__init__()
            self.kind = kind
            self.setMinimumHeight(190)

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.fillRect(self.rect(), QColor(theme["sunken"]))
            accent = QColor(theme["accent"])
            muted = QColor(theme["border"])
            text_color = QColor(theme["text"])
            painter.setPen(QPen(muted, 1))
            for x in range(0, self.width(), 25):
                painter.drawLine(x, 0, x, self.height())
            for y in range(0, self.height(), 25):
                painter.drawLine(0, y, self.width(), y)
            if self.kind == "nodes":
                names = ("Read1", "Grade1", "Viewer1")
                gap = max(15, (self.width() - 3 * 130) // 4)
                y = (self.height() - 58) // 2
                for i, name in enumerate(names):
                    x = gap + i * (130 + gap)
                    if i:
                        painter.setPen(QPen(accent, 2))
                        painter.drawLine(x - gap, y + 29, x, y + 29)
                    painter.setBrush(QColor(theme["node_fill"] if theme["override_node_fill"] else DEFAULTS["node_fill"]))
                    painter.setPen(QPen(accent if i == 1 else QColor(theme["node_border"]),
                                        max(1, theme["node_border_width"])))
                    painter.drawRoundedRect(x, y, 130, 58, theme["node_radius"], theme["node_radius"])
                    painter.setPen(QColor("#101010"))
                    painter.drawText(x, y, 130, 58, Qt.AlignCenter,
                                     name.upper() if theme["uppercase_node_names"] else name)
            elif self.kind == "dope":
                painter.setPen(text_color)
                for i, label in enumerate(("Transform1", "Position X", "Opacity")):
                    painter.drawText(12, 38 + i * 42, label.upper() if theme["uppercase_labels"] else label)
                painter.setPen(QPen(accent, 1))
                for frame in (1, 12, 24, 36):
                    x = 160 + frame * max(2, (self.width() - 190) // 45)
                    painter.drawText(x - 5, 18, str(frame))
                    for row in (0, 1, 2):
                        if (frame + row) % 3 != 0:
                            y = 33 + row * 42
                            painter.setBrush(accent if row == 1 else text_color)
                            painter.drawRect(x - 4, y - 4, 8, 8)
                painter.setPen(QPen(accent, 2))
                painter.drawLine(self.width() // 2, 20, self.width() // 2, self.height())
            else:
                painter.setPen(QPen(text_color, 1))
                painter.drawText(10, 20, "VALUE" if theme["uppercase_labels"] else "Value")
                points = [(70, self.height() - 35), (self.width() // 3, 45),
                          (2 * self.width() // 3, self.height() - 65),
                          (self.width() - 35, 55)]
                painter.setPen(QPen(accent, 2))
                for a, b in zip(points, points[1:]):
                    painter.drawLine(*a, *b)
                painter.setBrush(accent)
                for x, y in points:
                    painter.drawEllipse(x - 4, y - 4, 8, 8)
                    painter.drawLine(x - 18, y + 8, x + 18, y - 8)
            painter.end()

    class Editor(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Natron theme editor")
            self.resize(1450, 850)
            self.process = None
            self.save_timer = QTimer(self)
            self.save_timer.setSingleShot(True)
            self.save_timer.setInterval(400)
            self.save_timer.timeout.connect(self.auto_save)
            self.color_buttons = {}
            self.color_fields = {}
            self.color_dialogs = {}
            self.numeric_fields = {}
            self.numeric_sliders = {}
            self.numeric_ranges = {}
            root = QWidget()
            row = QHBoxLayout(root)
            self.setCentralWidget(root)

            controls = QWidget()
            controls_layout = QVBoxLayout(controls)
            colors_box = QGroupBox("Colors")
            colors_form = QFormLayout(colors_box)
            for key, label in COLORS:
                colors_form.addRow(label, self.color_field(key))
            controls_layout.addWidget(colors_box)

            sizes_box = QGroupBox("Corner radii (px)")
            sizes_form = QFormLayout(sizes_box)
            for key, label, minimum, maximum in SIZES:
                sizes_form.addRow(label, self.numeric_field(key, minimum, maximum))
            controls_layout.addWidget(sizes_box)

            borders_box = QGroupBox("Individual borders: color and width (px)")
            border_content = QWidget()
            borders_form = QFormLayout(border_content)
            for label, width_key, color_key in BORDER_STYLES:
                field = QWidget()
                field_layout = QHBoxLayout(field)
                field_layout.setContentsMargins(0, 0, 0, 0)
                field_layout.addWidget(self.color_field(color_key))
                field_layout.addWidget(self.numeric_field(width_key, 0, 6))
                borders_form.addRow(label, field)
            borders_scroll = QScrollArea()
            borders_scroll.setWidgetResizable(True)
            borders_scroll.setWidget(border_content)
            borders_scroll.setMinimumHeight(230)
            borders_scroll.setMaximumHeight(330)
            borders_layout = QVBoxLayout(borders_box)
            borders_layout.addWidget(borders_scroll)
            controls_layout.addWidget(borders_box)

            typography = QGroupBox("Typography and accent")
            typography_form = QFormLayout(typography)
            self.font_family = QComboBox()
            self.font_family.setEditable(True)
            self.font_family.addItems(QFontDatabase.families())
            self.font_family.setCurrentText(theme["font_family"])
            self.font_family.currentTextChanged.connect(lambda value: self.change("font_family", value))
            typography_form.addRow("Font family", self.font_family)
            typography_form.addRow("Font size (pt)", self.numeric_field("font_size", 6, 32))
            typography_form.addRow("Selected tab underline (px)",
                                   self.numeric_field("accent_underline_width", 0, 8))
            controls_layout.addWidget(typography)

            icons_box = QGroupBox(f"Bundled icons ({len(RESOURCE_ICONS)})")
            icons_layout = QVBoxLayout(icons_box)
            self.icon_search = QLineEdit()
            self.icon_search.setPlaceholderText("Search icon name or folder…")
            self.icon_search.textChanged.connect(self.filter_icons)
            icons_layout.addWidget(self.icon_search)
            self.icon_category = QComboBox()
            categories = sorted({name.split("/")[0] for name in RESOURCE_ICONS if "/" in name})
            self.icon_category.addItems(["All icons", "Top level", *categories])
            self.icon_category.currentTextChanged.connect(self.filter_icons)
            icons_layout.addWidget(self.icon_category)
            self.icon_list = QListWidget()
            self.icon_list.setIconSize(QSize(28, 28))
            for name in RESOURCE_ICONS:
                item = QListWidgetItem(QIcon(str(ROOT / "Gui/Resources/Images" / name)), name)
                item.setData(Qt.UserRole, name)
                self.icon_list.addItem(item)
            self.icon_list.currentItemChanged.connect(self.show_icon)
            icons_layout.addWidget(self.icon_list)
            self.icon_detail = QLabel("Select an icon to see its path")
            self.icon_detail.setWordWrap(True)
            icons_layout.addWidget(self.icon_detail)
            self.icon_preview = QLabel()
            self.icon_preview.setFixedHeight(48)
            icons_layout.addWidget(self.icon_preview)
            choose_icon = QPushButton("Replace selected icon with PNG or SVG…")
            choose_icon.clicked.connect(self.pick_selected_icon)
            icons_layout.addWidget(choose_icon)
            icons_box.setMinimumHeight(400)
            controls_layout.addWidget(icons_box)

            self.fill_box = QCheckBox("Use node fill color for all nodes")
            self.fill_box.setChecked(theme["override_node_fill"])
            self.fill_box.toggled.connect(lambda value: self.change("override_node_fill", value))
            controls_layout.addWidget(self.fill_box)
            self.uppercase_box = QCheckBox("Display interface labels in ALL CAPS")
            self.uppercase_box.setChecked(theme["uppercase_labels"])
            self.uppercase_box.toggled.connect(lambda value: self.change("uppercase_labels", value))
            controls_layout.addWidget(self.uppercase_box)
            self.uppercase_nodes_box = QCheckBox("Display graph node names in ALL CAPS")
            self.uppercase_nodes_box.setChecked(theme["uppercase_node_names"])
            self.uppercase_nodes_box.toggled.connect(lambda value: self.change("uppercase_node_names", value))
            controls_layout.addWidget(self.uppercase_nodes_box)
            controls_layout.addWidget(QLabel("Node fill overrides category and saved colors when enabled.\nBackdrop colors stay unchanged."))
            controls_layout.addStretch()
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(controls)
            scroll.setMinimumWidth(590)
            row.addWidget(scroll, 0)

            right = QWidget()
            right_layout = QVBoxLayout(right)
            self.preview = QWidget()
            preview_layout = QVBoxLayout(self.preview)
            tabs = QTabWidget()
            live = QWidget()
            live_layout = QVBoxLayout(live)
            live_layout.addWidget(QLabel(
                "Inspect the actual Natron Viewer, Node Graph, Properties, Dope Sheet and Curve Editor.\n"
                "The sample scene opens in a separate, fresh Natron session. Select Sphere1 to inspect animated controls."
            ))
            self.live_button = QPushButton("Open real Natron workspace")
            self.live_button.clicked.connect(self.open_live_preview)
            live_layout.addWidget(self.live_button)
            live_layout.addWidget(QLabel(
                "Colors, fonts, borders and tab accents update as this editor saves. "
                "Icons and node drawing need Build Natron, then a new preview window."
            ))
            live_layout.addStretch()
            tabs.addTab(live, "Real Natron")
            viewer = QWidget()
            viewer_layout = QVBoxLayout(viewer)
            viewer_layout.addWidget(QLabel("Viewer canvas and playback controls"))
            canvas = QLabel("VIEWER1  •  EMPTY FRAME")
            canvas.setAlignment(Qt.AlignCenter)
            canvas.setMinimumHeight(90)
            canvas.setStyleSheet(f"background-color: {theme['sunken']}; border: 1px solid {theme['border']};")
            self.viewer_canvas = canvas
            viewer_layout.addWidget(canvas)
            self.viewer_dropdown_samples = {}
            for controls in (
                (("layer", "Layer", "Color"), ("alpha", "Alpha", "Color.alpha"),
                 ("channels", "Channels", "RGB"), ("zoom", "Zoom", "100%")),
                (("render_scale", "Scale", "1x"), ("a", "A", "Viewer1"),
                 ("composite", "Composite", "W-Over"), ("b", "B", "Viewer2")),
            ):
                dropdown_row = QHBoxLayout()
                for key, label, value in controls:
                    dropdown_row.addWidget(QLabel(label))
                    combo = QComboBox()
                    combo.addItems((value, "Other"))
                    self.viewer_dropdown_samples[key] = combo
                    dropdown_row.addWidget(combo)
                viewer_layout.addLayout(dropdown_row)
            self.preview_icon_buttons = {}
            def icon_button(name):
                button = QPushButton()
                button.setToolTip(name)
                button.setFixedSize(34, 30)
                self.preview_icon_buttons.setdefault(name, []).append(button)
                return button
            buttons = QHBoxLayout()
            for name, label in ICONS:
                button = icon_button(name)
                button.setToolTip(label)
                buttons.addWidget(button)
            buttons.addStretch()
            viewer_layout.addLayout(buttons)
            frame_row = QHBoxLayout()
            for label, value in (("In", 1), ("Frame", 42), ("Out", 250), ("FPS", 24)):
                frame_row.addWidget(QLabel(label))
                spin = QSpinBox()
                spin.setRange(0, 10000)
                spin.setValue(value)
                frame_row.addWidget(spin)
            viewer_layout.addLayout(frame_row)
            for section, names in VIEWER_BUTTONS.items():
                box = QGroupBox(section)
                grid = QGridLayout(box)
                for index, name in enumerate(names):
                    cell = QWidget()
                    cell_layout = QVBoxLayout(cell)
                    cell_layout.setContentsMargins(2, 2, 2, 2)
                    cell_layout.addWidget(icon_button(name), alignment=Qt.AlignCenter)
                    caption = QLabel(name.removesuffix(".png"))
                    caption.setAlignment(Qt.AlignCenter)
                    caption.setWordWrap(True)
                    cell_layout.addWidget(caption)
                    grid.addWidget(cell, index // 9, index % 9)
                viewer_layout.addWidget(box)
            tabs.addTab(viewer, "Viewer sketch")

            graph = QWidget()
            graph_layout = QVBoxLayout(graph)
            graph_bar = QHBoxLayout()
            for name in ("undo.png", "redo.png", "layout.png", "splitHorizontally.png", "splitVertically.png"):
                graph_bar.addWidget(icon_button(name))
            graph_bar.addStretch()
            graph_layout.addLayout(graph_bar)
            graph_layout.addWidget(GraphSample("nodes"), 1)
            graph_layout.addWidget(NodeSample())
            tabs.addTab(graph, "Graph sketch")

            properties = QWidget()
            properties_layout = QVBoxLayout(properties)
            properties_tabs = QTabWidget()
            for page_name, fields in (
                ("Node", (("Name", "Blur1"), ("Label", "Soft blur"), ("Mix", 1.0),
                          ("Enabled", True), ("Filter", ["Gaussian", "Box", "Bilinear"]),
                          ("Size", 12.5), ("Color", "#f28a00"))),
                ("Transform", (("Translate X", 100.0), ("Translate Y", -20.0),
                               ("Scale", 1.0), ("Rotate", 45.0), ("Center", "960, 540"),
                               ("Motion blur", False))),
                ("Viewer", (("Channels", ["RGB", "RGBA", "Alpha"]),
                            ("Gain", 1.0), ("Gamma", 2.2), ("Auto contrast", False),
                            ("Display", ["sRGB", "Rec.709", "Linear"]))),
            ):
                page = QWidget()
                form = QFormLayout(page)
                for label, value in fields:
                    if isinstance(value, bool):
                        control = QCheckBox()
                        control.setChecked(value)
                    elif isinstance(value, list):
                        control = QComboBox()
                        control.addItems(value)
                    elif isinstance(value, float):
                        control = QDoubleSpinBox()
                        control.setRange(-10000, 10000)
                        control.setValue(value)
                    elif label == "Color":
                        control = QPushButton(value)
                        control.setStyleSheet(f"background-color: {value};")
                        self.properties_accent_button = control
                    else:
                        control = QLineEdit(value)
                    form.addRow(label, control)
                properties_tabs.addTab(page, page_name)
            properties_layout.addWidget(properties_tabs)
            state_box = QGroupBox("Control states")
            state_layout = QHBoxLayout(state_box)
            state_layout.addWidget(QPushButton("Normal"))
            disabled = QPushButton("Disabled")
            disabled.setEnabled(False)
            state_layout.addWidget(disabled)
            selected = QRadioButton("Selected")
            selected.setChecked(True)
            state_layout.addWidget(selected)
            progress = QProgressBar()
            progress.setValue(65)
            state_layout.addWidget(progress)
            properties_layout.addWidget(state_box)
            corners_box = QGroupBox("Other rounded surfaces")
            corners_layout = QFormLayout(corners_box)
            dropdown = QComboBox()
            dropdown.addItems(("Gaussian", "Box", "Bilinear"))
            dropdown.setToolTip("Dropdown body and popup list use separate corner settings")
            corners_layout.addRow("Dropdown / popup", dropdown)
            corners_layout.addRow("Input field", QLineEdit("Editable value"))
            menu_button = QPushButton("Open menu")
            menu = QMenu(menu_button)
            menu.addAction("First action")
            menu.addAction("Second action")
            menu_button.setMenu(menu)
            corners_layout.addRow("Menu", menu_button)
            properties_layout.addWidget(corners_box)
            tabs.addTab(properties, "Properties sketch")

            dope = QWidget()
            dope_layout = QVBoxLayout(dope)
            tree = QTreeWidget()
            tree.setHeaderLabels(["Animated object", "Channels", "Keys"])
            for label, channels, keys in (("Transform1", "Position, Rotation", "1, 12, 24"),
                                          ("Grade1", "Mix", "1, 18, 36")):
                QTreeWidgetItem(tree, [label, channels, keys])
            dope_layout.addWidget(tree)
            dope_layout.addWidget(GraphSample("dope"), 1)
            tabs.addTab(dope, "Dope Sheet sketch")

            curves = QWidget()
            curves_layout = QVBoxLayout(curves)
            curves_layout.addWidget(QLabel("Position X  •  Bezier handles and keyframes"))
            curves_layout.addWidget(GraphSample("curves"), 1)
            curves_layout.addWidget(QSlider(Qt.Horizontal))
            tabs.addTab(curves, "Curve sketch")

            atlas = QListWidget()
            atlas.setViewMode(QListWidget.IconMode)
            atlas.setIconSize(QSize(36, 36))
            atlas.setResizeMode(QListWidget.Adjust)
            atlas.setSpacing(8)
            for name in RESOURCE_ICONS:
                item = QListWidgetItem(QIcon(str(ROOT / "Gui/Resources/Images" / name)), name)
                item.setData(Qt.UserRole, name)
                atlas.addItem(item)
            self.icon_atlas = atlas
            atlas.currentItemChanged.connect(lambda current, _old: self.icon_list.setCurrentRow(RESOURCE_ICONS.index(current.data(Qt.UserRole))) if current else None)
            tabs.addTab(atlas, f"Icon Atlas ({len(RESOURCE_ICONS)})")

            preview_layout.addWidget(tabs, 1)
            right_layout.addWidget(self.preview, 1)

            actions = QHBoxLayout()
            self.apply_button = QPushButton("Apply to Natron source")
            self.apply_button.clicked.connect(self.apply)
            actions.addWidget(self.apply_button)
            self.build_button = QPushButton("Build Natron")
            self.build_button.clicked.connect(self.build)
            actions.addWidget(self.build_button)
            reset_button = QPushButton("Reset preview")
            reset_button.clicked.connect(self.reset)
            actions.addWidget(reset_button)
            right_layout.addLayout(actions)
            self.log = QTextEdit()
            self.log.setReadOnly(True)
            self.log.setMaximumHeight(150)
            right_layout.addWidget(self.log)
            row.addWidget(right, 1)
            self.refresh()

        def change(self, key, value):
            theme[key] = value
            self.refresh()
            self.save_timer.start()

        def color_field(self, key):
            field = QWidget()
            layout = QHBoxLayout(field)
            layout.setContentsMargins(0, 0, 0, 0)
            button = QPushButton()
            button.setFixedWidth(28)
            button.setToolTip("Open color picker")
            button.clicked.connect(lambda _=False, k=key: self.pick_color(k))
            layout.addWidget(button)
            edit = QLineEdit(theme[key])
            edit.setFixedWidth(82)
            edit.setToolTip("Enter a color as #RRGGBB, then press Enter")
            edit.editingFinished.connect(lambda k=key: self.commit_color(k))
            layout.addWidget(edit)
            self.color_buttons[key] = button
            self.color_fields[key] = edit
            return field

        def commit_color(self, key):
            edit = self.color_fields[key]
            value = edit.text().strip()
            if len(value) == 7 and value.startswith("#") and all(c in "0123456789abcdefABCDEF" for c in value[1:]):
                self.change(key, value.lower())
            else:
                edit.setText(theme[key])

        def numeric_field(self, key, minimum, maximum):
            field = QWidget()
            layout = QHBoxLayout(field)
            layout.setContentsMargins(0, 0, 0, 0)
            edit = QLineEdit(str(theme[key]))
            edit.setFixedWidth(46)
            edit.setValidator(QIntValidator(minimum, maximum, edit))
            edit.setToolTip(f"Type {minimum}–{maximum}, then press Enter")
            edit.editingFinished.connect(lambda k=key: self.commit_numeric(k))
            layout.addWidget(edit)
            slider = QSlider(Qt.Horizontal)
            slider.setRange(minimum, maximum)
            slider.setValue(theme[key])
            slider.setMinimumWidth(80)
            slider.valueChanged.connect(lambda value, k=key: self.slide_numeric(k, value))
            layout.addWidget(slider)
            self.numeric_fields[key] = edit
            self.numeric_sliders[key] = slider
            self.numeric_ranges[key] = (minimum, maximum)
            return field

        def commit_numeric(self, key):
            entered = self.numeric_fields[key].text().strip()
            if entered:
                minimum, maximum = self.numeric_ranges[key]
                try:
                    value = max(minimum, min(maximum, int(entered)))
                except ValueError:
                    value = theme[key]
                self.numeric_sliders[key].setValue(value)
            self.numeric_fields[key].setText(str(theme[key]))

        def slide_numeric(self, key, value):
            self.numeric_fields[key].setText(str(value))
            self.change(key, value)

        def pick_color(self, key):
            dialog = self.color_dialogs.get(key)
            if dialog is None:
                dialog = QColorDialog(QColor(theme[key]), self)
                dialog.setOption(QColorDialog.DontUseNativeDialog, True)
                dialog.setWindowTitle(f"Choose {key.replace('_', ' ')}")
                dialog.colorSelected.connect(lambda color, k=key: self.change(k, color.name()))
                self.color_dialogs[key] = dialog
            dialog.setCurrentColor(QColor(theme[key]))
            dialog.show()
            dialog.raise_()
            dialog.activateWindow()

        def pick_icon(self, name):
            path, _ = QFileDialog.getOpenFileName(self, f"Choose {name}", str(ROOT), "Icons (*.png *.svg)")
            if path:
                theme["icons"][name] = path
                self.refresh()
                self.save_timer.start()

        def pick_selected_icon(self):
            item = self.icon_list.currentItem()
            if item:
                self.pick_icon(item.data(Qt.UserRole))

        def filter_icons(self):
            query = self.icon_search.text().strip().lower()
            category = self.icon_category.currentText()
            for row in range(self.icon_list.count()):
                item = self.icon_list.item(row)
                name = item.data(Qt.UserRole)
                in_category = category == "All icons" or (category == "Top level" and "/" not in name) or name.startswith(category + "/")
                item.setHidden(not (in_category and query in name.lower()))

        def show_icon(self, current, _previous=None):
            if not current:
                return
            name = current.data(Qt.UserRole)
            source = theme["icons"].get(name) or str(ROOT / "Gui/Resources/Images" / name)
            self.icon_detail.setText(f"{name}\nSource: {source}")
            self.icon_preview.setPixmap(QIcon(source).pixmap(40, 40))

        def auto_save(self):
            try:
                apply_theme(theme)
            except (OSError, ValueError) as error:
                self.log.append(f"Could not auto-save: {error}")
                return
            self.log.append("Saved. Stylesheet changes update the real preview; icons and node drawing need a build and new window.")

        def open_live_preview(self):
            if not self.apply():
                return
            binary = ROOT / "build-qt6/App/Natron"
            if not binary.exists():
                QMessageBox.warning(self, "Natron is not built", f"Build Natron first. Expected: {binary}")
                return
            environment = QProcessEnvironment.systemEnvironment()
            environment.insert("NATRON_THEME_STYLESHEET", str(STYLESHEET))
            environment.insert("QT_QPA_PLATFORM", "wayland")
            preview_process = QProcess(self)
            preview_process.setProcessEnvironment(environment)
            preview_process.setProgram(str(binary))
            commands = (
                "sphere = app1.createNode('fr.inria.built-in.Sphere3D')",
                "viewer = app1.createNode('fr.inria.built-in.Viewer')",
                "sphere.setPosition(-150, 0)",
                "viewer.setPosition(100, 100)",
                "sphere.getParam('translateX').setValueAtTime(-1.0, 1)",
                "sphere.getParam('translateX').setValueAtTime(1.0, 24)",
                "sphere.getParam('translateX').setValueAtTime(-1.0, 48)",
            )
            preview_process.setArguments([part for command in commands for part in ("-c", command)])
            preview_process.setWorkingDirectory(str(ROOT))
            launched = preview_process.startDetached()
            if launched:
                self.log.append("Opened real Natron preview. Select Sphere1 for animated properties.")
            else:
                QMessageBox.critical(self, "Could not open Natron", "The preview process failed to start.")

        def refresh(self):
            for key, button in self.color_buttons.items():
                button.setStyleSheet(f"background-color: {theme[key]};")
                edit = self.color_fields[key]
                if not edit.hasFocus():
                    edit.setText(theme[key])
            self.preview.setStyleSheet(stylesheet(theme))
            for widget in self.preview.findChildren(QWidget):
                if isinstance(widget, (QLabel, QAbstractButton, QGroupBox, QTabBar)):
                    font = widget.font()
                    desired = QFont.AllUppercase if theme["uppercase_labels"] else QFont.MixedCase
                    if font.capitalization() != desired:
                        font.setCapitalization(desired)
                        widget.setFont(font)
            self.viewer_canvas.setStyleSheet(f"background-color: {theme['sunken']}; border: 1px solid {theme['border']};")
            self.properties_accent_button.setText(theme["accent"])
            self.properties_accent_button.setStyleSheet(f"background-color: {theme['accent']};")
            for name, buttons in self.preview_icon_buttons.items():
                source = theme["icons"].get(name) or str(ROOT / "Gui/Resources/Images" / name)
                for button in buttons:
                    button.setIcon(QIcon(source))
                    button.setIconSize(button.size() * 0.7)
            for key, combo in self.viewer_dropdown_samples.items():
                combo.setStyleSheet(
                    f'QComboBox {{ border: {theme[f"viewer_{key}_border_width"]}px solid '
                    f'{theme[f"viewer_{key}_border"]}; border-radius: {theme["dropdown_radius"]}px; '
                    f'background-color: {theme["raised"]}; color: {theme["text"]}; }}'
                )
            for row in range(self.icon_list.count()):
                item = self.icon_list.item(row)
                name = item.data(Qt.UserRole)
                source = theme["icons"].get(name) or str(ROOT / "Gui/Resources/Images" / name)
                item.setIcon(QIcon(source))
                item.setText(name + ("  • changed" if name in theme["icons"] else ""))
            self.show_icon(self.icon_list.currentItem())
            for row in range(self.icon_atlas.count()):
                item = self.icon_atlas.item(row)
                name = item.data(Qt.UserRole)
                source = theme["icons"].get(name) or str(ROOT / "Gui/Resources/Images" / name)
                item.setIcon(QIcon(source))
            self.preview.update()
            for node in self.preview.findChildren(NodeSample):
                node.update()

        def reset(self):
            theme.update(DEFAULTS)
            for key, edit in self.numeric_fields.items():
                edit.setText(str(theme[key]))
                self.numeric_sliders[key].setValue(theme[key])
            self.fill_box.setChecked(theme["override_node_fill"])
            self.uppercase_box.setChecked(theme["uppercase_labels"])
            self.uppercase_nodes_box.setChecked(theme["uppercase_node_names"])
            self.font_family.setCurrentText(theme["font_family"])
            for key, edit in self.color_fields.items():
                edit.setText(theme[key])
            self.refresh()
            self.save_timer.start()

        def apply(self):
            try:
                apply_theme(theme)
            except (OSError, ValueError) as error:
                QMessageBox.critical(self, "Could not save theme", str(error))
                return False
            self.log.append("Saved theme, stylesheet, and node appearance. Build Natron to see the changes in the app.")
            return True

        def build(self):
            if self.process and self.process.state() != QProcess.NotRunning:
                return
            if not (ROOT / "build-qt6/CMakeCache.txt").exists():
                QMessageBox.warning(self, "Build not configured", "Configure build-qt6 before building Natron.")
                return
            if not self.apply():
                return
            self.build_button.setEnabled(False)
            self.log.append("Building Natron…")
            self.process = QProcess(self)
            self.process.setWorkingDirectory(str(ROOT))
            self.process.readyReadStandardOutput.connect(self.read_output)
            self.process.readyReadStandardError.connect(self.read_output)
            self.process.finished.connect(self.build_finished)
            self.process.start("cmake", ["--build", "build-qt6", "--target", "Natron", "-j2"])

        def read_output(self):
            output = bytes(self.process.readAllStandardOutput()) + bytes(self.process.readAllStandardError())
            if output:
                self.log.append(output.decode("utf-8", errors="replace").rstrip())

        def build_finished(self, exit_code, _status):
            self.read_output()
            self.build_button.setEnabled(True)
            self.log.append("Build succeeded. Restart Natron to see the theme." if exit_code == 0 else f"Build failed (exit {exit_code}).")

    app = QApplication(sys.argv[:1])
    window = Editor()
    window.show()
    if open_live:
        QTimer.singleShot(1000, window.open_live_preview)
    if smoke:
        def check_controls():
            from PySide6.QtCore import QEvent
            from PySide6.QtGui import QKeyEvent
            def type_text(edit, value):
                edit.setFocus()
                edit.selectAll()
                for character in value:
                    app.sendEvent(edit, QKeyEvent(QEvent.KeyPress, 0, Qt.NoModifier, character))
                    app.sendEvent(edit, QKeyEvent(QEvent.KeyRelease, 0, Qt.NoModifier, character))
                app.sendEvent(edit, QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier))
            original = theme.copy()
            try:
                for key, edit in window.color_fields.items():
                    assert edit.isEnabled() and not edit.isReadOnly(), f"{key} color is disabled"
                    type_text(edit, "#123456")
                    assert theme[key] == "#123456", f"{key} color did not accept typing"
                for key, edit in window.numeric_fields.items():
                    assert edit.isEnabled() and not edit.isReadOnly(), f"{key} number is disabled"
                    minimum, maximum = window.numeric_ranges[key]
                    value = minimum + 1 if minimum < maximum else minimum
                    type_text(edit, str(value))
                    assert theme[key] == value, f"{key} number did not accept typing"
                type_text(window.icon_search, "rewind")
                assert window.icon_search.text() == "rewind", "Icon search did not accept typing"
                assert any(not window.icon_list.item(i).isHidden() for i in range(window.icon_list.count())), "Icon search returned no results"
                font_edit = window.font_family.lineEdit()
                assert font_edit is not None and not font_edit.isReadOnly(), "Font family is not editable"
                type_text(font_edit, "Ubuntu")
                assert window.font_family.currentText() == "Ubuntu", "Font family did not accept typing"
                color_key = COLORS[0][0]
                window.pick_color(color_key)
                assert window.color_dialogs[color_key].isVisible(), "Color picker did not open"
                assert window.isEnabled(), "Color picker blocked the editor"
                window.color_dialogs[color_key].close()
                window.icon_search.clear()
                print(f"Checked {len(window.color_fields)} colors, {len(window.numeric_fields)} numeric fields, icon search, font family, and color picker")
            except Exception as error:
                print(f"Theme editor control check failed: {error}", file=sys.stderr)
                app.exit(1)
                return
            finally:
                theme.update(original)
                window.save_timer.stop()
            app.quit()
        QTimer.singleShot(100, check_controls)
    return app.exec()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify generated theme files match theme.json")
    parser.add_argument("--apply", action="store_true", help="regenerate Natron theme files without opening the editor")
    parser.add_argument("--smoke", action="store_true", help="open the editor briefly for a headless UI check")
    parser.add_argument("--open-live", action="store_true", help="open the real Natron preview alongside the editor")
    args = parser.parse_args()
    try:
        theme = load_theme()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    if args.check:
        if check_theme(theme):
            print("Theme files are in sync")
            return 0
        print("Theme files differ from theme.json; run --apply")
        return 1
    if args.apply:
        apply_theme(theme)
        print("Applied Natron theme")
        return 0
    return run_gui(theme, smoke=args.smoke, open_live=args.open_live)


if __name__ == "__main__":
    raise SystemExit(main())
