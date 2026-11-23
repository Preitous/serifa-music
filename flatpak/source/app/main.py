import sys
import re
import getpass
import time
import os
import json
import math
import random
import copy
import shutil
from datetime import datetime
from pathlib import Path

from storage import StorageManager, StorageError
from library import LibraryScanner
from player import AudioPlayer
from playback_queue import PlaybackQueue
from appearance import AppearanceManager, get_theme_color, get_theme_value
from virtual_track_list import VirtualTrackList
from shortcuts import ShortcutManager
from i18n import load_language, save_language, tr
from mpris import MprisBridge, MprisService

from PySide6.QtCore import (
    Qt, QEvent, QRect, QRectF, QSize, QPoint, QPointF, QThread, Signal, QTimer, QSettings,
    QUrl, QMimeData,
    Property, QPropertyAnimation, QVariantAnimation, QParallelAnimationGroup, QEasingCurve
)
from PySide6.QtGui import (
    QPixmap, QIcon, QPainter, QPainterPath, QLinearGradient, QColor, QCursor, QPalette,
    QDesktopServices,
    QDrag, QTransform, QKeySequence, QPen, QFont
)
from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QApplication,
    QMainWindow,
    QDialog,
    QCheckBox,
    QWidget,
    QFrame,
    QGraphicsOpacityEffect,
    QGraphicsBlurEffect,
    QGraphicsDropShadowEffect,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QStyle,
    QStyleOptionSlider,
    QScrollArea,
    QLayout,
    QStackedWidget,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QMenu,
    QInputDialog,
    QFileDialog,
    QLineEdit,
    QTextEdit,
    QPlainTextEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QTabWidget,
    QProgressBar,
    QProxyStyle,
)


# --------------------------------------------------
# FLOW LAYOUT
# --------------------------------------------------


_THEME_STYLE_COLORS = {'#17141e': ('tons', 'hex_17141e'), '#17151e': ('tons', 'hex_17151e'), '#211d2b': ('tons', 'hex_211d2b'), '#211e2a': ('tons', 'hex_211e2a'), '#1b1823': ('tons', 'hex_1b1823'), '#25212e': ('tons', 'hex_25212e'), '#272330': ('tons', 'hex_272330'), '#292433': ('tons', 'hex_292433'), '#292532': ('tons', 'hex_292532'), '#2b2735': ('tons', 'hex_2b2735'), '#302a3b': ('tons', 'hex_302a3b'), '#332b40': ('tons', 'hex_332b40'), '#342b43': ('tons', 'hex_342b43'), '#393243': ('tons', 'hex_393243'), '#3b3049': ('tons', 'hex_3b3049'), '#40354f': ('tons', 'hex_40354f'), '#493243': ('tons', 'hex_493243'), '#49375f': ('tons', 'hex_49375f'), '#49395b': ('tons', 'hex_49395b'), '#493e58': ('tons', 'hex_493e58'), '#51445f': ('tons', 'hex_51445f'), '#51495c': ('tons', 'hex_51495c'), '#59466f': ('tons', 'hex_59466f'), '#594675': ('tons', 'hex_594675'), '#59496b': ('tons', 'hex_59496b'), '#66547f': ('tons', 'hex_66547f'), '#665b70': ('tons', 'hex_665b70'), '#713c49': ('tons', 'hex_713c49'), '#71617f': ('tons', 'hex_71617f'), '#76539a': ('tons', 'hex_76539a'), '#76599a': ('tons', 'hex_76599a'), '#77717f': ('tons', 'hex_77717f'), '#8056a4': ('tons', 'hex_8056a4'), '#80649e': ('tons', 'hex_80649e'), '#81798b': ('tons', 'hex_81798b'), '#8657a8': ('tons', 'hex_8657a8'), '#8964ad': ('tons', 'hex_8964ad'), '#898297': ('tons', 'hex_898297'), '#93899d': ('tons', 'hex_93899d'), '#95899f': ('tons', 'hex_95899f'), '#956bb8': ('tons', 'hex_956bb8'), '#9871bd': ('tons', 'hex_9871bd'), '#98d51f': ('tons', 'hex_98d51f'), '#a2d92a': ('tons', 'hex_a2d92a'), '#a49bad': ('tons', 'hex_a49bad'), '#a6e02e': ('tons', 'hex_a6e02e'), '#a99bb8': ('tons', 'hex_a99bb8'), '#aaa3b6': ('tons', 'hex_aaa3b6'), '#aaa4b5': ('tons', 'hex_aaa4b5'), '#ad83d5': ('tons', 'hex_ad83d5'), '#b58ae0': ('tons', 'hex_b58ae0'), '#b6f23a': ('tons', 'hex_b6f23a'), '#b7b1bd': ('tons', 'hex_b7b1bd'), '#b99add': ('tons', 'hex_b99add'), '#bdb3c9': ('tons', 'hex_bdb3c9'), '#c5f75c': ('tons', 'hex_c5f75c'), '#c6bdcf': ('tons', 'hex_c6bdcf'), '#c8bfd2': ('tons', 'hex_c8bfd2'), '#c8ff4a': ('tons', 'hex_c8ff4a'), '#c9a7ef': ('tons', 'hex_c9a7ef'), '#c9bdd5': ('tons', 'hex_c9bdd5'), '#d7b9f5': ('tons', 'hex_d7b9f5'), '#d8c3f4': ('tons', 'hex_d8c3f4'), '#d8cfe2': ('tons', 'hex_d8cfe2'), '#d9b6ff': ('tons', 'hex_d9b6ff'), '#e4d0f5': ('tons', 'hex_e4d0f5'), '#e58b91': ('tons', 'hex_e58b91'), '#e9d5ff': ('tons', 'hex_e9d5ff'), '#e9dcf7': ('tons', 'hex_e9dcf7'), '#eee5fa': ('tons', 'hex_eee5fa'), '#eee8f6': ('tons', 'hex_eee8f6'), '#eeeaf3': ('tons', 'hex_eeeaf3'), '#f0dfff': ('tons', 'hex_f0dfff'), '#f2eafa': ('tons', 'hex_f2eafa'), '#f2edf7': ('tons', 'hex_f2edf7'), '#f3edf9': ('tons', 'hex_f3edf9'), '#f5efff': ('tons', 'hex_f5efff'), '#ffffff': ('tons', 'hex_ffffff')}


def _set_theme_stylesheet(widget, stylesheet):
    """Aplica QSS usando cores e tipografia externas."""
    if not isinstance(stylesheet, str):
        return

    def replace_color(match):
        original = match.group(0)
        token = _THEME_STYLE_COLORS.get(original.lower())

        if token is None:
            return original

        section, key = token
        return get_theme_color(section, key, original)

    def replace_size(match):
        original = match.group(2)
        key = f"px_{original}"

        value = get_theme_value(
            "typography",
            "qss_sizes",
            key,
            int(original)
        )

        return f"{match.group(1)}{int(value)}px"

    def replace_weight(match):
        original = match.group(2).lower()

        names = {
            "normal": "regular",
            "bold": "bold",
            "400": "regular",
            "500": "medium",
            "600": "semibold",
            "700": "bold",
        }

        key = names.get(original)
        if key is None:
            return match.group(0)

        fallback = (
            int(original)
            if original.isdigit()
            else 700 if original == "bold" else 400
        )

        value = get_theme_value(
            "typography",
            "weights",
            key,
            fallback
        )

        return f"{match.group(1)}{int(value)}"

    stylesheet = re.sub(
        r'#[0-9a-fA-F]{6}\b',
        replace_color,
        stylesheet
    )

    stylesheet = re.sub(
        r'(font-size\s*:\s*)(\d+)px',
        replace_size,
        stylesheet,
        flags=re.IGNORECASE
    )

    stylesheet = re.sub(
        r'(font-weight\s*:\s*)(bold|normal|[1-9]00)\b',
        replace_weight,
        stylesheet,
        flags=re.IGNORECASE
    )

    # Estilos globais são aplicados somente à QApplication.
    _serifa_app = QApplication.instance()

    if widget is _serifa_app:
        _serifa_appearance = _serifa_app.property(
            'serifa_appearance_manager'
        )
        _serifa_custom_qss = getattr(
            _serifa_appearance, 'stylesheet', ''
        )

        if _serifa_custom_qss:
            stylesheet += '\n' + _serifa_custom_qss

        stylesheet += """
            QScrollBar:vertical {
                background: #211e2a;
                width: 7px;
                border-radius: 3px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: #59496b;
                border-radius: 3px;
                min-height: 28px;
            }
            QScrollBar::handle:vertical:hover {
                background: #80649e;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """

    widget.setStyleSheet(stylesheet)


def _set_shortcuts_scrollbar(scroll_area):
    scroll_area.verticalScrollBar().setStyleSheet("""
        QScrollBar:vertical {
            background: #211e2a;
            width: 7px;
            border-radius: 3px;
            margin: 2px;
        }
        QScrollBar::handle:vertical {
            background: #59496b;
            border-radius: 3px;
            min-height: 28px;
        }
        QScrollBar::handle:vertical:hover {
            background: #80649e;
        }
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0px;
        }
    """)


class FlowLayout(QLayout):
    """
    Layout em fluxo:
    - mantém a largura dos cards;
    - calcula quantos cabem em cada linha;
    - distribui o espaço excedente entre os cards das linhas completas;
    - mantém linhas incompletas alinhadas à esquerda.
    """

    def __init__(
        self,
        parent=None,
        min_horizontal_spacing=16,
        vertical_spacing=24
    ):
        super().__init__(parent)

        self._items = []
        self._min_horizontal_spacing = min_horizontal_spacing
        self._vertical_spacing = vertical_spacing

        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self._items.append(item)
        self.invalidate()

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            item = self._items.pop(index)
            self.invalidate()
            return item
        return None

    def expandingDirections(self):
        return Qt.Orientations()

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize(0, 0)

        for item in self._items:
            size = size.expandedTo(item.minimumSize())

        left, top, right, bottom = self.getContentsMargins()
        size += QSize(left + right, top + bottom)

        return size

    def _do_layout(self, rect, test_only):
        left, top, right, bottom = self.getContentsMargins()

        area = rect.adjusted(
            left,
            top,
            -right,
            -bottom
        )

        available_width = max(1, area.width())

        if not self._items:
            return top + bottom

        card_width = max(
            item.sizeHint().width()
            for item in self._items
        )

        card_width = max(card_width, 1)

        min_spacing = self._min_horizontal_spacing

        cards_per_row = max(
            1,
            (available_width + min_spacing)
            // (card_width + min_spacing)
        )

        y = area.y()
        last_row_height = 0

        for start in range(0, len(self._items), cards_per_row):
            row = self._items[start:start + cards_per_row]

            row_heights = [
                item.sizeHint().height()
                for item in row
            ]

            row_height = max(row_heights) if row_heights else 0
            last_row_height = row_height

            if len(row) == cards_per_row and len(row) > 1:
                extra_space = available_width - (
                    len(row) * card_width
                )

                spacing = max(
                    min_spacing,
                    extra_space / (len(row) - 1)
                )
            else:
                spacing = min_spacing

            x = area.x()

            for item in row:
                item_height = item.sizeHint().height()

                if not test_only:
                    item.setGeometry(
                        QRect(
                            int(x),
                            int(y),
                            card_width,
                            item_height
                        )
                    )

                x += card_width + spacing

            y += row_height + self._vertical_spacing

        return (
            y
            - self._vertical_spacing
            + bottom
            - rect.y()
        )



# --------------------------------------------------
# FAVORITOS
# --------------------------------------------------

def make_track_metadata_item(value, is_link=False):
    item = QTableWidgetItem(str(value))

    if is_link and str(value).strip() not in (
        "",
        "Artista desconhecido",
        "Álbum desconhecido"
    ):
        item.setForeground(QColor("#c9a7ef"))
        font = item.font()
        font.setUnderline(True)
        item.setFont(font)

    return item


def open_track_metadata(parent_window, tracks, row, column):
    if parent_window is None:
        return

    if row < 0 or row >= len(tracks):
        return

    track = tracks[row]

    if column == 1:
        artist = str(
            track.get("artist")
            or track.get("album_artist")
            or ""
        ).strip()

        if artist and artist != "Artista desconhecido":
            parent_window.open_artist_page(artist)

    elif column == 2:
        album = str(track.get("album") or "").strip()
        artist = str(
            track.get("album_artist")
            or track.get("artist")
            or ""
        ).strip()

        if album and album != "Álbum desconhecido":
            parent_window.open_album_page(album, artist)


class FavoritesView(QWidget):
    def __init__(self, scanner, parent_window):
        super().__init__()

        self.scanner = scanner
        self.parent_window = parent_window
        self.language = parent_window.interface_language
        self.tracks = []
        self._is_dirty = True

        self.sort_key = "artist"
        self.sort_ascending = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 28)
        layout.setSpacing(24)

        header = QVBoxLayout()
        header.setSpacing(5)

        header_top = QHBoxLayout()
        header_top.setSpacing(12)

        title_icon = QLabel()
        title_icon.setFixedSize(28, 28)
        icon_manager = getattr(
            getattr(self.parent_window, "appearance", None),
            "icon_manager",
            None
        )
        if icon_manager is not None:
            title_icon.setPixmap(
                icon_manager.icon(
                    "navigation.favorites_title"
                ).pixmap(QSize(26, 26))
            )

        title = QLabel(tr("favorites.title", self.language))
        title.setObjectName("pageTitle")

        header_top.addWidget(title_icon)
        header_top.addWidget(title)
        header_top.addStretch()

        self.search_button = QPushButton(
            tr("home.search", self.language)
        )
        self.search_button.setObjectName("searchButton")
        self.search_button.setFixedSize(130, 38)
        self.search_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        _set_theme_stylesheet(self.search_button, """
            QPushButton#searchButton {
                background: #49375f;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 12px;
                color: #f2eafa;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton#searchButton:hover {
                background: #594675;
            }
        """)
        self.search_button.clicked.connect(
            self.parent_window.open_global_search
        )
        header_top.addWidget(self.search_button)

        self.sort_button = QPushButton(
            tr("favorites.sort", self.language).format(
                label=tr("favorites.sort.artist", self.language),
                direction="↑"
            )
        )
        self.sort_button.setObjectName("sortButton")
        self.sort_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.sort_button.clicked.connect(
            self.show_sort_menu
        )
        header_top.addWidget(self.sort_button)

        header.addLayout(header_top)

        self.count_label = QLabel(
            tr("favorites.count.many", self.language).format(count=0)
        )
        self.count_label.setObjectName("pageSubtitle")
        header.addWidget(self.count_label)

        layout.addLayout(header)

        self.tracks_table = TrackRowsPanel(
            icon_manager=getattr(
                getattr(self.parent_window, "appearance", None),
                "icon_manager",
                None
            )
        )
        self.tracks_table.library_style = True
        layout.addWidget(self.tracks_table, 1)

    def format_duration(self, duration):
        try:
            seconds = int(float(duration or 0))
        except (TypeError, ValueError):
            seconds = 0

        minutes, seconds = divmod(seconds, 60)
        return f"{minutes}:{seconds:02d}"

    def show_sort_menu(self):
        menu = QMenu(self)

        options = [
            (tr("favorites.sort.artist", self.language), "artist"),
            (tr("favorites.sort.album", self.language), "album"),
            (tr("favorites.sort.title", self.language), "title"),
            (tr("favorites.sort.duration", self.language), "duration"),
            (tr("favorites.sort.added_recent", self.language), "added_recent"),
            (tr("favorites.sort.added_oldest", self.language), "added_oldest"),
        ]

        for label, key in options:
            action = menu.addAction(label)
            action.triggered.connect(
                lambda checked=False, selected=key:
                    self.apply_sort(selected)
            )

        menu.addSeparator()

        reset_action = menu.addAction(tr("favorites.sort.clear", self.language))
        reset_action.triggered.connect(
            self.reset_sort
        )

        menu.exec(
            self.sort_button.mapToGlobal(
                self.sort_button.rect().bottomLeft()
            )
        )

    def apply_sort(self, key):
        if key in ("artist", "album", "title", "duration"):
            if self.sort_key == key:
                self.sort_ascending = not self.sort_ascending
            else:
                self.sort_key = key
                self.sort_ascending = True

        elif key == "added_recent":
            self.sort_key = "favorited_at"
            self.sort_ascending = False

        elif key == "added_oldest":
            self.sort_key = "favorited_at"
            self.sort_ascending = True

        self.refresh_table()

    def reset_sort(self):
        self.sort_key = "artist"
        self.sort_ascending = True
        self.refresh_table()

    def _track_sort_value(self, track):
        key = self.sort_key

        if key == "duration":
            try:
                return float(track.get("duration") or 0)
            except (TypeError, ValueError):
                return 0

        if key == "favorited_at":
            return track.get("favorited_at") or ""

        value = track.get(key) or ""

        if key == "title" and not value:
            value = Path(track.get("path", "")).stem

        return str(value).casefold()

    def sort_tracks(self):
        self.tracks.sort(
            key=self._track_sort_value,
            reverse=not self.sort_ascending
        )

    def _insertion_index(self, track):
        value = self._track_sort_value(track)

        for index, existing in enumerate(self.tracks):
            existing_value = self._track_sort_value(existing)

            if self.sort_ascending and value < existing_value:
                return index

            if not self.sort_ascending and value > existing_value:
                return index

        return len(self.tracks)

    def _update_header(self):
        count = len(self.tracks)
        count_key = (
            "favorites.count.one"
            if count == 1
            else "favorites.count.many"
        )

        self.count_label.setText(
            tr(count_key, self.language).format(count=count)
        )

        labels = {
            "artist": tr("favorites.sort.artist", self.language),
            "album": tr("favorites.sort.album", self.language),
            "title": tr("favorites.sort.title", self.language),
            "duration": tr("favorites.sort.duration", self.language),
            "favorited_at": tr("favorites.sort.added", self.language)
        }

        label = labels.get(
            self.sort_key,
            tr("favorites.sort.artist", self.language)
        )

        if self.sort_key == "favorited_at":
            direction = "↓" if not self.sort_ascending else "↑"
        else:
            direction = "↑" if self.sort_ascending else "↓"

        self.sort_button.setText(
            tr("favorites.sort", self.language).format(
                label=label,
                direction=direction
            )
        )

    def refresh_table(self):
        self.sort_tracks()

        self.tracks_table.set_tracks(
            self.tracks,
            show_favorite=True
        )

        self._update_header()

    def update_track(self, track_id, is_favorite):
        panel = self.tracks_table

        # Se a lista estiver sendo construída, mantém o caminho seguro.
        if (
            panel._build_timer.isActive()
            or len(panel.rows) != len(panel.tracks)
        ):
            self.refresh()
            return

        current_index = next(
            (
                i for i, track in enumerate(self.tracks)
                if track.get("id") == track_id
            ),
            -1
        )

        if not is_favorite:
            if current_index < 0:
                return

            self.tracks.pop(current_index)
            panel.remove_track(track_id)
            self._update_header()
            return

        if current_index >= 0:
            return

        track = self.scanner.get_track_by_id(track_id)

        if not track:
            return

        if not self.parent_window._track_is_available(track):
            return

        track["is_favorite"] = 1

        index = self._insertion_index(track)

        self.tracks.insert(index, track)
        panel.insert_track(track, index)

        self._update_header()

    def refresh_if_needed(self):
        if self._is_dirty:
            self.refresh()

    def refresh(self):
        self._is_dirty = True

        if not self.parent_window.library_access_ready:
            self.tracks = []
            self.refresh_table()
            self._is_dirty = False
            return

        tracks = self.scanner.list_favorite_tracks()

        self.tracks = [
            track for track in tracks
            if self.parent_window._track_is_available(track)
        ]

        self.refresh_table()
        self._is_dirty = False


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

class Sidebar(QFrame):
    def __init__(self, appearance, language="pt_BR"):
        super().__init__()

        self.language = language
        self.appearance = appearance
        self.icon_manager = appearance.icon_manager
        self._pressed_buttons = set()

        self.settings = QSettings("SerifaPlayer", "SerifaPlayer")
        self.collapsed = False

        self.setObjectName("sidebar")
        self.setProperty("collapsed", False)

        self.expanded_width = int(
            get_theme_value("components", "sidebar", "width", 240)
        )
        self.collapsed_width = 76

        self.setFixedWidth(self.expanded_width)

        layout = QVBoxLayout(self)
        self.main_layout = layout

        layout.setContentsMargins(
            int(get_theme_value("components", "sidebar", "margin_left", 20)),
            int(get_theme_value("components", "sidebar", "margin_top", 24)),
            int(get_theme_value("components", "sidebar", "margin_right", 20)),
            int(get_theme_value("components", "sidebar", "margin_bottom", 20))
        )
        layout.setSpacing(
            int(get_theme_value("components", "sidebar", "button_spacing", 12))
        )

        # Cabeçalho com os dois espaços independentes de logo.
        self.header = QWidget()
        self.header.setObjectName("sidebarHeader")

        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)

        self.logo_horizontal = QLabel()
        self.logo_horizontal.setObjectName("logoHorizontal")
        self.logo_horizontal.setFixedSize(190, 42)

        horizontal_icon, _ = self.icon_manager.resolve(
            "brand.logo_horizontal", "normal"
        )
        if not horizontal_icon.isNull():
            self.logo_horizontal.setPixmap(
                horizontal_icon.pixmap(QSize(190, 42))
            )

        self.logo_square = QLabel()
        self.logo_square.setObjectName("logoSquare")
        self.logo_square.setFixedSize(42, 42)

        square_icon, _ = self.icon_manager.resolve(
            "brand.logo_square", "normal"
        )
        if not square_icon.isNull():
            self.logo_square.setPixmap(
                square_icon.pixmap(QSize(42, 42))
            )

        self.logo_square.hide()

        self.toggle_button = QPushButton()
        self.toggle_button.setObjectName("sidebarToggleButton")
        self.toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_button.setFixedSize(30, 34)
        self.toggle_button.setIconSize(QSize(20, 20))
        self.toggle_button.setProperty("appearanceIconId", "sidebar.collapse")
        self.toggle_button.installEventFilter(self)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(48, 43, 59, 0.98);
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 9px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: rgba(65, 58, 80, 1.0);
                border-color: rgba(182, 242, 58, 0.55);
            }
            QPushButton:pressed {
                background-color: rgba(35, 31, 44, 1.0);
            }
        """)

        header_layout.addWidget(self.logo_horizontal)
        header_layout.addWidget(self.logo_square)

        self.toggle_button.clicked.connect(self.toggle_collapsed)

        layout.addWidget(self.header)
        layout.addSpacing(25)

        self.section_label = QLabel("MENU")
        self.section_label.setObjectName("sectionLabel")
        layout.addWidget(self.section_label)

        self.buttons = []

        items = [
            ("navigation.home", tr("navigation.home", self.language)),
            ("navigation.favorites", tr("navigation.favorites", self.language)),
            ("navigation.playlists", tr("navigation.playlists", self.language)),
            ("navigation.artists", tr("navigation.artists", self.language)),
            ("navigation.albums", tr("navigation.albums", self.language)),
            ("navigation.library", tr("navigation.library", self.language)),
        ]

        for identifier, name in items:
            button = self.create_button(identifier, name)
            layout.addWidget(button)
            self.buttons.append(button)

        self.buttons[0].setProperty("active", True)
        self.set_button_icon_state(self.buttons[0], "active")

        layout.addStretch()

        self.import_button = self.create_button(
            "navigation.import",
            tr("navigation.import", self.language)
        )
        layout.addWidget(self.import_button)

        self.settings_button = self.create_button(
            "navigation.settings",
            tr("navigation.settings", self.language)
        )
        layout.addWidget(self.settings_button)

        saved_collapsed = self.settings.value(
            "sidebar_collapsed", False, type=bool
        )
        self.set_collapsed(saved_collapsed, persist=False)

    def attach_toggle_overlay(self, parent):
        """Posiciona o botão sobre a borda da Sidebar."""
        self.toggle_button.setParent(parent)
        self._toggle_overlay_parent = parent
        self._position_toggle_overlay()
        self.toggle_button.show()
        self.toggle_button.raise_()

    def _position_toggle_overlay(self):
        parent = getattr(self, "_toggle_overlay_parent", None)
        if parent is None:
            return

        position = self.mapTo(
            parent,
            QPoint(self.width() - 10, 30)
        )
        self.toggle_button.move(position)
        self.toggle_button.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_toggle_overlay()

    def create_button(self, identifier, text):
        button = QPushButton()
        button.setObjectName("navButton")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setIconSize(QSize(18, 18))

        button.setProperty("appearanceIconId", identifier)
        button.setProperty("appearanceLabel", text)
        button.installEventFilter(self)

        self.set_button_icon_state(button, "normal")
        return button

    def _button_state(self, button):
        if not button.isEnabled():
            return "disabled"
        if id(button) in self._pressed_buttons:
            return "pressed"
        if button.property("active"):
            return "active"
        if button.underMouse():
            return "hover"
        return "normal"

    def set_button_icon_state(self, button, state):
        identifier = button.property("appearanceIconId")
        label = button.property("appearanceLabel")

        icon, fallback = self.icon_manager.resolve(identifier, state)

        if icon.isNull():
            button.setIcon(QIcon())
            button.setText(
                str(fallback) if self.collapsed
                else f"{fallback}   {label}"
            )
        else:
            button.setIcon(icon)
            button.setText("" if self.collapsed else label)

        if button is self.toggle_button:
            button.setToolTip(
                "Expandir menu" if self.collapsed else "Recolher menu"
            )
        else:
            button.setToolTip(label if self.collapsed else "")

    def refresh_button_icon_state(self, button):
        self.set_button_icon_state(button, self._button_state(button))

    def toggle_collapsed(self):
        self.set_collapsed(not self.collapsed)

    def set_collapsed(self, collapsed, persist=True):
        self.collapsed = bool(collapsed)

        self.setFixedWidth(
            self.collapsed_width if self.collapsed
            else self.expanded_width
        )

        self.setProperty("collapsed", self.collapsed)

        if self.collapsed:
            self.logo_horizontal.hide()
            self.logo_square.show()
            self.section_label.hide()
            self.main_layout.setContentsMargins(20, 24, 14, 20)
            self.main_layout.setSpacing(10)
            self.toggle_button.setProperty("collapsed", True)
        else:
            self.logo_square.hide()
            self.logo_horizontal.show()
            self.section_label.show()
            self.main_layout.setContentsMargins(
                int(get_theme_value("components", "sidebar", "margin_left", 20)),
                int(get_theme_value("components", "sidebar", "margin_top", 24)),
                int(get_theme_value("components", "sidebar", "margin_right", 20)),
                int(get_theme_value("components", "sidebar", "margin_bottom", 20))
            )
            self.main_layout.setSpacing(
                int(get_theme_value("components", "sidebar", "button_spacing", 12))
            )
            self.toggle_button.setProperty("collapsed", False)

        self.toggle_button.setProperty(
            "appearanceIconId",
            "sidebar.expand" if self.collapsed else "sidebar.collapse"
        )

        buttons = (
            self.buttons
            + [self.import_button, self.settings_button]
        )

        for button in buttons:
            button.setProperty("collapsed", self.collapsed)
            self.refresh_button_icon_state(button)

        self.refresh_button_icon_state(self.toggle_button)

        # Atualiza os seletores QSS após a mudança de propriedades.
        for widget in [self, self.toggle_button, *buttons]:
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

        if persist:
            self.settings.setValue("sidebar_collapsed", self.collapsed)

    def eventFilter(self, watched, event):
        if not isinstance(watched, QPushButton):
            return super().eventFilter(watched, event)

        if not watched.property("appearanceIconId"):
            return super().eventFilter(watched, event)

        event_type = event.type()

        if event_type == QEvent.Type.MouseButtonPress:
            if (
                event.button() == Qt.MouseButton.LeftButton
                and watched.isEnabled()
            ):
                self._pressed_buttons.add(id(watched))

            self.refresh_button_icon_state(watched)

        elif event_type == QEvent.Type.MouseButtonRelease:
            self._pressed_buttons.discard(id(watched))
            self.refresh_button_icon_state(watched)

        elif event_type in (
            QEvent.Type.Enter,
            QEvent.Type.Leave,
            QEvent.Type.EnabledChange,
        ):
            self.refresh_button_icon_state(watched)

        return super().eventFilter(watched, event)


# TRABALHADOR DE IMPORTAÇÃO
# --------------------------------------------------


class LibraryAccessWorker(QThread):
    progress = Signal(str)
    completed = Signal(dict)

    def __init__(
        self,
        storage_manager,
        folders,
        registry,
        registry_error=None
    ):
        super().__init__()
        self.storage = storage_manager
        self.folders = list(folders)
        self.registry = registry or {}
        self.registry_error = registry_error
        self.resolved_volume_mountpoints = {}

    @staticmethod
    def _key(path):
        return os.path.normpath(
            os.path.abspath(
                os.path.expanduser(str(path))
            )
        )

    @staticmethod
    def _check_directory(path):
        target = Path(path)

        if not target.is_dir():
            raise RuntimeError("A pasta não existe ou não está disponível.")

        if not os.access(str(target), os.R_OK | os.X_OK):
            raise RuntimeError("Sem permissão de leitura da pasta.")

        try:
            with os.scandir(target) as entries:
                next(entries, None)
        except OSError as error:
            raise RuntimeError(
                f"Não foi possível ler a pasta: {error}"
            ) from error

        return str(target.resolve(strict=True))

    def _resolve_legacy(self, original):
        if not os.path.isdir(original):
            raise RuntimeError(
                "Pasta antiga indisponível e sem registro de UUID."
            )

        partition, mountpoint = (
            self.storage.find_partition_for_path(original)
        )

        if os.path.realpath(mountpoint) == os.path.realpath("/home"):
            return self._check_directory(original)

        if partition.read_only is not True:
            raise RuntimeError(
                "Volume antigo não está confirmado como somente leitura."
            )

        return self._check_directory(original)

    def _resolve_local(self, original, entry):
        target = entry.get("absolute_path") or original
        return self._check_directory(target)

    def _resolve_volume(self, volume_uuid, entries):
        try:
            self.progress.emit(
                f"Verificando volume {volume_uuid}..."
            )

            _, mountpoint = self.storage.mount_uuid_read_only(
                volume_uuid
            )

            partition = self.storage.find_partition_by_uuid(
                volume_uuid
            )

            if partition.read_only is not True:
                raise RuntimeError(
                    "O volume não foi confirmado como somente leitura."
                )

            root = Path(mountpoint).resolve(strict=True)

            if not root.is_dir():
                raise RuntimeError(
                    "O ponto de montagem não é uma pasta válida."
                )

            self.resolved_volume_mountpoints[volume_uuid] = str(root)

        except Exception as error:
            reason = str(error)
            return {
                self._key(original): (None, reason)
                for original, _ in entries
            }

        results = {}

        for original, entry in entries:
            try:
                relative = Path(
                    entry.get("relative_path") or "."
                )

                if relative.is_absolute() or ".." in relative.parts:
                    raise RuntimeError(
                        "Caminho relativo inválido no registro do volume."
                    )

                target = (root / relative).resolve(strict=True)

                if not target.is_relative_to(root):
                    raise RuntimeError(
                        "A pasta registrada ultrapassa os limites do volume."
                    )

                results[self._key(original)] = (
                    self._check_directory(target),
                    None
                )

            except Exception as error:
                results[self._key(original)] = (
                    None,
                    str(error)
                )

        return results

    def resolve(self):
        registry_folders = self.registry.get("folders", [])
        registry_map = {}

        for entry in registry_folders:
            if isinstance(entry, dict) and entry.get("path"):
                registry_map[self._key(entry["path"])] = entry

        resolved = {}
        volume_groups = {}
        warnings = []

        if self.registry_error:
            warnings.append(
                f"Registro de volumes: {self.registry_error}"
            )

        for original in self.folders:
            key = self._key(original)
            entry = registry_map.get(key)

            if entry is None:
                try:
                    resolved[key] = (
                        self._resolve_legacy(original),
                        None
                    )
                except Exception as error:
                    resolved[key] = (None, str(error))
                continue

            kind = entry.get("kind")

            if kind == "local":
                try:
                    resolved[key] = (
                        self._resolve_local(original, entry),
                        None
                    )
                except Exception as error:
                    resolved[key] = (None, str(error))

            elif kind == "volume":
                volume_uuid = entry.get("uuid")

                if not volume_uuid:
                    resolved[key] = (
                        None,
                        "Registro de volume sem UUID."
                    )
                    continue

                volume_groups.setdefault(
                    volume_uuid, []
                ).append((original, entry))

            else:
                resolved[key] = (
                    None,
                    "Tipo de registro de pasta desconhecido."
                )

        for volume_uuid, entries in volume_groups.items():
            resolved.update(
                self._resolve_volume(volume_uuid, entries)
            )

        available = []
        unavailable = []
        resolved_entries = []

        for original in self.folders:
            key = self._key(original)
            actual, reason = resolved.get(
                key,
                (None, "Pasta não processada.")
            )

            if actual:
                available.append(actual)
                entry = registry_map.get(key, {})
                details = {}

                if entry.get("kind") == "volume":
                    details = {
                        "kind": "volume",
                        "uuid": entry.get("uuid"),
                        "old_mountpoint": entry.get(
                            "registered_mountpoint"
                        ),
                        "new_mountpoint": (
                            self.resolved_volume_mountpoints.get(
                                entry.get("uuid")
                            )
                        )
                    }

                resolved_entries.append({
                    "original": original,
                    "resolved": actual,
                    **details
                })
            else:
                unavailable.append({
                    "path": original,
                    "reason": reason
                })

        return {
            "available_folders": available,
            "unavailable": unavailable,
            "resolved_entries": resolved_entries,
            "resolved_volumes": dict(
                self.resolved_volume_mountpoints
            ),
            "warnings": warnings
        }

    def run(self):
        try:
            self.completed.emit(self.resolve())
        except Exception as error:
            self.completed.emit({
                "available_folders": [],
                "unavailable": [
                    {
                        "path": "(biblioteca)",
                        "reason": str(error)
                    }
                ],
                "resolved_entries": [],
                "resolved_volumes": {},
                "warnings": []
            })


class ScanWorker(QThread):
    progress = Signal(str)
    completed = Signal(dict)
    failed = Signal(str)

    def __init__(self, scanner, folders):
        super().__init__()

        self.scanner = scanner
        self.folders = list(folders)

    def run(self):
        try:
            result = self.scanner.scan(
                self.folders,
                progress=self.progress.emit
            )

            self.completed.emit(result)

        except Exception as error:
            self.failed.emit(str(error))


# --------------------------------------------------
# BIBLIOTECA MUSICAL — CONFIGURAÇÕES
# --------------------------------------------------

class LibrarySettingsView(QWidget):
    def __init__(self, parent_window):
        super().__init__()

        self.parent_window = parent_window
        self.language = parent_window.interface_language

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 28)
        layout.setSpacing(18)

        title = QLabel(tr("import.title", self.language))
        title.setObjectName("pageTitle")

        subtitle = QLabel(tr("import.subtitle", self.language))
        subtitle.setObjectName("pageSubtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        section = QLabel(tr("import.folders", self.language))
        section.setObjectName("sectionTitle")
        layout.addWidget(section)

        self.folder_list = QListWidget()
        self.folder_list.setObjectName("folderList")
        self.folder_list.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        layout.addWidget(self.folder_list, 1)

        actions = QHBoxLayout()

        self.add_button = QPushButton(tr("import.add_folder", self.language))
        self.add_button.setObjectName("primaryButton")

        self.remove_button = QPushButton(tr("import.remove_selected", self.language))
        self.remove_button.setObjectName("secondaryButton")

        actions.addWidget(self.add_button)
        actions.addWidget(self.remove_button)
        actions.addStretch()

        layout.addLayout(actions)

        import_section = QLabel(tr("import.section", self.language))
        import_section.setObjectName("sectionTitle")
        layout.addWidget(import_section)

        self.scan_status = QLabel(tr("import.not_imported", self.language))
        self.scan_status.setObjectName("pageSubtitle")
        self.scan_status.setWordWrap(True)

        layout.addWidget(self.scan_status)

        scan_actions = QHBoxLayout()

        self.scan_button = QPushButton(tr("import.button", self.language))
        self.scan_button.setObjectName("primaryButton")

        scan_actions.addWidget(self.scan_button)
        scan_actions.addStretch()

        layout.addLayout(scan_actions)

        self.add_button.clicked.connect(
            parent_window.open_folder_browser
        )

        self.remove_button.clicked.connect(
            lambda: parent_window.remove_selected_folder()
        )

        self.scan_button.clicked.connect(
            parent_window.start_library_scan
        )

    def refresh(self, folders):
        self.folder_list.clear()

        for folder in folders:
            item = QListWidgetItem(folder)
            item.setToolTip(folder)
            self.folder_list.addItem(item)


# --------------------------------------------------
# SELETOR DE PASTAS INTEGRADO
# --------------------------------------------------

class FolderBrowserView(QWidget):
    def __init__(self, parent_window):
        super().__init__()

        self.parent_window = parent_window
        self.language = parent_window.interface_language
        self.storage = parent_window.storage_manager

        self.current_path = None
        self.history = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 28)
        layout.setSpacing(14)

        header = QHBoxLayout()

        self.back_button = QPushButton(tr("folder.back", self.language))
        self.back_button.setObjectName("secondaryButton")
        self.back_button.clicked.connect(self.go_back)

        header.addWidget(self.back_button)
        header.addStretch()

        layout.addLayout(header)

        self.title = QLabel(tr("folder.title", self.language))
        self.title.setObjectName("pageTitle")
        layout.addWidget(self.title)

        self.location_label = QLabel(tr("folder.location", self.language))
        self.location_label.setObjectName("pageSubtitle")
        self.location_label.setWordWrap(True)

        layout.addWidget(self.location_label)

        self.entries = QListWidget()
        self.entries.setObjectName("folderList")
        self.entries.setIconSize(QSize(20, 20))
        self.entries.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.entries.itemDoubleClicked.connect(self.open_item)

        layout.addWidget(self.entries, 1)

        footer = QHBoxLayout()

        self.cancel_button = QPushButton(tr("folder.cancel", self.language))
        self.cancel_button.setObjectName("secondaryButton")
        self.cancel_button.clicked.connect(
            self.cancel
        )

        self.choose_button = QPushButton(tr("folder.choose", self.language))
        self.choose_button.setObjectName("secondaryButton")
        self.choose_button.clicked.connect(
            self.choose_current_folder
        )

        self.choose_selected_button = QPushButton(
            tr("folder.choose_many", self.language)
        )
        self.choose_selected_button.setObjectName("primaryButton")
        self.choose_selected_button.clicked.connect(
            self.choose_selected_folders
        )

        footer.addStretch()
        footer.addWidget(self.cancel_button)
        footer.addWidget(self.choose_button)
        footer.addWidget(self.choose_selected_button)

        layout.addLayout(footer)

    def start(self):
        self.history.clear()
        self.current_path = None
        self.show_devices()

    def show_devices(self):
        self.current_path = None
        self.entries.clear()

        self.title.setText(tr("folder.title", self.language))
        self.location_label.setText(tr("folder.available", self.language))

        self.choose_button.setEnabled(False)
        self.choose_selected_button.setEnabled(False)
        self.back_button.setEnabled(False)

        try:
            partitions = self.storage.list_partitions()

        except StorageError as error:
            QMessageBox.critical(
                self,
                tr("folder.storage_error", self.language),
                str(error)
            )
            return

        for partition in partitions:
            size = self.storage.format_size(
                partition.size_bytes
            )

            if partition.mountpoint:
                status = tr("folder.available_status", self.language)
                path = partition.mountpoint

            else:
                status = (
                    tr("folder.readonly_status", self.language)
                )
                path = partition.device

            label = (
                f"{partition.display_name}  ·  "
                f"{size}  ·  {status}"
            )

            item = QListWidgetItem("▣  " + label)

            item.setData(
                Qt.ItemDataRole.UserRole,
                (partition.device, path)
            )

            self.entries.addItem(item)

    def open_item(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)

        if self.current_path is None:
            if not data:
                return

            device, path = data

            try:
                if path.startswith("/dev/"):
                    path = self.storage.mount_read_only(device)

            except StorageError as error:
                QMessageBox.critical(
                    self,
                    "Não foi possível acessar o disco",
                    str(error)
                )
                return

            self.history.append(None)

            self.open_directory(
                path,
                remember=False
            )
            return

        if not data:
            return

        target = data

        self.history.append(self.current_path)

        self.open_directory(
            target,
            remember=False
        )

    def open_directory(self, path, remember=True):
        path = os.path.abspath(path)

        if not os.path.isdir(path) or not os.access(path, os.R_OK):
            QMessageBox.warning(
                self,
                "Pasta indisponível",
                "Não foi possível ler esta pasta."
            )
            return

        self.current_path = path

        self.title.setText("Selecionar pasta")
        self.location_label.setText(path)

        self.choose_button.setEnabled(True)
        self.choose_selected_button.setEnabled(True)
        self.back_button.setEnabled(True)

        self.entries.clear()

        try:
            directories = []

            with os.scandir(path) as iterator:
                for entry in iterator:
                    try:
                        if (
                            entry.is_dir(follow_symlinks=False)
                            and not entry.name.startswith(".")
                        ):
                            directories.append(
                                (entry.name, entry.path)
                            )

                    except OSError:
                        continue

            directories.sort(
                key=lambda value: value[0].casefold()
            )

            for name, full_path in directories:
                item = QListWidgetItem(name)
                item.setIcon(
                    self.parent_window.appearance.icon_manager.icon(
                        "library.folder"
                    )
                )
                item.setData(
                    Qt.ItemDataRole.UserRole,
                    full_path
                )
                self.entries.addItem(item)

        except OSError as error:
            QMessageBox.warning(
                self,
                "Erro de leitura",
                str(error)
            )

    def go_back(self):
        if not self.history:
            self.show_devices()
            return

        previous = self.history.pop()

        if previous is None:
            self.show_devices()

        else:
            self.open_directory(
                previous,
                remember=False
            )

    def cancel(self):
        self.parent_window.show_library_settings()

    def choose_current_folder(self):
        if self.current_path:
            self.parent_window.add_library_folder(
                self.current_path
            )

    def choose_selected_folders(self):

        selected_items = self.entries.selectedItems()

        if not selected_items:
            QMessageBox.information(
                self,
                "Nenhuma pasta selecionada",
                "Selecione uma ou mais pastas para adicionar."
            )
            return

        folders = []

        for item in selected_items:

            folder = item.data(Qt.ItemDataRole.UserRole)

            if folder and os.path.isdir(folder):
                folders.append(os.path.abspath(folder))

        if not folders:
            return

        self.parent_window.add_library_folders(folders)

# --------------------------------------------------
# ALBUM CARD
# --------------------------------------------------
class PlayButton(QPushButton):
    """Botão de reprodução integrado ao sistema de ícones personalizáveis."""

    def __init__(self, parent=None, size=48):
        super().__init__(parent)

        self._icon_pressed = False
        self.icon_identifier = "player.play"

        self.setFixedSize(size, size)
        self.setIconSize(self.size())
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setStyleSheet(
            "QPushButton { background: transparent; border: none; padding: 0; }"
        )

        self.refresh_icon()

    def _find_icon_manager(self):
        candidates = []
        widget = self

        while widget is not None:
            candidates.append(widget)
            widget = widget.parentWidget()

        candidates.extend(QApplication.topLevelWidgets())

        for candidate in candidates:
            manager = getattr(candidate, "icon_manager", None)
            if manager is not None:
                return manager

            appearance = getattr(candidate, "appearance", None)
            manager = getattr(appearance, "icon_manager", None)
            if manager is not None:
                return manager

        return None

    def refresh_icon(self):
        manager = self._find_icon_manager()
        if manager is None:
            return

        if not self.isEnabled():
            state = "disabled"
        elif self._icon_pressed:
            state = "pressed"
        elif self.underMouse():
            state = "hover"
        else:
            state = "normal"

        icon, fallback = manager.resolve(self.icon_identifier, state)

        if icon is not None and not icon.isNull():
            self.setIcon(icon)
            self.setText("")
        else:
            self.setIcon(QIcon())
            self.setText(fallback or "▶")

    def enterEvent(self, event):
        super().enterEvent(event)
        self.refresh_icon()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.refresh_icon()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._icon_pressed = True
            self.refresh_icon()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self._icon_pressed = False
        self.refresh_icon()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_icon()

    def changeEvent(self, event):
        super().changeEvent(event)
        self.refresh_icon()


class AlbumCover(QWidget):
    def __init__(self, cover_path=None, gradient=None, title=None):
        super().__init__()

        self.setObjectName("albumCover")
        self.setFixedSize(
            int(get_theme_value("components", "album_card", "cover_size", 193)),
            int(get_theme_value("components", "album_card", "cover_size", 193))
        )
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        if gradient is None:
            gradient = (
                "qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                "stop:0 #49375f,stop:1 #211e2a)"
            )

        _set_theme_stylesheet(self, f"QWidget#albumCover {{ background: {gradient}; border-radius: 12px; }}"
        )

        self.pixmap = QPixmap()
        self.fallback_title = str(title or "").strip()
        if cover_path and os.path.isfile(str(cover_path)):
            self.pixmap = QPixmap(str(cover_path))

        if not self.pixmap.isNull():
            scaled = self.pixmap.scaled(
                QSize(193, 193),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            crop_x = max(0, (scaled.width() - 193) // 2)
            crop_y = max(0, (scaled.height() - 193) // 2)
            self.pixmap = scaled.copy(
                crop_x, crop_y, 193, 193
            )

        self._zoom = 1.0
        self._overlay_opacity = 0.0
        self._button_visible = False

        self.zoom_animation = QPropertyAnimation(self, b"zoom", self)
        self.zoom_animation.setDuration(190)
        self.zoom_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.overlay_animation = QPropertyAnimation(
            self, b"overlayOpacity", self
        )
        self.overlay_animation.setDuration(240)
        self.overlay_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.play_button = PlayButton(self, 48)
        self.play_button.hide()

        self.button_opacity = QGraphicsOpacityEffect(self.play_button)
        self.button_opacity.setOpacity(0.0)
        self.play_button.setGraphicsEffect(self.button_opacity)

        self.button_animation = QPropertyAnimation(
            self.button_opacity, b"opacity", self
        )
        self.button_animation.setDuration(160)
        self.button_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.button_animation.finished.connect(self._hide_button)
        self._position_play_button()

    def _position_play_button(self):
        self.play_button.move(
            (self.width() - self.play_button.width()) // 2,
            (self.height() - self.play_button.height()) // 2
        )

    def resizeEvent(self, event):
        self._position_play_button()
        super().resizeEvent(event)

    def get_zoom(self):
        return self._zoom

    def set_zoom(self, value):
        self._zoom = float(value)
        self.update()

    zoom = Property(float, get_zoom, set_zoom)

    def get_overlay_opacity(self):
        return self._overlay_opacity

    def set_overlay_opacity(self, value):
        self._overlay_opacity = float(value)
        self.update()

    overlayOpacity = Property(float, get_overlay_opacity, set_overlay_opacity)

    def set_desaturated(self, dimmed):
        target = 1.0 if dimmed else 0.0
        self.overlay_animation.stop()
        self.overlay_animation.setStartValue(self._overlay_opacity)
        self.overlay_animation.setEndValue(target)
        self.overlay_animation.start()

    def show_play_button(self, visible):
        self._button_visible = bool(visible)
        self.button_animation.stop()
        if visible:
            self.play_button.show()
        self.button_animation.setStartValue(self.button_opacity.opacity())
        self.button_animation.setEndValue(1.0 if visible else 0.0)
        self.button_animation.start()

    def _hide_button(self):
        if not self._button_visible and self.button_opacity.opacity() <= 0.01:
            self.play_button.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        side = 193.0 * self._zoom
        target = QRectF(
            (self.width() - side) / 2.0,
            (self.height() - side) / 2.0,
            side,
            side
        )
        rounded = QPainterPath()
        rounded.addRoundedRect(
            QRectF(0.0, 0.0, float(self.width()), float(self.height())),
            12.0,
            12.0
        )
        painter.setClipPath(rounded)

        if not self.pixmap.isNull():
            painter.drawPixmap(target.toRect(), self.pixmap)
        else:
            painter.fillRect(
                target.toRect(),
                QColor("#332b40")
            )
            initial = self.fallback_title[0].upper() if self.fallback_title else "♪"
            font = QFont(self.font())
            font.setBold(True)
            font.setPixelSize(76)
            painter.setFont(font)
            painter.setPen(QColor("#ffffff"))
            painter.drawText(
                target.toRect(),
                Qt.AlignmentFlag.AlignCenter,
                initial
            )

        if self._overlay_opacity > 0.0:
            painter.fillPath(
                rounded,
                QColor(0, 0, 0, int(125 * self._overlay_opacity))
            )


class CircleCover(QFrame):
    def __init__(self, cover_path=None, gradient=None):
        super().__init__()

        self.setObjectName("artistCover")
        self.setFixedSize(140, 140)

        if gradient is None:
            gradient = (
                "qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                "stop:0 #49375f,stop:1 #211e2a)"
            )

        _set_theme_stylesheet(self, f"""
            QFrame#artistCover {{
                background: {gradient};
                border-radius: 70px;
            }}
            """
        )

        if cover_path and os.path.isfile(str(cover_path)):

            pixmap = QPixmap(str(cover_path))

            if not pixmap.isNull():

                scaled = pixmap.scaled(
                    QSize(140, 140),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )

                x = (scaled.width() - 140) // 2
                y = (scaled.height() - 140) // 2

                cropped = scaled.copy(x, y, 140, 140)

                circular = QPixmap(140, 140)
                circular.fill(Qt.GlobalColor.transparent)

                painter = QPainter(circular)
                painter.setRenderHint(
                    QPainter.RenderHint.Antialiasing
                )

                circle = QPainterPath()
                circle.addEllipse(0, 0, 140, 140)

                painter.setClipPath(circle)
                painter.drawPixmap(0, 0, cropped)
                painter.end()

                image = QLabel(self)
                image.setGeometry(0, 0, 140, 140)
                image.setPixmap(circular)
                _set_theme_stylesheet(image, "background: transparent; border: none;"
                )


class ArtistCover(QWidget):

    def __init__(self, cover_path=None):
        super().__init__()

        self.setFixedSize(
            int(get_theme_value("components", "artist_card", "cover_size", 152)),
            int(get_theme_value("components", "artist_card", "cover_size", 152))
        )
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._zoom = 1.0
        self.pixmap = QPixmap()
        self._overlay_opacity = 0.0

        self.overlay_animation = QPropertyAnimation(
            self,
            b"overlayOpacity",
            self
        )
        self.overlay_animation.setDuration(240)
        self.overlay_animation.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )

        if cover_path and os.path.isfile(str(cover_path)):
            self.pixmap = QPixmap(str(cover_path))

        self.play_button = PlayButton(self, 42)
        self.play_button.move(7, 7)
        self.play_button.hide()

        self.button_opacity = QGraphicsOpacityEffect(
            self.play_button
        )
        self.button_opacity.setOpacity(0)
        self.play_button.setGraphicsEffect(
            self.button_opacity
        )

        self.button_animation = QPropertyAnimation(
            self.button_opacity,
            b"opacity",
            self
        )
        self.button_animation.setDuration(160)
        self.button_animation.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )
        self._button_visible = False
        self.button_animation.finished.connect(
            self._hide_button
        )

    def set_desaturated(self, desaturated):
        target = 1.0 if desaturated else 0.0

        self.overlay_animation.stop()
        self.overlay_animation.setStartValue(
            self._overlay_opacity
        )
        self.overlay_animation.setEndValue(target)
        self.overlay_animation.start()

    def get_overlay_opacity(self):
        return self._overlay_opacity

    def set_overlay_opacity(self, value):
        self._overlay_opacity = value
        self.update()

    overlayOpacity = Property(
        float,
        get_overlay_opacity,
        set_overlay_opacity
    )

    def get_zoom(self):
        return self._zoom

    def set_zoom(self, value):
        self._zoom = value
        self.update()

    zoom = Property(float, get_zoom, set_zoom)

    def show_play_button(self, visible):
        self._button_visible = visible
        self.button_animation.stop()

        if visible:
            self.play_button.show()

        self.button_animation.setStartValue(
            self.button_opacity.opacity()
        )
        self.button_animation.setEndValue(
            1.0 if visible else 0.0
        )
        self.button_animation.start()

    def _hide_button(self):
        if (
            not self._button_visible
            and self.button_opacity.opacity() <= 0.01
        ):
            self.play_button.hide()

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )
        painter.setRenderHint(
            QPainter.RenderHint.SmoothPixmapTransform
        )

        diameter = 140 * self._zoom

        x = (self.width() - diameter) / 2
        y = (self.height() - diameter) / 2

        target = QRectF(
            x,
            y,
            diameter,
            diameter
        )

        path = QPainterPath()
        path.addEllipse(target)

        painter.setClipPath(path)

        gradient = QLinearGradient(
            target.topLeft(),
            target.bottomRight()
        )
        gradient.setColorAt(0, QColor("#76516f"))
        gradient.setColorAt(1, QColor("#263b4b"))

        painter.fillPath(path, gradient)

        if not self.pixmap.isNull():
            size = int(diameter)

            scaled = self.pixmap.scaled(
                QSize(size, size),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )

            crop_x = (scaled.width() - size) // 2
            crop_y = (scaled.height() - size) // 2

            cropped = scaled.copy(
                crop_x,
                crop_y,
                size,
                size
            )

            painter.drawPixmap(
                target.toRect(),
                cropped
            )

        if self._overlay_opacity > 0:
            painter.fillPath(
                path,
                QColor(
                    0,
                    0,
                    0,
                    int(125 * self._overlay_opacity)
                )
            )


class ArtistCard(QFrame):
    clicked = Signal(str)
    play_requested = Signal(str)
    hover_changed = Signal(object, bool)

    def __init__(self, name, cover_path=None, gradient=None):
        super().__init__()

        self.name = name
        self._hover_active = False

        self.setObjectName("albumCard")
        self.setFixedWidth(int(get_theme_value("components", "artist_card", "width", 180)))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            *([int(get_theme_value("components", "cards", "padding", 10))] * 4)
        )
        layout.setSpacing(int(get_theme_value("components", "cards", "spacing", 10)))

        self.cover = ArtistCover(cover_path)
        self.cover.installEventFilter(self)

        self.cover.play_button.installEventFilter(self)

        layout.addWidget(
            self.cover,
            alignment=Qt.AlignmentFlag.AlignHCenter
        )

        self.cover.play_button.clicked.connect(
            lambda: self.play_requested.emit(self.name)
        )

        self.zoom_animation = QPropertyAnimation(
            self.cover,
            b"zoom",
            self
        )
        self.zoom_animation.setDuration(190)
        self.zoom_animation.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )

        name_label = QLabel(name)
        self.name_label = name_label
        self.name_label.installEventFilter(self)

        name_label.setObjectName("cardTitle")
        name_label.setAlignment(
            Qt.AlignmentFlag.AlignHCenter
        )
        name_label.setWordWrap(True)
        name_label.setFixedHeight(int(get_theme_value("components", "artist_card", "title_height", 40)))
        name_label.setToolTip(name)

        layout.addWidget(name_label)

    def set_dimmed(self, dimmed):
        self.cover.set_desaturated(dimmed)
        _set_theme_stylesheet(self.name_label, "color: #b7b1bd;" if dimmed else ""
        )

    def eventFilter(self, watched, event):

        monitored_widgets = (
            getattr(self, "cover", None),
            getattr(getattr(self, "cover", None), "play_button", None),
            getattr(self, "name_label", None)
        )

        if watched in monitored_widgets:

            if event.type() in (
                QEvent.Type.Enter,
                QEvent.Type.MouseMove
            ):
                self.activate_hover()

            elif event.type() == QEvent.Type.Leave:
                QTimer.singleShot(
                    40,
                    self._finish_hover_if_outside
                )

        return super().eventFilter(watched, event)

    def activate_hover(self):
        if self._hover_active:
            return

        self._hover_active = True
        self.hover_changed.emit(self, True)

        self.zoom_animation.stop()
        self.zoom_animation.setStartValue(
            self.cover.zoom
        )
        self.zoom_animation.setEndValue(1.055)
        self.zoom_animation.start()

        self.cover.show_play_button(True)

    def enterEvent(self, event):
        self.activate_hover()
        super().enterEvent(event)

    def leaveEvent(self, event):
        QTimer.singleShot(
            40,
            self._finish_hover_if_outside
        )
        super().leaveEvent(event)

    def _cursor_is_inside_card(self):

        widget = QApplication.widgetAt(QCursor.pos())

        while widget is not None:
            if widget is self:
                return True

            widget = widget.parentWidget()

        cursor_position = self.mapFromGlobal(
            QCursor.pos()
        )

        return self.rect().contains(cursor_position)

    def _finish_hover_if_outside(self):

        if self._cursor_is_inside_card():
            return

        if not self._hover_active:
            return

        self._hover_active = False
        self.hover_changed.emit(self, False)

        self.zoom_animation.stop()
        self.zoom_animation.setStartValue(
            self.cover.zoom
        )
        self.zoom_animation.setEndValue(1.0)
        self.zoom_animation.start()

        self.cover.show_play_button(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.name)
            event.accept()
            return

        super().mousePressEvent(event)


class AlbumCard(QFrame):
    clicked = Signal(str, str)
    play_requested = Signal(str, str)
    context_requested = Signal(str, str, object)
    hover_changed = Signal(object, bool)

    def __init__(self, title, artist, cover_path=None, gradient=None):
        super().__init__()

        self.title = title
        self.artist = artist
        self._hover_active = False
        self._is_dimmed = False
        self._drag_press_global = None
        self._drag_started = False

        self.setObjectName("albumCard")
        self.setFixedWidth(int(get_theme_value("components", "album_card", "width", 213)))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            *([int(get_theme_value("components", "cards", "padding", 10))] * 4)
        )
        layout.setSpacing(int(get_theme_value("components", "cards", "spacing", 10)))

        self.cover = AlbumCover(cover_path, gradient, title)
        self.cover.installEventFilter(self)
        self.cover.play_button.installEventFilter(self)
        layout.addWidget(self.cover, alignment=Qt.AlignmentFlag.AlignLeft)

        self.cover.play_button.clicked.connect(
            lambda: self.play_requested.emit(self.title, self.artist)
        )

        self.title_label = QLabel(title)
        self.title_label.setObjectName("cardTitle")
        self.title_label.setWordWrap(False)
        self.title_label.setToolTip(title)
        self.title_label.installEventFilter(self)
        layout.addWidget(self.title_label)

        self.artist_label = QueueElidedLabel(artist)
        self.artist_label.setObjectName("cardSubtitle")
        self.artist_label.setWordWrap(False)
        self.artist_label.setToolTip(artist)
        self.artist_label.installEventFilter(self)
        layout.addWidget(self.artist_label)

    def set_dimmed(self, dimmed):
        dimmed = bool(dimmed)
        if self._is_dimmed == dimmed:
            return
        self._is_dimmed = dimmed
        self.cover.set_desaturated(dimmed)
        _set_theme_stylesheet(self.title_label, "color: #b7b1bd;" if dimmed else ""
        )
        _set_theme_stylesheet(self.artist_label, "color: #77717f;" if dimmed else ""
        )

    def _begin_album_pointer(self, global_position):
        self._drag_press_global = global_position
        self._drag_started = False

    def _handle_album_drag_move(self, event):
        if self._drag_press_global is None or self._drag_started:
            return False

        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return False

        current_position = event.globalPosition().toPoint()

        if (
            (current_position - self._drag_press_global).manhattanLength()
            < QApplication.startDragDistance()
        ):
            return False

        self._drag_started = True

        mime_data = QMimeData()
        payload = json.dumps({
            "title": self.title,
            "artist": self.artist
        }).encode("utf-8")

        mime_data.setData(SERIFA_ALBUM_MIME, payload)

        drag = QDrag(self)
        drag.setMimeData(mime_data)

        source_preview = self.grab().scaled(
            QSize(180, 190),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        preview = QPixmap(source_preview.size())
        preview.fill(Qt.GlobalColor.transparent)

        painter = QPainter(preview)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(0.68)
        painter.drawPixmap(0, 0, source_preview)
        painter.end()

        drag.setPixmap(preview)
        drag.setHotSpot(QPoint(22, 24))

        drag.exec(Qt.DropAction.CopyAction)

        return True

    def _finish_album_pointer(self):
        if self._drag_press_global is None:
            return

        was_drag = self._drag_started

        self._drag_press_global = None
        self._drag_started = False

        if not was_drag:
            self.clicked.emit(self.title, self.artist)

    def eventFilter(self, watched, event):
        monitored = (
            self.cover,
            self.cover.play_button,
            getattr(self, "title_label", None),
            getattr(self, "artist_label", None)
        )

        if watched in monitored:
            if event.type() in (
                QEvent.Type.Enter,
                QEvent.Type.MouseMove
            ):
                self.activate_hover()

                if (
                    watched is not self.cover.play_button
                    and event.type() == QEvent.Type.MouseMove
                    and self._handle_album_drag_move(event)
                ):
                    return True

            elif event.type() == QEvent.Type.Leave:
                QTimer.singleShot(
                    40,
                    self._finish_hover_if_outside
                )

            elif (
                event.type() == QEvent.Type.MouseButtonPress
                and event.button() == Qt.MouseButton.RightButton
            ):
                self.context_requested.emit(
                    self.title,
                    self.artist,
                    event.globalPosition().toPoint()
                )
                return True

            elif (
                watched is not self.cover.play_button
                and event.type() == QEvent.Type.MouseButtonPress
                and event.button() == Qt.MouseButton.LeftButton
            ):
                self._begin_album_pointer(
                    event.globalPosition().toPoint()
                )
                return True

            elif (
                watched is not self.cover.play_button
                and event.type() == QEvent.Type.MouseButtonRelease
                and event.button() == Qt.MouseButton.LeftButton
            ):
                self._finish_album_pointer()
                return True

        return super().eventFilter(watched, event)

    def activate_hover(self):
        if self._hover_active:
            return
        self._hover_active = True
        self.hover_changed.emit(self, True)
        self.cover.zoom_animation.stop()
        self.cover.zoom_animation.setStartValue(self.cover.zoom)
        self.cover.zoom_animation.setEndValue(1.055)
        self.cover.zoom_animation.start()
        self.cover.show_play_button(True)

    def enterEvent(self, event):
        self.activate_hover()
        super().enterEvent(event)

    def leaveEvent(self, event):
        QTimer.singleShot(40, self._finish_hover_if_outside)
        super().leaveEvent(event)

    def _cursor_is_inside_card(self):
        widget = QApplication.widgetAt(QCursor.pos())
        while widget is not None:
            if widget is self:
                return True
            widget = widget.parentWidget()
        cursor_position = self.mapFromGlobal(QCursor.pos())
        return self.rect().contains(cursor_position)

    def _finish_hover_if_outside(self):
        if self._cursor_is_inside_card() or not self._hover_active:
            return
        self._hover_active = False
        self.hover_changed.emit(self, False)
        self.cover.zoom_animation.stop()
        self.cover.zoom_animation.setStartValue(self.cover.zoom)
        self.cover.zoom_animation.setEndValue(1.0)
        self.cover.zoom_animation.start()
        self.cover.show_play_button(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._begin_album_pointer(
                event.globalPosition().toPoint()
            )
            event.accept()
            return

        if event.button() == Qt.MouseButton.RightButton:
            self.context_requested.emit(
                self.title,
                self.artist,
                event.globalPosition().toPoint()
            )
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._handle_album_drag_move(event):
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._finish_album_pointer()
            event.accept()
            return

        super().mouseReleaseEvent(event)



class PlaylistCover(AlbumCover):
    def __init__(
        self,
        cover_paths=None,
        gradient=None,
        custom_cover_path=None
    ):
        super().__init__(None, gradient)

        self.cover_pixmaps = []
        self.custom_cover_pixmap = QPixmap()

        self.set_cover_paths(cover_paths or [])
        self.set_custom_cover_path(custom_cover_path)

    def set_cover_paths(self, cover_paths):
        self.cover_pixmaps = []

        for cover_path in (cover_paths or [])[:4]:
            if not cover_path or not os.path.isfile(str(cover_path)):
                continue

            pixmap = QPixmap(str(cover_path))

            if not pixmap.isNull():
                self.cover_pixmaps.append(pixmap)

        self.update()

    def set_custom_cover_path(self, cover_path):
        self.custom_cover_pixmap = QPixmap()

        if cover_path and os.path.isfile(str(cover_path)):
            pixmap = QPixmap(str(cover_path))

            if not pixmap.isNull():
                self.custom_cover_pixmap = pixmap

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(
            QPainter.RenderHint.SmoothPixmapTransform
        )

        side = min(
            193.0,
            float(self.width()),
            float(self.height())
        ) * self._zoom

        target = QRectF(
            (self.width() - side) / 2.0,
            (self.height() - side) / 2.0,
            side,
            side
        )

        rounded = QPainterPath()
        rounded.addRoundedRect(
            QRectF(0.0, 0.0, float(self.width()), float(self.height())),
            12.0,
            12.0
        )

        painter.setClipPath(rounded)

        if not self.custom_cover_pixmap.isNull():
            self._draw_playlist_image(
                painter,
                self.custom_cover_pixmap,
                target
            )

        elif len(self.cover_pixmaps) == 1:
            self._draw_playlist_image(
                painter,
                self.cover_pixmaps[0],
                target
            )

        elif self.cover_pixmaps:
            gap = 2.0
            half = (side - gap) / 2.0

            positions = [
                (0, 0),
                (1, 0),
                (0, 1),
                (1, 1)
            ]

            for index, (column, row) in enumerate(positions):
                pixmap = self.cover_pixmaps[
                    index % len(self.cover_pixmaps)
                ]

                tile = QRectF(
                    target.x() + column * (half + gap),
                    target.y() + row * (half + gap),
                    half,
                    half
                )

                self._draw_playlist_image(
                    painter,
                    pixmap,
                    tile
                )

        if self._overlay_opacity > 0.0:
            painter.fillPath(
                rounded,
                QColor(
                    0,
                    0,
                    0,
                    int(125 * self._overlay_opacity)
                )
            )

    def _draw_playlist_image(self, painter, pixmap, target):
        width = max(1, int(round(target.width())))
        height = max(1, int(round(target.height())))

        scaled = pixmap.scaled(
            QSize(width, height),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        crop_x = max(0, (scaled.width() - width) // 2)
        crop_y = max(0, (scaled.height() - height) // 2)

        cropped = scaled.copy(
            crop_x,
            crop_y,
            width,
            height
        )

        painter.drawPixmap(target.toRect(), cropped)


class PlaylistCard(QFrame):
    clicked = Signal(int)
    play_requested = Signal(int)
    context_requested = Signal(int, object)
    hover_changed = Signal(object, bool)

    def __init__(
        self,
        playlist_id,
        name,
        cover_paths,
        subtitle,
        gradient=None,
        custom_cover_path=None
    ):
        super().__init__()

        self.playlist_id = int(playlist_id)
        self.name = name

        self._hover_active = False
        self._drag_press_global = None
        self._drag_started = False

        self.setObjectName("albumCard")
        self.setFixedWidth(213)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.cover = PlaylistCover(
            cover_paths,
            gradient,
            custom_cover_path
        )

        self.cover.installEventFilter(self)
        self.cover.play_button.installEventFilter(self)

        layout.addWidget(
            self.cover,
            alignment=Qt.AlignmentFlag.AlignLeft
        )

        self.cover.play_button.clicked.connect(
            lambda: self.play_requested.emit(self.playlist_id)
        )

        self.title_label = QLabel(name)
        self.title_label.setObjectName("cardTitle")
        self.title_label.setWordWrap(False)
        self.title_label.setToolTip(name)
        self.title_label.installEventFilter(self)

        layout.addWidget(self.title_label)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("cardSubtitle")
        self.subtitle_label.setWordWrap(False)
        self.subtitle_label.setToolTip(subtitle)
        self.subtitle_label.installEventFilter(self)

        layout.addWidget(self.subtitle_label)

    def set_dimmed(self, dimmed):
        self.cover.set_desaturated(dimmed)
        _set_theme_stylesheet(self.title_label, "color: #b7b1bd;" if dimmed else ""
        )
        _set_theme_stylesheet(self.subtitle_label, "color: #77717f;" if dimmed else ""
        )

    def _begin_playlist_pointer(self, global_position):
        self._drag_press_global = global_position
        self._drag_started = False

    def _handle_playlist_drag_move(self, event):
        if (
            self._drag_press_global is None
            or self._drag_started
        ):
            return False

        if not (
            event.buttons() & Qt.MouseButton.LeftButton
        ):
            return False

        current_position = event.globalPosition().toPoint()

        if (
            (current_position - self._drag_press_global)
            .manhattanLength()
            < QApplication.startDragDistance()
        ):
            return False

        self._drag_started = True

        mime_data = QMimeData()

        payload = __import__("json").dumps({
            "id": self.playlist_id
        }).encode("utf-8")

        mime_data.setData(
            SERIFA_PLAYLIST_MIME,
            payload
        )

        drag = QDrag(self)
        drag.setMimeData(mime_data)

        source_preview = self.grab().scaled(
            QSize(180, 190),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        preview = QPixmap(source_preview.size())
        preview.fill(Qt.GlobalColor.transparent)

        painter = QPainter(preview)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )
        painter.setOpacity(0.68)
        painter.drawPixmap(0, 0, source_preview)
        painter.end()

        drag.setPixmap(preview)
        drag.setHotSpot(QPoint(22, 24))

        drag.exec(Qt.DropAction.CopyAction)

        return True

    def _finish_playlist_pointer(self):
        if self._drag_press_global is None:
            return

        was_drag = self._drag_started

        self._drag_press_global = None
        self._drag_started = False

        if not was_drag:
            self.clicked.emit(self.playlist_id)

    def eventFilter(self, watched, event):
        monitored = (
            self.cover,
            self.cover.play_button,
            getattr(self, "title_label", None),
            getattr(self, "subtitle_label", None)
        )

        if watched in monitored:
            if event.type() in (
                QEvent.Type.Enter,
                QEvent.Type.MouseMove
            ):
                self.activate_hover()

                if (
                    watched is not self.cover.play_button
                    and event.type() == QEvent.Type.MouseMove
                    and self._handle_playlist_drag_move(event)
                ):
                    return True

            elif event.type() == QEvent.Type.Leave:
                QTimer.singleShot(
                    40,
                    self._finish_hover_if_outside
                )

            elif (
                event.type() == QEvent.Type.MouseButtonPress
                and event.button() == Qt.MouseButton.RightButton
            ):
                self.context_requested.emit(
                    self.playlist_id,
                    event.globalPosition().toPoint()
                )
                return True

            elif (
                watched is not self.cover.play_button
                and event.type() == QEvent.Type.MouseButtonPress
                and event.button() == Qt.MouseButton.LeftButton
            ):
                self._begin_playlist_pointer(
                    event.globalPosition().toPoint()
                )
                return True

            elif (
                watched is not self.cover.play_button
                and event.type() == QEvent.Type.MouseButtonRelease
                and event.button() == Qt.MouseButton.LeftButton
            ):
                self._finish_playlist_pointer()
                return True

        return super().eventFilter(watched, event)

    def activate_hover(self):
        if self._hover_active:
            return

        self._hover_active = True
        self.hover_changed.emit(self, True)

        self.cover.zoom_animation.stop()
        self.cover.zoom_animation.setStartValue(
            self.cover.zoom
        )
        self.cover.zoom_animation.setEndValue(1.055)
        self.cover.zoom_animation.start()

        self.cover.show_play_button(True)

    def enterEvent(self, event):
        self.activate_hover()
        super().enterEvent(event)

    def leaveEvent(self, event):
        QTimer.singleShot(
            40,
            self._finish_hover_if_outside
        )
        super().leaveEvent(event)

    def _cursor_is_inside_card(self):
        widget = QApplication.widgetAt(QCursor.pos())

        while widget is not None:
            if widget is self:
                return True
            widget = widget.parentWidget()

        cursor_position = self.mapFromGlobal(QCursor.pos())
        return self.rect().contains(cursor_position)

    def _finish_hover_if_outside(self):
        if (
            self._cursor_is_inside_card()
            or not self._hover_active
        ):
            return

        self._hover_active = False
        self.hover_changed.emit(self, False)

        self.cover.zoom_animation.stop()
        self.cover.zoom_animation.setStartValue(
            self.cover.zoom
        )
        self.cover.zoom_animation.setEndValue(1.0)
        self.cover.zoom_animation.start()

        self.cover.show_play_button(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._begin_playlist_pointer(
                event.globalPosition().toPoint()
            )
            event.accept()
            return

        if event.button() == Qt.MouseButton.RightButton:
            self.context_requested.emit(
                self.playlist_id,
                event.globalPosition().toPoint()
            )
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._handle_playlist_drag_move(event):
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._finish_playlist_pointer()
            event.accept()
            return

        super().mouseReleaseEvent(event)


# --------------------------------------------------
# HOME VIEW
# --------------------------------------------------


# --------------------------------------------------
# PÁGINAS DE ARTISTA E ÁLBUM
# --------------------------------------------------

def apply_back_button_style(button):
    _set_theme_stylesheet(button, """
        QPushButton {
            background-color: #B6F23A;
            color: #49375F;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 0 16px;
            font-size: 13px;
            font-weight: 600;
        }

        QPushButton:hover {
            background-color: #A6E02E;
        }

        QPushButton:pressed {
            background-color: #98D51F;
        }
    """)


class BackdropPage(QWidget):
    cover_change_requested = Signal(str, str)
    cover_reset_requested = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.background = QLabel(self)
        self.background.setScaledContents(True)

        self.blur_effect = QGraphicsBlurEffect(self.background)
        self.blur_effect.setBlurRadius(38)
        self.background.setGraphicsEffect(self.blur_effect)

        self.overlay = None

        self.content = QWidget(self)
        _set_theme_stylesheet(self.content, "background: transparent;")

        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(32, 26, 32, 28)
        self.content_layout.setSpacing(20)

        self.background.lower()
        self.content.raise_()

    def set_backdrop(self, path):
        pixmap = QPixmap()

        if path and os.path.isfile(str(path)):
            pixmap = QPixmap(str(path))

        if not pixmap.isNull():
            painter = QPainter(pixmap)
            painter.fillRect(
                pixmap.rect(),
                QColor(15, 13, 22, 140)
            )
            painter.end()

        self.background.setPixmap(pixmap)

    def install_cover_context_menu(self, label, entity_type):
        label.setProperty("cover_entity_type", entity_type)
        label.setProperty("cover_entity_key", "")
        label.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        label.customContextMenuRequested.connect(
            lambda position, target=label:
                self._show_cover_context_menu(target, position)
        )

    def set_cover_entity_key(self, label, entity_key):
        label.setProperty("cover_entity_key", entity_key)

    def _show_cover_context_menu(self, label, position):
        entity_type = label.property("cover_entity_type")
        entity_key = label.property("cover_entity_key")

        if not entity_type or not entity_key:
            return

        menu = QMenu(self)

        if self.language == "en":
            change_action = menu.addAction("Change cover")
            reset_action = menu.addAction("Restore original cover")
        else:
            change_action = menu.addAction("Alterar capa")
            reset_action = menu.addAction("Restaurar capa original")

        change_action.triggered.connect(
            lambda checked=False:
                self.cover_change_requested.emit(
                    entity_type, entity_key
                )
        )
        reset_action.triggered.connect(
            lambda checked=False:
                self.cover_reset_requested.emit(
                    entity_type, entity_key
                )
        )

        menu.exec(label.mapToGlobal(position))

    def resizeEvent(self, event):
        self.background.setGeometry(self.rect())
        self.content.setGeometry(self.rect())

        self.background.lower()
        self.content.raise_()

        super().resizeEvent(event)

    @staticmethod
    def set_rounded_cover(label, path, radius=14):
        pixmap = QPixmap()

        if path and os.path.isfile(str(path)):
            pixmap = QPixmap(str(path))

        if pixmap.isNull():
            label.clear()
            label.setText("♫")
            return

        size = label.size()
        scaled = pixmap.scaled(
            size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        x = max(0, (scaled.width() - size.width()) // 2)
        y = max(0, (scaled.height() - size.height()) // 2)

        result = QPixmap(size)
        result.fill(Qt.GlobalColor.transparent)

        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(
            QPainter.RenderHint.SmoothPixmapTransform
        )

        rounded = QPainterPath()
        rounded.addRoundedRect(
            QRectF(0, 0, size.width(), size.height()),
            radius,
            radius
        )

        painter.setClipPath(rounded)
        painter.drawPixmap(
            QRect(0, 0, size.width(), size.height()),
            scaled,
            QRect(x, y, size.width(), size.height())
        )
        painter.end()

        label.setPixmap(result)
        label.setText("")

    @staticmethod
    def set_cover(label, path):
        BackdropPage.set_rounded_cover(label, path, 16)


class ArtistProfileView(BackdropPage):
    back_requested = Signal()
    album_requested = Signal(str, str)
    play_album_requested = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.language = getattr(parent, "interface_language", "pt_BR")
        self.artist_name = ""

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        _set_theme_stylesheet(self.scroll, "QScrollArea { background: transparent; border: none; }"
            "QScrollArea > QWidget > QWidget { background: transparent; }"
        )
        _set_theme_stylesheet(self.scroll.viewport(), "background: transparent;"
        )
        _set_shortcuts_scrollbar(self.scroll)

        self.inner = QWidget()
        _set_theme_stylesheet(self.inner, "background: transparent;")

        self.inner_layout = QVBoxLayout(self.inner)
        self.inner_layout.setContentsMargins(4, 4, 4, 20)
        self.inner_layout.setSpacing(24)

        self.scroll.setWidget(self.inner)
        self.content_layout.addWidget(self.scroll)

        top_bar = QHBoxLayout()

        self.back_button = QPushButton(tr("artist.back", self.language))
        self.back_button.setObjectName("backButton")
        apply_back_button_style(self.back_button)
        self.back_button.setFixedHeight(38)
        self.back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_button.clicked.connect(
            self.back_requested.emit
        )

        top_bar.addWidget(self.back_button)
        top_bar.addStretch()

        self.inner_layout.addLayout(top_bar)

        header = QHBoxLayout()
        header.setSpacing(28)

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(250, 250)
        self.cover_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        _set_theme_stylesheet(self.cover_label, "background: rgba(255,255,255,15);"
            "border: 1px solid rgba(255,255,255,35);"
            "border-radius: 16px;"
            "color: white;"
            "font-size: 48px;"
        )
        self.install_cover_context_menu(
            self.cover_label, "artist"
        )

        header.addWidget(self.cover_label)

        info = QVBoxLayout()
        info.setSpacing(12)

        artist_caption = QLabel(tr("artist.caption", self.language))
        _set_theme_stylesheet(artist_caption, "color: rgba(255,255,255,150);"
            "font-size: 12px;"
            "font-weight: bold;"
            "letter-spacing: 2px;"
        )

        self.name_label = QLabel(tr("artist.default", self.language))
        self.name_label.setWordWrap(True)
        _set_theme_stylesheet(self.name_label, "color: white;"
            "font-size: 42px;"
            "font-weight: bold;"
        )

        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        _set_theme_stylesheet(self.description_label, "color: rgba(255,255,255,190);"
            "font-size: 14px;"
            "line-height: 1.5;"
        )

        info.addWidget(artist_caption)
        info.addWidget(self.name_label)
        info.addWidget(self.description_label)
        info.addStretch()

        header.addLayout(info, 1)

        self.inner_layout.addLayout(header)

        album_heading = QLabel(tr("artist.discography", self.language))
        album_heading.setObjectName("sectionTitle")
        self.inner_layout.addWidget(album_heading)

        self.albums_layout = FlowLayout(
            min_horizontal_spacing=16,
            vertical_spacing=24
        )

        self.inner_layout.addLayout(self.albums_layout)
        self.inner_layout.addStretch()

    def set_artist(self, name, cover_path, description, albums):
        self.artist_name = name
        self.set_cover_entity_key(
            self.cover_label, name.strip().casefold()
        )

        self.name_label.setText(name)
        self.description_label.setText(description)

        self.set_cover(self.cover_label, cover_path)
        self.set_backdrop(cover_path)

        while self.albums_layout.count():
            item = self.albums_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        gradients = [
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #8d596d,stop:1 #38283d)",
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #537d85,stop:1 #243a4b)",
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #78634f,stop:1 #332b31)",
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #496c75,stop:1 #182c38)",
        ]

        if not albums:
            label = QLabel(tr("artist.empty", self.language))
            label.setObjectName("pageSubtitle")
            self.albums_layout.addWidget(label)
            return

        for index, album in enumerate(albums):
            title = album.get("album") or "Álbum desconhecido"
            artist = album.get("artist") or name

            card = AlbumCard(
                title=title,
                artist=artist,
                cover_path=album.get("cover_path"),
                gradient=gradients[index % len(gradients)]
            )

            card.clicked.connect(self.album_requested.emit)
            card.play_requested.connect(
                self.play_album_requested.emit
            )

            self.albums_layout.addWidget(card)


class AlbumDetailView(BackdropPage):
    back_requested = Signal()
    track_requested = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.language = getattr(parent, "interface_language", "pt_BR")
        self.tracks = []

        top_bar = QHBoxLayout()

        self.back_button = QPushButton(tr("album.back", self.language))
        self.back_button.setObjectName("backButton")
        apply_back_button_style(self.back_button)
        self.back_button.setFixedHeight(38)
        self.back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_button.clicked.connect(
            self.back_requested.emit
        )

        top_bar.addWidget(self.back_button)
        top_bar.addStretch()

        self.content_layout.addLayout(top_bar)

        header = QHBoxLayout()
        header.setSpacing(26)

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(220, 220)
        self.cover_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        _set_theme_stylesheet(self.cover_label, "background: rgba(255,255,255,15);"
            "border: 1px solid rgba(255,255,255,35);"
            "border-radius: 14px;"
            "color: white;"
            "font-size: 48px;"
        )
        self.install_cover_context_menu(
            self.cover_label, "album"
        )

        header.addWidget(self.cover_label)

        info = QVBoxLayout()
        info.setSpacing(10)

        caption = QLabel(tr("album.caption", self.language))
        _set_theme_stylesheet(caption, "color: rgba(255,255,255,150);"
            "font-size: 12px;"
            "font-weight: bold;"
            "letter-spacing: 2px;"
        )

        self.title_label = QLabel(tr("album.default", self.language))
        self.title_label.setWordWrap(True)
        _set_theme_stylesheet(self.title_label, "color: white;"
            "font-size: 32px;"
            "font-weight: bold;"
        )

        self.artist_label = QLabel()
        _set_theme_stylesheet(self.artist_label, "color: rgba(255,255,255,205);"
            "font-size: 17px;"
        )

        self.details_label = QLabel()
        _set_theme_stylesheet(self.details_label, "color: rgba(255,255,255,155);"
            "font-size: 13px;"
        )

        info.addWidget(caption)
        info.addWidget(self.title_label)
        info.addWidget(self.artist_label)
        info.addWidget(self.details_label)
        info.addStretch()

        header.addLayout(info, 1)

        self.content_layout.addLayout(header)

        tracks_heading = QLabel(tr("album.tracks", self.language))
        tracks_heading.setObjectName("sectionTitle")

        self.content_layout.addWidget(tracks_heading)

        self.tracks_table = TrackRowsPanel(
            icon_manager=getattr(
                getattr(parent, "appearance", None),
                "icon_manager",
                None
            )
        )
        self.tracks_table.library_style = True
        self.tracks_table.show_favorite = True
        self.tracks_table.play_requested.connect(
            self.track_requested.emit
        )
        self.content_layout.addWidget(self.tracks_table, 1)

    @staticmethod
    def _set_rounded_cover(label, path, radius=14):
        BackdropPage.set_rounded_cover(label, path, radius)

    @staticmethod
    def _duration(value):
        seconds = max(0, int(float(value or 0)))
        minutes = seconds // 60
        remaining = seconds % 60
        return f"{minutes}:{remaining:02d}"

    @staticmethod
    def _number(value):
        try:
            return int(str(value or "0").split("/")[0])
        except (ValueError, TypeError):
            return 0

    def set_album(self, title, artist, tracks, cover_path):
        self.tracks = list(tracks)

        album_key = json.dumps(
            [title.strip().casefold(), artist.strip().casefold()],
            ensure_ascii=False,
            separators=(",", ":")
        )
        self.set_cover_entity_key(
            self.cover_label, album_key
        )

        self.title_label.setText(title)
        self.artist_label.setText(artist)

        years = sorted({
            str(track.get("year"))
            for track in tracks
            if track.get("year")
        })

        year_text = years[0] if len(years) == 1 else (
            f"{years[0]} – {years[-1]}" if years else ""
        )

        count = len(tracks)
        count_key = "album.count.one" if count == 1 else "album.count.many"
        self.details_label.setText(
            tr(count_key, self.language).format(count=count)
            + (f"  •  {year_text}" if year_text else "")
        )

        self._set_rounded_cover(self.cover_label, cover_path)
        self.set_backdrop(cover_path)

        ordered = sorted(
            self.tracks,
            key=lambda track: (
                self._number(track.get("disc_number")),
                self._number(track.get("track_number")),
                (track.get("title") or "").casefold()
            )
        )

        self.tracks = ordered
        self.tracks_table.set_tracks(
            ordered,
            show_favorite=True
        )




def _set_cover_initial(label, title):
    value = str(title or "").strip()
    initial = value[0].upper() if value else "♪"

    font = QFont(label.font())
    font.setBold(True)
    font.setPixelSize(max(16, min(label.width(), label.height()) // 2))
    label.setFont(font)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setText(initial)


class HomeTrackCover(QWidget):
    def __init__(self, cover_path=None, title=None):
        super().__init__()

        self.setFixedSize(48, 48)
        self.title = str(title or '').strip()
        self.pixmap = QPixmap()

        if cover_path and os.path.isfile(str(cover_path)):
            self.pixmap = QPixmap(str(cover_path))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(
            QPainter.RenderHint.SmoothPixmapTransform
        )

        rect = QRectF(self.rect())

        rounded = QPainterPath()
        rounded.addRoundedRect(rect, 8.0, 8.0)

        painter.setClipPath(rounded)

        if not self.pixmap.isNull():
            size = self.size()

            scaled = self.pixmap.scaled(
                size,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )

            crop_x = max(0, (scaled.width() - size.width()) // 2)
            crop_y = max(0, (scaled.height() - size.height()) // 2)

            cropped = scaled.copy(
                crop_x,
                crop_y,
                size.width(),
                size.height()
            )

            painter.drawPixmap(self.rect(), cropped)

        else:
            painter.fillPath(
                rounded,
                QColor("#332b40")
            )

            painter.setPen(QColor("#ffffff"))
            font = QFont(self.font())
            font.setBold(True)
            font.setPixelSize(25)
            painter.setFont(font)
            initial = self.title[0].upper() if self.title else '♪'
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                initial
            )



def _track_visualizer_path(track):
    path = (track or {}).get("path")
    if not path:
        return None

    try:
        return str(Path(path).expanduser().resolve())
    except (OSError, RuntimeError, TypeError, ValueError):
        return None


def _draw_track_playback_indicator(
    painter,
    width,
    height,
    levels,
    visible
):
    if not visible:
        return

    painter.save()

    if levels:
        usable_width = max(1.0, width - 12.0)
        count = max(1, int(usable_width / 5.0))
        step = usable_width / count

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(182, 242, 58, 43))

        for index in range(count):
            bar_height = 2.0 + float(levels[index % len(levels)]) * 8.0
            x = 6.0 + index * step
            bar_width = max(1.2, step * 0.55)

            painter.drawRoundedRect(
                QRectF(
                    x,
                    height - bar_height - 2.0,
                    bar_width,
                    bar_height
                ),
                1.5,
                1.5
            )

    painter.setPen(QPen(QColor(182, 242, 58, 220), 0.6))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(
        QRectF(1.0, 1.0, width - 2.0, height - 2.0),
        9,
        9
    )

    painter.restore()


class HomeTrackRow(QFrame):
    clicked = Signal(object, str)
    play_requested = Signal(object, str)
    metadata_clicked = Signal(object, str)

    def __init__(self, item, item_type="track"):
        super().__init__()

        self.item = item
        self.item_type = item_type
        self._visualizer_path = (
            _track_visualizer_path(item)
            if item_type == "track"
            else None
        )
        self._visualizer_visible = False
        self._visualizer_levels = []

        self.setObjectName("homeTrackRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(58)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 8, 6)
        layout.setSpacing(10)

        self.cover_widget = HomeTrackCover(
            item.get("cover_path"),
            item.get("title") or item.get("album")
        )
        layout.addWidget(self.cover_widget)

        if item_type == "album":
            title = item.get("album") or "Álbum desconhecido"
            subtitle = item.get("artist") or "Artista desconhecido"
            metadata = f'{item.get("track_count", 0)} faixas'
        else:
            title = (
                item.get("title")
                or Path(item.get("path", "")).stem
                or "Faixa desconhecida"
            )
            subtitle = (
                item.get("artist")
                or item.get("album_artist")
                or "Artista desconhecido"
            )

            duration = item.get("duration")
            metadata = ""

            if duration is not None:
                try:
                    seconds = max(0, int(float(duration)))
                    metadata = f"{seconds // 60}:{seconds % 60:02d}"
                except (TypeError, ValueError):
                    pass

        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("homeTrackTitle")
        self.title_label.setToolTip(title)
        self.title_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("homeTrackSubtitle")
        self.subtitle_label.setToolTip(subtitle)
        self.subtitle_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.subtitle_label)

        layout.addLayout(text_layout, 1)

        if metadata:
            self.metadata_label = QLabel(metadata)
            self.metadata_label.setObjectName("homeTrackMetadata")
            self.metadata_label.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents,
                True
            )
            layout.addWidget(self.metadata_label)

        self.play_button = PlayButton(self, 30)
        self.play_button.setToolTip("Reproduzir")

        self.play_button.clicked.connect(
            lambda: self.play_requested.emit(
                self.item,
                self.item_type
            )
        )

        layout.addWidget(self.play_button)

        _set_theme_stylesheet(self, """
            QFrame#homeTrackRow {
                background: rgba(255,255,255,0.025);
                border: 1px solid rgba(255,255,255,0.045);
                border-radius: 9px;
            }

            QFrame#homeTrackRow:hover {
                background: rgba(255,255,255,0.075);
                border: 1px solid rgba(255,255,255,0.10);
            }

            QLabel#homeTrackTitle {
                color: #f2edf7;
                font-size: 13px;
                font-weight: 600;
                background: transparent;
                border: none;
            }

            QLabel#homeTrackSubtitle {
                color: #a49bad;
                font-size: 11px;
                background: transparent;
                border: none;
            }

            QLabel#homeTrackMetadata {
                color: #93899d;
                font-size: 10px;
                background: transparent;
                border: none;
            }

            QPushButton#homeTrackPlayButton {
                background: rgba(153,112,190,0.18);
                color: #e9d5ff;
                border: none;
                border-radius: 15px;
                font-size: 11px;
            }

            QPushButton#homeTrackPlayButton:hover {
                background: rgba(153,112,190,0.38);
            }
        """)


    def set_playback_visualizer(self, current_path, levels):
        visible = (
            self._visualizer_path is not None
            and self._visualizer_path == current_path
        )

        changed = (
            visible != self._visualizer_visible
            or (visible and levels != self._visualizer_levels)
        )

        if changed:
            self._visualizer_visible = visible
            self._visualizer_levels = list(levels) if visible else []
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

        if self._visualizer_visible:
            painter = QPainter(self)
            painter.setRenderHint(
                QPainter.RenderHint.Antialiasing
            )
            _draw_track_playback_indicator(
                painter,
                self.width(),
                self.height(),
                self._visualizer_levels,
                True
            )
            painter.end()

    def mouseReleaseEvent(self, event):
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.rect().contains(event.position().toPoint())
        ):
            self.clicked.emit(
                self.item,
                self.item_type
            )

        super().mouseReleaseEvent(event)



class TrackListRow(QFrame):
    clicked = Signal(object)
    play_requested = Signal(object)
    metadata_clicked = Signal(object, str)
    favorite_requested = Signal(object)
    context_requested = Signal(object, object)

    def __init__(self, track, show_favorite=True, parent=None, library_style=False, icon_manager=None):
        super().__init__(parent)

        self.track = track
        self.icon_manager = icon_manager
        self._visualizer_path = _track_visualizer_path(track)
        self._visualizer_visible = False
        self._visualizer_levels = []
        self.show_favorite = show_favorite
        self.library_style = library_style
        self.metadata_clickable = True
        self._selected = False
        self._drag_start = None

        self.setObjectName("homeTrackRow")
        self.setFixedHeight(int(get_theme_value("components", "track_row", "height", 66)))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            int(get_theme_value("components", "track_row", "margin_horizontal", 10)),
            int(get_theme_value("components", "track_row", "margin_vertical", 8)),
            int(get_theme_value("components", "track_row", "margin_horizontal", 10)),
            int(get_theme_value("components", "track_row", "margin_vertical", 8))
        )
        layout.setSpacing(10)

        self.cover_widget = HomeTrackCover(
            track.get("cover_path"),
            track.get("title") or Path(track.get("path", "")).stem
        )
        layout.addWidget(self.cover_widget)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(int(get_theme_value(
            "components", "track_row",
            "text_spacing_library" if library_style else "text_spacing_standard",
            1 if library_style else 3
        )))

        title = (
            track.get("title")
            or Path(track.get("path", "")).stem
            or "Faixa desconhecida"
        )

        artist = (
            track.get("artist")
            or track.get("album_artist")
            or "Artista desconhecido"
        )

        album = track.get("album") or "Álbum desconhecido"

        self.title_label = QLabel(title)
        self.title_label.setObjectName("homeTrackTitle")
        self.title_label.setToolTip(title)
        if library_style:
            _set_theme_stylesheet(self.title_label, "font-size: 15px;")

        self.artist_label = QLabel(artist)
        self.artist_label.setObjectName("homeTrackSubtitle")
        self.artist_label.setToolTip(f"Artista: {artist}")

        self.album_label = QLabel(album)
        self.album_label.setObjectName("homeTrackSubtitle")
        self.album_label.setToolTip(f"Álbum: {album}")

        for label in (
            self.title_label,
            self.artist_label,
            self.album_label
        ):
            label.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents,
                True
            )

        metadata_layout = QHBoxLayout()
        metadata_layout.setSpacing(int(get_theme_value("components", "track_row", "metadata_spacing", 7)))
        metadata_layout.addWidget(self.artist_label)

        separator = QLabel("·")
        separator.setObjectName("homeTrackMetadata")
        separator.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )
        metadata_layout.addWidget(separator)
        metadata_layout.addWidget(self.album_label)
        metadata_layout.addStretch()

        text_layout.addWidget(self.title_label)
        text_layout.addLayout(metadata_layout)

        layout.addLayout(text_layout, 1)

        duration = track.get("duration")

        try:
            seconds = max(0, int(float(duration or 0)))
            duration_text = f"{seconds // 60}:{seconds % 60:02d}"
        except (TypeError, ValueError):
            duration_text = "--:--"

        self.duration_label = QLabel(duration_text)
        self.duration_label.setObjectName("homeTrackMetadata")
        self.duration_label.setFixedWidth(48)
        self.duration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.duration_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )
        layout.addWidget(self.duration_label)

        if show_favorite:
            self.favorite_button = QPushButton()
            self.favorite_button.setFixedSize(
                int(get_theme_value("components", "track_row", "favorite_button_size", 30)),
                int(get_theme_value("components", "track_row", "favorite_button_size", 30))
            )
            self.favorite_button.setFlat(True)
            self.favorite_button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )
            self.favorite_button.setFocusPolicy(
                Qt.FocusPolicy.NoFocus
            )
            self.favorite_button.setAttribute(
                Qt.WidgetAttribute.WA_NoMousePropagation,
                True
            )

            if library_style:
                from PySide6.QtCore import QSize

                icon_state = (
                    "active"
                    if track.get("is_favorite")
                    else "normal"
                )
                if self.icon_manager is not None:
                    self.favorite_button.setIcon(
                        self.icon_manager.icon(
                            "actions.favorite",
                            icon_state
                        )
                    )
                self.favorite_button.setIconSize(QSize(20, 20))
                _set_theme_stylesheet(self.favorite_button, """
                    QPushButton {
                        border: none;
                        background: transparent;
                    }
                    QPushButton:hover {
                        background: rgba(182,242,58,0.08);
                        border-radius: 15px;
                    }
                """)
            else:
                self.favorite_button.setText(
                    "♥" if track.get("is_favorite") else "♡"
                )
                _set_theme_stylesheet(self.favorite_button, """
                    QPushButton {
                        color: #d9b6ff;
                        font-size: 19px;
                        border: none;
                        background: transparent;
                    }
                    QPushButton:hover {
                        color: #f0dfff;
                    }
                """)

            self.favorite_button.setToolTip(
                "Remover dos favoritos"
                if track.get("is_favorite")
                else "Adicionar aos favoritos"
            )
            self.favorite_button.clicked.connect(
                lambda: self.favorite_requested.emit(self.track)
            )
            layout.addWidget(self.favorite_button)

        self.play_button = PlayButton(self, 30)
        self.play_button.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
        )
        self.play_button.setAttribute(
            Qt.WidgetAttribute.WA_NoMousePropagation,
            True
        )
        self.play_button.setToolTip("Reproduzir")
        self.play_button.clicked.connect(
            lambda: self.play_requested.emit(self.track)
        )
        layout.addWidget(self.play_button)

        _set_theme_stylesheet(self, """
            QFrame#homeTrackRow {
                background: rgba(255,255,255,0.025);
                border: 1px solid rgba(255,255,255,0.045);
                border-radius: 9px;
            }
            QFrame#homeTrackRow:hover {
                background: rgba(255,255,255,0.075);
                border: 1px solid rgba(255,255,255,0.10);
            }
            QFrame#homeTrackRow[selected="true"] {
                background: rgba(153,112,190,0.15);
                border: 1px solid rgba(153,112,190,0.35);
            }
            QLabel#homeTrackTitle {
                color: #f2edf7;
                font-size: 13px;
                font-weight: 600;
                background: transparent;
                border: none;
            }
            QLabel#homeTrackSubtitle {
                color: #a49bad;
                font-size: 11px;
                background: transparent;
                border: none;
            }
            QLabel#homeTrackMetadata {
                color: #93899d;
                font-size: 12px;
                background: transparent;
                border: none;
            }
            QPushButton#homeTrackPlayButton {
                background: rgba(153,112,190,0.18);
                color: #e9d5ff;
                border: none;
                border-radius: 15px;
                font-size: 11px;
            }
            QPushButton#homeTrackPlayButton:hover {
                background: rgba(153,112,190,0.38);
            }
        """)

        self.set_selected(False)


    def set_favorite_state(self, is_favorite):
        is_favorite = bool(is_favorite)
        self.track["is_favorite"] = int(is_favorite)

        if not self.show_favorite:
            return

        if self.library_style:
            if self.icon_manager is not None:
                self.favorite_button.setIcon(
                    self.icon_manager.icon(
                        "actions.favorite",
                        "active" if is_favorite else "normal"
                    )
                )
        else:
            self.favorite_button.setText(
                "♥" if is_favorite else "♡"
            )

        self.favorite_button.setToolTip(
            "Remover dos favoritos"
            if is_favorite
            else "Adicionar aos favoritos"
        )

    def set_playback_visualizer(self, current_path, levels):
        visible = (
            self._visualizer_path is not None
            and self._visualizer_path == current_path
        )

        changed = (
            visible != self._visualizer_visible
            or (visible and levels != self._visualizer_levels)
        )

        if changed:
            self._visualizer_visible = visible
            self._visualizer_levels = list(levels) if visible else []
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

        if self._visualizer_visible:
            painter = QPainter(self)
            painter.setRenderHint(
                QPainter.RenderHint.Antialiasing
            )
            _draw_track_playback_indicator(
                painter,
                self.width(),
                self.height(),
                self._visualizer_levels,
                True
            )
            painter.end()

    def set_selected(self, selected):
        self._selected = bool(selected)
        self.setProperty("selected", self._selected)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def mousePressEvent(self, event):
        self._selection_modifiers = event.modifiers()

        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.position().toPoint()

        elif event.button() == Qt.MouseButton.RightButton:
            self.context_requested.emit(
                self.track,
                self.mapToGlobal(event.position().toPoint())
            )
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (
            self._drag_start is None
            or not (event.buttons() & Qt.MouseButton.LeftButton)
        ):
            super().mouseMoveEvent(event)
            return

        distance = (
            event.position().toPoint() - self._drag_start
        ).manhattanLength()

        if distance < QApplication.startDragDistance():
            return

        track_id = self.track.get("id")

        if track_id is None:
            self._drag_start = None
            return

        mime_data = QMimeData()
        mime_data.setData(
            SERIFA_TRACK_MIME,
            json.dumps({"id": int(track_id)}).encode("utf-8")
        )

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.setPixmap(create_track_drag_preview(self.track))
        drag.setHotSpot(QPoint(20, 22))

        self._drag_start = None
        drag.exec(Qt.DropAction.CopyAction)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._drag_start is None:
                super().mouseReleaseEvent(event)
                return

            position = event.position().toPoint()

            if (
                self.metadata_clickable
                and self.artist_label.geometry().contains(position)
            ):
                self.metadata_clicked.emit(
                    self.track,
                    "artist"
                )

            elif (
                self.metadata_clickable
                and self.album_label.geometry().contains(position)
            ):
                self.metadata_clicked.emit(
                    self.track,
                    "album"
                )

            else:
                self.clicked.emit(self.track)

            self._drag_start = None

        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.play_requested.emit(self.track)

        super().mouseDoubleClickEvent(event)



class TrackRowsPanel(QWidget):
    selection_changed = Signal(object, int)
    metadata_requested = Signal(object, str)
    play_requested = Signal(object)
    favorite_requested = Signal(object)
    context_requested = Signal(object, object)

    def __init__(self, parent=None, icon_manager=None):
        super().__init__(parent)

        self.icon_manager = icon_manager
        self.tracks = []
        self.rows = []
        self._current_row = -1
        self.show_favorite = True
        self.library_style = False
        self.metadata_clickable = True
        self._build_timer = QTimer(self)
        self._build_timer.setInterval(1)
        self._build_timer.timeout.connect(self._append_track_batch)
        self._build_index = 0
        self._build_batch_size = 35
        self._pending_selected_id = None
        self._pending_selected_index = None
        self._selected_ids = set()
        self._selection_anchor = None
        self._pending_selected_key = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setAttribute(
            Qt.WidgetAttribute.WA_StyledBackground, True
        )
        self.scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea::viewport {
                background: transparent;
            }
            QScrollBar:vertical {
                background: #211e2a;
                width: 7px;
                border-radius: 3px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: #59496b;
                border-radius: 3px;
                min-height: 28px;
            }
            QScrollBar::handle:vertical:hover {
                background: #80649e;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.content = QWidget()
        self.content.setAttribute(
            Qt.WidgetAttribute.WA_StyledBackground, True
        )
        self.content.setAutoFillBackground(False)
        self.content.setStyleSheet("background: transparent;")

        self.scroll.viewport().setAutoFillBackground(False)
        self.scroll.viewport().setStyleSheet("background: transparent;")

        self.rows_layout = QVBoxLayout(self.content)
        self.rows_layout.setContentsMargins(2, 4, 6, 4)
        self.rows_layout.setSpacing(8)

        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll)

    def set_tracks(self, tracks, show_favorite=True):
        self._build_timer.stop()

        current_key = None
        if 0 <= self._current_row < len(self.tracks):
            current_key = self._selection_key(
                self.tracks[self._current_row]
            )

        if current_key is not None:
            self._selected_ids.add(current_key)

        self.tracks = list(tracks or [])
        available_keys = {
            self._selection_key(track)
            for track in self.tracks
        }
        self._selected_ids.intersection_update(available_keys)

        self.rows = []
        self._current_row = -1
        self.show_favorite = show_favorite
        self._build_index = 0
        self._pending_selected_key = current_key

        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if self.tracks:
            self._build_timer.start()
        else:
            self._selected_ids.clear()
            self._pending_selected_key = None
            self.rows_layout.addStretch()

    def _append_track_batch(self):
        end = min(
            self._build_index + self._build_batch_size,
            len(self.tracks)
        )

        for index in range(self._build_index, end):
            track = self.tracks[index]
            row = TrackListRow(
                track,
                show_favorite=self.show_favorite,
                library_style=self.library_style,
                icon_manager=self.icon_manager
            )
            row.metadata_clickable = self.metadata_clickable

            row.clicked.connect(
                lambda selected, r=row:
                    self.select_row(
                        selected,
                        self.rows.index(r),
                        r._selection_modifiers
                    )
            )
            row.play_requested.connect(self.play_requested.emit)
            row.metadata_clicked.connect(self.metadata_requested.emit)
            row.favorite_requested.connect(
                lambda track: self._handle_favorite_request(track)
            )
            row.context_requested.connect(
                lambda selected, position, r=row:
                    self._handle_context_request(r, selected, position)
            )

            self.rows.append(row)
            self.rows_layout.addWidget(row)

            key = self._selection_key(track)
            row.set_selected(key in self._selected_ids)

            if (
                self._pending_selected_key is not None
                and key == self._pending_selected_key
            ):
                self._current_row = index
                self._pending_selected_key = None

            elif (
                self._current_row == -1
                and key in self._selected_ids
            ):
                self._current_row = index

        self._build_index = end

        if end >= len(self.tracks):
            self._build_timer.stop()
            self._pending_selected_key = None
            self.rows_layout.addStretch()

    def update_track_favorite(self, track_id, is_favorite):
        updated = False

        for track in self.tracks:
            if track.get("id") == track_id:
                track["is_favorite"] = int(bool(is_favorite))
                updated = True

        for row in self.rows:
            if row.track.get("id") == track_id:
                row.set_favorite_state(is_favorite)
                updated = True

        return updated

    def insert_track(self, track, index):
        current_key = None

        if 0 <= self._current_row < len(self.tracks):
            current_key = self._selection_key(
                self.tracks[self._current_row]
            )

        index = max(0, min(index, len(self.tracks)))

        if self.rows_layout.count():
            last_item = self.rows_layout.itemAt(
                self.rows_layout.count() - 1
            )
            if last_item is not None and last_item.widget() is None:
                self.rows_layout.takeAt(
                    self.rows_layout.count() - 1
                )

        self.tracks.insert(index, track)

        row = TrackListRow(
            track,
            show_favorite=self.show_favorite,
            library_style=self.library_style,
            icon_manager=self.icon_manager
        )
        row.metadata_clickable = self.metadata_clickable

        row.clicked.connect(
            lambda selected, r=row:
                self.select_row(
                    selected,
                    self.rows.index(r),
                    r._selection_modifiers
                )
        )
        row.play_requested.connect(self.play_requested.emit)
        row.metadata_clicked.connect(self.metadata_requested.emit)
        row.favorite_requested.connect(
            lambda track: self._handle_favorite_request(track)
        )
        row.context_requested.connect(
            lambda selected, position, r=row:
                self._handle_context_request(r, selected, position)
        )

        self.rows.insert(index, row)
        self.rows_layout.insertWidget(index, row)

        self._current_row = next(
            (
                i for i, item in enumerate(self.tracks)
                if current_key is not None
                and self._selection_key(item) == current_key
            ),
            -1
        )

        for existing_row in self.rows:
            existing_row.set_selected(
                self._selection_key(existing_row.track)
                in self._selected_ids
            )

        self.rows_layout.addStretch()

    def remove_track(self, track_id):
        index = next(
            (
                i for i, track in enumerate(self.tracks)
                if track.get("id") == track_id
            ),
            -1
        )

        if index < 0 or index >= len(self.rows):
            return False

        current_key = None
        if 0 <= self._current_row < len(self.tracks):
            current_key = self._selection_key(
                self.tracks[self._current_row]
            )

        removed_track = self.tracks.pop(index)
        self._selected_ids.discard(
            self._selection_key(removed_track)
        )

        row = self.rows.pop(index)
        self.rows_layout.removeWidget(row)
        row.deleteLater()

        if current_key == self._selection_key(removed_track):
            self._current_row = -1
        else:
            self._current_row = next(
                (
                    i for i, track in enumerate(self.tracks)
                    if self._selection_key(track) == current_key
                ),
                -1
            )

        for existing_row in self.rows:
            existing_row.set_selected(
                self._selection_key(existing_row.track)
                in self._selected_ids
            )

        if not self.rows:
            self.rows_layout.addStretch()

        return True

    def _selection_key(self, track):
        if not track:
            return None

        entry_id = track.get("playlist_entry_id")
        if entry_id is not None:
            return ("playlist", entry_id)

        track_id = track.get("id")
        if track_id is not None:
            return ("track", track_id)

        return None

    def selected_tracks(self):
        return [
            track for track in self.tracks
            if self._selection_key(track) in self._selected_ids
        ]

    def select_row(self, track, index, modifiers=None):
        if not (0 <= index < len(self.tracks)):
            return

        modifiers = (
            modifiers
            if modifiers is not None
            else Qt.KeyboardModifier.NoModifier
        )

        key = self._selection_key(self.tracks[index])
        if key is None:
            return

        ctrl = bool(
            modifiers & Qt.KeyboardModifier.ControlModifier
        )
        shift = bool(
            modifiers & Qt.KeyboardModifier.ShiftModifier
        )

        if shift:
            anchor = self._selection_anchor
            if anchor is None or not (0 <= anchor < len(self.tracks)):
                anchor = index

            start, end = sorted((anchor, index))
            interval = {
                self._selection_key(item)
                for item in self.tracks[start:end + 1]
            }
            interval.discard(None)

            if ctrl:
                self._selected_ids.update(interval)
            else:
                self._selected_ids = interval

        elif ctrl:
            if key in self._selected_ids:
                self._selected_ids.remove(key)
            else:
                self._selected_ids.add(key)

            self._selection_anchor = index

        else:
            self._selected_ids = {key}
            self._selection_anchor = index

        self._current_row = index
        self._pending_selected_key = None
        self._pending_selected_id = None
        self._pending_selected_index = None

        for row in self.rows:
            row.set_selected(
                self._selection_key(row.track) in self._selected_ids
            )

        self.selection_changed.emit(track, index)

    def _handle_favorite_request(self, track):
        # Favoritar encerra qualquer seleção múltipla.
        self._selected_ids.clear()
        self._selection_anchor = None
        self._current_row = -1
        self._pending_selected_key = None
        self._pending_selected_id = None
        self._pending_selected_index = None

        for row in self.rows:
            row.set_selected(False)

        self.favorite_requested.emit(track)

    def _handle_context_request(self, row_widget, track, position):
        try:
            index = self.rows.index(row_widget)
        except ValueError:
            return

        key = self._selection_key(track)

        if key not in self._selected_ids:
            self._selected_ids = {key}
            self._selection_anchor = index

        self._current_row = index

        for row in self.rows:
            row.set_selected(
                self._selection_key(row.track) in self._selected_ids
            )

        self.context_requested.emit(
            self.selected_tracks(),
            position
        )

    def currentRow(self):
        return self._current_row

    def setCurrentRow(self, index):
        if not 0 <= index < len(self.tracks):
            return

        self._current_row = index
        key = self._selection_key(self.tracks[index])

        self._selected_ids = {key} if key is not None else set()
        self._selection_anchor = index
        self._pending_selected_key = (
            key if index >= len(self.rows) else None
        )

        for row in self.rows:
            row.set_selected(
                self._selection_key(row.track) in self._selected_ids
            )

class HomeAlbumBanner(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._covers = []
        self._cover_paths = []
        self._tiles = []
        self._last_changed_tile = None

        self.setMinimumWidth(300)

        self.change_timer = QTimer(self)
        self.change_timer.setInterval(1100)
        self.change_timer.timeout.connect(
            self.change_random_tile
        )

        self.motion_timer = QTimer(self)
        self.motion_timer.setInterval(30)
        self.motion_timer.timeout.connect(
            self.update_tile_animations
        )

    def set_albums(self, albums):
        paths = []
        seen = set()

        for album in albums:
            path = str(album.get("cover_path") or "").strip()

            if (
                not path
                or path in seen
                or not os.path.isfile(path)
            ):
                continue

            seen.add(path)
            paths.append(path)

        if paths == self._cover_paths:
            return

        covers = []

        for path in paths:
            pixmap = QPixmap(path)

            if not pixmap.isNull():
                covers.append(pixmap)

        self.change_timer.stop()
        self.motion_timer.stop()

        self._covers = covers
        self._cover_paths = paths
        self._last_changed_tile = None

        self.create_tiles()

        if len(self._covers) > 1 and self._tiles:
            self.change_timer.start()
            self.motion_timer.start()

        self.update()

    def create_tiles(self):
        self._tiles = []

        if not self._covers:
            return

        unit = max(1, round(self.height() / 4))
        columns = max(1, (self.width() + unit - 1) // unit)

        def add_tile(column, row, span):
            rect = QRect(
                column * unit + 2,
                row * unit + 2,
                span * unit - 4,
                span * unit - 4
            )

            cover_index = random.randrange(len(self._covers))

            self._tiles.append({
                "rect": rect,
                "pixmap": self._covers[cover_index],
                "cover_index": cover_index,
                "opacity": 1.0,
                "direction": 0
            })

        column = 0

        while column + 4 <= columns:
            pattern = random.choice(("large", "medium", "small"))

            if pattern == "large":
                add_tile(column, 0, 4)

            elif pattern == "medium":
                add_tile(column, 0, 2)
                add_tile(column + 2, 0, 2)
                add_tile(column, 2, 2)
                add_tile(column + 2, 2, 2)

            else:
                for row in range(4):
                    for offset in range(4):
                        add_tile(column + offset, row, 1)

            column += 4

        remaining = columns - column

        if remaining >= 2:
            add_tile(column, 0, 2)
            add_tile(column, 2, 2)
            column += 2
            remaining -= 2

        if remaining == 1:
            for row in range(4):
                add_tile(column, row, 1)

    def change_random_tile(self):
        if len(self._tiles) < 1 or len(self._covers) < 2:
            return

        available = [
            index
            for index, tile in enumerate(self._tiles)
            if tile["direction"] == 0
            and index != self._last_changed_tile
        ]

        if not available:
            return

        index = random.choice(available)
        tile = self._tiles[index]

        tile["direction"] = -1
        self._last_changed_tile = index

    def update_tile_animations(self):
        changed = False

        for tile in self._tiles:
            direction = tile["direction"]

            if direction == 0:
                continue

            tile["opacity"] += direction * 0.055

            if tile["opacity"] <= 0:
                current_index = tile["cover_index"]

                choices = [
                    index
                    for index in range(len(self._covers))
                    if index != current_index
                ]

                if choices:
                    new_index = random.choice(choices)
                    tile["cover_index"] = new_index
                    tile["pixmap"] = self._covers[new_index]

                tile["opacity"] = 0.0
                tile["direction"] = 1

            elif tile["opacity"] >= 1:
                tile["opacity"] = 1.0
                tile["direction"] = 0

            changed = True

        if changed:
            self.update()

        elif not any(
            tile["direction"] != 0
            for tile in self._tiles
        ):
            self.motion_timer.stop()

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if not self._covers:
            return

        self.create_tiles()

        if len(self._covers) > 1 and self._tiles:
            if not self.change_timer.isActive():
                self.change_timer.start()

            if not self.motion_timer.isActive():
                self.motion_timer.start()

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )
        painter.setRenderHint(
            QPainter.RenderHint.SmoothPixmapTransform
        )

        path = QPainterPath()
        path.addRoundedRect(
            QRectF(self.rect()),
            18,
            18
        )

        painter.setClipPath(path)

        background = QLinearGradient(
            0,
            0,
            self.width(),
            self.height()
        )
        background.setColorAt(0.0, QColor("#393044"))
        background.setColorAt(0.5, QColor("#292433"))
        background.setColorAt(1.0, QColor("#211e2a"))

        painter.fillRect(self.rect(), background)

        for tile in self._tiles:
            rect = tile["rect"]
            pixmap = tile["pixmap"]

            if pixmap.isNull():
                continue

            scaled = pixmap.scaled(
                rect.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )

            source_x = max(
                0,
                (scaled.width() - rect.width()) // 2
            )
            source_y = max(
                0,
                (scaled.height() - rect.height()) // 2
            )

            source = QRect(
                source_x,
                source_y,
                rect.width(),
                rect.height()
            )

            painter.setOpacity(tile["opacity"])
            painter.drawPixmap(
                rect,
                scaled,
                source
            )

        painter.setOpacity(1.0)

        overlay = QLinearGradient(
            0,
            0,
            self.width(),
            0
        )
        overlay.setColorAt(0.0, QColor(10, 8, 15, 215))
        overlay.setColorAt(0.55, QColor(10, 8, 15, 185))
        overlay.setColorAt(1.0, QColor(10, 8, 15, 165))

        painter.fillRect(self.rect(), overlay)
        painter.end()


class HomeView(QWidget):
    shortcut_requested = Signal(str)
    search_requested = Signal()

    def __init__(self, scanner=None, language="pt_BR", icon_manager=None):
        super().__init__()

        self.language = language
        self.scanner = scanner
        self.icon_manager = icon_manager
        self.parent_window = None
        self._is_dirty = True

        self.album_cards = []
        self.artist_cards = []

        self.active_album_card = None
        self.active_artist_card = None

        self.most_played_rows = []
        self.recent_rows = []

        self.setObjectName("homeView")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 28)
        layout.setSpacing(26)

        # --------------------------------------------------
        # BANNER DE CAPAS
        # --------------------------------------------------

        self.hero_banner = HomeAlbumBanner()
        self.hero_banner.setFixedHeight(220)

        banner_layout = QVBoxLayout(self.hero_banner)
        banner_layout.setContentsMargins(30, 18, 30, 22)
        banner_layout.setSpacing(0)

        top_row = QHBoxLayout()
        top_row.addStretch()

        self.search_button = QPushButton(tr("home.search", self.language))
        self.search_button.setObjectName("searchButton")
        self.search_button.setFixedSize(130, 38)
        self.search_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        _set_theme_stylesheet(self.search_button, """
            QPushButton#searchButton {
                background: #49375f;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 12px;
                color: #f2eafa;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton#searchButton:hover {
                background: #594675;
            }
        """)

        self.search_button.clicked.connect(
            self.search_requested.emit
        )

        top_row.addWidget(self.search_button)
        banner_layout.addLayout(top_row)
        banner_layout.addStretch()

        welcome = QVBoxLayout()
        welcome.setSpacing(2)

        self.greeting_label = QLabel()
        self.greeting_label.setObjectName("pageTitle")

        subtitle = QLabel(tr("home.subtitle", self.language))
        subtitle.setObjectName("pageSubtitle")

        welcome.addWidget(self.greeting_label)
        welcome.addWidget(subtitle)

        banner_layout.addLayout(welcome)
        layout.addWidget(self.hero_banner)

        self.update_greeting()

        # --------------------------------------------------
        # MAIS TOCADAS / RECÉM-ADICIONADAS
        # --------------------------------------------------

        activity_layout = QGridLayout()
        activity_layout.setHorizontalSpacing(24)
        activity_layout.setVerticalSpacing(12)

        most_column = QVBoxLayout()
        most_column.setSpacing(10)

        most_title = QLabel(tr("home.most_played", self.language))
        most_title.setObjectName("sectionTitle")
        most_column.addWidget(most_title)

        most_tracks_label = QLabel(tr("home.tracks", self.language))
        most_tracks_label.setObjectName("pageSubtitle")
        most_column.addWidget(most_tracks_label)

        self.most_played_layout = QVBoxLayout()
        self.most_played_layout.setSpacing(6)
        most_column.addLayout(self.most_played_layout)

        recent_column = QVBoxLayout()
        recent_column.setSpacing(10)

        recent_title = QLabel(tr("home.recently_added", self.language))
        recent_title.setObjectName("sectionTitle")
        recent_column.addWidget(recent_title)

        recent_tracks_label = QLabel(tr("home.tracks", self.language))
        recent_tracks_label.setObjectName("pageSubtitle")
        recent_column.addWidget(recent_tracks_label)

        self.recent_tracks_layout = QVBoxLayout()
        self.recent_tracks_layout.setSpacing(6)
        recent_column.addLayout(self.recent_tracks_layout)

        recent_albums_label = QLabel(tr("home.albums", self.language))
        recent_albums_label.setObjectName("pageSubtitle")
        recent_column.addWidget(recent_albums_label)

        self.recent_albums_layout = QVBoxLayout()
        self.recent_albums_layout.setSpacing(6)
        recent_column.addLayout(self.recent_albums_layout)

        activity_layout.addLayout(
            most_column, 0, 0,
            Qt.AlignmentFlag.AlignTop
        )
        activity_layout.addLayout(
            recent_column, 0, 1,
            Qt.AlignmentFlag.AlignTop
        )

        layout.addLayout(activity_layout)

        # --------------------------------------------------
        # ÁLBUNS MAIS TOCADOS
        # --------------------------------------------------

        album_header = QHBoxLayout()

        album_title = QLabel(tr("home.most_played_albums", self.language))
        album_title.setObjectName("sectionTitle")

        album_header.addWidget(album_title)
        album_header.addStretch()

        layout.addLayout(album_header)

        self.albums_layout = FlowLayout(
            min_horizontal_spacing=16,
            vertical_spacing=24
        )

        layout.addLayout(self.albums_layout)

        # --------------------------------------------------
        # ARTISTAS MAIS TOCADOS
        # --------------------------------------------------

        artist_header = QHBoxLayout()

        artist_title = QLabel(tr("home.most_played_artists", self.language))
        artist_title.setObjectName("sectionTitle")

        artist_header.addWidget(artist_title)
        artist_header.addStretch()

        layout.addLayout(artist_header)

        self.artists_layout = FlowLayout(
            min_horizontal_spacing=16,
            vertical_spacing=24
        )

        layout.addLayout(self.artists_layout)
        layout.addStretch()

    # ======================================================
    # NAVEGAÇÃO
    # ======================================================

    def set_parent_window(self, parent):
        self.parent_window = parent

        self.shortcut_requested.connect(
            self.navigate_shortcut
        )

        self.search_requested.connect(
            self.parent_window.open_global_search
        )

        self.refresh()

    def navigate_shortcut(self, target):
        if self.parent_window is None:
            return

        if target == "playlists":
            self.parent_window.show_playlists()
            return

        tab_indexes = {
            "artists": 0,
            "albums": 1,
            "tracks": 3,
        }

        index = tab_indexes.get(target)

        if index is not None:
            self.parent_window.show_library(index)

    # ======================================================
    # SAUDAÇÃO
    # ======================================================

    def update_greeting(self):
        hour = datetime.now().hour

        if 6 <= hour < 12:
            greeting_key = "home.greeting.morning"
        elif 12 <= hour < 18:
            greeting_key = "home.greeting.afternoon"
        elif 18 <= hour < 24:
            greeting_key = "home.greeting.evening"
        else:
            greeting_key = "home.greeting.night"

        greeting = tr(greeting_key, self.language)

        if self.parent_window is not None:
            display_name = self.parent_window.get_display_name()
        else:
            display_name = getpass.getuser().strip()
            if display_name:
                display_name = display_name[:1].upper() + display_name[1:]

        greeting = greeting.rstrip("!")

        if display_name:
            greeting = f"{greeting}, {display_name}!"

        self.greeting_label.setText(greeting)

    # ======================================================
    # UTILITÁRIOS
    # ======================================================

    def clear_layout(self, target_layout):
        while target_layout.count():
            item = target_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def empty_label(self, text):
        label = QLabel(text)
        label.setObjectName("pageSubtitle")
        label.setWordWrap(True)
        return label

    def album_key(self, album):
        return (
            (album.get("album") or "").strip().casefold(),
            (album.get("artist") or "").strip().casefold()
        )

    # ======================================================
    # ATUALIZAÇÃO GERAL
    # ======================================================

    def invalidate(self):
        self._is_dirty = True

    def refresh_if_needed(self):
        self.update_greeting()

        if self._is_dirty:
            self.refresh()

    def refresh(self):
        self.update_greeting()

        parent = self.parent_window

        if (
            self.scanner is None
            or parent is None
            or not getattr(parent, "library_access_ready", False)
        ):
            self.hero_banner.set_albums([])
            self.refresh_most_played([])
            self.refresh_recent([], [])
            self.refresh_albums([])
            self.refresh_artists([])
            self._is_dirty = False
            return

        tracks = [
            track
            for track in self.scanner.list_tracks(limit=None)
            if parent._track_is_available(track)
        ]

        allowed_albums = {
            (
                (track.get("album") or "").strip().casefold(),
                (
                    track.get("album_artist")
                    or track.get("artist")
                    or "Artista desconhecido"
                ).strip().casefold()
            )
            for track in tracks
            if (track.get("album") or "").strip()
        }

        all_albums = [
            album
            for album in self.scanner.list_albums()
            if self.album_key(album) in allowed_albums
        ]

        self.hero_banner.set_albums(all_albums)

        allowed_artists = {
            (
                track.get("artist")
                or track.get("album_artist")
                or "Artista desconhecido"
            ).strip().casefold()
            for track in tracks
        }

        most_played = [
            track
            for track in self.scanner.list_most_played_tracks(100)
            if parent._track_is_available(track)
        ][:7]

        recent_tracks = [
            track
            for track in self.scanner.list_recent_tracks(100)
            if parent._track_is_available(track)
        ][:3]

        recent_albums = [
            album
            for album in self.scanner.list_recent_albums(100)
            if self.album_key(album) in allowed_albums
        ][:3]

        most_played_albums = [
            album
            for album in self.scanner.list_most_played_albums(100)
            if self.album_key(album) in allowed_albums
        ][:8]

        most_played_artists = [
            artist
            for artist in self.scanner.list_most_played_artists(100)
            if (artist.get("name") or "").strip().casefold()
            in allowed_artists
        ][:8]

        self.refresh_most_played(most_played)
        self.refresh_recent(recent_tracks, recent_albums)
        self.refresh_albums(most_played_albums)
        self.refresh_artists(most_played_artists)

        self._is_dirty = False

    # ======================================================
    # MAIS TOCADAS
    # ======================================================

    def refresh_most_played(self, tracks):
        self.clear_layout(self.most_played_layout)
        self.most_played_rows = []

        if not tracks:
            self.most_played_layout.addWidget(
                self.empty_label(
                    "Suas músicas mais reproduzidas aparecerão aqui."
                )
            )
            return

        parent = self.parent_window

        for track in tracks:
            row = HomeTrackRow(track, "track")

            if parent is not None:
                row.clicked.connect(
                    lambda item, kind, context=tracks:
                        parent.play_track_data(
                            item,
                            context_tracks=context
                        )
                )

                row.metadata_clicked.connect(
                    lambda item, kind:
                        parent.open_artist_page(
                            item.get("artist")
                            or item.get("album_artist")
                        )
                )

                row.play_requested.connect(
                    lambda item, kind, context=tracks:
                        parent.play_track_data(
                            item,
                            context_tracks=context
                        )
                )

            self.most_played_rows.append(row)
            self.most_played_layout.addWidget(row)

    # ======================================================
    # RECÉM-ADICIONADAS
    # ======================================================

    def refresh_recent(self, tracks, albums):
        self.clear_layout(self.recent_tracks_layout)
        self.clear_layout(self.recent_albums_layout)

        self.recent_rows = []

        parent = self.parent_window

        if tracks:
            for track in tracks:
                row = HomeTrackRow(track, "track")

                if parent is not None:
                    row.clicked.connect(
                        lambda item, kind, context=tracks:
                            parent.play_track_data(
                                item,
                                context_tracks=context
                            )
                    )

                    row.metadata_clicked.connect(
                        lambda item, kind:
                            parent.open_artist_page(
                                item.get("artist")
                                or item.get("album_artist")
                            )
                    )

                    row.play_requested.connect(
                        lambda item, kind, context=tracks:
                            parent.play_track_data(
                                item,
                                context_tracks=context
                            )
                    )

                self.recent_rows.append(row)
                self.recent_tracks_layout.addWidget(row)
        else:
            self.recent_tracks_layout.addWidget(
                self.empty_label("Nenhuma faixa recente.")
            )

        if albums:
            for album in albums:
                row = HomeTrackRow(album, "album")

                if parent is not None:
                    row.clicked.connect(
                        lambda item, kind:
                            parent.open_album_page(
                                item.get("album"),
                                item.get("artist")
                            )
                    )

                    row.metadata_clicked.connect(
                        lambda item, kind:
                            parent.open_artist_page(
                                item.get("artist")
                                or item.get("album_artist")
                            )
                    )

                    row.play_requested.connect(
                        lambda item, kind:
                            parent.play_album(
                                item.get("album"),
                                item.get("artist")
                            )
                    )

                self.recent_rows.append(row)
                self.recent_albums_layout.addWidget(row)
        else:
            self.recent_albums_layout.addWidget(
                self.empty_label("Nenhum álbum recente.")
            )

    # ======================================================
    # ÁLBUNS MAIS TOCADOS
    # ======================================================

    def refresh_albums(self, albums=None):
        if albums is None:
            albums = (
                self.scanner.list_most_played_albums(100)
                if self.scanner is not None else []
            )

            parent = self.parent_window

            if parent is not None:
                if parent.library_access_ready:
                    tracks = [
                        track
                        for track in self.scanner.list_tracks(limit=None)
                        if parent._track_is_available(track)
                    ]

                    allowed = {
                        (
                            (track.get("album") or "").strip().casefold(),
                            (
                                track.get("album_artist")
                                or track.get("artist")
                                or "Artista desconhecido"
                            ).strip().casefold()
                        )
                        for track in tracks
                    }

                    albums = [
                        album for album in albums
                        if self.album_key(album) in allowed
                    ]
                else:
                    albums = []

        albums = albums[:8]

        self.clear_layout(self.albums_layout)

        self.album_cards = []
        self.active_album_card = None

        gradients = [
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #8d596d,stop:1 #38283d)",
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #537d85,stop:1 #243a4b)",
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #78634f,stop:1 #332b31)",
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #496c75,stop:1 #182c38)",
        ]

        if not albums:
            self.albums_layout.addWidget(
                self.empty_label(
                    "As capas dos álbuns mais reproduzidos aparecerão aqui."
                )
            )
            return

        for index, album in enumerate(albums):
            card = AlbumCard(
                title=album.get("album", "Álbum desconhecido"),
                artist=album.get("artist", "Artista desconhecido"),
                cover_path=album.get("cover_path"),
                gradient=gradients[index % len(gradients)]
            )

            card.hover_changed.connect(
                self.update_album_hover_state
            )

            if self.parent_window is not None:
                card.clicked.connect(
                    self.parent_window.open_album_page
                )
                card.play_requested.connect(
                    self.parent_window.play_album
                )
                card.context_requested.connect(
                    self.parent_window.show_album_context_menu
                )

            self.album_cards.append(card)
            self.albums_layout.addWidget(card)

    # ======================================================
    # ARTISTAS MAIS TOCADOS
    # ======================================================

    def refresh_artists(self, artists=None):
        if artists is None:
            artists = (
                self.scanner.list_most_played_artists(100)
                if self.scanner is not None else []
            )

        artists = artists[:8]

        self.clear_layout(self.artists_layout)

        self.artist_cards = []
        self.active_artist_card = None

        gradients = [
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #8d596d,stop:1 #38283d)",
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #537d85,stop:1 #243a4b)",
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #78634f,stop:1 #332b31)",
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #496c75,stop:1 #182c38)",
        ]

        if not artists:
            self.artists_layout.addWidget(
                self.empty_label(
                    "Os artistas mais reproduzidos aparecerão aqui."
                )
            )
            return

        for index, artist in enumerate(artists):
            card = ArtistCard(
                name=artist.get("name", "Artista desconhecido"),
                cover_path=artist.get("cover_path"),
                gradient=gradients[index % len(gradients)]
            )

            card.hover_changed.connect(
                self.update_artist_hover_state
            )

            if self.parent_window is not None:
                card.clicked.connect(
                    self.parent_window.open_artist_page
                )
                card.play_requested.connect(
                    self.parent_window.play_artist
                )

            self.artist_cards.append(card)
            self.artists_layout.addWidget(card)

    # ======================================================
    # HOVER DOS CARDS
    # ======================================================

    def update_album_hover_state(self, active_card, hovered):
        if hovered:
            self.active_album_card = active_card
        elif self.active_album_card is active_card:
            self.active_album_card = None

        for card in self.album_cards:
            card.set_dimmed(
                self.active_album_card is not None
                and card is not self.active_album_card
            )

    def update_artist_hover_state(self, active_card, hovered):
        if hovered:
            self.active_artist_card = active_card
        elif self.active_artist_card is active_card:
            self.active_artist_card = None

        for card in self.artist_cards:
            card.set_dimmed(
                self.active_artist_card is not None
                and card is not self.active_artist_card
            )






# --------------------------------------------------
# LIBRARY VIEW
# --------------------------------------------------

SERIFA_TRACK_MIME = "application/x-serifaplayer-track"
SERIFA_ALBUM_MIME = "application/x-serifaplayer-album"
SERIFA_PLAYLIST_MIME = "application/x-serifaplayer-playlist"

def create_track_drag_preview(track):
    width, height = 300, 76
    preview = QPixmap(width, height)
    preview.fill(Qt.GlobalColor.transparent)

    painter = QPainter(preview)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setOpacity(0.68)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(35, 30, 46, 245))
    painter.drawRoundedRect(
        QRectF(0, 0, width, height),
        12,
        12
    )

    painter.setBrush(QColor(125, 84, 164, 235))
    painter.drawRoundedRect(
        QRectF(10, 10, 56, 56),
        9,
        9
    )

    painter.setPen(QColor("#ffffff"))
    painter.drawText(
        QRectF(10, 10, 56, 56),
        Qt.AlignmentFlag.AlignCenter,
        "♫"
    )

    title = str(track.get("title") or "Faixa desconhecida")
    artist = str(track.get("artist") or "Artista desconhecido")

    painter.setPen(QColor("#ffffff"))
    painter.drawText(
        QRectF(78, 11, 210, 27),
        Qt.AlignmentFlag.AlignVCenter
        | Qt.AlignmentFlag.AlignLeft,
        title
    )

    painter.setPen(QColor(190, 180, 205))
    painter.drawText(
        QRectF(78, 38, 210, 25),
        Qt.AlignmentFlag.AlignVCenter
        | Qt.AlignmentFlag.AlignLeft,
        artist
    )

    painter.end()
    return preview



class LibraryTrackTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drag_data_provider = None
        self.setDragEnabled(True)
        self.setDragDropMode(
            QAbstractItemView.DragDropMode.DragOnly
        )
        self.setDefaultDropAction(Qt.DropAction.CopyAction)

    def startDrag(self, supportedActions):
        if not self.drag_data_provider:
            return

        row = self.currentRow()
        track = self.drag_data_provider(row)

        if not track:
            return

        track_id = track.get("id")
        if track_id is None:
            return

        mime_data = QMimeData()
        payload = json.dumps({
            "id": int(track_id)
        }).encode("utf-8")

        mime_data.setData(SERIFA_TRACK_MIME, payload)

        drag = QDrag(self)
        drag.setMimeData(mime_data)

        drag.setPixmap(create_track_drag_preview(track))
        drag.setHotSpot(QPoint(20, 22))

        drag.exec(Qt.DropAction.CopyAction)


class PlaylistDragList(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setDragEnabled(True)
        self.setDragDropMode(
            QAbstractItemView.DragDropMode.DragOnly
        )
        self.setDefaultDropAction(Qt.DropAction.CopyAction)

    def startDrag(self, supportedActions):
        item = self.currentItem()

        if item is None:
            return

        playlist_id = item.data(
            Qt.ItemDataRole.UserRole
        )

        if playlist_id is None:
            return

        try:
            playlist_id = int(playlist_id)
        except (TypeError, ValueError):
            return

        mime_data = QMimeData()
        payload = json.dumps({
            "id": playlist_id
        }).encode("utf-8")

        mime_data.setData(
            SERIFA_PLAYLIST_MIME,
            payload
        )

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.CopyAction)


class PlaylistFolderCard(QFrame):
    clicked = Signal(int)
    context_requested = Signal(int, object)
    playlist_dropped = Signal(int, int)

    def __init__(self, folder_id, name, subtitle, icon_manager=None):
        super().__init__()

        self.folder_id = int(folder_id)
        self.name = str(name)

        self.setObjectName("playlistFolderCard")
        self.setFixedWidth(213)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        _set_theme_stylesheet(self, """
            QFrame#playlistFolderCard {
                background: rgba(255, 255, 255, 0.035);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 14px;
            }
            QFrame#playlistFolderCard:hover {
                background: rgba(255, 255, 255, 0.075);
                border: 1px solid rgba(255, 255, 255, 0.16);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        cover = QFrame()
        cover.setFixedSize(193, 193)
        _set_theme_stylesheet(cover, """
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #66547f,
                    stop:1 #30283f
                );
                border: none;
                border-radius: 10px;
            }
        """)

        cover_layout = QVBoxLayout(cover)
        cover_layout.setContentsMargins(0, 0, 0, 0)

        icon = QLabel()
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if icon_manager is not None:
            icon.setPixmap(
                icon_manager.icon(
                    "library.folder"
                ).pixmap(QSize(76, 76))
            )
        _set_theme_stylesheet(icon, "background: transparent; border: none;"
        )

        cover_layout.addWidget(icon)
        layout.addWidget(cover)

        title = QLabel(self.name)
        title.setObjectName("cardTitle")
        title.setWordWrap(False)
        title.setToolTip(self.name)
        layout.addWidget(title)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("cardSubtitle")
        subtitle_label.setWordWrap(False)
        layout.addWidget(subtitle_label)

        # Os filhos visuais também recebem eventos de arraste.
        self._drop_targets = [
            cover,
            icon,
            title,
            subtitle_label
        ]

        for target in self._drop_targets:
            target.setAcceptDrops(True)
            target.installEventFilter(self)

    def _accept_playlist_drag(self, event):
        if event.mimeData().hasFormat(SERIFA_PLAYLIST_MIME):
            event.acceptProposedAction()
            return True

        event.ignore()
        return False

    def _drop_playlist_drag(self, event):
        if not event.mimeData().hasFormat(SERIFA_PLAYLIST_MIME):
            event.ignore()
            return False

        try:
            payload = bytes(
                event.mimeData().data(SERIFA_PLAYLIST_MIME)
            )

            data = json.loads(payload.decode("utf-8"))
            playlist_id = int(data["id"])

        except (ValueError, TypeError, KeyError, UnicodeDecodeError):
            event.ignore()
            return False

        if playlist_id <= 0:
            event.ignore()
            return False

        self.playlist_dropped.emit(
            playlist_id,
            self.folder_id
        )

        event.acceptProposedAction()
        return True

    def eventFilter(self, watched, event):
        if watched in self._drop_targets:
            if event.type() == QEvent.Type.DragEnter:
                self._accept_playlist_drag(event)
                return True

            if event.type() == QEvent.Type.DragMove:
                self._accept_playlist_drag(event)
                return True

            if event.type() == QEvent.Type.Drop:
                self._drop_playlist_drag(event)
                return True

        return super().eventFilter(watched, event)

    def dragEnterEvent(self, event):
        self._accept_playlist_drag(event)

    def dragMoveEvent(self, event):
        self._accept_playlist_drag(event)

    def dropEvent(self, event):
        self._drop_playlist_drag(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.context_requested.emit(
                self.folder_id,
                event.globalPosition().toPoint()
            )
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.folder_id)
            event.accept()
            return

        super().mouseReleaseEvent(event)


class LibraryView(QWidget):
    def __init__(self, scanner, import_view):
        super().__init__()

        self.scanner = scanner
        self.import_view = import_view
        self.parent_window = import_view.parent_window
        self.language = self.parent_window.interface_language
        self._available_tracks_cache = None

        self._pending_album_data = []
        self._pending_album_index = 0
        self._pending_album_gradients = []

        self._album_load_timer = QTimer(self)
        self._album_load_timer.setInterval(10)
        self._album_load_timer.timeout.connect(
            self._add_album_cards_batch
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 28)
        layout.setSpacing(24)

        header = QVBoxLayout()
        header.setSpacing(5)

        header_top = QHBoxLayout()
        header_top.setSpacing(12)

        title = QLabel(tr("library.title", self.language))
        title.setObjectName("pageTitle")

        header_top.addWidget(title)
        header_top.addStretch()

        self.search_button = QPushButton(
            tr("home.search", self.language)
        )
        self.search_button.setObjectName("searchButton")
        self.search_button.setFixedSize(130, 38)
        self.search_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        _set_theme_stylesheet(self.search_button, """
            QPushButton#searchButton {
                background: #49375f;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 12px;
                color: #f2eafa;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton#searchButton:hover {
                background: #594675;
            }
        """)
        self.search_button.clicked.connect(
            self.parent_window.open_global_search
        )
        header_top.addWidget(self.search_button)

        subtitle = QLabel(tr("library.subtitle", self.language))
        subtitle.setObjectName("pageSubtitle")

        header.addLayout(header_top)
        header.addWidget(subtitle)

        layout.addLayout(header)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("libraryTabs")

        self.create_artists_tab()
        self.create_albums_tab()
        self.create_playlists_tab()
        self.create_tracks_tab()


        layout.addWidget(self.tabs)

        _set_theme_stylesheet(self, """
            QTabWidget#libraryTabs::pane {
                border: none;
                background: transparent;
                top: -1px;
            }

            QTabBar::tab {
                background: #211e2a;
                color: #aaa4b5;
                padding: 11px 20px;
                margin-right: 8px;
                border-radius: 8px;
            }

            QTabBar::tab:selected {
                background: #B6F23A;
                color: #211e2a;
            }

            QTableWidget {
                background: #211e2a;
                alternate-background-color: #272330;
                color: #eeeaf3;
                border: none;
                border-radius: 10px;
                selection-background-color: #49375f;
                selection-color: white;
            }

            QListWidget#playlistList {
                background: #211e2a;
                color: #eeeaf3;
                border: none;
                border-radius: 10px;
                outline: none;
                padding: 6px;
            }

            QListWidget#playlistList::item {
                background: #292532;
                border: 1px solid #393243;
                border-radius: 9px;
                padding: 12px;
                margin: 2px 0;
            }

            QListWidget#playlistList::item:hover {
                background: #332b40;
                border-color: #59466f;
            }

            QListWidget#playlistList::item:selected {
                background: #49375f;
                border-color: #76599a;
                color: white;
            }

            QHeaderView::section {
                background: #2b2735;
                color: #aaa4b5;
                border: none;
                padding: 12px;
                font-weight: bold;
            }

            QTableWidget::item {
                padding: 8px;
                border: none;
            }
        """)

        self._tab_dirty = {
            0: True,
            1: True,
            2: True,
            3: True,
        }

        self.tabs.currentChanged.connect(self.refresh_tab)
        self.tabs.currentChanged.connect(
            self.update_search_button_visibility
        )

        self.update_search_button_visibility(
            self.tabs.currentIndex()
        )

        self.refresh_tab(self.tabs.currentIndex())

    def create_tracks_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 18, 0, 0)
        layout.setSpacing(12)

        self.sort_key = "artist"
        self.sort_ascending = True

        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        self.track_count_label = QLabel(
            tr("library.count.many", self.language).format(count=0)
        )
        self.track_count_label.setObjectName("pageSubtitle")
        header_layout.addWidget(self.track_count_label)
        header_layout.addStretch()

        self.tracks_sort_button = QPushButton(
            tr("favorites.sort", self.language).format(
                label=tr("favorites.sort.artist", self.language),
                direction="↑"
            )
        )
        self.tracks_sort_button.setObjectName("sortButton")
        self.tracks_sort_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.tracks_sort_button.clicked.connect(
            self.show_tracks_sort_menu
        )
        header_layout.addWidget(self.tracks_sort_button)
        layout.addLayout(header_layout)

        self.tracks_table = VirtualTrackList(
            SERIFA_TRACK_MIME,
            create_track_drag_preview,
            icon_manager=getattr(
                getattr(self.parent_window, "appearance", None),
                "icon_manager",
                None
            )
        )
        self.tracks_table.metadata_clickable = False
        self.tracks_table.delegate.library_all_tracks_style = True
        layout.addWidget(self.tracks_table)

        self.tabs.addTab(page, tr("library.tab.tracks", self.language))

    def create_albums_tab(self):

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 18, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        _set_theme_stylesheet(
            scroll,
            "QScrollArea { background: transparent; border: none; }"
        )
        _set_shortcuts_scrollbar(scroll)

        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.albums_content = QWidget()

        self.albums_layout = FlowLayout(
            self.albums_content,
            min_horizontal_spacing=16,
            vertical_spacing=24
        )

        scroll.setWidget(self.albums_content)
        layout.addWidget(scroll)

        self.tabs.addTab(page, tr("library.tab.albums", self.language))

    def create_artists_tab(self):

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 18, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        _set_theme_stylesheet(
            scroll,
            "QScrollArea { background: transparent; border: none; }"
        )
        _set_shortcuts_scrollbar(scroll)

        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.artists_content = QWidget()

        self.artists_layout = FlowLayout(
            self.artists_content,
            min_horizontal_spacing=16,
            vertical_spacing=24
        )

        scroll.setWidget(self.artists_content)
        layout.addWidget(scroll)

        self.tabs.addTab(page, tr("library.tab.artists", self.language))

    def create_playlists_tab(self):

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 18, 0, 0)
        layout.setSpacing(14)

        self.playlist_stack = QStackedWidget()

        # ------------------------------------------
        # VISÃO GERAL
        # ------------------------------------------

        list_page = QWidget()
        list_layout = QVBoxLayout(list_page)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(14)

        header = QHBoxLayout()

        title = QLabel(tr("playlist.title", self.language))
        title.setObjectName("sectionTitle")

        self.new_playlist_button = QPushButton(
            tr("playlist.new", self.language)
        )
        self.new_playlist_button.setObjectName("primaryButton")
        self.new_playlist_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.new_playlist_button)
        list_layout.addLayout(header)

        self.new_playlist_menu = QMenu(self)

        create_playlist_action = self.new_playlist_menu.addAction(
            tr("playlist.new.playlist", self.language)
        )
        create_folder_action = self.new_playlist_menu.addAction(
            tr("playlist.new.folder", self.language)
        )

        create_playlist_action.triggered.connect(
            self.create_playlist_dialog
        )
        create_folder_action.triggered.connect(
            self.create_playlist_folder_dialog
        )

        self.new_playlist_button.clicked.connect(
            self.show_new_playlist_menu
        )

        self.playlist_cards = []
        self.folder_cards = []
        self.active_playlist_card = None
        self.current_folder_id = None
        self.current_folder_name = None

        playlists_scroll = QScrollArea()
        playlists_scroll.setWidgetResizable(True)
        playlists_scroll.setFrameShape(QFrame.Shape.NoFrame)
        playlists_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        _set_theme_stylesheet(playlists_scroll, "QScrollArea { background: transparent; border: none; }"
        )
        _set_shortcuts_scrollbar(playlists_scroll)

        self.playlists_content = QWidget()
        self.playlists_layout = FlowLayout(
            self.playlists_content,
            min_horizontal_spacing=16,
            vertical_spacing=24
        )

        playlists_scroll.setWidget(self.playlists_content)
        list_layout.addWidget(playlists_scroll, 1)

        # ------------------------------------------
        # CONTEÚDO DA PASTA
        # ------------------------------------------

        folder_page = QWidget()
        folder_layout = QVBoxLayout(folder_page)
        folder_layout.setContentsMargins(0, 0, 0, 0)
        folder_layout.setSpacing(14)

        folder_header = QHBoxLayout()

        self.folder_back_button = QPushButton(
            tr("playlist.folder.back", self.language)
        )
        self.folder_back_button.setObjectName("backButton")
        apply_back_button_style(self.folder_back_button)
        self.folder_back_button.setFixedHeight(38)
        self.folder_back_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.folder_back_button.clicked.connect(
            self.close_folder
        )

        self.folder_detail_title = QLabel("")
        self.folder_detail_title.setObjectName("sectionTitle")

        folder_header.addWidget(self.folder_back_button)
        folder_header.addSpacing(12)
        folder_header.addWidget(self.folder_detail_title)
        folder_header.addStretch()

        folder_layout.addLayout(folder_header)

        folder_scroll = QScrollArea()
        folder_scroll.setWidgetResizable(True)
        folder_scroll.setFrameShape(QFrame.Shape.NoFrame)
        folder_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        _set_theme_stylesheet(folder_scroll, "QScrollArea { background: transparent; border: none; }"
        )
        _set_shortcuts_scrollbar(folder_scroll)

        self.folder_playlists_content = QWidget()
        self.folder_playlists_layout = FlowLayout(
            self.folder_playlists_content,
            min_horizontal_spacing=16,
            vertical_spacing=24
        )

        folder_scroll.setWidget(self.folder_playlists_content)
        folder_layout.addWidget(folder_scroll, 1)

        # ------------------------------------------
        # CONTEÚDO DA PLAYLIST
        # ------------------------------------------

        detail_page = BackdropPage()
        detail_layout = detail_page.content_layout
        detail_layout.setContentsMargins(32, 26, 32, 28)
        detail_layout.setSpacing(20)

        # Cabeçalho da playlist
        detail_top_bar = QHBoxLayout()
        detail_top_bar.setSpacing(16)

        self.playlist_back_button = QPushButton(
            tr("playlist.back", self.language)
        )
        self.playlist_back_button.setObjectName("backButton")
        apply_back_button_style(self.playlist_back_button)
        self.playlist_back_button.setFixedHeight(38)
        self.playlist_back_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.playlist_back_button.clicked.connect(
            self.close_playlist_detail
        )

        self.playlist_detail_title = QLabel(
            tr("playlist.default", self.language)
        )
        self.playlist_detail_title.setWordWrap(False)
        _set_theme_stylesheet(self.playlist_detail_title, "color: white;"
            "font-size: 26px;"
            "font-weight: bold;"
        )

        self.playlist_detail_count = QLabel(
            tr("playlist.count.many", self.language).format(count=0)
        )
        _set_theme_stylesheet(self.playlist_detail_count, "color: rgba(255,255,255,170);"
            "font-size: 13px;"
        )

        detail_top_bar.addWidget(self.playlist_back_button)
        detail_top_bar.addWidget(self.playlist_detail_title)
        detail_top_bar.addWidget(self.playlist_detail_count)
        detail_top_bar.addStretch()

        detail_layout.addLayout(detail_top_bar)

        # Lista moderna de faixas
        self.playlist_tracks_table = TrackRowsPanel(
            icon_manager=getattr(
                getattr(self.parent_window, "appearance", None),
                "icon_manager",
                None
            )
        )
        self.playlist_tracks_table.library_style = True
        self.playlist_tracks_table.metadata_clickable = False
        self.playlist_tracks_table.show_favorite = True

        self.playlist_tracks_table.play_requested.connect(
            self.play_playlist_track
        )
        self.playlist_tracks_table.context_requested.connect(
            self.show_playlist_track_menu
        )
        self.playlist_tracks_table.favorite_requested.connect(
            self.toggle_playlist_track_favorite
        )

        detail_layout.addWidget(
            self.playlist_tracks_table,
            1
        )

        self.playlist_stack.addWidget(list_page)
        self.playlist_stack.addWidget(folder_page)
        self.playlist_stack.addWidget(detail_page)

        layout.addWidget(self.playlist_stack, 1)

        self.current_playlist_id = None
        self.playlist_tracks = []

        self.tabs.addTab(
            page,
            tr("library.tab.playlists", self.language)
        )

    def show_new_playlist_menu(self):
        position = self.new_playlist_button.mapToGlobal(
            QPoint(0, self.new_playlist_button.height())
        )
        self.new_playlist_menu.exec(position)

    def create_playlist_folder_dialog(self):

        name, accepted = QInputDialog.getText(
            self,
            tr("playlist.folder.create.title", self.language),
            tr("playlist.folder.create.prompt", self.language)
        )

        if not accepted:
            return

        name = name.strip()

        if not name:
            return

        try:
            self.scanner.create_playlist_folder(name)
        except Exception as error:
            QMessageBox.warning(
                self,
                tr("playlist.folder.create.error", self.language),
                str(error)
            )
            return

        self.refresh_playlists()

    def rename_playlist_folder_dialog(self, folder_id):

        folders = self.scanner.list_playlist_folders()
        folder = next(
            (
                item for item in folders
                if int(item["id"]) == int(folder_id)
            ),
            None
        )

        if not folder:
            return

        name, accepted = QInputDialog.getText(
            self,
            tr("playlist.folder.rename.title", self.language),
            tr("playlist.folder.rename.prompt", self.language),
            QLineEdit.EchoMode.Normal,
            folder["name"]
        )

        if not accepted:
            return

        name = name.strip()

        if not name:
            return

        try:
            self.scanner.rename_playlist_folder(
                folder_id,
                name
            )
        except Exception as error:
            QMessageBox.warning(
                self,
                tr("playlist.folder.rename.error", self.language),
                str(error)
            )
            return

        self.refresh_playlists()

    def show_folder_card_menu(self, folder_id, global_position):

        menu = QMenu(self)

        rename_action = menu.addAction(
            tr("playlist.folder.rename", self.language)
        )
        delete_action = menu.addAction(
            tr("playlist.folder.delete", self.language)
        )

        selected = menu.exec(global_position)

        if selected == rename_action:
            self.rename_playlist_folder_dialog(folder_id)

        elif selected == delete_action:
            self.confirm_delete_playlist_folder(folder_id)

    def confirm_delete_playlist_folder(self, folder_id):

        folders = self.scanner.list_playlist_folders()
        folder = next(
            (
                item for item in folders
                if int(item["id"]) == int(folder_id)
            ),
            None
        )

        if not folder:
            return

        answer = QMessageBox.question(
            self,
            tr("playlist.folder.delete.title", self.language),
            tr("playlist.folder.delete.confirm", self.language).format(
                name=folder["name"]
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.scanner.delete_playlist_folder(folder_id)

        if self.current_folder_id == int(folder_id):
            self.current_folder_id = None
            self.current_folder_name = None
            self.playlist_stack.setCurrentIndex(0)

        self.refresh_playlists()

    def open_folder(self, folder_id):

        folders = self.scanner.list_playlist_folders()
        folder = next(
            (
                item for item in folders
                if int(item["id"]) == int(folder_id)
            ),
            None
        )

        if not folder:
            self.refresh_playlists()
            return

        self.current_folder_id = int(folder_id)
        self.current_folder_name = folder["name"]

        self.refresh_folder_playlists()
        self.playlist_stack.setCurrentIndex(1)

    def close_folder(self):

        self.current_folder_id = None
        self.current_folder_name = None

        self.playlist_stack.setCurrentIndex(0)
        self.refresh_playlists()

    def move_playlist_to_folder(self, playlist_id, folder_id):

        try:
            self.scanner.move_playlist_to_folder(
                int(playlist_id),
                int(folder_id)
            )
        except Exception as error:
            QMessageBox.warning(
                self,
                tr("playlist.folder.move.error", self.language),
                str(error)
            )
            return

        self.refresh_playlists()

    def remove_playlist_from_folder(self, playlist_id):

        try:
            self.scanner.move_playlist_to_folder(
                int(playlist_id),
                None
            )
        except Exception as error:
            QMessageBox.warning(
                self,
                tr("playlist.folder.move.error", self.language),
                str(error)
            )
            return

        self.refresh_playlists()

    def show_playlist_folder_menu(self, playlist_id, global_position):

        folders = self.scanner.list_playlist_folders()

        if not folders:
            return

        menu = QMenu(self)

        folder_actions = {}

        for folder in folders:
            action = menu.addAction(folder["name"])
            folder_actions[action] = int(folder["id"])

        selected = menu.exec(global_position)

        if selected in folder_actions:
            self.move_playlist_to_folder(
                playlist_id,
                folder_actions[selected]
            )

    def refresh_folder_playlists(self):

        if not hasattr(self, "folder_playlists_layout"):
            return

        while self.folder_playlists_layout.count():
            item = self.folder_playlists_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        if self.current_folder_id is None:
            return

        folders = self.scanner.list_playlist_folders()
        folder = next(
            (
                item for item in folders
                if int(item["id"]) == self.current_folder_id
            ),
            None
        )

        if folder is None:
            self.current_folder_id = None
            self.current_folder_name = None
            self.playlist_stack.setCurrentIndex(0)
            return

        self.current_folder_name = folder["name"]
        self.folder_detail_title.setText(folder["name"])

        playlists = [
            item
            for item in self.scanner.list_playlists()
            if item.get("folder_id") is not None
            and int(item["folder_id"]) == self.current_folder_id
        ]

        self._render_playlist_cards(
            playlists,
            self.folder_playlists_layout
        )

        if not playlists:
            label = QLabel(
                tr("playlist.folder.empty", self.language)
            )
            label.setObjectName("pageSubtitle")
            self.folder_playlists_layout.addWidget(label)

    def create_playlist_dialog(self):

        name, accepted = QInputDialog.getText(
            self,
            tr("playlist.create.title", self.language),
            tr("playlist.create.prompt", self.language)
        )

        if not accepted:
            return

        name = name.strip()

        if not name:
            return

        try:
            self.scanner.create_playlist(name)
        except Exception as error:
            QMessageBox.warning(
                self,
                tr("playlist.create.error", self.language),
                str(error)
            )
            return

        self.refresh_playlists()

    def create_playlist_folder(self, name):
        name = str(name or "").strip()

        if not name:
            raise ValueError("O nome da pasta não pode ficar vazio.")

        with self._connect() as db:
            existing = db.execute(
                """
                SELECT id
                FROM playlist_folders
                WHERE name = ? COLLATE NOCASE
                """,
                (name,)
            ).fetchone()

            if existing:
                raise ValueError("Já existe uma pasta com esse nome.")

            cursor = db.execute(
                """
                INSERT INTO playlist_folders (name)
                VALUES (?)
                """,
                (name,)
            )

            row = db.execute(
                """
                SELECT *
                FROM playlist_folders
                WHERE id = ?
                """,
                (cursor.lastrowid,)
            ).fetchone()

            return dict(row)

    def list_playlist_folders(self):
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT
                    playlist_folders.*,
                    COUNT(playlists.id) AS playlist_count
                FROM playlist_folders
                LEFT JOIN playlists
                    ON playlists.folder_id = playlist_folders.id
                GROUP BY playlist_folders.id
                ORDER BY playlist_folders.name COLLATE NOCASE
                """
            ).fetchall()

            return [dict(row) for row in rows]

    def rename_playlist_folder(self, folder_id, new_name):
        new_name = str(new_name or "").strip()

        if not new_name:
            raise ValueError("O nome da pasta não pode ficar vazio.")

        with self._connect() as db:
            existing = db.execute(
                """
                SELECT id
                FROM playlist_folders
                WHERE name = ? COLLATE NOCASE
                  AND id != ?
                """,
                (new_name, folder_id)
            ).fetchone()

            if existing:
                raise ValueError("Já existe uma pasta com esse nome.")

            cursor = db.execute(
                """
                UPDATE playlist_folders
                SET name = ?
                WHERE id = ?
                """,
                (new_name, folder_id)
            )

            return cursor.rowcount > 0

    def delete_playlist_folder(self, folder_id):
        with self._connect() as db:
            db.execute(
                """
                UPDATE playlists
                SET folder_id = NULL
                WHERE folder_id = ?
                """,
                (folder_id,)
            )

            cursor = db.execute(
                """
                DELETE FROM playlist_folders
                WHERE id = ?
                """,
                (folder_id,)
            )

            return cursor.rowcount > 0


    def refresh_playlists(self):

        if not hasattr(self, "playlists_layout"):
            return

        while self.playlists_layout.count():
            item = self.playlists_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        self.folder_cards = []

        folders = self.scanner.list_playlist_folders()

        for folder in folders:
            folder_id = int(folder["id"])
            count = int(folder.get("playlist_count") or 0)

            count_text = tr(
                "playlist.folder.count.one"
                if count == 1
                else "playlist.folder.count.many",
                self.language
            ).format(count=count)

            card = PlaylistFolderCard(
                folder_id,
                folder["name"],
                count_text,
                icon_manager=getattr(
                    getattr(self.parent_window, "appearance", None),
                    "icon_manager",
                    None
                )
            )

            card.clicked.connect(self.open_folder)
            card.context_requested.connect(
                self.show_folder_card_menu
            )
            card.playlist_dropped.connect(
                self.move_playlist_to_folder
            )

            self.folder_cards.append(card)
            self.playlists_layout.addWidget(card)

        playlists = [
            item
            for item in self.scanner.list_playlists()
            if item.get("folder_id") is None
        ]

        self._render_playlist_cards(
            playlists,
            self.playlists_layout
        )

        if not folders and not playlists:
            label = QLabel(
                tr("playlist.empty", self.language)
            )
            label.setObjectName("pageSubtitle")
            self.playlists_layout.addWidget(label)

        if self.current_folder_id is not None:
            self.refresh_folder_playlists()

    def _render_playlist_cards(self, playlists, target_layout):

        self.playlist_cards = []
        self.active_playlist_card = None

        gradients = [
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #8d596d,stop:1 #38283d)",
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #537d85,stop:1 #243a4b)",
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #78634f,stop:1 #332b31)",
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #496c75,stop:1 #182c38)",
        ]

        for index, playlist in enumerate(playlists):
            playlist_id = int(playlist["id"])

            all_tracks = self.scanner.list_playlist_tracks(
                playlist_id
            )

            if self.parent_window.library_access_ready:
                tracks = [
                    track
                    for track in all_tracks
                    if self.parent_window._track_is_available(track)
                ]
            else:
                tracks = []

            cover_paths = []
            seen_covers = set()

            for track in tracks:
                cover_path = track.get("cover_path")

                if not cover_path:
                    continue

                cover_path = str(cover_path)

                if (
                    cover_path in seen_covers
                    or not os.path.isfile(cover_path)
                ):
                    continue

                seen_covers.add(cover_path)
                cover_paths.append(cover_path)

                if len(cover_paths) == 4:
                    break

            total_seconds = 0.0

            for track in tracks:
                try:
                    total_seconds += max(
                        0.0,
                        float(track.get("duration") or 0)
                    )
                except (TypeError, ValueError):
                    continue

            total_minutes = int(round(total_seconds / 60))
            hours, minutes = divmod(total_minutes, 60)

            if hours:
                duration_text = f"{hours}h"

                if minutes:
                    duration_text += f" {minutes}min"
            else:
                duration_text = f"{minutes}min"

            count = len(tracks)
            music_label = tr(
                "playlist.count.one"
                if count == 1
                else "playlist.count.many",
                self.language
            ).format(count=count)

            subtitle = f"{music_label} · {duration_text}"

            card = PlaylistCard(
                playlist_id=playlist_id,
                name=playlist.get("name") or "Playlist sem nome",
                cover_paths=cover_paths,
                subtitle=subtitle,
                gradient=gradients[index % len(gradients)],
                custom_cover_path=playlist.get("cover_path")
            )

            card.hover_changed.connect(
                self.update_playlist_hover_state
            )
            card.clicked.connect(self.open_playlist)
            card.play_requested.connect(self.play_playlist)
            card.context_requested.connect(
                self.show_playlist_card_menu
            )

            self.playlist_cards.append(card)
            target_layout.addWidget(card)

    def update_playlist_hover_state(self, active_card, hovered):

        if hovered:
            self.active_playlist_card = active_card

        elif self.active_playlist_card is active_card:
            self.active_playlist_card = None

        for card in self.playlist_cards:
            card.set_dimmed(
                self.active_playlist_card is not None
                and card is not self.active_playlist_card
            )


    def choose_playlist_cover(self, playlist_id):
        try:
            playlist_id = int(playlist_id)
        except (TypeError, ValueError):
            return

        if self.language == "en":
            title = "Choose playlist cover"
            file_filter = (
                "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
            )
            invalid_title = "Invalid image"
            invalid_message = "The selected file is not a valid image."
            error_title = "Could not change cover"
        else:
            title = "Escolher capa da playlist"
            file_filter = (
                "Imagens (*.png *.jpg *.jpeg *.webp *.bmp)"
            )
            invalid_title = "Imagem inválida"
            invalid_message = "O arquivo selecionado não é uma imagem válida."
            error_title = "Não foi possível alterar a capa"

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            title,
            str(Path.home()),
            file_filter
        )

        if not file_path:
            return

        image = QPixmap(file_path)

        if image.isNull():
            QMessageBox.warning(
                self,
                invalid_title,
                invalid_message
            )
            return

        try:
            self.scanner.set_playlist_cover(
                playlist_id,
                file_path
            )
        except Exception as error:
            QMessageBox.warning(
                self,
                error_title,
                str(error)
            )
            return

        self.refresh_playlists()

        if self.current_playlist_id == playlist_id:
            self.refresh_playlist_detail()

    def reset_playlist_cover(self, playlist_id):
        try:
            playlist_id = int(playlist_id)
        except (TypeError, ValueError):
            return

        try:
            self.scanner.reset_playlist_cover(playlist_id)
        except Exception as error:
            title = (
                "Could not restore cover"
                if self.language == "en"
                else "Não foi possível restaurar a capa"
            )
            QMessageBox.warning(self, title, str(error))
            return

        self.refresh_playlists()

        if self.current_playlist_id == playlist_id:
            self.refresh_playlist_detail()

    def show_playlist_card_menu(
        self,
        playlist_id,
        global_position
    ):

        try:
            playlist_id = int(playlist_id)
        except (TypeError, ValueError):
            return

        tracks = self.scanner.list_playlist_tracks(
            playlist_id
        )

        extra_actions = []
        extra_submenus = []

        if self.current_folder_id is None:
            folders = self.scanner.list_playlist_folders()

            if folders:
                folder_items = []

                for folder in folders:
                    folder_id = int(folder["id"])
                    folder_name = str(folder["name"])

                    folder_items.append((
                        folder_name,
                        lambda checked=False,
                               playlist_id=playlist_id,
                               folder_id=folder_id:
                            self.move_playlist_to_folder(
                                playlist_id,
                                folder_id
                            )
                    ))

                extra_submenus.append((
                    tr("playlist.folder.add_to", self.language),
                    folder_items
                ))

        else:
            extra_actions.append((
                tr("playlist.folder.remove", self.language),
                lambda playlist_id=playlist_id:
                    self.remove_playlist_from_folder(playlist_id)
            ))

        if self.language == "en":
            change_cover_label = "Change playlist cover"
            reset_cover_label = "Restore default cover"
        else:
            change_cover_label = "Alterar capa da playlist"
            reset_cover_label = "Restaurar capa padrão"

        extra_actions.extend([
            (
                change_cover_label,
                lambda playlist_id=playlist_id:
                    self.choose_playlist_cover(playlist_id)
            ),
            (
                reset_cover_label,
                lambda playlist_id=playlist_id:
                    self.reset_playlist_cover(playlist_id)
            ),
            (
                tr("playlist.rename", self.language),
                lambda playlist_id=playlist_id:
                    self.rename_playlist_dialog(playlist_id)
            ),
            (
                tr("playlist.delete", self.language),
                lambda playlist_id=playlist_id:
                    self.confirm_delete_playlist(playlist_id)
            ),
        ])

        self.parent_window.show_context_actions(
            tracks,
            global_position,
            extra_actions=extra_actions,
            extra_submenus=extra_submenus,
            include_playlist_menu=False
        )

    def play_playlist(self, playlist_id):

        if not self.parent_window.library_access_ready:
            return

        try:
            playlist_id = int(playlist_id)
        except (TypeError, ValueError):
            return

        tracks = [
            track
            for track in self.scanner.list_playlist_tracks(
                playlist_id
            )
            if self.parent_window._track_is_available(track)
        ]

        if not tracks:
            return

        self.parent_window.play_track_data(
            tracks[0],
            tracks
        )

    def rename_playlist_dialog(self, playlist_id):

        playlist = self.scanner.get_playlist(playlist_id)

        if not playlist:
            return

        name, accepted = QInputDialog.getText(
            self,
            tr("playlist.rename.title", self.language),
            tr("playlist.rename.prompt", self.language),
            QLineEdit.EchoMode.Normal,
            playlist["name"]
        )

        if not accepted:
            return

        name = name.strip()

        if not name:
            return

        try:
            self.scanner.rename_playlist(
                playlist_id,
                name
            )
        except Exception as error:
            QMessageBox.warning(
                self,
                tr("playlist.rename.error", self.language),
                str(error)
            )
            return

        self.refresh_playlists()

        if self.current_playlist_id == playlist_id:
            self.playlist_detail_title.setText(name)

    def confirm_delete_playlist(self, playlist_id):

        playlist = self.scanner.get_playlist(playlist_id)

        if not playlist:
            return

        answer = QMessageBox.question(
            self,
            tr("playlist.delete.title", self.language),
            tr("playlist.delete.confirm", self.language).format(
                name=playlist["name"]
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.scanner.delete_playlist(playlist_id)

        if self.current_playlist_id == playlist_id:
            self.current_playlist_id = None
            self.playlist_tracks = []
            self.playlist_stack.setCurrentIndex(
                1 if self.current_folder_id is not None else 0
            )

        self.refresh_playlists()

    def open_playlist(self, playlist_id):

        try:
            playlist_id = int(playlist_id)
        except (TypeError, ValueError):
            return

        playlist = self.scanner.get_playlist(playlist_id)

        if not playlist:
            self.refresh_playlists()
            return

        self.current_playlist_id = playlist_id
        self.playlist_detail_title.setText(
            playlist["name"]
        )

        self.refresh_playlist_detail()
        self.playlist_stack.setCurrentIndex(2)

    def refresh_playlist_detail(self):

        if self.current_playlist_id is None:
            return

        playlist = self.scanner.get_playlist(
            self.current_playlist_id
        )

        if playlist:
            self.playlist_detail_title.setText(
                playlist.get("name") or "Playlist sem nome"
            )

        all_tracks = self.scanner.list_playlist_tracks(
            self.current_playlist_id
        )

        if self.parent_window.library_access_ready:
            self.playlist_tracks = [
                track
                for track in all_tracks
                if self.parent_window._track_is_available(track)
            ]
        else:
            self.playlist_tracks = []

        self.playlist_tracks_table.set_tracks(
            self.playlist_tracks,
            show_favorite=True
        )

        count = len(self.playlist_tracks)
        count_key = (
            "playlist.count.one"
            if count == 1
            else "playlist.count.many"
        )
        self.playlist_detail_count.setText(
            tr(count_key, self.language).format(count=count)
        )

    def toggle_playlist_track_favorite(self, track):
        track_id = track.get("id") if track else None

        if not track_id:
            return

        self.parent_window.toggle_track_favorite(track_id)
        self.refresh_playlist_detail()

    def close_playlist_detail(self):

        self.current_playlist_id = None
        self.playlist_tracks = []

        if self.current_folder_id is not None:
            self.refresh_folder_playlists()
            self.playlist_stack.setCurrentIndex(1)
        else:
            self.playlist_stack.setCurrentIndex(0)
            self.refresh_playlists()

    def play_playlist_track(self, track):

        if not track:
            return

        self.parent_window.play_track_data(
            track,
            self.playlist_tracks
        )

    def show_playlist_track_menu(self, tracks, global_position):
        if not tracks:
            return

        entry_ids = [
            track.get("playlist_entry_id")
            for track in tracks
            if track.get("playlist_entry_id") is not None
        ]

        if not entry_ids:
            return

        if len(entry_ids) == 1:
            label = tr("playlist.remove_track", self.language)
            action = lambda entry_id=entry_ids[0]: (
                self.remove_playlist_track_from_context(entry_id)
            )
        else:
            label = f"Remover {len(entry_ids)} faixas da playlist"
            action = lambda ids=list(entry_ids): (
                self.remove_playlist_tracks_from_context(ids)
            )

        self.parent_window.show_context_actions(
            tracks,
            global_position,
            extra_actions=[(label, action)]
        )

    def remove_playlist_track_from_context(self, entry_id):
        self.scanner.remove_playlist_track(entry_id)
        self.refresh_playlist_detail()
        self.refresh_playlists()

    def remove_playlist_tracks_from_context(self, entry_ids):
        for entry_id in entry_ids:
            self.scanner.remove_playlist_track(entry_id)

        self.refresh_playlist_detail()
        self.refresh_playlists()

    def format_duration(self, duration):

        try:
            seconds = int(float(duration or 0))
        except (ValueError, TypeError):
            seconds = 0

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        remaining = seconds % 60

        if hours:
            return f"{hours}:{minutes:02d}:{remaining:02d}"

        return f"{minutes}:{remaining:02d}"

    def get_available_tracks(self):
        if self._available_tracks_cache is None:
            if self.parent_window.library_access_ready:
                tracks = self.scanner.list_tracks(limit=None)
                self._available_tracks_cache = [
                    track for track in tracks
                    if self.parent_window._track_is_available(track)
                ]
            else:
                self._available_tracks_cache = []

        return self._available_tracks_cache

    def show_tracks_sort_menu(self):
        menu = QMenu(self)

        options = [
            (tr("favorites.sort.artist", self.language), "artist"),
            (tr("favorites.sort.album", self.language), "album"),
            (tr("favorites.sort.title", self.language), "title"),
            (tr("favorites.sort.duration", self.language), "duration"),
            (tr("favorites.sort.added_recent", self.language), "added_recent"),
            (tr("favorites.sort.added_oldest", self.language), "added_oldest"),
        ]

        for label, key in options:
            action = menu.addAction(label)
            action.triggered.connect(
                lambda checked=False, selected=key:
                    self.apply_tracks_sort(selected)
            )

        menu.addSeparator()

        reset_action = menu.addAction(
            tr("favorites.sort.clear", self.language)
        )
        reset_action.triggered.connect(self.reset_tracks_sort)

        menu.exec(
            self.tracks_sort_button.mapToGlobal(
                self.tracks_sort_button.rect().bottomLeft()
            )
        )

    def apply_tracks_sort(self, key):
        if key in ("artist", "album", "title", "duration"):
            if self.sort_key == key:
                self.sort_ascending = not self.sort_ascending
            else:
                self.sort_key = key
                self.sort_ascending = True

        elif key == "added_recent":
            self.sort_key = "imported_at"
            self.sort_ascending = False

        elif key == "added_oldest":
            self.sort_key = "imported_at"
            self.sort_ascending = True

        self.tracks = list(self.get_available_tracks())
        self.sort_library_tracks()
        self.tracks_table.reorder_tracks(self.tracks)
        self.update_tracks_sort_button()

    def reset_tracks_sort(self):
        self.sort_key = "artist"
        self.sort_ascending = True
        self.tracks = list(self.get_available_tracks())
        self.sort_library_tracks()
        self.tracks_table.reorder_tracks(self.tracks)
        self.update_tracks_sort_button()

    def sort_library_tracks(self):
        key = self.sort_key

        if key == "duration":
            def sort_value(track):
                try:
                    return float(track.get("duration") or 0)
                except (TypeError, ValueError):
                    return 0

        elif key == "imported_at":
            def sort_value(track):
                return track.get("imported_at") or ""

        else:
            def sort_value(track):
                value = track.get(key) or ""

                if key == "title" and not value:
                    value = Path(track.get("path", "")).stem

                return str(value).casefold()

        self.tracks.sort(
            key=sort_value,
            reverse=not self.sort_ascending
        )

    def update_tracks_sort_button(self):
        labels = {
            "artist": tr("favorites.sort.artist", self.language),
            "album": tr("favorites.sort.album", self.language),
            "title": tr("favorites.sort.title", self.language),
            "duration": tr("favorites.sort.duration", self.language),
            "imported_at": tr("favorites.sort.added", self.language),
        }

        label = labels.get(
            self.sort_key,
            tr("favorites.sort.artist", self.language)
        )

        if self.sort_key == "imported_at":
            direction = "↓" if not self.sort_ascending else "↑"
        else:
            direction = "↑" if self.sort_ascending else "↓"

        self.tracks_sort_button.setText(
            tr("favorites.sort", self.language).format(
                label=label,
                direction=direction
            )
        )

    def refresh_tracks(self):
        self.tracks = list(self.get_available_tracks())
        self.sort_library_tracks()

        self.tracks_table.set_tracks(
            self.tracks,
            show_favorite=True
        )

        count = len(self.tracks)
        count_key = "library.count.one" if count == 1 else "library.count.many"
        self.track_count_label.setText(
            tr(count_key, self.language).format(count=count)
        )
        self.update_tracks_sort_button()

    def refresh_albums(self):

        self._album_load_timer.stop()
        self._pending_album_data = []
        self._pending_album_index = 0
        self._pending_album_gradients = []

        self.album_cards = []
        self.active_album_card = None

        while self.albums_layout.count():
            item = self.albums_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        albums = self.scanner.list_albums()

        if self.parent_window.library_access_ready:
            tracks = self.get_available_tracks()
            allowed = {
                (
                    (track.get("album") or "").strip().casefold(),
                    (
                        track.get("album_artist")
                        or track.get("artist")
                        or ""
                    ).strip().casefold()
                )
                for track in tracks
            }
            albums = [
                album for album in albums
                if (
                    (album.get("album") or "").strip().casefold(),
                    (album.get("artist") or "").strip().casefold()
                ) in allowed
            ]
        else:
            albums = []

        gradients = [
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #8d596d,stop:1 #38283d)",
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #537d85,stop:1 #243a4b)",
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #78634f,stop:1 #332b31)",
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #496c75,stop:1 #182c38)",
        ]

        if not albums:
            label = QLabel("Nenhum álbum encontrado.")
            label.setObjectName("pageSubtitle")
            self.albums_layout.addWidget(label)
            return

        self._pending_album_data = albums
        self._pending_album_gradients = gradients
        self._pending_album_index = 0

        self._add_album_cards_batch()

        if self._pending_album_index < len(self._pending_album_data):
            self._album_load_timer.start()

    def _add_album_cards_batch(self):
        batch_size = 8

        start = self._pending_album_index
        end = min(
            start + batch_size,
            len(self._pending_album_data)
        )

        for index in range(start, end):
            album = self._pending_album_data[index]

            card = AlbumCard(
                title=album.get("album", "Álbum desconhecido"),
                artist=album.get("artist", "Artista desconhecido"),
                cover_path=album.get("cover_path"),
                gradient=self._pending_album_gradients[
                    index % len(self._pending_album_gradients)
                ]
            )

            card.hover_changed.connect(
                self.update_album_hover_state
            )
            card.clicked.connect(
                self.parent_window.open_album_page
            )
            card.play_requested.connect(
                self.parent_window.play_album
            )
            card.context_requested.connect(
                self.parent_window.show_album_context_menu
            )

            self.album_cards.append(card)
            self.albums_layout.addWidget(card)

        self._pending_album_index = end

        if self._pending_album_index >= len(self._pending_album_data):
            self._album_load_timer.stop()
            self._pending_album_data = []
            self._pending_album_gradients = []

    def update_album_hover_state(self, active_card, hovered):
        if hovered:
            self.active_album_card = active_card
        elif self.active_album_card is active_card:
            self.active_album_card = None

        for card in self.album_cards:
            card.set_dimmed(
                self.active_album_card is not None
                and card is not self.active_album_card
            )


    def refresh_artists(self):

        while self.artists_layout.count():

            item = self.artists_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        self.artist_cards = []
        self.active_artist_card = None

        tracks = self.scanner.list_tracks(limit=None)

        if self.parent_window.library_access_ready:
            tracks = [
                track for track in tracks
                if self.parent_window._track_is_available(track)
            ]
        else:
            tracks = []

        artists = {}

        for track in tracks:

            artist = (
                track.get("artist")
                or track.get("album_artist")
                or "Artista desconhecido"
            ).strip()

            key = artist.casefold()

            if key not in artists:
                artists[key] = {
                    "name": artist,
                    "cover_path": None
                }

            cover_path = track.get("cover_path")

            if (
                not artists[key]["cover_path"]
                and cover_path
                and Path(cover_path).is_file()
            ):
                artists[key]["cover_path"] = cover_path

        ordered = sorted(
            artists.values(),
            key=lambda item: item["name"].casefold()
        )

        gradients = [
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #8d596d,stop:1 #38283d)",
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #537d85,stop:1 #243a4b)",
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #78634f,stop:1 #332b31)",
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #496c75,stop:1 #182c38)",
        ]

        if not ordered:

            label = QLabel("Nenhum artista encontrado.")
            label.setObjectName("pageSubtitle")

            self.artists_layout.addWidget(label)
            return

        for index, artist in enumerate(ordered):

            card = ArtistCard(
                name=artist["name"],
                cover_path=artist["cover_path"],
                gradient=gradients[
                    index % len(gradients)
                ]
            )

            card.hover_changed.connect(
                self.update_artist_hover_state
            )
            card.clicked.connect(self.parent_window.open_artist_page)
            card.play_requested.connect(self.parent_window.play_artist)

            self.artist_cards.append(card)
            self.artists_layout.addWidget(card)

    def update_artist_hover_state(self, active_card, hovered):

        if hovered:
            self.active_artist_card = active_card

        elif self.active_artist_card is active_card:
            self.active_artist_card = None

        for card in self.artist_cards:
            card.set_dimmed(
                self.active_artist_card is not None
                and card is not self.active_artist_card
            )

    def update_search_button_visibility(self, index=None):
        if index is None:
            index = self.tabs.currentIndex()

        self.search_button.setVisible(index in (0, 1, 2, 3))

    def refresh_tab(self, index=None):

        if index is None:
            index = self.tabs.currentIndex()

        if index not in self._tab_dirty:
            return

        if not self._tab_dirty[index]:
            return

        if index == 0:
            self.refresh_artists()

        elif index == 1:
            self.refresh_albums()

        elif index == 2:
            if (
                self.current_playlist_id is not None
                and self.playlist_stack.currentIndex() == 1
            ):
                self.refresh_playlist_detail()
            else:
                self.refresh_playlists()

        elif index == 3:
            self.refresh_tracks()

        self._tab_dirty[index] = False

    def refresh(self):

        self._available_tracks_cache = None

        for index in self._tab_dirty:
            self._tab_dirty[index] = True

        self.refresh_tab(self.tabs.currentIndex())



# --------------------------------------------------
# PLAYER BAR
# --------------------------------------------------

class ClickableSlider(QSlider):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self._dragging = False
        self.setTracking(True)

    def _value_from_mouse(self, event):
        option = QStyleOptionSlider()
        self.initStyleOption(option)

        groove = self.style().subControlRect(
            QStyle.ComplexControl.CC_Slider,
            option,
            QStyle.SubControl.SC_SliderGroove,
            self
        )

        handle = self.style().subControlRect(
            QStyle.ComplexControl.CC_Slider,
            option,
            QStyle.SubControl.SC_SliderHandle,
            self
        )

        slider_min = groove.x()
        slider_max = groove.right() - handle.width() + 1
        span = slider_max - slider_min

        if span <= 0:
            return self.value()

        mouse_x = event.position().x()

        click_position = (
            mouse_x - handle.width() / 2 - slider_min
        )

        return QStyle.sliderValueFromPosition(
            self.minimum(),
            self.maximum(),
            round(click_position),
            span,
            option.upsideDown
        )

    def mousePressEvent(self, event):
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.orientation() == Qt.Orientation.Horizontal
        ):
            self._dragging = True
            self.setSliderDown(True)

            value = self._value_from_mouse(event)
            self.setSliderPosition(value)

            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (
            self._dragging
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            value = self._value_from_mouse(event)
            self.setSliderPosition(value)

            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if (
            self._dragging
            and event.button() == Qt.MouseButton.LeftButton
        ):
            value = self._value_from_mouse(event)
            self.setSliderPosition(value)

            self._dragging = False
            self.setSliderDown(False)

            event.accept()
            return

        super().mouseReleaseEvent(event)


class AppearanceIconButton(QPushButton):
    """Botão com ícone externo e cinco estados visuais."""

    def __init__(self, icon_manager, identifier, icon_size=20, parent=None):
        super().__init__(parent)
        self.icon_manager = icon_manager
        self.icon_identifier = identifier
        self.icon_size = icon_size
        self._icon_pressed = False
        self.setIconSize(QSize(icon_size, icon_size))
        self.refresh_icon_state()

    def set_identifier(self, identifier):
        self.icon_identifier = identifier
        self.refresh_icon_state()

    def set_active(self, active):
        self.setProperty("active", bool(active))
        self.refresh_icon_state()

    def refresh_icon_state(self):
        if not hasattr(self, "icon_manager"):
            return

        if not self.isEnabled():
            state = "disabled"
        elif self._icon_pressed:
            state = "pressed"
        elif self.property("active"):
            state = "active"
        elif self.underMouse():
            state = "hover"
        else:
            state = "normal"

        icon, fallback = self.icon_manager.resolve(
            self.icon_identifier,
            state
        )

        self.setIconSize(QSize(self.icon_size, self.icon_size))

        if icon.isNull():
            self.setIcon(QIcon())
            self.setText(fallback)
        else:
            self.setIcon(icon)
            self.setText("")

    def enterEvent(self, event):
        super().enterEvent(event)
        self.refresh_icon_state()

    def leaveEvent(self, event):
        self._icon_pressed = False
        super().leaveEvent(event)
        self.refresh_icon_state()

    def mousePressEvent(self, event):
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.isEnabled()
        ):
            self._icon_pressed = True

        super().mousePressEvent(event)
        self.refresh_icon_state()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self._icon_pressed = False
        self.refresh_icon_state()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.EnabledChange:
            self.refresh_icon_state()


class PlayerBusyOverlay(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self.setObjectName("playerBusyOverlay")
        self.setAttribute(
            Qt.WidgetAttribute.WA_StyledBackground,
            True
        )
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        _set_theme_stylesheet(self, """
            QWidget#playerBusyOverlay {
                background-color: rgba(12, 10, 18, 215);
                border-radius: 8px;
            }
            QLabel {
                color: white;
                background: transparent;
                border: none;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 8, 20, 8)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Biblioteca sendo atualizada")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _set_theme_stylesheet(title, "font-size: 14px; font-weight: 600;"
        )

        subtitle = QLabel("Aguarde a conclusão da indexação")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _set_theme_stylesheet(subtitle, "font-size: 11px; color: rgba(255,255,255,175);"
        )

        layout.addWidget(title)
        layout.addWidget(subtitle)


class PlayerBar(QFrame):
    def __init__(self, appearance, language='pt_BR'):
        super().__init__()

        self.icon_manager = appearance.icon_manager
        self.interface_language = language

        self.setObjectName("playerBar")
        self.setFixedHeight(int(get_theme_value("components", "player", "height", 90)))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            int(get_theme_value("components", "player", "margin_horizontal", 24)),
            int(get_theme_value("components", "player", "margin_vertical", 10)),
            int(get_theme_value("components", "player", "margin_horizontal", 24)),
            int(get_theme_value("components", "player", "margin_vertical", 10))
        )
        layout.setSpacing(20)

        # Música atual

        music = QHBoxLayout()
        music.setSpacing(10)

        cover = QLabel()
        cover.setFixedSize(
            int(get_theme_value("components", "player", "cover_size", 52)),
            int(get_theme_value("components", "player", "cover_size", 52))
        )
        cover.setAlignment(Qt.AlignmentFlag.AlignCenter)

        _set_theme_stylesheet(cover, """
            background: qlineargradient(
                x1:0,y1:0,x2:1,y2:1,
                stop:0 #8657a8,
                stop:1 #29213d
            );
            border-radius: 8px;
            """
        )

        self.cover_widget = cover

        music_info = QVBoxLayout()
        music_info.setSpacing(3)

        self.song_label = QLabel(tr("controls.no_track", self.interface_language))
        self.song_label.setObjectName("songTitle")

        self.artist_label = QLabel(tr("controls.select_track", self.interface_language))
        self.artist_label.setObjectName("songArtist")

        music_info.addWidget(self.song_label)
        music_info.addWidget(self.artist_label)

        music.addWidget(cover)
        music.addLayout(music_info, 1)

        self.favorite_button = AppearanceIconButton(self.icon_manager, "actions.favorite", 20)
        self.favorite_button.setObjectName("controlButton")
        self.favorite_button.setToolTip(tr("controls.favorite", self.interface_language))
        self.favorite_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.favorite_button.setFixedSize(
            int(get_theme_value("components", "player", "favorite_size", 30)),
            int(get_theme_value("components", "player", "favorite_size", 30))
        )

        music.addWidget(self.favorite_button)

        self.add_playlist_button = AppearanceIconButton(self.icon_manager, "actions.add_playlist", 20)
        self.add_playlist_button.setObjectName("controlButton")
        self.add_playlist_button.setToolTip(
            tr("controls.add_playlist", self.interface_language)
        )
        self.add_playlist_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.add_playlist_button.setFixedSize(
            int(get_theme_value("components", "player", "favorite_size", 30)),
            int(get_theme_value("components", "player", "favorite_size", 30))
        )

        music.addWidget(self.add_playlist_button)

        music_container = QWidget()
        music_container.setLayout(music)
        music_container.setFixedWidth(270)

        layout.addWidget(music_container)

        # Controles de reprodução

        controls = QVBoxLayout()
        controls.setSpacing(4)

        buttons = QHBoxLayout()
        buttons.setAlignment(Qt.AlignmentFlag.AlignCenter)
        buttons.setSpacing(8)

        self.shuffle_button = AppearanceIconButton(self.icon_manager, "player.shuffle", 19)
        self.previous_button = AppearanceIconButton(self.icon_manager, "player.previous", 19)
        self.play_button = AppearanceIconButton(self.icon_manager, "player.play", 28)
        self.next_button = AppearanceIconButton(self.icon_manager, "player.next", 19)
        self.repeat_button = AppearanceIconButton(self.icon_manager, "player.repeat", 19)
        self.infinity_button = AppearanceIconButton(self.icon_manager, "player.infinity", 20)
        self.queue_button = AppearanceIconButton(self.icon_manager, "player.queue", 20)

        playback_buttons = [
            self.shuffle_button,
            self.previous_button,
            self.play_button,
            self.next_button,
            self.repeat_button,
            self.infinity_button,
            self.queue_button
        ]

        playback_tooltips = [
            tr("controls.shuffle", self.interface_language),
            tr("controls.previous", self.interface_language),
            tr("controls.play", self.interface_language),
            tr("controls.next", self.interface_language),
            tr("controls.repeat", self.interface_language),
            tr("controls.infinity", self.interface_language),
            tr("controls.queue", self.interface_language)
        ]

        for button, tooltip in zip(
            playback_buttons,
            playback_tooltips
        ):
            button.setObjectName("controlButton")
            button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )
            button.setFixedSize(38, 34) if button is self.play_button else button.setFixedSize(32, 30)
            button.setToolTip(tooltip)
            buttons.addWidget(button)

        progress = ClickableSlider(
            Qt.Orientation.Horizontal
        )
        progress.setObjectName("progressSlider")
        progress.setRange(0, 1000)
        progress.setValue(0)

        self.progress_slider = progress

        self.current_time_label = QLabel("0:00")
        self.current_time_label.setObjectName("timeLabel")
        self.current_time_label.setFixedWidth(42)
        self.current_time_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft |
            Qt.AlignmentFlag.AlignVCenter
        )

        self.duration_label = QLabel("0:00")
        self.duration_label.setObjectName("timeLabel")
        self.duration_label.setFixedWidth(42)
        self.duration_label.setAlignment(
            Qt.AlignmentFlag.AlignRight |
            Qt.AlignmentFlag.AlignVCenter
        )

        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(8)
        progress_layout.addWidget(self.current_time_label)
        progress_layout.addWidget(progress, 1)
        progress_layout.addWidget(self.duration_label)

        controls.addLayout(buttons)
        controls.addLayout(progress_layout)

        layout.addLayout(controls, 1)

        # Equalizador e volume

        volume = QHBoxLayout()
        volume.setSpacing(8)

        self.equalizer_button = AppearanceIconButton(self.icon_manager, "player.equalizer", 20)
        self.equalizer_button.setObjectName("controlButton")
        self.equalizer_button.setToolTip(tr("controls.equalizer", self.interface_language))
        self.equalizer_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.equalizer_button.setFixedSize(34, 30)

        volume.addWidget(self.equalizer_button)

        self.volume_button = AppearanceIconButton(self.icon_manager, "player.volume", 20)
        self.volume_button.setObjectName("controlButton")
        self.volume_button.setToolTip(tr("controls.mute", self.interface_language))
        self.volume_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.volume_button.setFixedSize(28, 30)

        volume_slider = ClickableSlider(
            Qt.Orientation.Horizontal
        )
        volume_slider.setObjectName("volumeSlider")
        volume_slider.setRange(0, 100)
        volume_slider.setValue(70)
        volume_slider.setFixedWidth(100)

        self.volume_slider = volume_slider

        volume.addWidget(self.volume_button)
        volume.addWidget(volume_slider)

        volume.addStretch(1)

        self.fullscreen_button = AppearanceIconButton(self.icon_manager, "player.fullscreen", 20)
        self.fullscreen_button.setObjectName("controlButton")
        self.fullscreen_button.setToolTip(tr("controls.fullscreen", self.interface_language))
        self.fullscreen_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.fullscreen_button.setFixedSize(32, 30)

        volume.addWidget(self.fullscreen_button)

        volume_container = QWidget()
        volume_container.setLayout(volume)
        volume_container.setFixedWidth(270)

        layout.addWidget(volume_container)

        self.busy_overlay = PlayerBusyOverlay(self)
        self.busy_overlay.setGeometry(self.rect())
        self.busy_overlay.hide()


    def set_busy(self, busy):
        if busy:
            self.busy_overlay.setGeometry(self.rect())
            self.busy_overlay.show()
            self.busy_overlay.raise_()
        else:
            self.busy_overlay.hide()


    def resizeEvent(self, event):
        super().resizeEvent(event)

        if hasattr(self, "busy_overlay"):
            self.busy_overlay.setGeometry(self.rect())
            if self.busy_overlay.isVisible():
                self.busy_overlay.raise_()


    def set_playing(self, playing):
        self.play_button.set_identifier(
            "player.pause" if playing else "player.play"
        )
        self.play_button.setToolTip(
            tr(
                "controls.pause" if playing else "controls.play",
                self.interface_language
            )
        )

    def set_track(self, track):
        title = track.get("title") or Path(
            track.get("path", "")
        ).stem or tr("controls.unknown_track", self.interface_language)

        artist = track.get("artist") or tr("controls.unknown_artist", self.interface_language)

        self.song_label.setText(title)
        self.artist_label.setText(artist)

        cover_path = track.get("cover_path")

        if cover_path and Path(cover_path).is_file():
            pixmap = QPixmap(cover_path)

            if not pixmap.isNull():
                self.cover_widget.setPixmap(
                    pixmap.scaled(
                        52,
                        52,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
                )
                _set_theme_stylesheet(self.cover_widget, "background: transparent; border-radius: 8px;"
                )
                return

        self.cover_widget.clear()
        _set_cover_initial(self.cover_widget, title)
        _set_theme_stylesheet(self.cover_widget, """
            background: qlineargradient(
                x1:0,y1:0,x2:1,y2:1,
                stop:0 #8657a8,
                stop:1 #29213d
            );
            border-radius: 8px;
            """
        )




class QueueCoverLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = QPixmap()
        self.setMinimumSize(0, 0)
        self.setMaximumSize(308, 308)

        policy = QSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName("queueCurrentCover")
        self.setText("♫")

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return max(0, min(308, width))

    def set_cover(self, cover_path, title=None):
        self._pixmap = QPixmap()

        if cover_path and Path(cover_path).is_file():
            self._pixmap = QPixmap(str(cover_path))

        if self._pixmap.isNull():
            _set_cover_initial(self, title)
        else:
            self.setText("")
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()

    def paintEvent(self, event):
        if self._pixmap.isNull():
            super().paintEvent(event)
            return

        side = min(self.width(), self.height())
        if side <= 0:
            return

        scaled = self._pixmap.scaled(
            side,
            side,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        x = (scaled.width() - side) // 2
        y = (scaled.height() - side) // 2

        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True
        )
        painter.setRenderHint(
            QPainter.RenderHint.SmoothPixmapTransform,
            True
        )

        target_rect = QRect(
            (self.width() - side) // 2,
            (self.height() - side) // 2,
            side,
            side
        )

        path = QPainterPath()
        path.addRoundedRect(
            QRectF(target_rect),
            14,
            14
        )
        painter.setClipPath(path)

        painter.drawPixmap(
            target_rect,
            scaled,
            QRect(x, y, side, side)
        )

class QueueDropContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAcceptDrops(True)
        self.drop_callback = None
        self.library_drop_callback = None

        self.drop_indicator = QFrame(self)
        self.drop_indicator.setFixedHeight(3)
        _set_theme_stylesheet(self.drop_indicator, "background-color: #b58ae8; border-radius: 1px;"
        )
        self.drop_indicator.hide()

    def remove_drop_indicator(self):
        self.layout().removeWidget(self.drop_indicator)
        self.drop_indicator.hide()
        self.drop_indicator.setParent(self)

    def insertion_index(self, y, dragged_id):
        self.remove_drop_indicator()

        index = 0

        for position in range(self.layout().count()):
            widget = self.layout().itemAt(position).widget()

            if not hasattr(widget, "entry_id"):
                continue

            if dragged_id is not None and widget.entry_id == dragged_id:
                continue

            if y < widget.geometry().center().y():
                break

            index += 1

        return index



    def library_mime_type(self, mime_data):
        for mime_type in (
            SERIFA_TRACK_MIME,
            SERIFA_ALBUM_MIME,
            SERIFA_PLAYLIST_MIME
        ):
            if mime_data.hasFormat(mime_type):
                return mime_type

        return None

    def dragEnterEvent(self, event):
        mime_data = event.mimeData()

        if (
            mime_data.hasText()
            or self.library_mime_type(mime_data)
        ):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        mime_data = event.mimeData()

        if mime_data.hasText():
            dragged_id = mime_data.text()
        elif self.library_mime_type(mime_data):
            dragged_id = None
        else:
            event.ignore()
            return

        index = self.insertion_index(
            event.position().toPoint().y(),
            dragged_id
        )

        self.layout().insertWidget(
            index,
            self.drop_indicator
        )
        self.drop_indicator.show()

        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.remove_drop_indicator()
        event.accept()

    def dropEvent(self, event):
        mime_data = event.mimeData()

        if mime_data.hasText():
            entry_id = mime_data.text()

            index = self.insertion_index(
                event.position().toPoint().y(),
                entry_id
            )

            self.remove_drop_indicator()

            if self.drop_callback:
                self.drop_callback(entry_id, index)

            event.acceptProposedAction()
            return

        mime_type = self.library_mime_type(mime_data)

        if not mime_type:
            self.remove_drop_indicator()
            event.ignore()
            return

        index = self.insertion_index(
            event.position().toPoint().y(),
            None
        )

        try:
            payload = bytes(
                mime_data.data(mime_type)
            ).decode("utf-8")
        except (TypeError, ValueError, UnicodeDecodeError):
            self.remove_drop_indicator()
            event.ignore()
            return

        self.remove_drop_indicator()

        if self.library_drop_callback:
            self.library_drop_callback(
                mime_type,
                payload,
                index
            )
            event.acceptProposedAction()
        else:
            event.ignore()


class QueueElidedLabel(QLabel):
    def __init__(self, text, parent=None):
        self.full_text = str(text or "")
        super().__init__(self.full_text, parent)

        self.setMinimumWidth(0)
        self.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred
        )
        self.setToolTip(self.full_text)
        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)

        available_width = max(0, self.contentsRect().width())

        displayed_text = self.fontMetrics().elidedText(
            self.full_text,
            Qt.TextElideMode.ElideRight,
            available_width
        )

        if self.text() != displayed_text:
            self.setText(displayed_text)


class QueueTrackRow(QFrame):
    from PySide6.QtCore import Signal

    clicked = Signal(str)
    double_clicked = Signal(str)
    remove_requested = Signal(str)

    def __init__(self, entry_id, track, duration_text, parent=None, language='pt_BR'):
        super().__init__(parent)

        self.entry_id = str(entry_id)
        self.track = track
        self.language = language
        self._drag_start_position = None

        self.setObjectName("queueTrackRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("selected", False)
        self.setMinimumWidth(0)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 7, 7, 7)
        layout.setSpacing(9)

        self.indicator = QLabel("▶")
        self.indicator.setObjectName("queueTrackIndicator")
        self.indicator.setFixedWidth(12)
        self.indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.indicator.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )

        self.cover = QLabel()
        self.cover.setFixedSize(42, 42)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _set_cover_initial(self.cover, track.get("title") or Path(track.get("path", "")).stem)
        self.cover.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )
        _set_theme_stylesheet(self.cover, "background: rgba(255,255,255,15); border-radius: 6px;"
        )

        cover_path = track.get("cover_path")

        if cover_path and Path(cover_path).is_file():
            pixmap = QPixmap(str(cover_path))

            if not pixmap.isNull():
                self.cover.setPixmap(
                    pixmap.scaled(
                        42,
                        42,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
                )

        layout.addWidget(self.cover)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)

        self.full_title = (
            track.get("title")
            or Path(track.get("path", "")).stem
            or tr("queue.unknown_track", self.language)
        )

        self.title_label = QueueElidedLabel(self.full_title)
        self.title_label.setObjectName("queueTrackTitle")
        _set_theme_stylesheet(self.title_label, """
            color: white;
            font-size: 12px;
            font-weight: 600;
        """)

        artist = (
            track.get("artist")
            or track.get("album_artist")
            or tr("queue.unknown_artist", self.language)
        )

        self.artist_label = QueueElidedLabel(artist)
        self.artist_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )
        _set_theme_stylesheet(self.artist_label, "color: rgba(255,255,255,145); font-size: 10px;"
        )

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.artist_label)
        layout.addLayout(text_layout, 1)

        self.duration_label = QLabel(duration_text)
        self.duration_label.setFixedWidth(38)
        self.duration_label.setAlignment(
            Qt.AlignmentFlag.AlignRight |
            Qt.AlignmentFlag.AlignVCenter
        )
        self.duration_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )
        _set_theme_stylesheet(self.duration_label, "color: rgba(255,255,255,130); font-size: 10px;"
        )

        layout.addWidget(self.duration_label)

        self.remove_button = QPushButton("×")
        self.remove_button.setObjectName("queueRemoveButton")
        self.remove_button.setFixedSize(25, 25)
        self.remove_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.remove_button.setToolTip(
            tr("queue.remove", self.language)
        )
        self.remove_button.clicked.connect(
            lambda: self.remove_requested.emit(self.entry_id)
        )

        layout.addWidget(self.remove_button)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_position = event.position().toPoint()
            self.clicked.emit(self.entry_id)

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_position = None
            self.double_clicked.emit(self.entry_id)

        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        if (
            self._drag_start_position is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            distance = (
                event.position().toPoint()
                - self._drag_start_position
            ).manhattanLength()

            if distance >= QApplication.startDragDistance():
                drag = QDrag(self)
                mime = QMimeData()
                mime.setText(self.entry_id)

                drag.setMimeData(mime)
                drag.setPixmap(self.grab())
                drag.setHotSpot(
                    self._drag_start_position
                )

                self._drag_start_position = None
                drag.exec(Qt.DropAction.MoveAction)
                return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_start_position = None
        super().mouseReleaseEvent(event)

    def set_selected(self, selected):
        self.setProperty("selected", bool(selected))
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


# --------------------------------------------------
# MAIN WINDOW
# --------------------------------------------------


class EqualizerDialog(QDialog):
    PRESETS = {
        "Flat": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "Rock": [4, 3, 2, 1, -1, -1, 1, 2, 3, 3],
        "Metal": [4, 3, 1, -2, -2, 1, 2, 3, 2, 1],
        "Vocal": [-3, -2, -1, 2, 3, 3, 2, 1, 0, -1],
        "Bass Boost": [6, 5, 4, 2, 0, 0, 0, 0, 0, 0],
        "Treble Boost": [0, 0, 0, 0, 0, 0, 1, 2, 4, 5],
        "Pop": [-1, 1, 3, 4, 1, -1, 0, 1, 2, 2],
        "Classical": [3, 2, 1, 0, -1, -1, 0, 1, 2, 3],
        "Jazz": [3, 2, 1, 1, -1, -1, 0, 1, 2, 2],
        "Electronic": [4, 3, 1, 0, -2, 1, 0, 2, 3, 4],
    }

    BASIC_FREQUENCIES = [
        29, 59, 119, 237, 474,
        947, 1889, 3770, 7523, 15011
    ]

    def __init__(self, audio_player, settings, parent=None):
        super().__init__(parent)

        self.audio_player = audio_player
        self.settings = settings
        self.interface_language = getattr(parent, "interface_language", "pt_BR")

        self.setWindowTitle(tr("equalizer.title", self.interface_language))
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
        )
        self.setSizeGripEnabled(False)
        self.setModal(False)

        self.enabled = self.settings.value(
            "equalizer/enabled", False, type=bool
        )

        self.mode = self.settings.value(
            "equalizer/mode", "basic", type=str
        )
        if self.mode not in ("basic", "advanced"):
            self.mode = "basic"

        self.preamp = self.settings.value(
            "equalizer/preamp", 0.0, type=float
        )
        self.preamp = max(-12.0, min(12.0, self.preamp))

        self.basic_gains = self._read_gains(
            "equalizer/basic_gains", 10
        )
        self.advanced_gains = self._read_gains(
            "equalizer/advanced_gains", 25
        )

        self.preset_name = self.settings.value(
            "equalizer/preset", "Flat", type=str
        )

        self.custom_presets = self._read_custom_presets()
        self._editing_custom_preset = None

        self._build_interface()

        # Mantém a referência do perfil personalizado que estava selecionado.
        if self.preset_name in self.custom_presets:
            self._editing_custom_preset = self.preset_name

        # A altura é calculada uma única vez para manter a janela estável.
        self._equalizer_window_height = max(
            440,
            self.sizeHint().height()
        )
        self._fit_mode_width()

        self.audio_player.set_eq_settings(
            enabled=self.enabled,
            mode=self.mode,
            preamp=self.preamp,
            basic_gains=self.basic_gains,
            advanced_gains=self.advanced_gains
        )


    def _read_gains(self, key, count):
        value = self.settings.value(key, None)

        if isinstance(value, str):
            try:
                value = json.loads(value)
            except Exception:
                value = None

        if not isinstance(value, (list, tuple)):
            return [0.0] * count

        result = []

        for item in value[:count]:
            try:
                result.append(
                    max(-24.0, min(12.0, float(item)))
                )
            except (TypeError, ValueError):
                result.append(0.0)

        result.extend([0.0] * (count - len(result)))
        return result

    def _build_interface(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 8, 22, 12)
        root.setSpacing(9)

        class DragTitleBar(QFrame):
            def __init__(self, dialog):
                super().__init__(dialog)
                self.dialog = dialog
                self.setCursor(Qt.CursorShape.SizeAllCursor)

            def mousePressEvent(self, event):
                if event.button() == Qt.MouseButton.LeftButton:
                    handle = self.dialog.windowHandle()
                    if handle is not None:
                        handle.startSystemMove()
                    event.accept()
                    return
                super().mousePressEvent(event)

        title_bar = DragTitleBar(self)
        title_bar.setFixedHeight(34)

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 2, 0)
        title_layout.setSpacing(8)

        title_label = QLabel(
            tr("equalizer.title", self.interface_language)
        )
        title_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )
        title_layout.addWidget(title_label)
        title_layout.addStretch(1)

        title_close_button = QPushButton("×")
        title_close_button.setFixedSize(32, 28)
        title_close_button.setToolTip(
            tr("equalizer.finish", self.interface_language)
        )
        title_close_button.clicked.connect(self.close)
        title_layout.addWidget(title_close_button)

        root.addWidget(title_bar)

        _set_theme_stylesheet(self, """
            QDialog {
                background: #211e2a;
                color: #f3edf9;
            }
            QLabel {
                color: #f3edf9;
            }
            QComboBox {
                background: #302a3b;
                border: 1px solid #493243;
                border-radius: 7px;
                padding: 7px 10px;
                color: #f3edf9;
                min-width: 120px;
            }
            QCheckBox {
                spacing: 8px;
                color: #f3edf9;
            }

            QCheckBox::indicator {
                width: 15px;
                height: 15px;
                border-radius: 4px;
                border: 1px solid #71617f;
                background: #17141e;
            }

            QCheckBox::indicator:checked {
                background: #B6F23A;
                border: 1px solid #B6F23A;
            }
            QSlider::groove:horizontal {
                height: 5px;
                background: #493243;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #d9b6ff;
                width: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QSlider::groove:vertical {
                width: 5px;
                background: #493243;
                border-radius: 2px;
            }
            QSlider::handle:vertical {
                background: #d9b6ff;
                height: 14px;
                margin: 0 -5px;
                border-radius: 7px;
            }
            QPushButton {
                background: #302a3b;
                color: #f3edf9;
                border: 1px solid #493243;
                border-radius: 8px;
                padding: 8px 14px;
            }
            QPushButton:hover {
                background: #493243;
            }
        """)

        header = QHBoxLayout()

        self.enabled_checkbox = QCheckBox(tr("equalizer.enabled", self.interface_language))
        self.enabled_checkbox.setChecked(self.enabled)
        self.enabled_checkbox.toggled.connect(
            self._on_enabled_changed
        )
        header.addWidget(self.enabled_checkbox)
        header.addStretch(1)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem(tr("equalizer.basic", self.interface_language), "basic")
        self.mode_combo.addItem(tr("equalizer.advanced", self.interface_language), "advanced")
        self.mode_combo.setCurrentIndex(
            0 if self.mode == "basic" else 1
        )
        self.mode_combo.currentIndexChanged.connect(
            self._on_mode_changed
        )
        header.addWidget(self.mode_combo)

        root.addLayout(header)

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel(tr("equalizer.preset", self.interface_language)))

        self.preset_combo = QComboBox()

        self.preset_combo.addItems(
            list(self.PRESETS.keys())
            + list(self.custom_presets.keys())
            + ["Personalizado"]
        )

        if (
            self.preset_name not in self.PRESETS
            and self.preset_name not in self.custom_presets
        ):
            self.preset_name = "Personalizado"

        self.preset_combo.setCurrentText(self.preset_name)
        self.preset_combo.currentTextChanged.connect(
            self._on_preset_changed
        )

        preset_row.addWidget(self.preset_combo)

        self.save_preset_button = QPushButton(tr("equalizer.save", self.interface_language))
        self.save_preset_button.clicked.connect(
            self._save_custom_preset
        )
        preset_row.addWidget(self.save_preset_button)

        self.delete_preset_button = QPushButton(tr("equalizer.delete", self.interface_language))
        self.delete_preset_button.clicked.connect(
            self._delete_custom_preset
        )
        preset_row.addWidget(self.delete_preset_button)

        preset_row.addStretch(1)
        root.addLayout(preset_row)

        self._update_custom_preset_controls()

        preamp_row = QHBoxLayout()

        preamp_label = QLabel(tr("equalizer.preamp", self.interface_language))
        preamp_label.setMinimumWidth(65)
        preamp_row.addWidget(preamp_label)

        self.preamp_slider = QSlider(Qt.Orientation.Horizontal)
        self.preamp_slider.setRange(-120, 120)
        self.preamp_slider.setValue(round(self.preamp * 10))
        self.preamp_slider.valueChanged.connect(
            self._on_preamp_changed
        )
        preamp_row.addWidget(self.preamp_slider, 1)

        self.preamp_value = QLabel(
            f"{self.preamp:+.1f} dB"
        )
        self.preamp_value.setMinimumWidth(65)
        self.preamp_value.setAlignment(
            Qt.AlignmentFlag.AlignRight |
            Qt.AlignmentFlag.AlignVCenter
        )
        preamp_row.addWidget(self.preamp_value)

        root.addLayout(preamp_row)

        self.band_scroll = QScrollArea()
        self.band_scroll.setWidgetResizable(False)
        self.band_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.band_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.band_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.band_scroll.setMinimumHeight(220)
        self.band_scroll.setMaximumHeight(300)
        self.band_scroll.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self.band_container = QWidget()
        self.band_layout = QHBoxLayout(self.band_container)
        self.band_layout.setContentsMargins(8, 8, 8, 8)
        self.band_layout.setSpacing(12)

        self.band_scroll.setWidget(self.band_container)
        root.addWidget(self.band_scroll, 1)

        footer = QHBoxLayout()

        restore_button = QPushButton(tr("equalizer.restore", self.interface_language))
        restore_button.clicked.connect(self._restore_flat)
        footer.addWidget(restore_button)

        footer.addStretch(1)

        close_button = QPushButton(tr("equalizer.finish", self.interface_language))
        close_button.clicked.connect(self.accept)
        footer.addWidget(close_button)

        root.addLayout(footer)

        self._rebuild_bands()

    def _read_custom_presets(self):
        value = self.settings.value(
            "equalizer/custom_presets", {}
        )

        if isinstance(value, str):
            try:
                value = json.loads(value)
            except Exception:
                value = {}

        if not isinstance(value, dict):
            return {}

        result = {}

        for name, data in value.items():
            name = str(name).strip()

            if (
                not name
                or name in self.PRESETS
                or name == "Personalizado"
                or not isinstance(data, dict)
            ):
                continue

            try:
                basic = [
                    max(-24.0, min(12.0, float(v)))
                    for v in data["basic_gains"]
                ]
                advanced = [
                    max(-24.0, min(12.0, float(v)))
                    for v in data["advanced_gains"]
                ]
                preamp = max(
                    -12.0,
                    min(12.0, float(data.get("preamp", 0.0)))
                )
            except (KeyError, TypeError, ValueError):
                continue

            if len(basic) != 10 or len(advanced) != 25:
                continue

            mode = data.get("mode", "basic")
            if mode not in ("basic", "advanced"):
                mode = "basic"

            result[name] = {
                "basic_gains": basic,
                "advanced_gains": advanced,
                "preamp": preamp,
                "mode": mode
            }

        return result

    def _write_custom_presets(self):
        self.settings.setValue(
            "equalizer/custom_presets",
            json.dumps(self.custom_presets, ensure_ascii=False)
        )
        self.settings.sync()

    def _refresh_preset_combo(self, selected=None):
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()

        self.preset_combo.addItems(
            list(self.PRESETS.keys())
            + list(self.custom_presets.keys())
            + ["Personalizado"]
        )

        self.preset_combo.setCurrentText(
            selected or "Personalizado"
        )
        self.preset_combo.blockSignals(False)

        self._update_custom_preset_controls()

    def _update_custom_preset_controls(self):
        if not hasattr(self, "delete_preset_button"):
            return

        selected = self.preset_combo.currentText()

        self.delete_preset_button.setEnabled(
            selected in self.custom_presets
        )

    def _mark_customized(self):
        current = self.preset_combo.currentText()

        # Perfil personalizado: mantém o nome e a referência de origem.
        if current in self.custom_presets:
            self._editing_custom_preset = current
            self.preset_name = current
            self._update_custom_preset_controls()
            return

        # Presets originais passam a representar uma edição personalizada.
        self._editing_custom_preset = None
        self.preset_name = "Personalizado"

        self.preset_combo.blockSignals(True)
        self.preset_combo.setCurrentText("Personalizado")
        self.preset_combo.blockSignals(False)

        self._update_custom_preset_controls()

    def _save_custom_preset(self):
        editing_name = self._editing_custom_preset

        if editing_name not in self.custom_presets:
            editing_name = None

        name = None

        if editing_name:
            is_pt = str(self.interface_language).lower().startswith("pt")

            dialog = QMessageBox(self)
            dialog.setIcon(QMessageBox.Icon.Question)
            dialog.setWindowTitle(
                "Salvar perfil" if is_pt else "Save preset"
            )
            dialog.setText(
                f'O perfil "{editing_name}" foi alterado. Como deseja salvar?'
                if is_pt else
                f'The preset "{editing_name}" was modified. How would you like to save it?'
            )

            update_button = dialog.addButton(
                "Atualizar definição atual" if is_pt else "Update current preset",
                QMessageBox.ButtonRole.AcceptRole
            )
            create_button = dialog.addButton(
                "Criar nova definição" if is_pt else "Create new preset",
                QMessageBox.ButtonRole.ActionRole
            )
            cancel_button = dialog.addButton(
                "Cancelar" if is_pt else "Cancel",
                QMessageBox.ButtonRole.RejectRole
            )

            dialog.setDefaultButton(update_button)
            dialog.setEscapeButton(cancel_button)
            dialog.exec()

            clicked = dialog.clickedButton()

            if clicked is update_button:
                name = editing_name
            elif clicked is create_button:
                name = None
            else:
                return

        if name is None:
            name, accepted = QInputDialog.getText(
                self,
                tr("equalizer.dialog.save_title", self.interface_language),
                tr("equalizer.dialog.name_label", self.interface_language),
                QLineEdit.EchoMode.Normal,
                ""
            )

            if not accepted:
                return

            name = name.strip()

            if not name:
                QMessageBox.warning(
                    self,
                    tr("equalizer.dialog.invalid_title", self.interface_language),
                    tr("equalizer.dialog.invalid_body", self.interface_language)
                )
                return

            if name == "Personalizado":
                QMessageBox.warning(
                    self,
                    tr("equalizer.dialog.reserved_title", self.interface_language),
                    tr("equalizer.dialog.reserved_custom", self.interface_language)
                )
                return

            if name in self.PRESETS:
                QMessageBox.warning(
                    self,
                    tr("equalizer.dialog.reserved_title", self.interface_language),
                    tr("equalizer.dialog.reserved_original", self.interface_language)
                )
                return

            if name in self.custom_presets:
                resposta = QMessageBox.question(
                    self,
                    tr("equalizer.dialog.replace_title", self.interface_language),
                    tr("equalizer.dialog.replace_body", self.interface_language).format(name=name),
                    QMessageBox.StandardButton.Yes |
                    QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if resposta != QMessageBox.StandardButton.Yes:
                    return

        self.custom_presets[name] = {
            "basic_gains": list(self.basic_gains),
            "advanced_gains": list(self.advanced_gains),
            "preamp": float(self.preamp),
            "mode": self.mode
        }

        self._write_custom_presets()

        self.preset_name = name
        self._editing_custom_preset = name

        self._refresh_preset_combo(name)
        self.save_settings()

    def _delete_custom_preset(self):
        name = self.preset_combo.currentText()

        if name not in self.custom_presets:
            return

        resposta = QMessageBox.question(
            self,
            tr("equalizer.dialog.delete_title", self.interface_language),
            tr("equalizer.dialog.delete_body", self.interface_language).format(name=name),
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if resposta != QMessageBox.StandardButton.Yes:
            return

        del self.custom_presets[name]

        self._write_custom_presets()

        self.preset_name = "Personalizado"
        self._editing_custom_preset = None
        self._refresh_preset_combo("Personalizado")
        self.save_settings()

    def _get_frequencies(self, mode):
        if mode == "basic":
            return self.BASIC_FREQUENCIES

        try:
            frequencies = self.audio_player.get_eq_band_frequencies(
                "advanced"
            )
            if len(frequencies) == 25:
                return list(frequencies)
        except Exception:
            pass

        return [
            23.18, 30.56, 40.29, 53.11, 70.01,
            92.29, 121.66, 160.38, 211.43, 278.72,
            367.42, 484.35, 638.50, 841.71, 1109.59,
            1462.72, 1928.24, 2541.92, 3350.90,
            4417.35, 5823.20, 7676.47, 10119.56,
            13340.18, 17585.78
        ]

    def _format_frequency(self, frequency):
        if frequency >= 1000:
            return f"{frequency / 1000:.1f} kHz"
        return f"{frequency:.0f} Hz"

    def _rebuild_bands(self):
        while self.band_layout.count():
            item = self.band_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        gains = (
            self.basic_gains
            if self.mode == "basic"
            else self.advanced_gains
        )

        frequencies = self._get_frequencies(self.mode)

        for index, frequency in enumerate(frequencies):
            column = QWidget()
            column.setFixedWidth(48)

            layout = QVBoxLayout(column)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(5)

            value_label = QLabel(f"{gains[index]:+.1f}")
            value_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            _set_theme_stylesheet(value_label, "font-size: 11px; color: #d9b6ff;"
            )
            layout.addWidget(value_label)

            slider = QSlider(Qt.Orientation.Vertical)
            slider.setRange(-240, 120)
            slider.setValue(round(gains[index] * 10))
            slider.setMinimumHeight(190)
            slider.setTickPosition(
                QSlider.TickPosition.TicksBothSides
            )
            slider.setTickInterval(60)

            slider.valueChanged.connect(
                lambda value, i=index, m=self.mode, label=value_label:
                    self._on_band_changed(i, m, value, label)
            )

            slider_layout = QHBoxLayout()
            slider_layout.addStretch(1)
            slider_layout.addWidget(slider)
            slider_layout.addStretch(1)
            layout.addLayout(slider_layout, 1)

            frequency_label = QLabel(
                self._format_frequency(frequency)
            )
            frequency_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            _set_theme_stylesheet(frequency_label, "font-size: 10px; color: #95899f;"
            )
            layout.addWidget(frequency_label)

            self.band_layout.addWidget(column)

        self.band_layout.addStretch(1)

        width = max(700, len(frequencies) * 60 + 30)
        self.band_container.setFixedSize(width, 275)

    def _apply_audio_settings(self):
        self.audio_player.set_eq_settings(
            enabled=self.enabled,
            mode=self.mode,
            preamp=self.preamp,
            basic_gains=self.basic_gains,
            advanced_gains=self.advanced_gains
        )
        self.save_settings()

    def _on_enabled_changed(self, enabled):
        self.enabled = bool(enabled)
        self._apply_audio_settings()

    def _on_mode_changed(self, index):
        mode = self.mode_combo.itemData(index)

        if mode not in ("basic", "advanced"):
            return

        self.mode = mode
        self._rebuild_bands()
        self._fit_mode_width()
        self._apply_audio_settings()

    def _fit_mode_width(self):
        screen = self.screen()
        if screen is None:
            screen = QApplication.primaryScreen()

        available = (
            screen.availableGeometry()
            if screen is not None
            else None
        )

        available_width = available.width() if available else 1920
        available_height = available.height() if available else 1080

        if self.mode == "basic":
            target_width = min(800, available_width - 40)
        else:
            target_width = min(1600, available_width - 40)

        target_height = min(
            520,
            available_height - 40
        )

        self.setFixedSize(
            max(640, target_width),
            max(400, target_height)
        )

    def _on_preamp_changed(self, value):
        self.preamp = value / 10.0
        self.preamp_value.setText(
            f"{self.preamp:+.1f} dB"
        )
        self._mark_customized()
        self._apply_audio_settings()

    def _on_band_changed(self, index, mode, value, label):
        gain = value / 10.0
        label.setText(f"{gain:+.1f}")

        gains = (
            self.basic_gains
            if mode == "basic"
            else self.advanced_gains
        )

        gains[index] = gain
        self._mark_customized()
        self._apply_audio_settings()

    def _interpolate_preset(self, source_gains, target_frequencies):
        source_frequencies = self.BASIC_FREQUENCIES
        result = []

        for target in target_frequencies:
            if target <= source_frequencies[0]:
                result.append(float(source_gains[0]))
                continue

            if target >= source_frequencies[-1]:
                result.append(float(source_gains[-1]))
                continue

            for index in range(len(source_frequencies) - 1):
                low = source_frequencies[index]
                high = source_frequencies[index + 1]

                if low <= target <= high:
                    ratio = (
                        math.log(target) - math.log(low)
                    ) / (
                        math.log(high) - math.log(low)
                    )

                    gain = (
                        source_gains[index] * (1 - ratio)
                        + source_gains[index + 1] * ratio
                    )
                    result.append(float(gain))
                    break

        return result

    def _on_preset_changed(self, name):
        if name == "Personalizado":
            self._editing_custom_preset = None
            self.preset_name = name
            self._update_custom_preset_controls()
            self.save_settings()
            return

        if name in self.custom_presets:
            data = self.custom_presets[name]

            self._editing_custom_preset = name
            self.preset_name = name
            self.basic_gains = list(data["basic_gains"])
            self.advanced_gains = list(data["advanced_gains"])
            self.preamp = float(data["preamp"])
            self.mode = data["mode"]

            self.mode_combo.blockSignals(True)
            self.mode_combo.setCurrentIndex(
                0 if self.mode == "basic" else 1
            )
            self.mode_combo.blockSignals(False)

            self.preamp_slider.blockSignals(True)
            self.preamp_slider.setValue(
                round(self.preamp * 10)
            )
            self.preamp_slider.blockSignals(False)

            self.preamp_value.setText(
                f"{self.preamp:+.1f} dB"
            )

            self._rebuild_bands()
            self._fit_mode_width()
            self._apply_audio_settings()
            self._update_custom_preset_controls()
            return

        if name not in self.PRESETS:
            return

        self._editing_custom_preset = None
        self.preset_name = name

        self.basic_gains = [
            float(value) for value in self.PRESETS[name]
        ]

        self.advanced_gains = self._interpolate_preset(
            self.basic_gains,
            self._get_frequencies("advanced")
        )

        self._rebuild_bands()
        self._fit_mode_width()
        self._apply_audio_settings()
        self._update_custom_preset_controls()

    def _restore_flat(self):
        self.basic_gains = [0.0] * 10
        self.advanced_gains = [0.0] * 25
        self.preamp = 0.0
        self.preset_name = "Flat"
        self._editing_custom_preset = None

        self.preamp_slider.blockSignals(True)
        self.preamp_slider.setValue(0)
        self.preamp_slider.blockSignals(False)

        self.preamp_value.setText("+0.0 dB")

        self.preset_combo.blockSignals(True)
        self.preset_combo.setCurrentText("Flat")
        self.preset_combo.blockSignals(False)

        self._rebuild_bands()
        self._apply_audio_settings()

    def save_settings(self):
        self.settings.setValue(
            "equalizer/enabled", self.enabled
        )
        self.settings.setValue(
            "equalizer/mode", self.mode
        )
        self.settings.setValue(
            "equalizer/preamp", self.preamp
        )
        self.settings.setValue(
            "equalizer/preset", self.preset_name
        )
        self.settings.setValue(
            "equalizer/basic_gains", self.basic_gains
        )
        self.settings.setValue(
            "equalizer/advanced_gains", self.advanced_gains
        )
        self.settings.sync()

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)





class FullscreenCover(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.pixmap = QPixmap()
        self._scaled_pixmap = QPixmap()
        self._scaled_size = QSize()
        self.fallback_title = ""

        self._tilt_x = 0.0
        self._tilt_y = 0.0
        self._target_tilt_x = 0.0
        self._target_tilt_y = 0.0

        self.setMinimumSize(180, 180)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMouseTracking(True)

        self._tilt_timer = QTimer(self)
        self._tilt_timer.setInterval(16)
        self._tilt_timer.setTimerType(
            Qt.TimerType.PreciseTimer
        )
        self._tilt_timer.timeout.connect(
            self._update_tilt
        )

    def get_tilt_x(self):
        return self._tilt_x

    def set_tilt_x(self, value):
        self._tilt_x = float(value)
        self.update()

    tilt_x = Property(float, get_tilt_x, set_tilt_x)

    def get_tilt_y(self):
        return self._tilt_y

    def set_tilt_y(self, value):
        self._tilt_y = float(value)
        self.update()

    tilt_y = Property(float, get_tilt_y, set_tilt_y)

    def set_fallback_title(self, title):
        self.fallback_title = str(title or '').strip()
        self.update()

    def set_pixmap(self, pixmap):
        self.pixmap = QPixmap(pixmap)
        self._scaled_pixmap = QPixmap()
        self._scaled_size = QSize()
        self.update()

    def set_cover(self, path):
        pixmap = QPixmap()

        if path and Path(path).is_file():
            pixmap = QPixmap(str(path))

        self.set_pixmap(pixmap)

    def _animate_tilt(self, target_x, target_y, duration=200):
        self._target_tilt_x = float(target_x)
        self._target_tilt_y = float(target_y)

        if not self._tilt_timer.isActive():
            self._tilt_timer.start()


    def mouseMoveEvent(self, event):
        position = event.position()

        normalized_x = (
            position.x() / max(1, self.width())
        ) * 2.0 - 1.0

        normalized_y = (
            position.y() / max(1, self.height())
        ) * 2.0 - 1.0

        self._animate_tilt(
            -normalized_y * 2.0,
            normalized_x * 2.0
        )

        super().mouseMoveEvent(event)

    def _update_tilt(self):
        # Interpolação linear independente da curva Bézier.
        smoothing = 0.28

        dx = self._target_tilt_x - self._tilt_x
        dy = self._target_tilt_y - self._tilt_y

        if abs(dx) < 0.015 and abs(dy) < 0.015:
            self._tilt_x = self._target_tilt_x
            self._tilt_y = self._target_tilt_y

            self.update()
            self._tilt_timer.stop()
            return

        self._tilt_x += dx * smoothing
        self._tilt_y += dy * smoothing

        self.update()

    def leaveEvent(self, event):
        self._animate_tilt(0.0, 0.0, 280)
        super().leaveEvent(event)

    def resizeEvent(self, event):
        self._scaled_pixmap = QPixmap()
        self._scaled_size = QSize()

        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )
        painter.setRenderHint(
            QPainter.RenderHint.SmoothPixmapTransform
        )

        center_x = self.width() / 2
        center_y = self.height() / 2

        transform = QTransform()
        transform.translate(center_x, center_y)
        transform.shear(
            self._tilt_y * 0.012,
            self._tilt_x * 0.012
        )
        transform.scale(
            1.0 - abs(self._tilt_y) * 0.004,
            1.0 - abs(self._tilt_x) * 0.004
        )
        transform.translate(-center_x, -center_y)

        painter.setTransform(transform, True)

        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)

        path = QPainterPath()
        path.addRoundedRect(rect, 18, 18)
        painter.setClipPath(path)

        if self.pixmap.isNull():
            gradient = QLinearGradient(
                rect.topLeft(),
                rect.bottomRight()
            )
            gradient.setColorAt(0, QColor("#8657a8"))
            gradient.setColorAt(1, QColor("#211b30"))

            painter.fillRect(rect, gradient)
            painter.setPen(QColor("#ffffff"))
            font = QFont(self.font())
            font.setBold(True)
            font.setPixelSize(max(48, min(self.width(), self.height()) // 2))
            painter.setFont(font)
            initial = self.fallback_title[0].upper() if self.fallback_title else '♪'
            painter.drawText(
                rect,
                Qt.AlignmentFlag.AlignCenter,
                initial
            )
            return

        if (
            self._scaled_pixmap.isNull()
            or self._scaled_size != self.size()
        ):
            self._scaled_pixmap = self.pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self._scaled_size = self.size()

        x = (
            self._scaled_pixmap.width() - self.width()
        ) // 2

        y = (
            self._scaled_pixmap.height() - self.height()
        ) // 2

        painter.drawPixmap(
            self.rect(),
            self._scaled_pixmap,
            QRect(x, y, self.width(), self.height())
        )



class FullscreenQueueRow(QFrame):
    play_requested = Signal(str)
    remove_requested = Signal(str)

    def __init__(self, entry_id, track, controller, parent=None):
        super().__init__(parent)

        self.entry_id = str(entry_id)
        self.track = track
        self._drag_start_position = None

        self.setObjectName("fullscreenQueueRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        _set_theme_stylesheet(self, """
            QFrame#fullscreenQueueRow {
                background: rgba(255,255,255,9);
                border: 1px solid rgba(255,255,255,15);
                border-radius: 10px;
            }
            QFrame#fullscreenQueueRow:hover {
                background: rgba(255,255,255,19);
                border: 1px solid rgba(190,155,230,90);
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 7, 7, 7)
        layout.setSpacing(9)

        self.cover = QLabel()
        self.cover.setFixedSize(42, 42)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _set_cover_initial(self.cover, track.get("title") or Path(track.get("path", "")).stem)
        self.cover.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )
        _set_theme_stylesheet(self.cover, "background: rgba(255,255,255,15); border-radius: 6px;"
        )

        cover_path = track.get("cover_path")

        if cover_path and Path(cover_path).is_file():
            pixmap = QPixmap(str(cover_path))

            if not pixmap.isNull():
                self.cover.setPixmap(
                    pixmap.scaled(
                        42,
                        42,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
                )

        layout.addWidget(self.cover)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)

        title = (
            track.get("title")
            or Path(track.get("path", "")).stem
            or tr("queue.unknown_track", controller.interface_language)
        )

        artist = track.get("artist") or tr("queue.unknown_artist", controller.interface_language)

        self.title_label = QueueElidedLabel(title)
        _set_theme_stylesheet(self.title_label, """
            color: white;
            font-size: 12px;
            font-weight: 600;
        """)

        self.artist_label = QLabel(artist)
        self.artist_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )
        _set_theme_stylesheet(self.artist_label, "color: rgba(255,255,255,145); font-size: 10px;"
        )

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.artist_label)
        layout.addLayout(text_layout, 1)

        duration = track.get("duration") or 0

        try:
            duration_text = controller.format_time(float(duration))
        except (TypeError, ValueError):
            duration_text = "0:00"

        self.duration_label = QLabel(duration_text)
        self.duration_label.setFixedWidth(38)
        self.duration_label.setAlignment(
            Qt.AlignmentFlag.AlignRight |
            Qt.AlignmentFlag.AlignVCenter
        )
        self.duration_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )
        _set_theme_stylesheet(self.duration_label, "color: rgba(255,255,255,130); font-size: 10px;"
        )

        layout.addWidget(self.duration_label)

        self.remove_button = QPushButton("×")
        self.remove_button.setObjectName("queueRemoveButton")
        self.remove_button.setFixedSize(25, 25)
        self.remove_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.remove_button.setToolTip(
            tr("queue.remove", controller.interface_language)
        )
        _set_theme_stylesheet(self.remove_button, """
            QPushButton {
                color: rgba(255,255,255,180);
                background: transparent;
                border: none;
                border-radius: 7px;
                font-size: 18px;
            }
            QPushButton:hover {
                color: #211E2A;
                background: #B6F23A;
            }
            QPushButton:pressed {
                color: #211E2A;
                background: #A2D92A;
            }
        """)

        layout.addWidget(self.remove_button)

        self.remove_button.clicked.connect(
            lambda: self.remove_requested.emit(self.entry_id)
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_position = event.position().toPoint()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (
            self._drag_start_position is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            distance = (
                event.position().toPoint()
                - self._drag_start_position
            ).manhattanLength()

            if distance >= QApplication.startDragDistance():
                drag = QDrag(self)
                mime = QMimeData()
                mime.setText(self.entry_id)

                drag.setMimeData(mime)
                drag.setPixmap(self.grab())
                drag.setHotSpot(self._drag_start_position)

                self._drag_start_position = None

                drag.exec(Qt.DropAction.MoveAction)
                return

        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_position = None
            self.play_requested.emit(self.entry_id)

        super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_start_position = None
        super().mouseReleaseEvent(event)





class CircularPreviewCover(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(58, 58)
        self._pixmap = QPixmap()
        self._display_pixmap = QPixmap()
        self.fallback_title = ""

    def set_cover(self, path, title=None):
        self.fallback_title = str(title or '').strip()
        total_start = time.perf_counter()
        decode_ms = 0.0
        crop_ms = 0.0
        scale_ms = 0.0

        self._pixmap = QPixmap()
        self._display_pixmap = QPixmap()

        if path:
            started = time.perf_counter()
            pixmap = QPixmap(str(path))
            decode_ms = (time.perf_counter() - started) * 1000

            if not pixmap.isNull():
                size = min(pixmap.width(), pixmap.height())
                x = (pixmap.width() - size) // 2
                y = (pixmap.height() - size) // 2

                started = time.perf_counter()
                self._pixmap = pixmap.copy(x, y, size, size)
                crop_ms = (time.perf_counter() - started) * 1000

                started = time.perf_counter()
                self._display_pixmap = self._pixmap.scaled(
                    self.size(),
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                scale_ms = (time.perf_counter() - started) * 1000

        self.update()

        total_ms = (time.perf_counter() - total_start) * 1000

        if total_ms >= 2.0:
            print(
                f"[Preview Cover] total={total_ms:.1f} ms | "
                f"decode={decode_ms:.1f} ms | "
                f"crop={crop_ms:.1f} ms | "
                f"scale={scale_ms:.1f} ms",
                flush=True
            )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(1, 1, self.width() - 2, self.height() - 2)
        clip = QPainterPath()
        clip.addEllipse(rect)

        painter.setClipPath(clip)

        if not self._display_pixmap.isNull():
            painter.drawPixmap(0, 0, self._display_pixmap)
        else:
            painter.fillRect(rect, QColor("#342b43"))
            painter.setPen(QColor("#ffffff"))
            font = QFont(self.font())
            font.setBold(True)
            font.setPixelSize(28)
            painter.setFont(font)
            initial = self.fallback_title[0].upper() if self.fallback_title else '♪'
            painter.drawText(
                rect,
                Qt.AlignmentFlag.AlignCenter,
                initial
            )

        painter.end()


class FadingDropShadowEffect(QGraphicsDropShadowEffect):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._opacity = 1.0

    def set_opacity(self, value):
        self._opacity = max(0.0, min(1.0, float(value)))
        self.update()

    def draw(self, painter):
        painter.save()
        painter.setOpacity(painter.opacity() * self._opacity)
        super().draw(painter)
        painter.restore()


class NextTrackPreview(QWidget):
    def __init__(self, parent=None, language='pt_BR'):
        super().__init__(parent)
        self.interface_language = language

        self.setFixedSize(430, 92)
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )
        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )

        _set_theme_stylesheet(self, """
            NextTrackPreview {
                background-color: rgba(27, 23, 37, 242);
                border: 1px solid rgba(190, 157, 226, 85);
                border-radius: 19px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)

        shadow = FadingDropShadowEffect(self)
        shadow.setBlurRadius(38)
        shadow.setOffset(0, 11)
        shadow.setColor(QColor(0, 0, 0, 195))
        self._shadow_effect = shadow
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 13)
        layout.setSpacing(13)

        self.cover = CircularPreviewCover(self)
        layout.addWidget(self.cover)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self.heading = QLabel(tr("preview.next", self.interface_language))
        _set_theme_stylesheet(self.heading, "color: #c9a7ef; font-size: 10px; font-weight: 600;"
        )

        self.title = QLabel("")
        _set_theme_stylesheet(self.title, "color: #ffffff; font-size: 14px; font-weight: 600;"
        )

        self.artist = QLabel("")
        _set_theme_stylesheet(self.artist, "color: rgba(255,255,255,165); font-size: 11px;"
        )

        for label in (self.heading, self.title, self.artist):
            label.setMaximumWidth(320)
            label.setTextInteractionFlags(
                Qt.TextInteractionFlag.NoTextInteraction
            )

        text_layout.addWidget(self.heading)
        text_layout.addWidget(self.title)
        text_layout.addWidget(self.artist)
        text_layout.addStretch(1)

        layout.addLayout(text_layout, 1)

        self._display_timer = QTimer(self)
        self._display_timer.setSingleShot(True)
        self._display_timer.setInterval(5000)
        self._display_timer.timeout.connect(self.hide_preview)
        self._visible = False
        self._slide_animation = QPropertyAnimation(
            self,
            b"pos",
            self
        )
        self._hide_finished_connected = False

        curve = QEasingCurve(QEasingCurve.Type.BezierSpline)
        curve.addCubicBezierSegment(
            QPointF(0.18, 0.82),
            QPointF(0.28, 1.08),
            QPointF(1.0, 1.0)
        )
        self._entry_curve = curve

        self._slide_animation.setDuration(560)
        self._slide_animation.setEasingCurve(self._entry_curve)

        self._fade_timer = QTimer(self)
        self._fade_timer.setInterval(16)
        self._fade_timer.timeout.connect(self._animate_fade_out)
        self._fade_started = 0.0
        self._fade_duration = 0.72
        self._fade_start_opacity = 1.0

        parent.installEventFilter(self)
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(
            0.7,
            0.7,
            self.width() - 1.4,
            self.height() - 1.4
        )

        painter.setPen(QColor(190, 157, 226, 115))
        painter.setBrush(QColor(27, 23, 37, 248))
        painter.drawRoundedRect(rect, 20, 20)

        painter.end()
    def _target_position(self):
        parent = self.parentWidget()
        x = (parent.width() - self.width()) // 2
        return QPoint(x, 22)

    def _reposition(self):
        if not self.parentWidget():
            return

        target = self._target_position()

        if self._visible and self._slide_animation.state() != (
            QPropertyAnimation.State.Running
        ):
            self.move(target)
        elif not self._visible:
            self.move(target.x(), -self.height() - 20)

    def eventFilter(self, watched, event):
        if (
            watched is self.parentWidget()
            and event.type() == QEvent.Type.Resize
        ):
            self._reposition()

        return super().eventFilter(watched, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def show_track(self, track):
        self._hide_generation = getattr(
            self,
            "_hide_generation",
            0
        ) + 1

        self._display_timer.stop()

        title = track.get("title") or Path(
            track.get("path", "")
        ).stem

        artist = track.get("artist") or "Artista desconhecido"

        self.title.setText(title)
        self.artist.setText(artist)
        self.cover.set_cover(
            track.get("cover_path"),
            track.get("title") or Path(track.get("path", "")).stem
        )


        if self._hide_finished_connected:
            try:
                self._slide_animation.finished.disconnect(
                    self._finish_hide
                )
            except (RuntimeError, TypeError):
                pass
            self._hide_finished_connected = False

        self._slide_animation.stop()

        target = self._target_position()

        self.move(target.x(), -self.height() - 20)
        self._fade_timer.stop()
        self._shadow_effect.set_opacity(1.0)
        self._shadow_effect.setEnabled(True)
        self.show()
        self.raise_()
        self._visible = True

        self._slide_animation.setStartValue(self.pos())
        self._slide_animation.setEndValue(target)
        self._slide_animation.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )
        self._slide_animation.setDuration(850)
        self._slide_animation.start()
        self._display_timer.start()

    def finish(self):
        # A prévia segue seu ciclo visual independente de 5 segundos.
        pass

    def _animate_fade_out(self):
        elapsed = time.monotonic() - self._fade_started
        progress = max(0.0, min(1.0, elapsed / self._fade_duration))

        if progress < 0.5:
            eased = 4.0 * progress ** 3
        else:
            eased = 1.0 - ((-2.0 * progress + 2.0) ** 3) / 2.0

        opacity = self._fade_start_opacity * (1.0 - eased)
        self._shadow_effect.set_opacity(opacity)

        if progress >= 1.0:
            self._fade_timer.stop()
            self._shadow_effect.set_opacity(0.0)

    def hide_preview(self):
        self._hide_generation = getattr(
            self,
            "_hide_generation",
            0
        ) + 1

        self._display_timer.stop()

        if not self._visible:
            return

        self._slide_animation.stop()
        self._visible = False

        start = self.pos()
        end = QPoint(start.x(), -self.height() - 20)

        self._slide_animation.setDuration(720)
        self._slide_animation.setEasingCurve(
            QEasingCurve.Type.InOutCubic
        )
        self._slide_animation.setStartValue(start)
        self._slide_animation.setEndValue(end)

        self._fade_timer.stop()
        self._fade_start_opacity = 1.0
        self._shadow_effect.set_opacity(1.0)
        self._fade_started = time.monotonic()
        self._fade_timer.start()

        if not self._hide_finished_connected:
            self._slide_animation.finished.connect(
                self._finish_hide
            )
            self._hide_finished_connected = True

        self._slide_animation.start()

    def _finish_hide(self):
        if self._hide_finished_connected:
            try:
                self._slide_animation.finished.disconnect(
                    self._finish_hide
                )
            except (RuntimeError, TypeError):
                pass
            self._hide_finished_connected = False

        self._fade_timer.stop()
        self._shadow_effect.set_opacity(0.0)
        self._shadow_effect.setEnabled(False)
        self.hide()


class FullscreenPlayer(QDialog):
    def __init__(self, controller):
        super().__init__(controller)

        self.controller = controller
        self._seeking = False
        self._track_pixmap = QPixmap()

        self._current_cover_path = None
        self._pending_cover_pixmap = QPixmap()
        self._cover_transition_group = None
        self._cover_transition_widgets = []
        self._background_transition_animation = None
        self._background_transition_container = None
        self._background_transition_label = None
        self._background_from_pixmap = QPixmap()
        self._background_pending_pixmap = QPixmap()


        self.setWindowTitle("Serifa Music")
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint
        )
        self.setModal(False)
        self.setMinimumSize(
            int(get_theme_value("components", "fullscreen", "minimum_width", 640)),
            int(get_theme_value("components", "fullscreen", "minimum_height", 480))
        )
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.background_label = QLabel(self)
        self.background_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.background_blur = QGraphicsBlurEffect()
        self.background_blur.setBlurRadius(65)
        self.background_label.setGraphicsEffect(
            self.background_blur
        )

        self.overlay = QFrame(self)
        _set_theme_stylesheet(self.overlay, "background-color: rgba(10, 8, 16, 155);"
        )

        self.content = QWidget(self)
        self.content.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.next_track_preview = NextTrackPreview(
            self, self.controller.interface_language
        )

        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(48, 34, 48, 28)
        layout.setSpacing(12)

        layout.addStretch(2)

        self.cover = FullscreenCover()
        self.cover.setFixedSize(
            int(get_theme_value("components", "fullscreen", "cover_size", 480)),
            int(get_theme_value("components", "fullscreen", "cover_size", 480))
        )

        shadow = QGraphicsDropShadowEffect(self.cover)
        shadow.setBlurRadius(48)
        shadow.setOffset(0, 14)
        shadow.setColor(QColor(0, 0, 0, 175))
        self.cover.setGraphicsEffect(shadow)

        cover_layout = QHBoxLayout()
        cover_layout.addStretch(1)
        cover_layout.addWidget(self.cover)
        cover_layout.addStretch(1)
        layout.addLayout(cover_layout)

        layout.addSpacing(24)

        self.title_label = QLabel("Nenhuma música")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _set_theme_stylesheet(self.title_label, "color: white; font-size: 27px; font-weight: 600;"
        )
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        self.artist_label = QLabel("Selecione uma faixa")
        self.artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _set_theme_stylesheet(self.artist_label, "color: rgba(255,255,255,190); font-size: 15px;"
        )
        self.artist_label.setWordWrap(True)
        layout.addWidget(self.artist_label)

        layout.addStretch(2)

        controls = QWidget()
        self.controls_widget = controls

        self.controls_opacity = QGraphicsOpacityEffect(controls)
        self.controls_opacity.setOpacity(1.0)
        controls.setGraphicsEffect(self.controls_opacity)

        self.controls_animation = QPropertyAnimation(
            self.controls_opacity,
            b"opacity",
            self
        )
        self.controls_animation.setDuration(220)
        self.controls_animation.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )
        self.controls_animation.finished.connect(
            self._finish_controls_fade
        )

        self._controls_hidden = False
        self._last_cursor_position = QCursor.pos()

        self.controls_hide_timer = QTimer(self)
        self.controls_hide_timer.setSingleShot(True)
        self.controls_hide_timer.setInterval(4000)
        self.controls_hide_timer.timeout.connect(
            self._hide_controls
        )

        self.cursor_watch_timer = QTimer(self)
        self.cursor_watch_timer.setInterval(120)
        self.cursor_watch_timer.timeout.connect(
            self._check_cursor_activity
        )

        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(12)

        self.current_time_label = QLabel("0:00")
        self.duration_label = QLabel("0:00")

        for label in (
            self.current_time_label,
            self.duration_label
        ):
            _set_theme_stylesheet(label, "color: rgba(255,255,255,190); font-size: 12px;"
            )

        self.progress_slider = ClickableSlider(
            Qt.Orientation.Horizontal
        )
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setValue(0)
        _set_theme_stylesheet(self.progress_slider, """
            QSlider::groove:horizontal {
                height: 4px;
                background: rgba(255,255,255,65);
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: white;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                width: 12px;
                height: 12px;
                margin: -4px 0;
                background: white;
                border-radius: 6px;
            }
        """)

        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(12)
        progress_layout.addWidget(self.current_time_label)
        progress_layout.addWidget(self.progress_slider, 1)
        progress_layout.addWidget(self.duration_label)
        controls_layout.addLayout(progress_layout)

        buttons = QHBoxLayout()
        buttons.setAlignment(Qt.AlignmentFlag.AlignCenter)
        buttons.setSpacing(28)

        self.shuffle_button = self._make_button("player.shuffle", 22)
        self.previous_button = self._make_button("player.previous", 22)
        self.play_button = self._make_button("player.play", 40)
        self.next_button = self._make_button("player.next", 22)
        self.repeat_button = self._make_button("player.repeat", 22)
        self.infinity_button = self._make_button("player.infinity", 22)
        self.infinity_button.setEnabled(True)
        self.infinity_button.setToolTip(tr("controls.infinity", self.controller.interface_language))

        self.queue_button = self._make_button("player.queue", 22)
        self.queue_button.setToolTip(tr("controls.open_queue", self.controller.interface_language))

        self.favorite_button = self._make_button("actions.favorite", 22)
        self.favorite_button.setEnabled(False)

        self.add_queue_button = self._make_button("actions.add_playlist", 22)
        self.add_queue_button.setEnabled(False)
        self.add_queue_button.setToolTip(
            tr("context.add_queue", self.controller.interface_language)
        )

        self.play_button.setFixedSize(58, 58)
        _set_theme_stylesheet(self.play_button, """
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background: transparent;
            }
        """)

        for button in (
            self.shuffle_button,
            self.previous_button,
            self.play_button,
            self.next_button,
            self.repeat_button,
            self.queue_button,
            self.infinity_button
        ):
            buttons.addWidget(button)

        self.fullscreen_buttons_layout = buttons

        controls_layout.addLayout(buttons)

        buttons.insertWidget(0, self.favorite_button)
        buttons.insertWidget(1, self.add_queue_button)
        layout.addWidget(controls)

        self.bottom_gradient = QFrame(self)
        self.bottom_gradient.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )
        _set_theme_stylesheet(self.bottom_gradient, """
            QFrame {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(0, 0, 0, 0),
                    stop: 0.45 rgba(0, 0, 0, 105),
                    stop: 1 rgba(0, 0, 0, 225)
                );
                border: none;
            }
        """)
        self.bottom_gradient.setGeometry(
            0, max(0, self.height() - 250), self.width(), 250
        )

        self.bottom_gradient_opacity = QGraphicsOpacityEffect(
            self.bottom_gradient
        )
        self.bottom_gradient_opacity.setOpacity(1.0)
        self.bottom_gradient.setGraphicsEffect(
            self.bottom_gradient_opacity
        )

        self.bottom_gradient_animation = QPropertyAnimation(
            self.bottom_gradient_opacity,
            b"opacity",
            self
        )
        self.bottom_gradient_animation.setDuration(220)
        self.bottom_gradient_animation.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )

        self.bottom_gradient.raise_()
        self.content.raise_()

        self.busy_overlay = PlayerBusyOverlay(controls)
        self.busy_overlay.setGeometry(controls.rect())
        self.busy_overlay.hide()

        controls.installEventFilter(self)

        self._build_queue_panel()

        self.exit_fullscreen_button = AppearanceIconButton(
            self.controller.appearance.icon_manager,
            "player.exit_fullscreen", 21, self
        )
        self.exit_fullscreen_button.setFixedSize(40, 40)
        self.exit_fullscreen_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.exit_fullscreen_button.setToolTip(tr("controls.exit_fullscreen", self.controller.interface_language))
        _set_theme_stylesheet(self.exit_fullscreen_button, """
            QPushButton {
                color: rgba(255,255,255,205);
                background: transparent;
                border: none;
                font-size: 21px;
            }
            QPushButton:hover {
                color: white;
                background: transparent;
            }
        """)
        self.exit_fullscreen_button.clicked.connect(self.close)

        self.exit_fullscreen_button.move(
            self.width() - 54,
            self.height() - 54
        )

        self.exit_button_animation = QPropertyAnimation(
            self.exit_fullscreen_button,
            b"pos",
            self
        )
        self.exit_button_animation.setDuration(280)
        self.exit_button_animation.setEasingCurve(
            QEasingCurve.Type.InOutCubic
        )

        self.exit_fullscreen_button.raise_()

        self.shuffle_button.clicked.connect(
            controller.toggle_shuffle
        )
        self.previous_button.clicked.connect(
            controller.play_previous_track
        )
        self.play_button.clicked.connect(
            controller.toggle_playback
        )
        self.next_button.clicked.connect(
            controller.play_next_track
        )
        self.repeat_button.clicked.connect(
            controller.cycle_repeat
        )
        self.infinity_button.clicked.connect(
            controller.toggle_infinity_play
        )
        self.queue_button.clicked.connect(self.toggle_queue_panel)
        self.favorite_button.clicked.connect(self._toggle_current_favorite)
        self.add_queue_button.clicked.connect(self._add_current_to_queue)

        self.progress_slider.sliderPressed.connect(
            self._start_seeking
        )
        self.progress_slider.sliderReleased.connect(
            self._finish_seeking
        )


    def _build_queue_panel(self):
        self.queue_panel_width = 360
        self.queue_panel_open = False
        self.queue_panel_pinned = False

        self.queue_panel = QFrame(self)
        self.queue_panel.setObjectName("fullscreenQueuePanel")
        self.queue_panel.setFixedWidth(self.queue_panel_width)
        _set_theme_stylesheet(self.queue_panel, """
            QFrame#fullscreenQueuePanel {
                background-color: rgba(24, 21, 32, 246);
                border-left: 1px solid rgba(255,255,255,25);
            }
        """)

        panel_layout = QVBoxLayout(self.queue_panel)
        panel_layout.setContentsMargins(20, 22, 16, 18)
        panel_layout.setSpacing(14)

        header = QHBoxLayout()
        header.setSpacing(10)

        heading = QLabel(tr("queue.title", self.controller.interface_language))
        _set_theme_stylesheet(heading, "color: white; font-size: 17px; font-weight: 600;"
        )
        header.addWidget(heading, 1)

        self.queue_pin_button = QPushButton("⌁")
        self.queue_pin_button.setFixedSize(34, 34)
        self.queue_pin_button.setToolTip(tr("queue.pin", self.controller.interface_language))
        self.queue_pin_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        _set_theme_stylesheet(self.queue_pin_button, """
            QPushButton {
                color: rgba(255,255,255,180);
                background: rgba(255,255,255,12);
                border: 1px solid rgba(255,255,255,25);
                border-radius: 8px;
                font-size: 18px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,25);
                color: white;
            }
        """)
        self.queue_pin_button.clicked.connect(
            self.toggle_queue_pin
        )
        header.addWidget(self.queue_pin_button)

        close_button = QPushButton("×")
        close_button.setFixedSize(34, 34)
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.setToolTip(tr("queue.close", self.controller.interface_language))
        _set_theme_stylesheet(close_button, """
            QPushButton {
                color: rgba(255,255,255,180);
                background: rgba(255,255,255,12);
                border: 1px solid rgba(255,255,255,25);
                border-radius: 8px;
                font-size: 20px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,25);
                color: white;
            }
        """)
        close_button.clicked.connect(self.close_queue_panel)
        header.addWidget(close_button)

        panel_layout.addLayout(header)

        current_heading = QLabel(tr("queue.now_playing", self.controller.interface_language))
        _set_theme_stylesheet(current_heading, """
            color: rgba(255,255,255,115);
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
        """)
        panel_layout.addWidget(current_heading)

        self.queue_current_label = QLabel(tr("queue.no_music", self.controller.interface_language))
        self.queue_current_label.setWordWrap(True)
        _set_theme_stylesheet(self.queue_current_label, """
            color: white;
            font-size: 13px;
            font-weight: 600;
            background: rgba(255,255,255,12);
            border: 1px solid rgba(255,255,255,20);
            border-radius: 9px;
            padding: 12px;
        """)
        panel_layout.addWidget(self.queue_current_label)

        upcoming_heading = QLabel(tr("queue.upcoming", self.controller.interface_language).upper())
        _set_theme_stylesheet(upcoming_heading, """
            color: rgba(255,255,255,115);
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
            margin-top: 7px;
        """)
        panel_layout.addWidget(upcoming_heading)

        self.queue_scroll = QScrollArea()
        self.queue_scroll.setWidgetResizable(True)
        self.queue_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.queue_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        _set_theme_stylesheet(self.queue_scroll, """
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)

        self.queue_list_widget = QueueDropContainer()
        self.queue_list_widget.drop_callback = (
            self.controller.reorder_queue_entry
        )

        self.queue_list_layout = QVBoxLayout(
            self.queue_list_widget
        )
        self.queue_list_layout.setContentsMargins(0, 2, 5, 2)
        self.queue_list_layout.setSpacing(7)

        self.queue_empty_label = QLabel(
            tr("queue.empty", self.controller.interface_language)
        )
        self.queue_empty_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.queue_empty_label.setWordWrap(True)
        _set_theme_stylesheet(self.queue_empty_label, """
            color: rgba(255,255,255,125);
            font-size: 12px;
            padding: 25px;
        """)

        self.queue_list_layout.addWidget(self.queue_empty_label)
        self.queue_list_layout.addStretch(1)

        self.queue_scroll.setWidget(self.queue_list_widget)
        panel_layout.addWidget(self.queue_scroll, 1)

        self.queue_animation = QPropertyAnimation(
            self.queue_panel,
            b"pos",
            self
        )
        self.queue_animation.setDuration(280)
        self.queue_animation.setEasingCurve(
            QEasingCurve.Type.InOutCubic
        )

        self.content_animation = QPropertyAnimation(
            self.content,
            b"geometry",
            self
        )
        self.content_animation.setDuration(280)
        self.content_animation.setEasingCurve(
            QEasingCurve.Type.InOutCubic
        )

        self.queue_panel.move(self.width(), 0)
        self.queue_panel.raise_()

    def toggle_queue_panel(self):
        if self.queue_panel_open:
            if self.queue_panel_pinned:
                return
            self.set_queue_panel_open(False)
        else:
            self.set_queue_panel_open(True)

    def _update_responsive_layout(self, content_width=None):
        if content_width is None:
            content_width = (
                max(280, self.width() - self.queue_panel_width)
                if self.queue_panel_open else self.width()
            )

        content_width = max(280, int(content_width))

        layout = self.content.layout()

        if self.queue_panel_open:
            layout.setContentsMargins(18, 24, 18, 22)
        else:
            layout.setContentsMargins(48, 34, 48, 28)

        available_width = max(
            150,
            content_width - layout.contentsMargins().left()
            - layout.contentsMargins().right()
        )

        available_height = max(150, self.height() - 210)

        cover_size = min(
            int(available_height * 0.58),
            int(available_width * 0.72),
            520
        )

        cover_size = max(150, cover_size)
        self.cover.setFixedSize(cover_size, cover_size)

        button_widths = (
            22 + 22 + 58 + 22 + 22 + 22 + 22
        )

        intervals = 6
        spacing = max(
            4,
            min(28, (available_width - button_widths) // intervals)
        )

        self.fullscreen_buttons_layout.setSpacing(spacing)


    def set_queue_panel_open(self, opened):
        opened = bool(opened)

        if self.queue_panel_open == opened:
            return

        self.queue_panel_open = opened

        if opened:
            self.refresh_queue()
            self.queue_panel.raise_()

        self.queue_animation.stop()
        self.queue_animation.setStartValue(
            self.queue_panel.pos()
        )

        target_x = (
            self.width() - self.queue_panel_width
            if opened else self.width()
        )

        self.queue_animation.setEndValue(
            QPoint(target_x, 0)
        )

        self.content_animation.stop()

        target_width = (
            max(280, self.width() - self.queue_panel_width)
            if opened else self.width()
        )

        self.content_animation.setStartValue(
            self.content.geometry()
        )
        self.content_animation.setEndValue(
            QRect(0, 0, target_width, self.height())
        )

        self._update_responsive_layout(target_width)

        self.exit_button_animation.stop()
        self.exit_button_animation.setStartValue(
            self.exit_fullscreen_button.pos()
        )
        self.exit_button_animation.setEndValue(
            QPoint(
                target_width - 54,
                self.height() - 54
            )
        )

        self.queue_animation.start()
        self.content_animation.start()
        self.exit_button_animation.start()

        _set_theme_stylesheet(self.queue_button, "color: #d7b9f5; background: rgba(160,110,210,35);"
            "border: none; font-size: 22px;"
            if opened else
            "color: white; background: transparent;"
            "border: none; font-size: 22px;"
        )



    def toggle_queue_pin(self):
        self.queue_panel_pinned = not self.queue_panel_pinned

        if self.queue_panel_pinned:
            self.queue_pin_button.setText("⌖")
            self.queue_pin_button.setToolTip(tr("queue.unpin", self.controller.interface_language))
            if not self.queue_panel_open:
                self.set_queue_panel_open(True)
        else:
            self.queue_pin_button.setText("⌁")
            self.queue_pin_button.setToolTip(tr("queue.pin", self.controller.interface_language))

    def close_queue_panel(self):
        self.queue_panel_pinned = False
        self.queue_pin_button.setText("⌁")
        self.queue_pin_button.setToolTip(tr("queue.pin", self.controller.interface_language))
        self.set_queue_panel_open(False)

    def refresh_queue(self):
        if not hasattr(self, "queue_list_layout"):
            return

        current_entry = self.controller.playback_queue.get_current_entry()
        current_track = (
            current_entry.get("track")
            if current_entry else self.controller.current_track
        )

        if current_track:
            title = (
                current_track.get("title")
                or Path(current_track.get("path", "")).stem
                or tr("queue.unknown_track", self.controller.interface_language)
            )
            artist = current_track.get("artist") or tr("queue.unknown_artist", self.controller.interface_language)
            album = current_track.get("album") or tr("queue.unknown_album", self.controller.interface_language)

            self.queue_current_label.setText(
                f"♫  {title}\n{artist} — {album}"
            )
        else:
            self.queue_current_label.setText(tr("queue.no_music", self.controller.interface_language))

        while self.queue_list_layout.count():
            item = self.queue_list_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        entries = self.controller.playback_queue.get_upcoming_entries()

        if not entries:
            self.queue_empty_label = QLabel(tr("queue.empty", self.controller.interface_language))
            self.queue_empty_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            self.queue_empty_label.setWordWrap(True)
            _set_theme_stylesheet(self.queue_empty_label, """
                color: rgba(255,255,255,125);
                font-size: 12px;
                padding: 25px;
            """)
            self.queue_list_layout.addWidget(
                self.queue_empty_label
            )
            self.queue_list_layout.addStretch(1)
            return

        for entry in entries:
            row = FullscreenQueueRow(
                entry["id"],
                entry["track"],
                self.controller
            )

            row.play_requested.connect(
                self.controller.play_queue_entry
            )
            row.remove_requested.connect(
                self.controller.remove_queue_entry
            )

            self.queue_list_layout.addWidget(row)

        self.queue_list_layout.addStretch(1)

    def _sync_favorite_button(self):
        track = self.controller.current_track

        if not track or not track.get("id"):
            self.favorite_button.setEnabled(False)
            self.favorite_button.set_active(False)
            self.favorite_button.setToolTip(
                tr(
                    "controls.no_favorite_track",
                    self.controller.interface_language
                )
            )
            self.add_queue_button.setEnabled(False)
            return

        is_favorite = self.controller.scanner.is_track_favorite(
            track["id"]
        )

        self.favorite_button.setEnabled(True)
        self.favorite_button.set_active(bool(is_favorite))
        self.favorite_button.setToolTip(
            tr(
                "controls.remove_favorite",
                self.controller.interface_language
            )
            if is_favorite
            else tr(
                "controls.add_favorite",
                self.controller.interface_language
            )
        )

        self.add_queue_button.setEnabled(True)
        self.add_queue_button.setToolTip(
            tr(
                "context.add_queue",
                self.controller.interface_language
            )
        )


    def _toggle_current_favorite(self):
        track = self.controller.current_track

        if not track or not track.get("id"):
            return

        self.controller.toggle_track_favorite(track["id"])
        self._sync_favorite_button()


    def _add_current_to_queue(self):
        self.controller.show_add_to_playlist_menu(
            self.add_queue_button
        )


    def _show_controls(self):
        self._controls_hidden = False

        self.controls_widget.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            False
        )

        self.controls_animation.stop()
        self.controls_animation.setStartValue(
            self.controls_opacity.opacity()
        )
        self.controls_animation.setEndValue(1.0)
        self.controls_animation.start()

        self.bottom_gradient_animation.stop()
        self.bottom_gradient_animation.setStartValue(
            self.bottom_gradient_opacity.opacity()
        )
        self.bottom_gradient_animation.setEndValue(1.0)
        self.bottom_gradient_animation.start()

        self.controls_hide_timer.start(4000)


    def _hide_controls(self):
        cursor_position = self.controls_widget.mapFromGlobal(
            QCursor.pos()
        )

        if self.controls_widget.rect().contains(cursor_position):
            self.controls_hide_timer.start(1000)
            return

        if self._seeking or self.busy_overlay.isVisible():
            self.controls_hide_timer.start(1000)
            return

        self._controls_hidden = True

        self.controls_animation.stop()
        self.controls_animation.setStartValue(
            self.controls_opacity.opacity()
        )
        self.controls_animation.setEndValue(0.0)
        self.controls_animation.start()

        self.bottom_gradient_animation.stop()
        self.bottom_gradient_animation.setStartValue(
            self.bottom_gradient_opacity.opacity()
        )
        self.bottom_gradient_animation.setEndValue(0.0)
        self.bottom_gradient_animation.start()


    def _finish_controls_fade(self):
        if self._controls_hidden:
            self.controls_widget.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents,
                True
            )


    def _check_cursor_activity(self):
        position = QCursor.pos()

        if position == self._last_cursor_position:
            return

        self._last_cursor_position = position

        if self.frameGeometry().contains(position):
            self._show_controls()


    def _make_button(self, identifier, size):
        button = AppearanceIconButton(
            self.controller.appearance.icon_manager,
            identifier,
            size
        )
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedSize(42, 42)
        _set_theme_stylesheet(button, """
            QPushButton {
                background: transparent;
                border: none;
            }
        """)
        return button


    def _create_cover_transition_layer(self, pixmap):
        wrapper = QWidget(self.content)
        wrapper.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )
        wrapper.setFixedSize(self.cover.size())

        cover = FullscreenCover(wrapper)
        cover.setGeometry(wrapper.rect())
        cover.set_pixmap(pixmap)

        shadow = QGraphicsDropShadowEffect(cover)
        shadow.setBlurRadius(48)
        shadow.setOffset(0, 14)
        shadow.setColor(QColor(0, 0, 0, 175))
        cover.setGraphicsEffect(shadow)

        opacity = QGraphicsOpacityEffect(wrapper)
        opacity.setOpacity(1.0)
        wrapper.setGraphicsEffect(opacity)

        return wrapper, opacity

    def _cancel_cover_transition(self, commit_pending=True):
        group = self._cover_transition_group
        self._cover_transition_group = None

        if group is not None:
            group.stop()
            group.deleteLater()

        for widget in self._cover_transition_widgets:
            widget.hide()
            widget.deleteLater()

        self._cover_transition_widgets = []

        if (
            commit_pending
            and not self._pending_cover_pixmap.isNull()
        ):
            self.cover.set_pixmap(
                self._pending_cover_pixmap
            )

        self._pending_cover_pixmap = QPixmap()

    def _finish_cover_transition(self):
        group = self._cover_transition_group
        self._cover_transition_group = None

        if not self._pending_cover_pixmap.isNull():
            self.cover.set_pixmap(
                self._pending_cover_pixmap
            )

        for widget in self._cover_transition_widgets:
            widget.hide()
            widget.deleteLater()

        self._cover_transition_widgets = []
        self._pending_cover_pixmap = QPixmap()

        if group is not None:
            group.deleteLater()

    def _start_cover_transition(
        self,
        old_pixmap,
        new_pixmap,
        transition
    ):
        center = self.cover.mapTo(
            self.content,
            QPoint(0, 0)
        )

        old_layer, old_opacity = (
            self._create_cover_transition_layer(old_pixmap)
        )

        new_layer, new_opacity = (
            self._create_cover_transition_layer(new_pixmap)
        )

        offset = max(
            70,
            min(130, int(self.cover.width() * 0.22))
        )

        if transition == "next":
            incoming_offset = offset
            outgoing_offset = -offset

        elif transition == "previous":
            incoming_offset = -offset
            outgoing_offset = offset

        else:
            incoming_offset = 0
            outgoing_offset = 0

        old_layer.move(center)
        new_layer.move(
            center.x() + incoming_offset,
            center.y()
        )

        old_opacity.setOpacity(1.0)
        new_opacity.setOpacity(0.0)

        old_layer.show()
        new_layer.show()
        old_layer.raise_()
        new_layer.raise_()

        self._cover_transition_widgets = [
            old_layer,
            new_layer
        ]

        self._pending_cover_pixmap = QPixmap(new_pixmap)

        group = QParallelAnimationGroup(self)
        self._cover_transition_group = group

        duration = 650

        position_easing = QEasingCurve(

            QEasingCurve.Type.BezierSpline

        )

        position_easing.addCubicBezierSegment(

            QPointF(0.30, 0.30),

            QPointF(0.50, 1.0),

            QPointF(1.0, 1.0)

        )

        opacity_easing = QEasingCurve(

            QEasingCurve.Type.InOutCubic

        )
        animations = (
            (
                old_layer,
                b"pos",
                center,
                QPoint(
                    center.x() + outgoing_offset,
                    center.y()
                )
            ),
            (
                new_layer,
                b"pos",
                new_layer.pos(),
                center
            ),
            (
                old_opacity,
                b"opacity",
                1.0,
                0.0
            ),
            (
                new_opacity,
                b"opacity",
                0.0,
                1.0
            )
        )

        for target, prop, start_value, end_value in animations:
            animation = QPropertyAnimation(target, prop)
            animation.setDuration(duration)
            animation.setStartValue(start_value)
            animation.setEndValue(end_value)
            animation.setEasingCurve(
                position_easing
                if prop == b'pos'
                else opacity_easing
            )
            group.addAnimation(animation)

        group.finished.connect(
            self._finish_cover_transition
        )

        group.start()


    def set_track(self, track, transition="fade"):
        self._sync_favorite_button()
        if not track:
            return

        title = (
            track.get("title")
            or Path(track.get("path", "")).stem
            or "Faixa desconhecida"
        )
        artist = track.get("artist") or "Artista desconhecido"
        album = track.get("album") or "Álbum desconhecido"

        self.title_label.setText(title)
        self.artist_label.setText(f"{artist}  —  {album}")
        self.cover.set_fallback_title(title)

        cover_path = track.get("cover_path")
        cover_key = str(cover_path or "")

        if (
            self._cover_transition_group is not None
            and not self._pending_cover_pixmap.isNull()
        ):
            old_pixmap = QPixmap(self._pending_cover_pixmap)
        else:
            old_pixmap = QPixmap(self.cover.pixmap)

        self._cancel_cover_transition(
            commit_pending=True
        )

        new_pixmap = QPixmap()

        if cover_path and Path(cover_path).is_file():
            new_pixmap = QPixmap(str(cover_path))

        same_cover = (
            cover_key == (self._current_cover_path or "")
        )

        self._current_cover_path = cover_key

        if same_cover:
            self._track_pixmap = QPixmap(new_pixmap)
            self._update_background()
            self.cover.set_pixmap(new_pixmap)
            return

        self._start_background_transition(new_pixmap)

        if old_pixmap.isNull() or new_pixmap.isNull():
            self.cover.set_pixmap(new_pixmap)
            return

        self._start_cover_transition(
            old_pixmap,
            new_pixmap,
            transition
        )

    def _start_background_transition(self, new_pixmap):
        if (
            self._background_transition_animation is not None
            and not self._background_pending_pixmap.isNull()
        ):
            old_pixmap = QPixmap(self._background_pending_pixmap)
        else:
            old_pixmap = QPixmap(self._track_pixmap)

        self._cancel_background_transition(
            commit_pending=False
        )

        if old_pixmap.isNull() or new_pixmap.isNull():
            self._track_pixmap = QPixmap(new_pixmap)
            self._background_from_pixmap = QPixmap()
            self._update_background()
            return

        self._track_pixmap = QPixmap(old_pixmap)
        self._background_from_pixmap = QPixmap(old_pixmap)
        self._background_pending_pixmap = QPixmap(new_pixmap)

        container = QWidget(self)
        container.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        label = QLabel(container)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        blur = QGraphicsBlurEffect(label)
        blur.setBlurRadius(65)
        label.setGraphicsEffect(blur)

        opacity = QGraphicsOpacityEffect(container)
        opacity.setOpacity(0.0)
        container.setGraphicsEffect(opacity)

        self._background_transition_container = container
        self._background_transition_label = label

        container.setGeometry(self.rect())
        label.setGeometry(container.rect())

        self._update_background()

        container.show()
        container.stackUnder(self.overlay)

        animation = QPropertyAnimation(
            opacity,
            b"opacity",
            self
        )
        animation.setDuration(1600)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(
            QEasingCurve.Type.InOutCubic
        )

        self._background_transition_animation = animation
        animation.finished.connect(
            self._finish_background_transition
        )
        animation.start()

    def _finish_background_transition(self):
        animation = self._background_transition_animation
        container = self._background_transition_container

        if not self._background_pending_pixmap.isNull():
            self._track_pixmap = QPixmap(
                self._background_pending_pixmap
            )

        self._background_transition_animation = None
        self._background_transition_container = None
        self._background_transition_label = None
        self._background_from_pixmap = QPixmap()
        self._background_pending_pixmap = QPixmap()

        self._update_background()

        if container is not None:
            container.hide()
            container.deleteLater()

        if animation is not None:
            animation.deleteLater()

    def _cancel_background_transition(self, commit_pending=True):
        animation = self._background_transition_animation
        container = self._background_transition_container

        self._background_transition_animation = None
        self._background_transition_container = None
        self._background_transition_label = None

        if animation is not None:
            animation.stop()
            animation.deleteLater()

        if container is not None:
            container.hide()
            container.deleteLater()

        if (
            commit_pending
            and not self._background_pending_pixmap.isNull()
        ):
            self._track_pixmap = QPixmap(
                self._background_pending_pixmap
            )

        self._background_from_pixmap = QPixmap()
        self._background_pending_pixmap = QPixmap()

        if commit_pending:
            self._update_background()

    def _update_background(self):
        transitioning = (
            self._background_transition_container is not None
            and not self._background_pending_pixmap.isNull()
        )

        base_pixmap = (
            self._background_from_pixmap
            if transitioning
            else self._track_pixmap
        )

        if base_pixmap.isNull():
            self.background_label.clear()
            _set_theme_stylesheet(self.background_label, "background: qlineargradient("
                "x1:0,y1:0,x2:1,y2:1,"
                "stop:0 #30243e, stop:1 #100e16);"
            )
        else:
            scaled = base_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            _set_theme_stylesheet(self.background_label, "background: transparent;"
            )
            self.background_label.setPixmap(scaled)

        if transitioning:
            container = self._background_transition_container
            label = self._background_transition_label

            container.setGeometry(self.rect())
            label.setGeometry(container.rect())

            scaled = self._background_pending_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            _set_theme_stylesheet(label, "background: transparent;")
            label.setPixmap(scaled)

    def set_playing(self, playing):
        self.play_button.set_identifier(
            "player.pause" if playing else "player.play"
        )
        self.play_button.setToolTip(
            tr(
                "controls.pause" if playing else "controls.play",
                self.controller.interface_language
            )
        )

    def set_progress(self, position, duration):
        if duration <= 0:
            return

        self.current_time_label.setText(
            self.controller.format_time(position)
        )
        self.duration_label.setText(
            self.controller.format_time(duration)
        )

        if not self._seeking:
            value = round((position / duration) * 1000)
            self.progress_slider.blockSignals(True)
            self.progress_slider.setValue(
                max(0, min(1000, value))
            )
            self.progress_slider.blockSignals(False)

    def _start_seeking(self):
        self._seeking = True

    def _finish_seeking(self):
        self._seeking = False

        if self.controller.audio_player.current_path is None:
            return

        duration = self.controller.audio_player.get_duration()

        if duration <= 0:
            return

        percentage = self.progress_slider.value() / 1000
        self.controller._request_seek(
            duration * percentage,
            duration
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)

        self.background_label.setGeometry(self.rect())
        self.overlay.setGeometry(self.rect())
        self.bottom_gradient.setGeometry(
            0, max(0, self.height() - 250), self.width(), 250
        )

        content_width = (
            max(280, self.width() - self.queue_panel_width)
            if self.queue_panel_open else self.width()
        )

        self.content_animation.stop()
        self.content.setGeometry(
            QRect(0, 0, content_width, self.height())
        )

        self._update_responsive_layout(content_width)
        self._update_background()

        if hasattr(self, "queue_panel"):
            panel_x = (
                self.width() - self.queue_panel_width
                if self.queue_panel_open else self.width()
            )

            self.queue_animation.stop()
            self.queue_panel.move(panel_x, 0)
            self.queue_panel.setFixedHeight(self.height())
            self.queue_panel.raise_()

        if hasattr(self, "exit_fullscreen_button"):
            self.exit_button_animation.stop()
            self.exit_fullscreen_button.move(
                content_width - 54,
                self.height() - 54
            )
            self.exit_fullscreen_button.raise_()



    def set_busy(self, busy):
        if busy:
            self.busy_overlay.setGeometry(
                self.controls_widget.rect()
            )
            self.busy_overlay.show()
            self.busy_overlay.raise_()
        else:
            self.busy_overlay.hide()


    def eventFilter(self, watched, event):
        if (
            watched is self.controls_widget
            and event.type() == QEvent.Type.Resize
        ):
            self.busy_overlay.setGeometry(watched.rect())

            if self.busy_overlay.isVisible():
                self.busy_overlay.raise_()

        if (
            event.type() == QEvent.Type.MouseButtonPress
            and self.queue_panel_open
            and not self.queue_panel_pinned
            and isinstance(watched, QWidget)
            and (watched is self or self.isAncestorOf(watched))
        ):
            if (
                watched is self.queue_button
                or self.queue_button.isAncestorOf(watched)
            ):
                return super().eventFilter(watched, event)

            if (
                watched is self.queue_panel
                or self.queue_panel.isAncestorOf(watched)
            ):
                return super().eventFilter(watched, event)

            self.set_queue_panel_open(False)

        return super().eventFilter(watched, event)


    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            event.accept()
            return

        super().keyPressEvent(event)

    def showEvent(self, event):
        super().showEvent(event)

        app = QApplication.instance()

        if app is not None:
            app.installEventFilter(self)

        if self.controller.current_track:
            self.set_track(self.controller.current_track)

        self.set_playing(
            self.controller.audio_player.is_playing
        )

        if self.queue_panel_open:
            self.refresh_queue()

        self._update_responsive_layout()
        self.setFocus()
        self._last_cursor_position = QCursor.pos()
        self.cursor_watch_timer.start()
        self._show_controls()



    def closeEvent(self, event):
        app = QApplication.instance()

        if app is not None:
            app.removeEventFilter(self)

        self.queue_animation.stop()
        self.content_animation.stop()
        self.exit_button_animation.stop()

        self._cancel_cover_transition(
            commit_pending=False
        )
        self._cancel_background_transition(
            commit_pending=False
        )

        event.accept()
        super().closeEvent(event)
        self.controls_hide_timer.stop()
        self.cursor_watch_timer.stop()






class GlobalSearchOverlay(QWidget):
    def __init__(
        self,
        parent_window,
        host,
        sidebar,
        right_area
    ):
        super().__init__(host)

        self.parent_window = parent_window
        self.host = host
        self.sidebar = sidebar
        self.right_area = right_area

        self.tracks = []
        self.albums = []
        self.artists = []
        self.playlists = []

        self.results = []
        self.result_buttons = []
        self.selected_index = 0

        self._animation = None
        self._sidebar_blur = None
        self._right_blur = None

        self.setObjectName("globalSearchOverlay")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(
            Qt.WidgetAttribute.WA_StyledBackground,
            True
        )

        _set_theme_stylesheet(self, """
            QWidget#globalSearchOverlay {
                background: rgba(9, 7, 14, 178);
            }

            QFrame#searchPanel {
                background: #211d2b;
                border: 1px solid rgba(220, 200, 255, 35);
                border-radius: 20px;
            }

            QLabel#searchHeading {
                color: #f3edf9;
                font-size: 20px;
                font-weight: 700;
            }

            QLabel#searchHint {
                color: #a99bb8;
                font-size: 12px;
            }

            QLineEdit#globalSearchInput {
                background: #17141e;
                border: 1px solid #51445f;
                border-radius: 12px;
                color: #f3edf9;
                padding: 0 16px;
                font-size: 16px;
                selection-background-color: #72558d;
            }

            QLineEdit#globalSearchInput:focus {
                border: 1px solid #b99add;
            }

            QPushButton#searchAction {
                background: #B6F23A;
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 12px;
                color: #211E2A;
            }

            QPushButton#searchAction:hover {
                background: #C8FF4A;
            }

            QPushButton#searchAction:pressed {
                background: #A2D92A;
            }

            QPushButton#searchClose {
                background: transparent;
                border: none;
                color: #a99bb8;
                font-size: 24px;
                border-radius: 8px;
            }

            QPushButton#searchClose:hover {
                background: rgba(255,255,255,0.08);
                color: #ffffff;
            }

            QCheckBox#searchFilter {
                color: #c9bdd5;
                spacing: 7px;
                font-size: 12px;
            }

            QCheckBox#searchFilter::indicator {
                width: 15px;
                height: 15px;
                border-radius: 4px;
                border: 1px solid #71617f;
                background: #17141e;
            }

            QCheckBox#searchFilter::indicator:checked {
                background: #B6F23A;
                border: 1px solid #B6F23A;
            }

            QLabel#searchGroupTitle {
                color: #b99add;
                font-size: 11px;
                font-weight: 700;
                padding-top: 8px;
            }

            QPushButton#searchResult {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 10px;
                color: #f3edf9;
                text-align: left;
                padding: 10px 14px;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton#searchResult:hover,
            QPushButton#searchResult:checked {
                background: rgba(151, 116, 185, 0.18);
                border: 1px solid rgba(185, 154, 221, 0.28);
            }

            QScrollArea#searchResultsScroll {
                background: transparent;
                border: none;
            }

            QWidget#searchResultsContent {
                background: transparent;
            }

            QLabel#searchEmpty {
                color: #a99bb8;
                font-size: 13px;
                padding: 30px 12px;
            }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 30, 30, 30)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.panel = QFrame()
        self.panel.setObjectName("searchPanel")
        self.panel.setFixedWidth(int(get_theme_value("components", "search", "panel_width", 700)))
        self.panel.setMaximumHeight(int(get_theme_value("components", "search", "maximum_height", 640)))

        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(24, 20, 24, 22)
        panel_layout.setSpacing(15)

        heading_row = QHBoxLayout()

        heading = QLabel(tr("search.heading", self.parent_window.interface_language))
        heading.setObjectName("searchHeading")
        heading_row.addWidget(heading)
        heading_row.addStretch()

        self.close_button = QPushButton("×")
        self.close_button.setObjectName("searchClose")
        self.close_button.setFixedSize(34, 34)
        self.close_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.close_button.clicked.connect(self.close_overlay)
        heading_row.addWidget(self.close_button)

        panel_layout.addLayout(heading_row)

        search_row = QHBoxLayout()
        search_row.setSpacing(10)

        self.input = QLineEdit()
        self.input.setObjectName("globalSearchInput")
        self.input.setPlaceholderText(
            tr("search.placeholder", self.parent_window.interface_language)
        )
        self.input.setMinimumHeight(int(get_theme_value("components", "search", "input_height", 54)))
        self.input.textChanged.connect(
            self.schedule_search
        )
        self.input.returnPressed.connect(
            self.activate_selected
        )
        self.input.installEventFilter(self)

        search_row.addWidget(self.input, 1)

        self.search_button = QPushButton()
        self.search_button.setObjectName("searchAction")
        self.search_button.setIcon(
            self.parent_window.appearance.icon_manager.icon(
                "actions.search"
            )
        )
        self.search_button.setIconSize(QSize(28, 28))
        self.search_button.setFixedSize(54, 54)
        self.search_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.search_button.clicked.connect(
            self.refresh_results
        )
        search_row.addWidget(self.search_button)

        panel_layout.addLayout(search_row)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(18)

        self.filters = {}

        for key, label in (
            ("track", tr("search.filter.tracks", self.parent_window.interface_language)),
            ("playlist", tr("search.filter.playlists", self.parent_window.interface_language)),
            ("artist", tr("search.filter.artists", self.parent_window.interface_language)),
            ("album", tr("search.filter.albums", self.parent_window.interface_language))
        ):
            checkbox = QCheckBox(label)
            checkbox.setObjectName("searchFilter")
            checkbox.setChecked(False)
            checkbox.toggled.connect(
                self.refresh_results
            )
            self.filters[key] = checkbox
            filter_row.addWidget(checkbox)

        filter_row.addStretch()
        panel_layout.addLayout(filter_row)

        self.results_scroll = QScrollArea()
        self.results_scroll.setObjectName(
            "searchResultsScroll"
        )
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.results_scroll.setMinimumHeight(300)

        self.results_content = QWidget()
        self.results_content.setObjectName(
            "searchResultsContent"
        )

        self.results_layout = QVBoxLayout(
            self.results_content
        )
        self.results_layout.setContentsMargins(2, 2, 2, 2)
        self.results_layout.setSpacing(5)

        self.results_scroll.setWidget(
            self.results_content
        )
        panel_layout.addWidget(self.results_scroll, 1)

        outer.addWidget(self.panel)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(280)
        self.timer.timeout.connect(
            self.refresh_results
        )

        self.host.installEventFilter(self)
        self.setGeometry(self.host.rect())
        self.hide()

    def eventFilter(self, watched, event):
        if watched is self.host:
            if event.type() == QEvent.Type.Resize:
                self.setGeometry(self.host.rect())

        if watched is self.input:
            if event.type() == QEvent.Type.KeyPress:
                key = event.key()

                if key == Qt.Key.Key_Escape:
                    self.close_overlay()
                    return True

                if key == Qt.Key.Key_Down:
                    self.move_selection(1)
                    return True

                if key == Qt.Key.Key_Up:
                    self.move_selection(-1)
                    return True

        return super().eventFilter(watched, event)

    def mousePressEvent(self, event):
        if not self.panel.geometry().contains(
            event.position().toPoint()
        ):
            self.close_overlay()
            event.accept()
            return

        super().mousePressEvent(event)

    def open(self):
        self.setGeometry(self.host.rect())

        self._load_library_data()
        self.input.clear()
        self.refresh_results()

        self._sidebar_blur = QGraphicsBlurEffect()
        self._sidebar_blur.setBlurRadius(8)
        self.sidebar.setGraphicsEffect(
            self._sidebar_blur
        )

        self._right_blur = QGraphicsBlurEffect()
        self._right_blur.setBlurRadius(8)
        self.right_area.setGraphicsEffect(
            self._right_blur
        )

        self.show()
        self.raise_()
        self.activateWindow()
        self.input.setFocus()

        if self._animation is not None:
            self._animation.stop()

        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        self._opacity.setOpacity(0.0)

        self._animation = QPropertyAnimation(
            self._opacity,
            b"opacity",
            self
        )
        self._animation.setDuration(170)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )
        self._animation.start()

    def close_overlay(self, immediate=False):
        self.timer.stop()

        if not self.isVisible():
            return

        if immediate:
            self._finish_close()
            return

        if self._animation is not None:
            self._animation.stop()

        if not hasattr(self, "_opacity"):
            self._finish_close()
            return

        self._animation = QPropertyAnimation(
            self._opacity,
            b"opacity",
            self
        )
        self._animation.setDuration(130)
        self._animation.setStartValue(
            self._opacity.opacity()
        )
        self._animation.setEndValue(0.0)
        self._animation.setEasingCurve(
            QEasingCurve.Type.InCubic
        )
        self._animation.finished.connect(
            self._finish_close
        )
        self._animation.start()

    def _finish_close(self):
        self.hide()

        self.sidebar.setGraphicsEffect(None)
        self.right_area.setGraphicsEffect(None)

        self._sidebar_blur = None
        self._right_blur = None
        self._opacity = None

        self.setGraphicsEffect(None)

    def _load_library_data(self):
        if not self.parent_window.library_access_ready:
            self.tracks = []
            self.albums = []
            self.artists = []
            self.playlists = []
            return

        scanner = self.parent_window.scanner

        self.tracks = [
            track
            for track in scanner.list_tracks(limit=None)
            if self.parent_window._track_is_available(track)
        ]

        self.albums = scanner.list_albums()
        self.playlists = scanner.list_playlists()

        for playlist in self.playlists:
            playlist_tracks = scanner.list_playlist_tracks(
                playlist.get("id")
            )
            available_tracks = [
                track for track in playlist_tracks
                if self.parent_window._track_is_available(track)
            ]
            playlist["cover_path"] = self._find_cover_path(
                available_tracks
            )

        artist_map = {}
        artist_cover_paths = {}

        for track in self.tracks:
            cover_path = track.get("cover_path")

            if not (
                cover_path
                and Path(cover_path).is_file()
            ):
                cover_path = None

            for field in ("artist", "album_artist"):
                name = (track.get(field) or "").strip()

                if name:
                    key = name.casefold()
                    artist_map.setdefault(key, name)

                    if key not in artist_cover_paths and cover_path:
                        artist_cover_paths[key] = cover_path

        self.artist_cover_paths = artist_cover_paths

        self.artists = sorted(
            artist_map.values(),
            key=str.casefold
        )

    def _find_cover_path(self, tracks):
        return next(
            (
                track.get("cover_path")
                for track in tracks
                if (
                    track.get("cover_path")
                    and Path(track["cover_path"]).is_file()
                )
            ),
            None
        )

    def schedule_search(self):
        self.timer.start()

    def _clear_results(self):
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        self.result_buttons = []
        self.results = []
        self.selected_index = 0

    def _matches(self, query, *values):
        text = " ".join(
            str(value or "")
            for value in values
        ).casefold()

        return query in text

    def refresh_results(self, *args):
        self.timer.stop()
        self._clear_results()

        query = self.input.text().strip().casefold()

        if not self.parent_window.library_access_ready:
            self._show_empty(
                tr("search.wait", self.parent_window.interface_language)
            )
            return

        if not query:
            self._show_empty(
                tr("search.hint", self.parent_window.interface_language)
            )
            return

        active_filters = {
            key
            for key, checkbox in self.filters.items()
            if checkbox.isChecked()
        }

        groups = []

        if not active_filters or "track" in active_filters:
            matches = []

            for track in self.tracks:
                title = (
                    track.get("title")
                    or Path(track.get("path", "")).stem
                )

                if self._matches(
                    query,
                    title,
                    track.get("artist"),
                    track.get("album"),
                    track.get("album_artist"),
                    track.get("genre")
                ):
                    matches.append({
                        "kind": "track",
                        "data": track,
                        "title": title,
                        "subtitle": " • ".join(
                            value for value in (
                                track.get("artist") or "",
                                track.get("album") or ""
                            ) if value
                        ),
                        "cover_path": track.get("cover_path")
                    })

            if matches:
                groups.append((tr("search.group.tracks", self.parent_window.interface_language), matches))

        if not active_filters or "playlist" in active_filters:
            matches = []

            for playlist in self.playlists:
                if self._matches(
                    query,
                    playlist.get("name")
                ):
                    matches.append({
                        "kind": "playlist",
                        "data": playlist,
                        "title": playlist.get("name", tr("search.fallback.playlist", self.parent_window.interface_language)),
                        "subtitle": tr(
                            "search.subtitle.playlist",
                            self.parent_window.interface_language
                        ).format(count=playlist.get("track_count", 0)),
                        "cover_path": playlist.get("cover_path")
                    })

            if matches:
                groups.append((tr("search.group.playlists", self.parent_window.interface_language), matches))

        if not active_filters or "artist" in active_filters:
            matches = []

            for artist in self.artists:
                if self._matches(query, artist):
                    matches.append({
                        "kind": "artist",
                        "data": artist,
                        "title": artist,
                        "subtitle": tr("search.subtitle.artist", self.parent_window.interface_language),
                        "cover_path": self.artist_cover_paths.get(
                            artist.casefold()
                        )
                    })

            if matches:
                groups.append((tr("search.group.artists", self.parent_window.interface_language), matches))

        if not active_filters or "album" in active_filters:
            matches = []

            for album in self.albums:
                if self._matches(
                    query,
                    album.get("album"),
                    album.get("artist")
                ):
                    matches.append({
                        "kind": "album",
                        "data": album,
                        "title": album.get("album", tr("search.fallback.album", self.parent_window.interface_language)),
                        "subtitle": " • ".join(
                            value for value in (
                                album.get("artist") or "",
                                (
                                    tr("search.subtitle.track_count", self.parent_window.interface_language).format(count=album.get("track_count"))
                                    if album.get("track_count") is not None
                                    else ""
                                )
                            ) if value
                        ),
                        "cover_path": album.get("cover_path")
                    })

            if matches:
                groups.append((tr("search.group.albums", self.parent_window.interface_language), matches))

        total = 0
        limit = 45

        for group_name, items in groups:
            if total >= limit:
                break

            label = QLabel(group_name)
            label.setObjectName("searchGroupTitle")
            label.setFixedHeight(24)
            self.results_layout.addWidget(label)

            for result in items:
                if total >= limit:
                    break

                button = QPushButton()
                button.setObjectName("searchResult")
                button.setCheckable(True)
                button.setMinimumHeight(76)
                button.setCursor(
                    Qt.CursorShape.PointingHandCursor
                )

                if result["kind"] == "artist":
                    button.setFixedHeight(76)
                    button.setText(
                        f"{result['title']}\\n"
                        f"{result['subtitle']}"
                    )
                    button.setIconSize(QSize(48, 48))

                    cover_path = result.get("cover_path")

                    if cover_path and Path(cover_path).is_file():
                        source_pixmap = QPixmap(str(cover_path))

                        if not source_pixmap.isNull():
                            scaled = source_pixmap.scaled(
                                QSize(48, 48),
                                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                Qt.TransformationMode.SmoothTransformation
                            )

                            crop_x = (scaled.width() - 48) // 2
                            crop_y = (scaled.height() - 48) // 2

                            circular_pixmap = QPixmap(48, 48)
                            circular_pixmap.fill(
                                Qt.GlobalColor.transparent
                            )

                            painter = QPainter(circular_pixmap)
                            painter.setRenderHint(
                                QPainter.RenderHint.Antialiasing
                            )
                            painter.setRenderHint(
                                QPainter.RenderHint.SmoothPixmapTransform
                            )

                            clip_path = QPainterPath()
                            clip_path.addEllipse(0, 0, 48, 48)

                            painter.setClipPath(clip_path)
                            painter.drawPixmap(
                                -crop_x,
                                -crop_y,
                                scaled
                            )
                            painter.end()

                            button.setIcon(QIcon(circular_pixmap))

                else:
                    button.setText(
                        f"{result['title']}\n"
                        f"{result['subtitle']}"
                    )
                    button.setIconSize(QSize(48, 48))

                    cover_path = result.get("cover_path")

                    if cover_path and Path(cover_path).is_file():
                        cover_pixmap = QPixmap(str(cover_path))

                        if not cover_pixmap.isNull():
                            button.setIcon(QIcon(cover_pixmap))

                button.clicked.connect(
                    lambda checked=False, item=result:
                        self.select_result(item)
                )

                self.results_layout.addWidget(button)
                self.result_buttons.append(button)
                self.results.append(result)
                total += 1

        if total:
            self.results_layout.addStretch(1)

        if not total:
            self._show_empty(
                tr("search.empty", self.parent_window.interface_language)
            )

        self._update_selection()

    def _show_empty(self, message):
        label = QLabel(message)
        label.setObjectName("searchEmpty")
        label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        label.setWordWrap(True)
        self.results_layout.addWidget(label)

    def move_selection(self, direction):
        if not self.result_buttons:
            return

        self.selected_index = (
            self.selected_index + direction
        ) % len(self.result_buttons)

        self._update_selection()

    def _update_selection(self):
        for index, button in enumerate(self.result_buttons):
            button.setChecked(
                index == self.selected_index
            )

        if self.result_buttons:
            self.results_scroll.ensureWidgetVisible(
                self.result_buttons[self.selected_index]
            )

    def activate_selected(self):
        if not self.results:
            return

        self.select_result(
            self.results[self.selected_index]
        )

    def select_result(self, result):
        self.close_overlay(immediate=True)
        self.parent_window.handle_global_search_result(
            result
        )



class SplashScreen(QWidget):
    # ==================================================
    # SPLASHSCREEN CONFIGURATION
    # Edite esta seção para personalizar a apresentação.
    # ==================================================

    BRAND_NAME = "SERIFA MUSIC"
    TAGLINE = "Sua música. Do seu jeito."

    INITIAL_STATUS = "Preparando sua biblioteca..."
    READY_STATUS = "Tudo pronto!"

    BACKGROUND_COLOR = "#17151e"
    PANEL_COLOR = "#211e2a"
    ACCENT_COLOR = "#b58ae0"
    TEXT_COLOR = "#f3edf9"
    MUTED_COLOR = "#95899f"

    WINDOW_WIDTH = 680
    WINDOW_HEIGHT = 380

    MINIMUM_DISPLAY_TIME = 1800

    USE_CUSTOM_IMAGE = True
    CUSTOM_IMAGE_PATH = "assets/splash.png"

    # ==================================================

    def __init__(self, language=None):
        super().__init__()

        app = QApplication.instance()
        self.appearance = (
            app.property("serifa_appearance_manager")
            if app is not None else None
        )

        configuration = (
            self.appearance.splash
            if self.appearance is not None else {}
        )

        brand = configuration.get("marca", {})
        texts = configuration.get("textos", {})
        colors = configuration.get("cores", {})
        window = configuration.get("janela", {})
        image = configuration.get("imagem", {})
        logo = configuration.get("logotipo", {})

        self.language = language or "pt_BR"
        language_key = (
            "en" if self.language.lower().startswith("en")
            else "pt_BR"
        )
        localized = texts.get(language_key, {})

        self.BRAND_NAME = brand.get("nome", self.BRAND_NAME)
        self.TAGLINE = localized.get("slogan", self.TAGLINE)
        self.INITIAL_STATUS = localized.get(
            "status_inicial", self.INITIAL_STATUS
        )
        self.READY_STATUS = localized.get(
            "status_pronto", self.READY_STATUS
        )

        self.BACKGROUND_COLOR = colors.get(
            "fundo", self.BACKGROUND_COLOR
        )
        self.PANEL_COLOR = colors.get(
            "painel", self.PANEL_COLOR
        )
        self.ACCENT_COLOR = colors.get(
            "destaque", self.ACCENT_COLOR
        )
        self.TEXT_COLOR = colors.get(
            "texto", self.TEXT_COLOR
        )
        self.MUTED_COLOR = colors.get(
            "texto_discreto", self.MUTED_COLOR
        )

        self.WINDOW_WIDTH = int(
            window.get("largura", self.WINDOW_WIDTH)
        )
        self.WINDOW_HEIGHT = int(
            window.get("altura", self.WINDOW_HEIGHT)
        )
        self.MINIMUM_DISPLAY_TIME = int(
            window.get("tempo_minimo_ms", self.MINIMUM_DISPLAY_TIME)
        )

        self.USE_CUSTOM_IMAGE = bool(
            image.get("usar_imagem", self.USE_CUSTOM_IMAGE)
        )
        self.CUSTOM_IMAGE_PATH = image.get(
            "arquivo", "customization/images/splash.png"
        )

        self.USE_CUSTOM_LOGO = bool(
            logo.get("usar_logotipo", False)
        )
        self.CUSTOM_LOGO_PATH = logo.get(
            "arquivo", "customization/logos/logo.png"
        )
        self.LOGO_WIDTH = int(logo.get("largura", 100))
        self.LOGO_HEIGHT = int(logo.get("altura", 100))

        self.language = language or 'pt_BR'
        self._started_at = time.monotonic()
        self._source_pixmap = None

        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        if self.USE_CUSTOM_IMAGE:
            self.setAttribute(
                Qt.WidgetAttribute.WA_TranslucentBackground,
                True
            )
            self.setAttribute(
                Qt.WidgetAttribute.WA_NoSystemBackground,
                True
            )

        self.setFixedSize(
            self.WINDOW_WIDTH,
            self.WINDOW_HEIGHT
        )

        splash_background = (
            "transparent"
            if self.USE_CUSTOM_IMAGE
            else self.BACKGROUND_COLOR
        )

        _set_theme_stylesheet(self, f"""
            QWidget {{
                background: {splash_background};
                color: {self.TEXT_COLOR};
                font-family: "Sans Serif";
            }}

            QFrame#splashPanel {{
                background: {self.PANEL_COLOR};
                border: 1px solid #393243;
                border-radius: 18px;
            }}

            QLabel#splashLogo {{
                color: {self.ACCENT_COLOR};
                font-size: 76px;
                font-weight: 800;
                background: transparent;
            }}

            QLabel#splashBrand {{
                color: {self.TEXT_COLOR};
                font-size: 23px;
                font-weight: 800;
                letter-spacing: 3px;
                background: transparent;
            }}

            QLabel#splashTagline {{
                color: {self.MUTED_COLOR};
                font-size: 13px;
                background: transparent;
            }}

            QLabel#splashStatus {{
                color: {self.MUTED_COLOR};
                font-size: 11px;
                background: transparent;
            }}

            QProgressBar {{
                background: #302a3b;
                border: none;
                border-radius: 3px;
                height: 5px;
                text-align: center;
            }}

            QProgressBar::chunk {{
                background: {self.ACCENT_COLOR};
                border-radius: 3px;
            }}
        """)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setGeometry(self.rect())
        _set_theme_stylesheet(
            self.image_label,
            "background: transparent; border: none;"
        )

        overlay = QWidget(self)
        overlay.setObjectName("splashOverlay")
        overlay.setGeometry(self.rect())
        overlay.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )
        _set_theme_stylesheet(
            overlay,
            "background: transparent; border: none;"
        )

        overlay_layout = QVBoxLayout(overlay)
        overlay_layout.setContentsMargins(30, 22, 30, 22)
        overlay_layout.setSpacing(12)

        self.placeholder = QWidget()
        placeholder_layout = QVBoxLayout(self.placeholder)
        placeholder_layout.setContentsMargins(0, 0, 0, 0)
        placeholder_layout.setSpacing(2)

        self.logo_label = QLabel("S")
        self.logo_label.setObjectName("splashLogo")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setFixedSize(
            self.LOGO_WIDTH, self.LOGO_HEIGHT
        )

        self.brand_label = QLabel(self.BRAND_NAME)
        self.brand_label.setObjectName("splashBrand")
        self.brand_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.tagline_label = QLabel(self.TAGLINE)
        self.tagline_label.setObjectName("splashTagline")
        self.tagline_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        placeholder_layout.addWidget(self.logo_label)
        placeholder_layout.addWidget(self.brand_label)
        placeholder_layout.addWidget(self.tagline_label)

        overlay_layout.addStretch(1)
        overlay_layout.addWidget(self.placeholder, 1)

        self.status_label = QLabel(self.INITIAL_STATUS)
        self.status_label.setObjectName("splashStatus")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        overlay_layout.addWidget(self.progress_bar)

        overlay.raise_()

        self._load_custom_logo()
        self._load_custom_image()
        self._center_on_screen()

    def _load_custom_logo(self):
        if not self.USE_CUSTOM_LOGO:
            return

        project_root = Path(__file__).resolve().parent.parent
        logo_path = project_root / self.CUSTOM_LOGO_PATH

        if not logo_path.is_file():
            return

        pixmap = QPixmap(str(logo_path))

        if pixmap.isNull():
            return

        self.logo_label.setText("")
        self.logo_label.setPixmap(
            pixmap.scaled(
                self.LOGO_WIDTH,
                self.LOGO_HEIGHT,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

    def _load_custom_image(self):
        if not self.USE_CUSTOM_IMAGE:
            return

        project_root = Path(__file__).resolve().parent.parent
        image_path = project_root / self.CUSTOM_IMAGE_PATH

        if not image_path.is_file():
            return

        pixmap = QPixmap(str(image_path))

        if pixmap.isNull():
            return

        self._source_pixmap = pixmap
        self.placeholder.hide()
        self.image_label.show()

        self._update_image()

    def _update_image(self):
        if self._source_pixmap is None:
            return

        size = self.size()
        scaled = self._source_pixmap.scaled(
            size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        x = (scaled.width() - size.width()) // 2
        y = (scaled.height() - size.height()) // 2
        self.image_label.setPixmap(
            scaled.copy(x, y, size.width(), size.height())
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "image_label"):
            self.image_label.setGeometry(self.rect())
        overlay = self.findChild(QWidget, "splashOverlay")
        if overlay is not None:
            overlay.setGeometry(self.rect())
        self._update_image()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()

        if screen is None:
            return

        geometry = screen.availableGeometry()

        self.move(
            geometry.center() - self.rect().center()
        )

    def set_status(self, message):
        self.status_label.setText(str(message))

    def finish(self):
        self.set_status(tr('splash.ready', self.language))

        elapsed = (
            time.monotonic() - self._started_at
        ) * 1000

        remaining = max(
            0,
            int(self.MINIMUM_DISPLAY_TIME - elapsed)
        )

        QTimer.singleShot(remaining, self.close)





class ShortcutCaptureDialog(QDialog):
    def __init__(self, parent=None, current_binding=None, language='pt_BR'):
        super().__init__(parent)

        self.language = language
        self.binding = None

        self.setWindowTitle(tr('shortcut.capture.title', self.language))
        self.setFixedSize(390, 220)
        self.setModal(True)

        _set_theme_stylesheet(self, """
            QDialog {
                background: #211e2a;
                color: #f3edf9;
            }
            QLabel {
                color: #f3edf9;
            }
            QPushButton {
                background: #302a3b;
                color: #e9dcf7;
                border: 1px solid #59496b;
                border-radius: 8px;
                padding: 9px 14px;
            }
            QPushButton:hover {
                background: #40354f;
                border-color: #b58ae0;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(12)

        title = QLabel(tr("shortcut.capture.heading", self.language))
        _set_theme_stylesheet(title, "font-size: 16px; font-weight: 700;"
        )
        layout.addWidget(title)

        description = QLabel(tr("shortcut.capture.description", self.language))
        description.setWordWrap(True)
        _set_theme_stylesheet(description, "color: #bdb3c9;")
        layout.addWidget(description)

        self.capture_label = QLabel(tr("shortcut.capture.waiting", self.language))
        self.capture_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.capture_label.setMinimumHeight(48)
        _set_theme_stylesheet(self.capture_label, """
            QLabel {
                background: #17151e;
                border: 1px solid #59496b;
                border-radius: 9px;
                color: #d9b6ff;
                font-size: 14px;
                font-weight: 700;
            }
        """)
        layout.addWidget(self.capture_label)

        buttons = QHBoxLayout()
        buttons.addStretch(1)

        cancel = QPushButton(tr("shortcut.capture.cancel", self.language))
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)

        layout.addLayout(buttons)

        if current_binding:
            self.capture_label.setText(
                tr("shortcut.capture.current", self.language).format(binding=current_binding)
            )

    def handle_key_event(self, event):
        if event.isAutoRepeat():
            event.accept()
            return

        key = event.key()

        if key == Qt.Key.Key_Escape:
            self.reject()
            event.accept()
            return

        modifier_keys = {
            Qt.Key.Key_Control,
            Qt.Key.Key_Shift,
            Qt.Key.Key_Alt,
            Qt.Key.Key_Meta,
        }

        modifiers = event.modifiers()

        if key in modifier_keys:
            if modifiers & (
                Qt.KeyboardModifier.AltModifier
                | Qt.KeyboardModifier.MetaModifier
            ):
                self.capture_label.setText(
                    tr("shortcut.capture.reserved", self.language)
                )
            else:
                pressed = []

                if modifiers & Qt.KeyboardModifier.ControlModifier:
                    pressed.append("Ctrl")

                if modifiers & Qt.KeyboardModifier.ShiftModifier:
                    pressed.append("Shift")

                if pressed:
                    self.capture_label.setText(
                        tr("shortcut.capture.modifier_wait", self.language).format(
                            modifiers=" + ".join(pressed)
                        )
                    )
                else:
                    self.capture_label.setText(
                        tr("shortcut.capture.combination_wait", self.language)
                    )

            event.accept()
            return

        if modifiers & (
            Qt.KeyboardModifier.AltModifier
            | Qt.KeyboardModifier.MetaModifier
        ):
            self.capture_label.setText(
                tr("shortcut.capture.reserved", self.language)
            )
            event.accept()
            return

        allowed_modifiers = (
            Qt.KeyboardModifier.ControlModifier
            | Qt.KeyboardModifier.ShiftModifier
        )

        modifiers = modifiers & allowed_modifiers

        sequence = QKeySequence(
            int(key) | int(modifiers.value)
        )

        binding = sequence.toString(
            QKeySequence.SequenceFormat.PortableText
        ).strip()

        if not binding:
            event.accept()
            return

        self.binding = binding
        self.accept()
        event.accept()

    def keyPressEvent(self, event):
        self.handle_key_event(event)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.controller = parent
        self.language = getattr(parent, 'interface_language', 'pt_BR')

        self.setWindowTitle(tr('settings.title', self.language))
        self.resize(900, 620)
        self.setMinimumSize(760, 520)
        self.setModal(False)

        self.sections = [
            (tr('settings.general', self.language),
             tr('settings.general.description', self.language)),
            (tr('settings.library', self.language),
             tr('settings.library.description', self.language)),
            (tr('settings.shortcuts', self.language),
             tr('settings.shortcuts.description', self.language)),
            (tr('settings.language', self.language),
             tr('settings.language.description', self.language)),
            (tr('settings.about', self.language),
             tr('settings.about.description', self.language)),
        ]

        self.section_buttons = []
        self.pages = QStackedWidget()

        self._build_interface()
        self.show_section(0)

    def _build_interface(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("settingsSidebar")
        sidebar.setFixedWidth(220)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 28, 20, 24)
        sidebar_layout.setSpacing(10)

        brand = QLabel("SERIFA MUSIC")
        brand.setObjectName("settingsBrand")

        subtitle = QLabel(tr("settings.title", self.language).split(" — ")[0].upper())
        subtitle.setObjectName("settingsSubtitle")

        sidebar_layout.addWidget(brand)
        sidebar_layout.addWidget(subtitle)
        sidebar_layout.addSpacing(28)

        for index, (name, description) in enumerate(self.sections):
            button = QPushButton(name)
            button.setObjectName("settingsNavButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setCheckable(True)
            button.clicked.connect(
                lambda checked=False, i=index: self.show_section(i)
            )

            self.section_buttons.append(button)
            sidebar_layout.addWidget(button)

        sidebar_layout.addStretch(1)

        version_label = QLabel("SERIFA MUSIC")
        version_label.setObjectName("settingsFooter")
        sidebar_layout.addWidget(version_label)

        content = QWidget()
        content.setObjectName("settingsContent")

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(38, 34, 38, 30)
        content_layout.setSpacing(0)
        content_layout.addWidget(self.pages)

        for index, (name, description) in enumerate(self.sections):
            if index == 0:
                page = self._create_general_page()
            elif index == 1:
                page = self._create_library_page()
            elif index == 2:
                page = self._create_shortcuts_page()
            elif index == 3:
                page = self._create_language_page()
            elif index == 4:
                page = self._create_about_page()
            else:
                page = self._create_section_page(name, description)

            self.pages.addWidget(page)

        root.addWidget(sidebar)
        root.addWidget(content, 1)

        _set_theme_stylesheet(self, """
            QDialog {
                background-color: #17151e;
                color: #f3edf9;
                font-family: "Inter", "Noto Sans", sans-serif;
            }

            QFrame#settingsSidebar {
                background-color: #211e2a;
                border-right: 1px solid #393243;
            }

            QLabel#settingsBrand {
                color: #f3edf9;
                font-size: 17px;
                font-weight: 800;
                letter-spacing: 1px;
            }

            QLabel#settingsSubtitle {
                color: #95899f;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 2px;
            }

            QLabel#settingsFooter {
                color: #81798b;
                font-size: 10px;
                letter-spacing: 1px;
            }

            QWidget#settingsContent {
                background-color: #17151e;
            }

            QPushButton#settingsNavButton {
                background-color: transparent;
                color: #bdb3c9;
                border: none;
                border-radius: 8px;
                padding: 12px 14px;
                text-align: left;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton#settingsNavButton:hover {
                background-color: #302a3b;
                color: #f3edf9;
            }

            QPushButton#settingsNavButton:checked {
                background-color: #493e58;
                color: #d9b6ff;
            }

            QLabel#settingsPageTitle {
                color: #f3edf9;
                font-size: 25px;
                font-weight: 700;
            }

            QLabel#settingsPageDescription {
                color: #bdb3c9;
                font-size: 13px;
            }

            QFrame#settingsInfoCard {
                background-color: #211e2a;
                border: 1px solid #393243;
                border-radius: 12px;
            }

            QLabel#settingsInfoTitle {
                color: #d9b6ff;
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 1px;
            }

            QLabel#settingsInfoText {
                color: #bdb3c9;
                font-size: 13px;
            }

            QFrame#settingsAboutCard {
                background-color: #211e2a;
                border: 1px solid #393243;
                border-radius: 12px;
            }

            QLabel#settingsAboutSectionTitle {
                color: #d9b6ff;
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 1px;
            }

            QLabel#settingsAboutText {
                color: #bdb3c9;
                font-size: 13px;
            }

            QLabel#settingsBetaBadge {
                background-color: #B6F23A;
                color: #242719;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 1px;
            }

            QPushButton#settingsActionButton {
                background-color: #493e58;
                color: #f3edf9;
                border: 1px solid #66547f;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 12px;
                font-weight: 700;
            }

            QPushButton#settingsActionButton:hover {
                background-color: #59496b;
            }

            QPushButton#settingsCoffeeButton {
                background-color: #FFDD00;
                color: #24200a;
                border: none;
                border-radius: 8px;
                padding: 11px 12px;
                font-size: 12px;
                font-weight: 800;
            }

            QPushButton#settingsCoffeeButton:hover {
                background-color: #FFE84A;
            }

            QPushButton#settingsPixButton {
                background-color: #32BCAD;
                color: #102a27;
                border: none;
                border-radius: 8px;
                padding: 11px 12px;
                font-size: 12px;
                font-weight: 800;
            }

            QPushButton#settingsPixButton:hover {
                background-color: #54CDBF;
            }

            QDialog#pixDonationDialog {
                background-color: #17151e;
                color: #f3edf9;
            }

            QLabel#pixQrFrame {
                background-color: #ffffff;
                border-radius: 10px;
                padding: 8px;
            }

            QCheckBox#settingsOptionCheck {
                color: #f3edf9;
                font-size: 13px;
                font-weight: 600;
                spacing: 10px;
            }

            QCheckBox#settingsOptionCheck::indicator {
                width: 15px;
                height: 15px;
                border: 1px solid #71617f;
                border-radius: 4px;
                background-color: #17141e;
            }

            QCheckBox#settingsOptionCheck::indicator:checked {
                background-color: #B6F23A;
                border: 1px solid #B6F23A;
            }
        """)

    def _create_general_page(self):
        content = QWidget()
        content.setObjectName("settingsGeneralContent")

        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        heading = QLabel(tr("settings.general", self.language))
        heading.setObjectName("settingsPageTitle")

        detail = QLabel(
            tr("settings.general.description", self.language)
        )
        detail.setObjectName("settingsPageDescription")
        detail.setWordWrap(True)

        layout.addWidget(heading)
        layout.addWidget(detail)
        layout.addSpacing(24)

        name_card = QFrame()
        name_card.setObjectName("settingsInfoCard")

        name_layout = QVBoxLayout(name_card)
        name_layout.setContentsMargins(22, 20, 22, 20)
        name_layout.setSpacing(10)

        name_title = QLabel(
            tr("settings.name.title", self.language)
        )
        name_title.setObjectName("settingsInfoTitle")

        name_description = QLabel(
            tr("settings.name.description", self.language)
        )
        name_description.setObjectName("settingsInfoText")
        name_description.setWordWrap(True)

        self.display_name_input = QLineEdit()
        self.display_name_input.setObjectName("settingsNameInput")
        self.display_name_input.setMaxLength(20)
        self.display_name_input.setMinimumHeight(42)

        system_name = (
            self.controller.get_system_display_name()
            if self.controller is not None
            else getpass.getuser()
        )
        self.display_name_input.setPlaceholderText(system_name)

        _set_theme_stylesheet(self.display_name_input, """
            QLineEdit#settingsNameInput {
                background: rgba(255,255,255,0.045);
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 8px;
                color: #f2eafa;
                padding: 8px 12px;
                selection-background-color: #76539a;
            }

            QLineEdit#settingsNameInput:focus {
                border: 1px solid #9871bd;
                background: rgba(255,255,255,0.065);
            }
        """)

        if self.controller is not None:
            saved_name = str(
                self.controller.settings.value("display_name", "")
            )
            self.display_name_input.setText(saved_name.strip())

        name_input_row = QHBoxLayout()
        name_input_row.setSpacing(10)

        name_input_row.addWidget(
            self.display_name_input,
            1
        )

        self.save_display_name_button = QPushButton(
            tr("settings.name.save", self.language)
        )
        self.save_display_name_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.save_display_name_button.setFixedSize(110, 42)
        self.save_display_name_button.setEnabled(False)
        _set_theme_stylesheet(self.save_display_name_button, """
            QPushButton {
                background: #76539a;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #8964ad;
            }

            QPushButton:disabled {
                background: #393243;
                color: #81798b;
            }
        """)

        self.display_name_input.textChanged.connect(
            self._display_name_changed
        )

        self.save_display_name_button.clicked.connect(
            self._save_display_name
        )

        name_input_row.addWidget(
            self.save_display_name_button
        )

        name_layout.addWidget(name_title)
        name_layout.addWidget(name_description)
        name_layout.addLayout(name_input_row)

        layout.addWidget(name_card)

        card = QFrame()
        card.setObjectName("settingsInfoCard")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(12)

        title = QLabel(tr("settings.preview.title", self.language))
        title.setObjectName("settingsInfoTitle")

        description = QLabel(
            tr("settings.preview.description", self.language)
        )
        description.setObjectName("settingsInfoText")
        description.setWordWrap(True)

        self.preview_checkbox = QCheckBox(
            tr("settings.preview.checkbox", self.language)
        )
        self.preview_checkbox.setObjectName(
            "settingsOptionCheck"
        )

        enabled = True
        if self.controller is not None:
            enabled = self.controller.next_track_preview_enabled

        self.preview_checkbox.setChecked(enabled)

        if self.controller is not None:
            self.preview_checkbox.toggled.connect(
                self.controller.set_next_track_preview_enabled
            )

        card_layout.addWidget(title)
        card_layout.addWidget(description)
        card_layout.addSpacing(6)
        card_layout.addWidget(self.preview_checkbox)

        layout.addWidget(card)
        crossfade_card = QFrame()
        crossfade_card.setObjectName("settingsInfoCard")

        crossfade_layout = QVBoxLayout(crossfade_card)
        crossfade_layout.setContentsMargins(22, 20, 22, 20)
        crossfade_layout.setSpacing(12)

        crossfade_title = QLabel(
            tr("settings.crossfade.title", self.language)
        )
        crossfade_title.setObjectName("settingsInfoTitle")

        crossfade_description = QLabel(
            tr("settings.crossfade.description", self.language)
        )
        crossfade_description.setObjectName("settingsInfoText")
        crossfade_description.setWordWrap(True)

        self.crossfade_checkbox = QCheckBox(
            tr("settings.crossfade.checkbox", self.language)
        )
        self.crossfade_checkbox.setObjectName(
            "settingsOptionCheck"
        )

        crossfade_enabled = False
        crossfade_duration = 5

        if self.controller is not None:
            crossfade_enabled = self.controller.crossfade_enabled
            crossfade_duration = self.controller.crossfade_duration

        self.crossfade_checkbox.setChecked(crossfade_enabled)

        duration_row = QHBoxLayout()
        duration_row.setSpacing(12)

        duration_label = QLabel(
            tr("settings.crossfade.duration", self.language)
        )
        duration_label.setObjectName("settingsInfoText")

        self.crossfade_duration_spinbox = QSpinBox()
        self.crossfade_duration_spinbox.setRange(1, 12)
        self.crossfade_duration_spinbox.setValue(crossfade_duration)
        self.crossfade_duration_spinbox.setSuffix(" s")
        self.crossfade_duration_spinbox.setFixedWidth(90)
        self.crossfade_duration_spinbox.setMinimumHeight(38)
        self.crossfade_duration_spinbox.setEnabled(crossfade_enabled)

        _set_theme_stylesheet(self.crossfade_duration_spinbox, """
            QSpinBox {
                background: rgba(255,255,255,0.045);
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 8px;
                color: #f2eafa;
                padding: 5px 8px;
            }

            QSpinBox:focus {
                border: 1px solid #9871bd;
            }

            QSpinBox::up-button,
            QSpinBox::down-button {
                width: 18px;
                border: none;
            }
        """)

        self.crossfade_duration_spinbox.lineEdit().setTextMargins(
            10, 0, 0, 0
        )

        self.crossfade_checkbox.toggled.connect(
            self.crossfade_duration_spinbox.setEnabled
        )

        if self.controller is not None:
            self.crossfade_checkbox.toggled.connect(
                self.controller.set_crossfade_enabled
            )

            self.crossfade_duration_spinbox.valueChanged.connect(
                self.controller.set_crossfade_duration
            )

        duration_row.addWidget(duration_label)
        duration_row.addStretch(1)
        duration_row.addWidget(self.crossfade_duration_spinbox)

        crossfade_layout.addWidget(crossfade_title)
        crossfade_layout.addWidget(crossfade_description)
        crossfade_layout.addSpacing(4)
        crossfade_layout.addWidget(self.crossfade_checkbox)
        crossfade_layout.addLayout(duration_row)

        layout.addWidget(crossfade_card)

        layout.addStretch(1)

        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setObjectName("settingsGeneralScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        _set_theme_stylesheet(scroll, """
            QScrollArea#settingsGeneralScroll {
                background: transparent;
                border: none;
            }

            QScrollArea#settingsGeneralScroll > QWidget > QWidget {
                background: transparent;
            }
        """)
        _set_shortcuts_scrollbar(scroll)

        scroll.setWidget(content)
        page_layout.addWidget(scroll)

        return page

    def _display_name_changed(self):
        self.save_display_name_button.setText(
            tr("settings.name.save", self.language)
        )
        self.save_display_name_button.setEnabled(True)

    def _save_display_name(self):
        if self.controller is None:
            return

        self.controller.set_display_name(
            self.display_name_input.text()
        )

        self.save_display_name_button.setText(
            tr("settings.name.saved", self.language)
        )
        self.save_display_name_button.setEnabled(False)

        QTimer.singleShot(
            1800,
            lambda: self.save_display_name_button.setText(
                tr("settings.name.save", self.language)
            )
        )

    def _create_library_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        heading = QLabel(tr("settings.library", self.language))
        heading.setObjectName("settingsPageTitle")

        detail = QLabel(
            tr("settings.library.description", self.language)
        )
        detail.setObjectName("settingsPageDescription")
        detail.setWordWrap(True)

        layout.addWidget(heading)
        layout.addWidget(detail)
        layout.addSpacing(18)

        scan_card = QFrame()
        scan_card.setObjectName("settingsInfoCard")
        scan_layout = QVBoxLayout(scan_card)
        scan_layout.setContentsMargins(22, 20, 22, 20)
        scan_layout.setSpacing(10)

        scan_title = QLabel(tr("settings.scan.title", self.language))
        scan_title.setObjectName("settingsInfoTitle")

        scan_text = QLabel(
            tr("settings.scan.description", self.language)
        )
        scan_text.setObjectName("settingsInfoText")
        scan_text.setWordWrap(True)

        self.rescan_button = QPushButton(tr("settings.scan.button", self.language))
        self.rescan_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rescan_button.setMinimumHeight(40)
        _set_theme_stylesheet(self.rescan_button, """
            QPushButton {
                background: #76539a;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover { background: #8964ad; }
            QPushButton:disabled {
                background: #393243;
                color: #81798b;
            }
        """)
        self.rescan_button.clicked.connect(
            self.controller.start_library_scan
        )

        scan_layout.addWidget(scan_title)
        scan_layout.addWidget(scan_text)
        scan_layout.addWidget(self.rescan_button)
        layout.addWidget(scan_card)

        reset_card = QFrame()
        reset_card.setObjectName("settingsInfoCard")
        reset_layout = QVBoxLayout(reset_card)
        reset_layout.setContentsMargins(22, 20, 22, 20)
        reset_layout.setSpacing(10)

        reset_title = QLabel(tr("settings.reset.title", self.language))
        _set_theme_stylesheet(reset_title, "color: #e58b91; font-size: 11px; font-weight: 800;"
            "letter-spacing: 1px;"
        )

        reset_text = QLabel(
            tr("settings.reset.description", self.language)
        )
        reset_text.setObjectName("settingsInfoText")
        reset_text.setWordWrap(True)

        self.reset_library_button = QPushButton(tr("settings.reset.button", self.language))
        self.reset_library_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.reset_library_button.setMinimumHeight(40)
        _set_theme_stylesheet(self.reset_library_button, """
            QPushButton {
                background: #713c49;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover { background: #8b4655; }
            QPushButton:disabled {
                background: #393243;
                color: #81798b;
            }
        """)
        self.reset_library_button.clicked.connect(
            self.controller.confirm_library_reset
        )

        reset_layout.addWidget(reset_title)
        reset_layout.addWidget(reset_text)
        reset_layout.addWidget(self.reset_library_button)
        layout.addWidget(reset_card)

        layout.addStretch(1)
        return page

    def _format_shortcut_binding(self, binding):
        labels = {
            "Space": "Espaço" if self.language == "pt_BR" else "Space",
            "Return": "Enter",
            "Escape": "Esc",
            "Up": "↑",
            "Down": "↓",
            "Left": "←",
            "Right": "→",
            ",": ",",
        }

        return " + ".join(
            labels.get(part, part)
            for part in binding.split("+")
        )

    def _refresh_shortcuts_page(self):
        old_page = self.pages.widget(2)

        if old_page is not None:
            self.pages.removeWidget(old_page)
            old_page.deleteLater()

        self.pages.insertWidget(
            2,
            self._create_shortcuts_page()
        )
        self.pages.setCurrentIndex(2)

    def _edit_shortcut_binding(
        self,
        action_id,
        binding_index
    ):
        manager = self.controller.shortcut_manager
        bindings = manager.get_bindings(action_id)

        if binding_index >= len(bindings):
            return

        current = bindings[binding_index]
        dialog = ShortcutCaptureDialog(self, current, self.language)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        replacement = dialog.binding

        if not replacement:
            return

        if replacement == current:
            return

        updated = list(bindings)
        updated[binding_index] = replacement

        try:
            manager.set_bindings(action_id, updated)
        except (ValueError, KeyError) as error:
            QMessageBox.warning(
                self,
                tr("settings.shortcuts.conflict.title", self.language),
                tr("settings.shortcuts.conflict.body", self.language)
                if isinstance(error, ValueError) else str(error)
            )
            return

        self._refresh_shortcuts_page()

    def _add_shortcut_binding(self, action_id):
        manager = self.controller.shortcut_manager
        dialog = ShortcutCaptureDialog(self, language=self.language)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        if not dialog.binding:
            return

        bindings = manager.get_bindings(action_id)
        bindings.append(dialog.binding)

        try:
            manager.set_bindings(action_id, bindings)
        except (ValueError, KeyError) as error:
            QMessageBox.warning(
                self,
                tr("settings.shortcuts.conflict.title", self.language),
                tr("settings.shortcuts.conflict.body", self.language)
                if isinstance(error, ValueError) else str(error)
            )
            return

        self._refresh_shortcuts_page()

    def _reset_shortcut_action(self, action_id):
        answer = QMessageBox.question(
            self,
            tr("settings.shortcuts.reset_action", self.language),
            tr("settings.shortcuts.reset_action.question", self.language),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.controller.shortcut_manager.reset_binding(
            action_id
        )
        self._refresh_shortcuts_page()

    def _reset_all_shortcuts(self):
        answer = QMessageBox.question(
            self,
            tr("settings.shortcuts.reset_all", self.language),
            tr("settings.shortcuts.reset_all.question", self.language),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.controller.shortcut_manager.reset_all()
        self._refresh_shortcuts_page()

    def _create_shortcuts_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        heading_row = QHBoxLayout()

        heading = QLabel(tr("settings.shortcuts", self.language))
        heading.setObjectName("settingsPageTitle")
        heading_row.addWidget(heading)
        heading_row.addStretch(1)

        reset_all = QPushButton(tr("settings.shortcuts.reset", self.language))
        reset_all.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        _set_theme_stylesheet(reset_all, """
            QPushButton {
                color: #c9a7ef;
                background: transparent;
                border: 1px solid #59496b;
                border-radius: 7px;
                padding: 7px 11px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #302a3b;
                border-color: #b58ae0;
            }
        """)
        reset_all.clicked.connect(
            self._reset_all_shortcuts
        )
        heading_row.addWidget(reset_all)

        detail = QLabel(
            tr("settings.shortcuts.description", self.language)
        )
        detail.setObjectName("settingsPageDescription")
        detail.setWordWrap(True)

        layout.addLayout(heading_row)
        layout.addWidget(detail)
        layout.addSpacing(6)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        _set_theme_stylesheet(scroll, """
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #211e2a;
                width: 7px;
                border-radius: 3px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: #59496b;
                border-radius: 3px;
                min-height: 28px;
            }
            QScrollBar::handle:vertical:hover {
                background: #80649e;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 4, 8, 8)
        content_layout.setSpacing(14)

        manager = self.controller.shortcut_manager
        actions = manager.all_actions()
        categories = {}

        for action in actions:
            categories.setdefault(
                action["category"], []
            ).append(action)

        for category, category_actions in categories.items():
            card = QFrame()
            card.setObjectName("settingsInfoCard")

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(18, 16, 18, 14)
            card_layout.setSpacing(8)

            category_keys = {
                "Reprodução": "playback",
                "Favoritos": "favorites",
                "Navegação": "navigation",
                "Fila e playlists": "queue",
                "Recursos adicionais": "additional",
            }
            category_key = category_keys.get(category)
            category_title = (
                tr(f"shortcut.category.{category_key}", self.language)
                if category_key else category
            )
            title = QLabel(category_title.upper())
            title.setObjectName("settingsInfoTitle")
            card_layout.addWidget(title)

            for action_index, action in enumerate(category_actions):
                row = QWidget()
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(0, 5, 0, 5)
                row_layout.setSpacing(10)

                description = QLabel(
                    tr(f"shortcut.action.{action['id']}", self.language)
                )
                description.setObjectName("settingsInfoText")
                description.setWordWrap(True)
                row_layout.addWidget(description, 1)

                bindings_widget = QWidget()
                bindings_layout = QHBoxLayout(bindings_widget)
                bindings_layout.setContentsMargins(0, 0, 0, 0)
                bindings_layout.setSpacing(5)

                if action["id"] == "seek_percentage":
                    fixed = QPushButton("Num 1–9")
                    fixed.setEnabled(False)
                    fixed.setToolTip(
                        tr("settings.shortcuts.fixed.tooltip", self.language)
                    )
                    _set_theme_stylesheet(fixed, """
                        QPushButton {
                            color: #e9dcf7;
                            background: #302a3b;
                            border: 1px solid #59496b;
                            border-radius: 6px;
                            padding: 5px 9px;
                            font-size: 11px;
                            font-weight: 700;
                        }
                        QPushButton:disabled {
                            color: #e9dcf7;
                            opacity: 1;
                        }
                    """)
                    bindings_layout.addWidget(fixed)
                else:
                    for binding_index, binding in enumerate(
                        action["bindings"]
                    ):
                        if binding_index:
                            separator = QLabel(tr("settings.shortcuts.separator", self.language))
                            _set_theme_stylesheet(separator, "color: #95899f; font-size: 10px;"
                            )
                            bindings_layout.addWidget(separator)

                        key_button = QPushButton(
                            self._format_shortcut_binding(binding)
                        )
                        key_button.setCursor(
                            Qt.CursorShape.PointingHandCursor
                        )
                        key_button.setToolTip(
                            tr("settings.shortcuts.edit.tooltip", self.language)
                        )
                        _set_theme_stylesheet(key_button, """
                            QPushButton {
                                color: #e9dcf7;
                                background: #302a3b;
                                border: 1px solid #59496b;
                                border-radius: 6px;
                                padding: 5px 9px;
                                font-size: 11px;
                                font-weight: 700;
                            }
                            QPushButton:hover {
                                background: #40354f;
                                border-color: #b58ae0;
                            }
                        """)
                        key_button.clicked.connect(
                            lambda checked=False,
                            aid=action["id"],
                            index=binding_index:
                                self._edit_shortcut_binding(
                                    aid, index
                                )
                        )
                        bindings_layout.addWidget(key_button)

                    add_button = QPushButton("+")
                    add_button.setFixedSize(27, 27)
                    add_button.setCursor(
                        Qt.CursorShape.PointingHandCursor
                    )
                    add_button.setToolTip(
                        tr("settings.shortcuts.add.tooltip", self.language)
                    )
                    _set_theme_stylesheet(add_button, """
                        QPushButton {
                            color: #c9a7ef;
                            background: transparent;
                            border: 1px dashed #80649e;
                            border-radius: 6px;
                            font-size: 16px;
                            font-weight: 700;
                        }
                        QPushButton:hover {
                            background: #302a3b;
                            border-style: solid;
                        }
                    """)
                    add_button.clicked.connect(
                        lambda checked=False,
                        aid=action["id"]:
                            self._add_shortcut_binding(aid)
                    )
                    bindings_layout.addWidget(add_button)

                    defaults = action["defaults"]
                    is_default = (
                        action["bindings"] == defaults
                    )

                    reset_button = QPushButton("↺")
                    reset_button.setFixedSize(27, 27)
                    reset_button.setEnabled(not is_default)
                    reset_button.setToolTip(
                        tr("settings.shortcuts.restore.tooltip", self.language)
                    )
                    _set_theme_stylesheet(reset_button, """
                        QPushButton {
                            color: #c9a7ef;
                            background: transparent;
                            border: 1px solid #59496b;
                            border-radius: 6px;
                            font-size: 15px;
                        }
                        QPushButton:hover {
                            background: #302a3b;
                        }
                        QPushButton:disabled {
                            color: #665b70;
                            border-color: #393243;
                        }
                    """)
                    reset_button.clicked.connect(
                        lambda checked=False,
                        aid=action["id"]:
                            self._reset_shortcut_action(aid)
                    )
                    bindings_layout.addWidget(reset_button)

                row_layout.addWidget(
                    bindings_widget,
                    0,
                    Qt.AlignmentFlag.AlignRight
                )

                card_layout.addWidget(row)

                if action_index < len(category_actions) - 1:
                    divider = QFrame()
                    divider.setFixedHeight(1)
                    _set_theme_stylesheet(divider, "background-color: #393243; border: none;"
                    )
                    card_layout.addWidget(divider)

            content_layout.addWidget(card)

        content_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        return page

    def _create_language_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        heading = QLabel(tr("settings.language", self.language))
        heading.setObjectName("settingsPageTitle")

        detail = QLabel(
            tr("settings.language.description", self.language)
        )
        detail.setObjectName("settingsPageDescription")
        detail.setWordWrap(True)

        layout.addWidget(heading)
        layout.addWidget(detail)
        layout.addSpacing(24)

        card = QFrame()
        card.setObjectName("settingsInfoCard")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(12)

        title = QLabel(tr("settings.language.card", self.language))
        title.setObjectName("settingsInfoTitle")

        description = QLabel(
            tr("settings.language.description.card", self.language)
        )
        description.setObjectName("settingsInfoText")
        description.setWordWrap(True)

        self.language_combo = QComboBox()
        self.language_combo.addItem("🇧🇷  Português (Brasil)", "pt_BR")
        self.language_combo.addItem("🇺🇸  English", "en")

        current_language = "pt_BR"
        if self.controller is not None:
            current_language = self.controller.interface_language

        current_index = self.language_combo.findData(current_language)
        if current_index >= 0:
            self.language_combo.setCurrentIndex(current_index)

        save_button = QPushButton(tr("settings.language.save", self.language))
        save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        save_button.clicked.connect(self._save_language)

        self.language_status = QLabel(
            tr("settings.language.pending", self.language)
        )
        self.language_status.setObjectName("settingsInfoText")
        self.language_status.setWordWrap(True)

        card_layout.addWidget(title)
        card_layout.addWidget(description)
        card_layout.addWidget(self.language_combo)
        card_layout.addWidget(save_button)
        card_layout.addWidget(self.language_status)

        layout.addWidget(card)
        layout.addStretch(1)

        return page

    def _save_language(self):
        if self.controller is None:
            return

        language = self.language_combo.currentData()

        try:
            save_language(self.controller.settings, language)
        except (ValueError, RuntimeError):
            error_key = (
                "settings.language.error.invalid"
                if not language or language not in ("pt_BR", "en")
                else "settings.language.error.save"
            )
            QMessageBox.warning(
                self,
                tr("settings.language.error.title", self.language),
                tr(error_key, self.language)
            )
            return

        self.controller.interface_language = language

        self.language_status.setText(
            tr("settings.language.saved", self.language)
        )

    def _create_about_page(self):
        is_english = str(self.language).lower().startswith("en")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(12)

        title = QLabel(
            "About Serifa Music" if is_english else "Sobre o Serifa Music"
        )
        title.setObjectName("settingsPageTitle")
        layout.addWidget(title)

        version_row = QHBoxLayout()
        version_row.setSpacing(8)

        version = QLabel("0.2.9")
        version.setObjectName("settingsAboutText")

        beta = QLabel("BETA")
        beta.setObjectName("settingsBetaBadge")

        version_row.addWidget(version, 0, Qt.AlignmentFlag.AlignVCenter)
        version_row.addWidget(beta, 0, Qt.AlignmentFlag.AlignVCenter)
        version_row.addStretch(1)
        layout.addLayout(version_row)

        description = QLabel(
            "Bring your music library together in one place, "
            "with a customizable desktop experience. Free and fully offline."
            if is_english else
            "Reúna sua biblioteca musical em um só lugar, com uma "
            "experiência desktop personalizável. Gratuito e totalmente offline."
        )
        description.setObjectName("settingsPageDescription")
        description.setWordWrap(True)
        layout.addWidget(description)

        layout.addSpacing(18)

        support_title = QLabel(
            "Support the development"
            if is_english else
            "Apoie o desenvolvimento"
        )
        support_title.setObjectName("settingsAboutSectionTitle")
        layout.addWidget(support_title)

        support_text = QLabel(
            "If you enjoy Serifa Music, you can support its development "
            "and help keep new ideas moving forward."
            if is_english else
            "Se você gosta do Serifa Music, pode apoiar seu desenvolvimento "
            "e ajudar a manter novas ideias em desenvolvimento."
        )
        support_text.setObjectName("settingsAboutText")
        support_text.setWordWrap(True)
        layout.addWidget(support_text)

        layout.addSpacing(6)

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(12)

        coffee_button = QPushButton("☕ Buy Me a Coffee")
        coffee_button.setObjectName("settingsCoffeeButton")
        coffee_button.setCursor(Qt.CursorShape.PointingHandCursor)
        coffee_button.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://buymeacoffee.com/vitorhenrique")
            )
        )

        pix_button = QPushButton(
            "🪙 Contribute via PIX" if is_english else "🪙 Contribuir via PIX"
        )
        pix_button.setObjectName("settingsPixButton")
        pix_button.setCursor(Qt.CursorShape.PointingHandCursor)
        pix_button.clicked.connect(self._show_pix_donation)

        buttons_row.addWidget(coffee_button, 1)
        buttons_row.addWidget(pix_button, 1)
        layout.addLayout(buttons_row)

        layout.addStretch(1)
        scroll.setWidget(content)

        return scroll

    def _show_pix_donation(self):
        import qrcode
        from io import BytesIO

        is_english = str(self.language).lower().startswith("en")

        pix_payload = (
            "00020126840014br.gov.bcb.pix0122victorhiache@gmail.com"
            "0236Cofrinho de VITOR HENRIQUE CONCEICAO520400005303986"
            "5802BR5924VITOR HENRIQUE CONCEICAO6010Cristalina"
            "61087385000062270523COFRVjIwMDRUN1BUMDAwMDY630435D1"
        )

        dialog = QDialog(self)
        dialog.setObjectName("pixDonationDialog")
        dialog.setWindowTitle(
            "Contribute via PIX" if is_english else "Contribuir via PIX"
        )
        dialog.setModal(True)
        dialog.setFixedSize(390, 500)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(12)

        title = QLabel(
            "Scan the QR code" if is_english else "Escaneie o QR Code"
        )
        title.setObjectName("settingsPageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=4,
        )
        qr.add_data(pix_payload)
        qr.make(fit=True)

        qr_image = qr.make_image(
            fill_color="black",
            back_color="white"
        )

        buffer = BytesIO()
        qr_image.save(buffer, format="PNG")

        qr_pixmap = QPixmap()
        qr_pixmap.loadFromData(buffer.getvalue(), "PNG")

        qr_label = QLabel()
        qr_label.setObjectName("pixQrFrame")
        qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_label.setFixedSize(244, 244)
        qr_label.setStyleSheet(
            "background-color: white; border-radius: 10px; padding: 8px;"
        )
        qr_label.setPixmap(
            qr_pixmap.scaled(
                224,
                224,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        layout.addWidget(qr_label, 0, Qt.AlignmentFlag.AlignHCenter)

        instruction = QLabel(
            "Copy the PIX code to make your contribution."
            if is_english else
            "Copie o código PIX para fazer sua contribuição."
        )
        instruction.setObjectName("settingsAboutText")
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instruction)

        status = QLabel("")
        status.setObjectName("settingsAboutText")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        code_button = QPushButton(
            "Copy PIX code" if is_english else "Copiar código PIX"
        )
        code_button.setObjectName("settingsActionButton")
        code_button.setCursor(Qt.CursorShape.PointingHandCursor)

        def copy_pix_code():
            QApplication.clipboard().setText(pix_payload)
            status.setText(
                "PIX code copied!" if is_english else "Código PIX copiado!"
            )

        code_button.clicked.connect(copy_pix_code)

        layout.addWidget(code_button)
        layout.addWidget(status)
        layout.addStretch(1)

        close_button = QPushButton(
            "Close" if is_english else "Fechar"
        )
        close_button.setObjectName("settingsActionButton")
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.exec()

    def _create_section_page(self, title, description):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        heading = QLabel(title)
        heading.setObjectName("settingsPageTitle")

        detail = QLabel(description)
        detail.setObjectName("settingsPageDescription")
        detail.setWordWrap(True)

        layout.addWidget(heading)
        layout.addWidget(detail)
        layout.addSpacing(24)

        card = QFrame()
        card.setObjectName("settingsInfoCard")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(10)

        info_title = QLabel(tr("settings.about.placeholder.title", self.language))
        info_title.setObjectName("settingsInfoTitle")

        info_text = QLabel(
            tr("settings.about.placeholder.body", self.language)
        )
        info_text.setObjectName("settingsInfoText")
        info_text.setWordWrap(True)

        card_layout.addWidget(info_title)
        card_layout.addWidget(info_text)

        layout.addWidget(card)
        layout.addStretch(1)

        return page

    def show_section(self, index):
        if index < 0 or index >= len(self.section_buttons):
            return

        self.pages.setCurrentIndex(index)

        for button_index, button in enumerate(self.section_buttons):
            button.setChecked(button_index == index)


class SerifaPlayer(QMainWindow):
    def __init__(self):
        self._next_preview_data = None
        super().__init__()

        # Carrega as preferências antes de construir a interface.
        self.settings = QSettings("SerifaPlayer", "SerifaPlayer")
        self.interface_language = load_language(self.settings)

        self.setWindowTitle("Serifa Music")
        self.resize(
            get_theme_value("layout", "window", "initial_width", 1200),
            get_theme_value("layout", "window", "initial_height", 760)
        )
        self.setMinimumSize(
            get_theme_value("layout", "window", "minimum_width", 1000),
            get_theme_value("layout", "window", "minimum_height", 650)
        )

        application = QApplication.instance()
        self.appearance = (
            application.property("serifa_appearance_manager")
            or AppearanceManager()
        )

        central = QWidget()
        central.setObjectName("central")

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = Sidebar(self.appearance, self.interface_language)
        main_layout.addWidget(self.sidebar)

        right_area = QWidget()

        right_layout = QVBoxLayout(right_area)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        content_area = QWidget()
        content_layout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.data_dir = Path(
            os.environ.get(
                "XDG_DATA_HOME",
                Path.home() / ".local/share"
            )
        ) / "SerifaPlayer"

        self.data_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.library_file = self.data_dir / "library.json"
        self.library_volume_file = self.data_dir / "library_volumes.json"
        self.library_folders = self.load_library_folders()
        self.library_volume_registry_error = None
        self.library_volume_registry = self.load_library_volume_registry()

        self.database_file = self.data_dir / "library.sqlite3"
        self.covers_dir = self.data_dir / "covers"

        self.scanner = LibraryScanner(
            self.database_file,
            self.covers_dir
        )

        self.scan_worker = None
        self.library_access_worker = None
        self.library_access_ready = False
        self.library_access_result = None
        self.available_library_folders = []

        self.pages = QStackedWidget()

        self.home = HomeView(
            self.scanner,
            self.interface_language,
            self.appearance.icon_manager
        )
        self.library_settings = LibrarySettingsView(self)
        self.library_view = LibraryView(
            self.scanner,
            self.library_settings
        )
        self.storage_manager = StorageManager()
        self.folder_browser = FolderBrowserView(self)
        self.favorites_view = FavoritesView(
            self.scanner,
            self
        )

        home_scroll = QScrollArea()
        home_scroll.setObjectName("homeScroll")
        home_scroll.setWidgetResizable(True)
        home_scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )
        _set_shortcuts_scrollbar(home_scroll)

        home_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        home_scroll.setWidget(self.home)

        self.pages.addWidget(home_scroll)
        self.pages.addWidget(self.library_view)
        self.pages.addWidget(self.folder_browser)
        self.pages.addWidget(self.favorites_view)

        self.shortcut_manager = ShortcutManager(self.settings)
        self.next_track_preview_enabled = self.settings.value(
            "next_track_preview_enabled",
            True,
            type=bool
        )

        self.crossfade_enabled = self.settings.value(
            "crossfade_enabled",
            False,
            type=bool
        )

        self.crossfade_duration = max(
            1,
            min(
                12,
                self.settings.value(
                    "crossfade_duration",
                    5,
                    type=int
                )
            )
        )

        self._crossfade_transition_started = False
        self._crossfade_checked_path = None

        saved_volume = self.settings.value("volume", 70, type=int)
        saved_volume = max(0, min(100, saved_volume))

        self.player = PlayerBar(self.appearance, self.interface_language)
        self.player.volume_slider.setValue(saved_volume)

        self.audio_player = AudioPlayer()

        self._playback_visualizer_levels = [
            0.35 for _ in range(512)
        ]
        self._playback_visualizer_targets = [
            0.35 for _ in range(512)
        ]
        self._playback_visualizer_tick = 0

        self._playback_visualizer_timer = QTimer(self)
        self._playback_visualizer_timer.setInterval(50)
        self._playback_visualizer_timer.timeout.connect(
            self._update_playback_visualizer
        )
        self._playback_visualizer_timer.start()
        self.audio_player.set_volume(saved_volume)
        self.equalizer_dialog = EqualizerDialog(
            self.audio_player,
            self.settings,
            self
        )
        self.playback_queue = PlaybackQueue()
        self.current_track = None

        # Histórico de utilização: uma sessão independente por deck.
        self._usage_sessions = {}
        self._usage_checkpoint_interval = 5.0

        self.infinity_play_enabled = self.settings.value(
            "infinity_play_enabled",
            False,
            type=bool
        )
        self._infinity_cycle_seen = set()
        self._infinity_queue_entry_ids = set()
        self._infinity_queue_target = 7
        self.fullscreen_player = FullscreenPlayer(self)
        self.seeking = False
        self._pending_seek_position = None
        self._pending_seek_deadline = 0.0

        self.artist_profile = ArtistProfileView(self)
        self.album_detail = AlbumDetailView(self)
        self.album_return_page = None

        self.pages.addWidget(self.artist_profile)
        self.pages.addWidget(self.album_detail)
        self.pages.addWidget(self.library_settings)

        self.artist_profile.back_requested.connect(
            self.show_library
        )
        self.artist_profile.album_requested.connect(
            self.open_album_page
        )
        self.artist_profile.play_album_requested.connect(
            self.play_album
        )
        self.artist_profile.cover_change_requested.connect(
            self.choose_entity_cover
        )
        self.artist_profile.cover_reset_requested.connect(
            self.reset_entity_cover
        )
        self.album_detail.cover_change_requested.connect(
            self.choose_entity_cover
        )
        self.album_detail.cover_reset_requested.connect(
            self.reset_entity_cover
        )
        self.album_detail.back_requested.connect(
            self.return_from_album_page
        )
        self.album_detail.track_requested.connect(
            lambda track: self.play_track_data(
                track,
                self.album_detail.tracks
            )
        )
        self.album_detail.tracks_table.context_requested.connect(
            lambda tracks, position: self.show_context_actions(
                tracks,
                position
            )
        )
        self.album_detail.tracks_table.metadata_requested.connect(
            lambda track, field: open_track_metadata(
                self,
                [track],
                0,
                1 if field == "artist" else 2
            )
        )
        self.album_detail.tracks_table.favorite_requested.connect(
            self.toggle_album_track_favorite
        )

        self.home.set_parent_window(self)

        self.progress_timer = QTimer(self)
        self.progress_timer.setInterval(250)
        self.progress_timer.timeout.connect(
            self.update_progress
        )
        self.progress_timer.start()

        self._session_restore_attempted = False
        self._session_restore_position = 0.0
        self._session_restore_attempts = 0

        self.session_save_timer = QTimer(self)
        self.session_save_timer.setInterval(3000)
        self.session_save_timer.timeout.connect(
            self.save_playback_session
        )
        self.session_save_timer.start()

        self.session_restore_timer = QTimer(self)
        self.session_restore_timer.setInterval(100)
        self.session_restore_timer.timeout.connect(
            self.finish_session_restore
        )

        self.player.equalizer_button.clicked.connect(
            self.show_equalizer
        )
        self.player.fullscreen_button.clicked.connect(
            self.show_fullscreen_player
        )
        self.player.play_button.clicked.connect(
            self.toggle_playback
        )

        self.player.shuffle_button.clicked.connect(
            self.toggle_shuffle
        )

        self.player.previous_button.clicked.connect(
            self.play_previous_track
        )

        self.player.next_button.clicked.connect(
            self.play_next_track
        )

        self.player.repeat_button.clicked.connect(
            self.cycle_repeat
        )

        self.player.infinity_button.clicked.connect(
            self.toggle_infinity_play
        )

        self._refresh_playback_controls()

        self.player.favorite_button.clicked.connect(
            self.toggle_current_favorite
        )

        self.player.add_playlist_button.clicked.connect(
            self.show_add_to_playlist_menu
        )

        self._last_nonzero_volume = self.settings.value(
            "last_nonzero_volume", saved_volume or 70, type=int
        )
        self._last_nonzero_volume = max(
            1, min(100, self._last_nonzero_volume)
        )

        self.player.volume_slider.valueChanged.connect(
            self.handle_volume_changed
        )
        self.player.volume_button.clicked.connect(
            self.toggle_mute
        )
        self.update_volume_button()

        self.player.progress_slider.sliderPressed.connect(
            self.start_seeking
        )

        self.player.progress_slider.sliderReleased.connect(
            self.seek_from_slider
        )

        self.library_view.tracks_table.selection_changed.connect(
            self.update_player_selection
        )
        self.library_view.tracks_table.play_requested.connect(
            lambda track: self.play_track_data(
                track,
                self.library_view.tracks
            )
        )
        self.library_view.tracks_table.metadata_requested.connect(
            lambda track, field: open_track_metadata(
                self,
                [track],
                0,
                1 if field == "artist" else 2
            )
        )
        self.library_view.tracks_table.favorite_requested.connect(
            lambda track: self.toggle_track_favorite(track.get("id"))
        )
        self.library_view.tracks_table.context_requested.connect(
            lambda tracks, position: self.show_context_actions(
                tracks,
                position
            )
        )

        self.favorites_view.tracks_table.selection_changed.connect(
            self.update_favorite_selection
        )
        self.favorites_view.tracks_table.play_requested.connect(
            lambda track: self.play_track_data(
                track,
                self.favorites_view.tracks
            )
        )
        self.favorites_view.tracks_table.metadata_requested.connect(
            lambda track, field: open_track_metadata(
                self,
                [track],
                0,
                1 if field == "artist" else 2
            )
        )
        self.favorites_view.tracks_table.favorite_requested.connect(
            lambda track: self.toggle_track_favorite(track.get("id"))
        )
        self.favorites_view.tracks_table.context_requested.connect(
            lambda tracks, position: self.show_context_actions(
                tracks,
                position
            )
        )

        self.queue_panel = QFrame()
        self.queue_panel.setObjectName("queuePanel")
        self.queue_panel.setMinimumWidth(0)
        self.queue_panel.setMaximumWidth(0)

        queue_panel_layout = QVBoxLayout(self.queue_panel)
        queue_panel_layout.setContentsMargins(16, 18, 16, 16)
        queue_panel_layout.setSpacing(14)

        queue_header = QHBoxLayout()

        self.right_panel_title = QLabel(
            tr("queue.title", self.interface_language)
        )
        self.right_panel_title.setObjectName("queueTitle")

        self.queue_pin_button = QPushButton("⌁")
        self.queue_pin_button.setObjectName("queuePinButton")
        self.queue_pin_button.setFixedSize(32, 32)
        self.queue_pin_button.setToolTip(
            tr("queue.pin", self.interface_language)
        )
        self.queue_pin_button.setCursor(Qt.CursorShape.PointingHandCursor)

        queue_header.addWidget(self.right_panel_title)
        queue_header.addStretch(1)
        queue_header.addWidget(self.queue_pin_button)
        queue_panel_layout.addLayout(queue_header)

        self.right_panel_stack = QStackedWidget()
        self.right_panel_stack.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Ignored
        )
        queue_panel_layout.addWidget(self.right_panel_stack, 1)

        self.queue_content = QWidget()
        queue_content_layout = QVBoxLayout(self.queue_content)
        queue_content_layout.setContentsMargins(0, 0, 0, 0)
        queue_content_layout.setSpacing(14)

        self.queue_current_cover = QueueCoverLabel()

        self.queue_current_title = QLabel(
            tr("queue.no_track", self.interface_language)
        )
        self.queue_current_title.setObjectName("queueCurrentTitle")
        self.queue_current_title.setWordWrap(True)

        self.queue_current_duration = QLabel("")
        self.queue_current_duration.setObjectName("queueCurrentDuration")

        queue_content_layout.addWidget(self.queue_current_cover)
        queue_content_layout.addWidget(self.queue_current_title)
        queue_content_layout.addWidget(self.queue_current_duration)

        self.queue_upcoming_label = QLabel(
            tr("queue.upcoming", self.interface_language)
        )
        self.queue_upcoming_label.setObjectName("queueUpcomingTitle")
        queue_content_layout.addWidget(self.queue_upcoming_label)

        self.queue_list_scroll = QScrollArea()
        self.queue_list_scroll.setWidgetResizable(True)
        self.queue_list_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.queue_list_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.queue_list_container = QueueDropContainer()
        self.queue_list_container.drop_callback = self.reorder_queue_entry
        self.queue_list_container.library_drop_callback = (
            self.add_library_drag_to_queue
        )

        self.queue_list_layout = QVBoxLayout(self.queue_list_container)
        self.queue_list_layout.setContentsMargins(0, 0, 0, 0)
        self.queue_list_layout.setSpacing(6)
        self.queue_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.queue_empty_label = QLabel(
            tr("queue.empty", self.interface_language)
        )
        self.queue_empty_label.setObjectName("queueEmptyLabel")
        self.queue_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.queue_empty_label.setWordWrap(True)

        self.queue_list_layout.addWidget(self.queue_empty_label)
        self.queue_list_scroll.setWidget(self.queue_list_container)
        queue_content_layout.addWidget(self.queue_list_scroll, 1)

        self.right_panel_stack.addWidget(self.queue_content)

        self.usage_content = QWidget()
        self.usage_content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Ignored
        )
        usage_layout = QVBoxLayout(self.usage_content)
        usage_layout.setContentsMargins(0, 0, 0, 0)
        usage_layout.setSpacing(12)

        is_english = self.interface_language == "en"

        self.usage_period_label = QLabel("")
        self.usage_period_label.setObjectName("usagePeriodTitle")
        self.usage_period_label.setWordWrap(True)
        usage_layout.addWidget(self.usage_period_label)

        self.usage_month_selector = QComboBox()
        self.usage_month_selector.setObjectName("usageMonthSelector")
        self.usage_month_selector.setToolTip(
            "Choose a month" if is_english else "Escolher mês"
        )
        usage_layout.addWidget(self.usage_month_selector)

        self.usage_hours_label = QLabel(
            "Listening time:" if is_english else "Tempo ouvindo:"
        )
        self.usage_hours_label.setObjectName("usageSectionLabel")
        usage_layout.addWidget(self.usage_hours_label)

        self.usage_hours_value = QLabel("0h00")
        self.usage_hours_value.setObjectName("usageMetricValue")
        usage_layout.addWidget(self.usage_hours_value)

        self.usage_top_artist_label = QLabel(
            "Favorite artist:" if is_english else "Artista favorito:"
        )
        self.usage_top_artist_label.setObjectName("usageSectionLabel")
        usage_layout.addWidget(self.usage_top_artist_label)

        artist_row = QHBoxLayout()
        artist_row.setSpacing(12)

        self.usage_artist_cover = QLabel("♪")
        self.usage_artist_cover.setObjectName("usageArtistCover")
        self.usage_artist_cover.setFixedSize(76, 76)
        self.usage_artist_cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        artist_row.addWidget(self.usage_artist_cover)

        self.usage_top_artist_value = QLabel("—")
        self.usage_top_artist_value.setObjectName("usageHighlightValue")
        self.usage_top_artist_value.setWordWrap(True)
        artist_row.addWidget(
            self.usage_top_artist_value, 1,
            Qt.AlignmentFlag.AlignVCenter
        )
        usage_layout.addLayout(artist_row)

        self.usage_top_track_label = QLabel(
            "Most played track:" if is_english else "Música mais ouvida:"
        )
        self.usage_top_track_label.setObjectName("usageSectionLabel")
        usage_layout.addWidget(self.usage_top_track_label)

        track_row = QHBoxLayout()
        track_row.setSpacing(12)

        self.usage_track_cover = QLabel("♪")
        self.usage_track_cover.setObjectName("usageTrackCover")
        self.usage_track_cover.setFixedSize(76, 76)
        self.usage_track_cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        track_row.addWidget(self.usage_track_cover)

        track_text = QVBoxLayout()
        track_text.setSpacing(0)
        track_text.setContentsMargins(0, 0, 0, 0)

        self.usage_top_track_value = QLabel("—")
        self.usage_top_track_value.setObjectName("usageHighlightValue")
        self.usage_top_track_value.setWordWrap(True)
        self.usage_top_track_value.setContentsMargins(0, 0, 0, 0)
        track_text.addWidget(self.usage_top_track_value)

        self.usage_top_track_artist_value = QLabel("")
        self.usage_top_track_artist_value.setObjectName(
            "usageTrackArtistValue"
        )
        self.usage_top_track_artist_value.setWordWrap(True)
        self.usage_top_track_artist_value.setContentsMargins(0, 0, 0, 0)
        track_text.addWidget(self.usage_top_track_artist_value)

        track_row.addLayout(track_text, 1)
        usage_layout.addLayout(track_row)

        self.usage_status_label = QLabel("")
        self.usage_status_label.setObjectName("usageStatusLabel")
        self.usage_status_label.setWordWrap(True)
        self.usage_status_label.setFixedHeight(54)
        self.usage_status_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        usage_layout.addWidget(self.usage_status_label)

        self.usage_year_playlist_button = QPushButton(
            "Create yearly playlist" if is_english
            else "Criar playlist do ano"
        )
        self.usage_year_playlist_button.setObjectName(
            "usageYearPlaylistButton"
        )
        self.usage_year_playlist_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.usage_year_playlist_button.hide()
        usage_layout.addWidget(self.usage_year_playlist_button)

        usage_layout.addStretch(1)
        self.right_panel_stack.addWidget(self.usage_content)

        self.queue_tab_button = QPushButton(
            "Q\nU\nE\nU\nE" if is_english else "F\nI\nL\nA"
        )
        self.queue_tab_button.setObjectName("queueTabButton")
        self.queue_tab_button.setFixedSize(28, 112)
        self.queue_tab_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.queue_tab_button.setToolTip(
            tr("queue.open", self.interface_language)
        )

        self.usage_tab_button = QPushButton(
            "S\nU\nM\nM\nA\nR\nY"
            if is_english else "R\nE\nS\nU\nM\nO"
        )
        self.usage_tab_button.setObjectName("usageTabButton")
        self.usage_tab_button.setFixedSize(28, 132)
        self.usage_tab_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.usage_tab_button.setToolTip(
            "Summary" if is_english else "Resumo"
        )

        self.queue_tab_container = QWidget()
        self.queue_tab_container.setObjectName("queueTabRail")
        self.queue_tab_container.setFixedWidth(36)

        queue_tab_layout = QVBoxLayout(self.queue_tab_container)
        queue_tab_layout.setContentsMargins(4, 0, 4, 0)
        queue_tab_layout.setSpacing(10)
        queue_tab_layout.addSpacing(70)
        queue_tab_layout.addWidget(
            self.queue_tab_button, 0, Qt.AlignmentFlag.AlignHCenter
        )
        queue_tab_layout.addWidget(
            self.usage_tab_button, 0, Qt.AlignmentFlag.AlignHCenter
        )
        queue_tab_layout.addStretch(1)

        self.queue_panel_host = QWidget()
        self.queue_panel_host.setMinimumWidth(28)

        queue_host_layout = QHBoxLayout(self.queue_panel_host)
        queue_host_layout.setContentsMargins(0, 0, 0, 0)
        queue_host_layout.setSpacing(0)
        queue_host_layout.addWidget(self.queue_panel)
        queue_host_layout.addWidget(self.queue_tab_container)

        content_layout.addWidget(self.pages, 1)
        content_layout.addWidget(self.queue_panel_host, 0)

        right_layout.addWidget(content_area, 1)
        right_layout.addWidget(self.player, 0)

        self.queue_panel_animation = QPropertyAnimation(
            self.queue_panel,
            b"maximumWidth",
            self
        )
        self.queue_panel_animation.setDuration(240)
        self.queue_panel_animation.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )

        self.queue_panel_animation.finished.connect(
            self.finish_queue_panel_animation
        )

        self.queue_panel_open = False
        self.queue_panel_pinned = False
        self.active_right_panel = "queue"

        self.player.queue_button.clicked.connect(
            self.toggle_queue_panel
        )
        self.queue_tab_button.clicked.connect(
            self.toggle_queue_panel
        )
        self.usage_tab_button.clicked.connect(
            self.toggle_usage_panel
        )
        self.usage_month_selector.currentIndexChanged.connect(
            self.refresh_usage_panel
        )
        self.usage_year_playlist_button.clicked.connect(
            self.create_yearly_usage_playlist
        )
        self.queue_pin_button.clicked.connect(
            self.toggle_queue_panel_pin
        )

        self.sidebar.buttons[0].clicked.connect(
            self.show_home
        )

        self.sidebar.buttons[1].clicked.connect(
            self.show_favorites
        )

        self.sidebar.buttons[2].clicked.connect(
            self.show_playlists
        )

        self.sidebar.buttons[3].clicked.connect(
            lambda checked=False: self.show_library(0)
        )

        self.sidebar.buttons[4].clicked.connect(
            lambda checked=False: self.show_library(1)
        )

        self.sidebar.buttons[5].clicked.connect(
            lambda checked=False: self.show_library(3)
        )

        self.sidebar.import_button.clicked.connect(
            self.show_library_settings
        )

        self.sidebar.settings_button.clicked.connect(
            lambda checked=False: self.show_settings()
        )

        self.library_settings.refresh(
            self.library_folders
        )

        self.update_library_status()

        main_layout.addWidget(right_area, 1)

        self.setCentralWidget(central)
        self.sidebar.attach_toggle_overlay(central)

        self.next_track_preview = NextTrackPreview(
            central, self.interface_language
        )

        self.global_search_overlay = GlobalSearchOverlay(
            self,
            central,
            self.sidebar,
            right_area
        )

        _set_theme_stylesheet(self, """
            QPushButton#sortButton {
                background: #B6F23A;
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 12px;
                color: #211E2A;
                font-size: 13px;
                font-weight: 600;
                min-width: 130px;
                max-width: 130px;
                min-height: 38px;
                max-height: 38px;
            }

            QPushButton#sortButton:hover {
                background: #C8FF4A;
            }

            QPushButton#sortButton:pressed {
                background: #A2D92A;
            }

            QWidget#central {
                background-color: #17151e;
                color: #f3edf9;
                font-family: "Inter", "Noto Sans", sans-serif;
            }

            QScrollArea#homeScroll {
                background: #17151e;
                border: none;
            }

            QScrollArea#homeScroll > QWidget > QWidget {
                background: #17151e;
            }

            QFrame#sidebar {
                background-color: #211e2a;
                border-right: 1px solid rgba(255,255,255,0.06);
            }

            QWidget#sidebarHeader {
                background: transparent;
            }

            QLabel#logoHorizontal,
            QLabel#logoSquare {
                background: transparent;
                border: none;
            }

            QPushButton#sidebarToggleButton {
                background: transparent;
                border: none;
                border-radius: 8px;
                padding: 2px;
            }

            QPushButton#sidebarToggleButton:hover {
                background: rgba(255,255,255,0.08);
            }

            QPushButton#sidebarToggleButton:pressed {
                background: rgba(255,255,255,0.14);
            }

            QFrame#sidebar[collapsed="true"] {
                border-right: 1px solid rgba(255,255,255,0.06);
            }

            QPushButton#navButton[collapsed="true"] {
                text-align: center;
                padding: 10px 8px;
                min-height: 40px;
                max-height: 40px;
            }

            QPushButton#navButton[collapsed="true"]:hover {
                background: rgba(255,255,255,0.06);
            }

            QPushButton#navButton[collapsed="true"][active="true"] {
                background: rgba(153,112,190,0.20);
            }

            QLabel#sectionLabel {
                color: #898297;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 2px;
            }

            QPushButton#navButton {
                background: transparent;
                border: none;
                color: #aaa3b6;
                text-align: left;
                padding: 11px;
                border-radius: 9px;
                font-size: 14px;
            }

            QPushButton#navButton:hover {
                background: rgba(255,255,255,0.06);
                color: white;
            }

            QPushButton#navButton[active="true"] {
                background: rgba(153,112,190,0.20);
                color: #e9d5ff;
                font-weight: 600;
            }

            QLabel#pageTitle {
                font-size: 30px;
                font-weight: 700;
                color: #f5efff;
            }

            QLabel#pageSubtitle {
                color: #a49bad;
                font-size: 14px;
            }

            QLabel#sectionTitle {
                font-size: 20px;
                font-weight: 650;
                color: #eee8f6;
            }

            QPushButton#searchButton {
                background: rgba(255,255,255,0.07);
                border: 1px solid rgba(255,255,255,0.09);
                border-radius: 18px;
                color: #c6bdcf;
            }

            QPushButton#searchButton:hover {
                background: rgba(255,255,255,0.12);
            }

            QPushButton#backButton {
                background-color: #B6F23A;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 12px;
                color: #49375F;
                padding: 0 16px;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton#backButton:hover {
                background-color: #A6E02E;
            }

            QPushButton#backButton:pressed {
                background-color: #98D51F;
            }


            QLabel#shortcutText {
                color: #f2eafa;
                font-size: 14px;
                font-weight: 600;
                background: transparent;
                padding-left: 5px;
            }

            QFrame#albumCard {
                background: transparent;
                border-radius: 13px;
            }

            QFrame#albumCard:hover {
                background: rgba(255,255,255,0.055);
            }

            QLabel#cardTitle {
                color: #f2edf7;
                font-size: 14px;
                font-weight: 600;
            }

            QLabel#cardSubtitle {
                color: #a49bad;
                font-size: 12px;
            }

            QListWidget#folderList {
                background: #211e2a;
                color: #eee8f6;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 10px;
                padding: 8px;
                font-size: 14px;
            }

            QListWidget#folderList::item {
                padding: 12px;
                border-radius: 7px;
            }

            QListWidget#folderList::item:hover {
                background: rgba(255,255,255,0.07);
            }

            QListWidget#folderList::item:selected {
                background: rgba(153,112,190,0.28);
                color: #ffffff;
            }

            QPushButton#primaryButton {
                background: #8056a4;
                color: white;
                border: none;
                border-radius: 9px;
                padding: 11px 16px;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton#primaryButton:hover {
                background: #956bb8;
            }

            QPushButton#primaryButton:disabled {
                background: #51445f;
                color: #aaa3b6;
            }

            QPushButton#secondaryButton {
                background: rgba(255,255,255,0.07);
                color: #d8cfe2;
                border: 1px solid rgba(255,255,255,0.09);
                border-radius: 9px;
                padding: 10px 14px;
                font-size: 13px;
            }

            QPushButton#secondaryButton:hover {
                background: rgba(255,255,255,0.12);
            }

            QFrame#playerBar {
                background-color: #25212e;
                border-top: 1px solid rgba(255,255,255,0.09);
            }

            QLabel#songTitle {
                color: #f2edf7;
                font-size: 13px;
                font-weight: 600;
            }

            QLabel#songArtist {
                color: #a49bad;
                font-size: 12px;
            }

            QFrame#queuePanel {
                background-color: #17151e;
                border-left: 1px solid #393243;
            }

            QWidget#queueTabRail {
                background-color: #302a3b;
                border-left: 1px solid #493e58;
            }

            QLabel#queueTitle {
                color: #f3edf9;
                font-size: 16px;
                font-weight: 600;
            }

            QLabel#usagePeriodTitle {
                color: #f3edf9;
                font-size: 15px;
                font-weight: 600;
            }
            QLabel#usageSectionLabel {
                color: #B6F23A;
                font-size: 12px;
                font-weight: 400;
                padding-top: 5px;
            }
            QLabel#usageMetricValue {
                color: #f3edf9;
                font-size: 29px;
                font-weight: 700;
            }
            QLabel#usageHighlightValue {
                color: #f3edf9;
                font-size: 15px;
                font-weight: 700;
                padding: 0px;
                margin: 0px;
            }
            QLabel#usageTrackArtistValue {
                color: #a49bad;
                font-size: 11px;
                padding: 0px;
                margin: -4px 0px 0px 0px;
            }
            QLabel#usageArtistCover,
            QLabel#usageTrackCover {
                background: transparent;
                background-color: transparent;
                color: #B6F23A;
                font-size: 24px;
                border: none;
                padding: 0px;
                margin: 0px;
            }

            QComboBox#usageMonthSelector {
                background-color: #302a3b;
                border: 1px solid #493e58;
                border-radius: 10px;
                color: #f3edf9;
                padding: 8px 12px;
                min-height: 20px;
                selection-background-color: #493e58;
            }

            QComboBox#usageMonthSelector:hover {
                border: 1px solid #71617f;
                background-color: #342d40;
            }

            QComboBox#usageMonthSelector:focus {
                border: 1px solid #B6F23A;
            }

            QComboBox#usageMonthSelector::drop-down {
                border: none;
                width: 28px;
                subcontrol-origin: padding;
                subcontrol-position: top right;
            }

            QComboBox#usageMonthSelector QAbstractItemView {
                background-color: #211e2a;
                color: #f3edf9;
                border: 1px solid #493e58;
                border-radius: 8px;
                padding: 5px;
                selection-background-color: #493e58;
                selection-color: #B6F23A;
                outline: none;
            }

            QLabel#queuePlaceholder {
                color: #95899f;
                font-size: 13px;
            }

            QLabel#queueCurrentCover {
                background-color: transparent;
                color: #d9b6ff;
                font-size: 54px;
            }

            QLabel#queueCurrentTitle {
                color: #f3edf9;
                font-size: 16px;
                font-weight: 700;
            }

            QLabel#queueCurrentDuration {
                color: #95899f;
                font-size: 11px;
            }

            QLabel#queueUpcomingTitle {
                color: #c8bfd2;
                font-size: 13px;
                font-weight: 600;
                padding-top: 5px;
            }

            QLabel#queueEmptyLabel {
                color: #95899f;
                font-size: 12px;
                padding: 18px 5px;
            }

            QScrollArea {
                background: transparent;
                border: none;
            }

            QWidget#queueTrackRow {
                background: rgba(255,255,255,9);
                border: 1px solid rgba(255,255,255,15);
                border-radius: 10px;
            }

            QWidget#queueTrackRow:hover {
                background: rgba(255,255,255,19);
                border: 1px solid rgba(255,255,255,35);
            }

            QWidget#queueTrackRow[selected="true"] {
                background-color: #49395b;
                border: 1px solid #72558d;
                border-radius: 10px;
            }

            QLabel#queueTrackIndicator {
                color: #d9b6ff;
                font-size: 10px;
            }

            QLabel#queueTrackTitle {
                color: #e5deeb;
                font-size: 11px;
            }

            QLabel#queueTrackDuration {
                color: #95899f;
                font-size: 10px;
            }

            QPushButton#queueRemoveButton {
                background: transparent;
                border: none;
                border-radius: 7px;
                color: rgba(255,255,255,180);
                font-size: 18px;
            }

            QPushButton#queueRemoveButton:hover {
                background-color: #B6F23A;
                color: #211E2A;
            }

            QPushButton#queueRemoveButton:pressed {
                background-color: #A2D92A;
                color: #211E2A;
            }

            QPushButton#queuePinButton {
                background: #302a3b;
                border: 1px solid #493e58;
                border-radius: 10px;
                color: #c8bfd2;
                font-size: 19px;
            }

            QPushButton#queuePinButton:hover {
                color: #d9b6ff;
                background: #3b3049;
            }

            QPushButton#queueTabButton {
                background: #B6F23A;
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 10px;
                color: #211E2A;
                font-size: 11px;
                font-weight: 700;
                padding: 8px 3px;
            }

            QPushButton#queueTabButton:hover {
                background: #C8FF4A;
            }

            QPushButton#queueTabButton[active="true"] {
                background: #211E2A;
                border: 1px solid #B6F23A;
                color: #B6F23A;
            }

            QPushButton#queueTabButton[active="true"]:hover {
                background: #342D40;
            }

            QPushButton#usageTabButton {
                background: #B6F23A;
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 10px;
                color: #211E2A;
                font-size: 11px;
                font-weight: 700;
                padding: 8px 3px;
            }

            QPushButton#usageTabButton:hover {
                background: #C8FF4A;
            }

            QPushButton#usageTabButton[active="true"] {
                background: #211E2A;
                border: 1px solid #B6F23A;
                color: #B6F23A;
            }

            QPushButton#usageTabButton[active="true"]:hover {
                background: #342D40;
            }

            QPushButton#controlButton {
                background: transparent;
                border: none;
                color: #c8bfd2;
                font-size: 18px;
            }

            QPushButton#controlButton:hover {
                color: #d9b6ff;
            }

            QSlider::groove:horizontal {
                background: #51495c;
                height: 4px;
                border-radius: 2px;
            }

            QSlider::sub-page:horizontal {
                background: #ad83d5;
                border-radius: 2px;
            }

            QSlider::handle:horizontal {
                background: #e4d0f5;
                width: 10px;
                height: 10px;
                margin: -4px 0;
                border-radius: 5px;
            }

            QLabel#volumeIcon {
                color: #bdb3c9;
                font-size: 20px;
            }
        """)

        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)

        self._infinity_prefill_timer = QTimer(self)
        self._infinity_prefill_timer.setInterval(2500)
        self._infinity_prefill_timer.timeout.connect(
            self._maintain_infinity_queue
        )
        self._infinity_prefill_timer.start()

        self.mpris_bridge = MprisBridge(self)
        self.mpris_bridge.play_pause.connect(
            self.toggle_playback
        )
        self.mpris_bridge.play.connect(
            self._mpris_play
        )
        self.mpris_bridge.pause.connect(
            self._mpris_pause
        )
        self.mpris_bridge.stop.connect(
            self.stop_playback
        )
        self.mpris_bridge.next_track.connect(
            self.play_next_track
        )
        self.mpris_bridge.previous_track.connect(
            self.play_previous_track
        )
        self.mpris_bridge.seek_relative.connect(
            self._mpris_seek_relative
        )
        self.mpris_bridge.seek_absolute.connect(
            self._mpris_seek_absolute
        )
        self.mpris_bridge.set_volume.connect(
            self._mpris_set_volume
        )

        self.mpris_service = MprisService(
            self.mpris_bridge
        )
        self.mpris_service.start()

        QTimer.singleShot(
            0,
            self.start_library_access_check
        )

    def open_global_search(self):
        if hasattr(self, "global_search_overlay"):
            self.global_search_overlay.open()

    def handle_global_search_result(self, result):
        kind = result.get("kind")
        data = result.get("data")

        if not data:
            return

        if kind == "track":
            tracks = [
                track
                for track in self.scanner.list_tracks(limit=None)
                if self._track_is_available(track)
            ]

            self.play_track_data(data, tracks)
            return

        if kind == "artist":
            self.open_artist_page(data)
            return

        if kind == "album":
            self.open_album_page(
                data.get("album", ""),
                data.get("artist", "")
            )
            return

        if kind == "playlist":
            self.show_playlists()
            self.library_view.open_playlist(
                data.get("id")
            )
            return

    def show_equalizer(self):
        self.equalizer_dialog.show()
        self.equalizer_dialog.raise_()
        self.equalizer_dialog.activateWindow()

    def _handle_shortcut_key_event(self, event):
        if event.isAutoRepeat():
            return False

        active_window = QApplication.activeWindow()

        if active_window not in (self, self.fullscreen_player):
            return False

        focus_widget = QApplication.focusWidget()

        if event.modifiers() == Qt.KeyboardModifier.NoModifier:
            if isinstance(
                focus_widget,
                (QLineEdit, QTextEdit, QPlainTextEdit)
            ):
                return False

            if (
                isinstance(focus_widget, QComboBox)
                and focus_widget.isEditable()
            ):
                return False

        sequence = QKeySequence(
            int(event.key()) | int(event.modifiers().value)
        )

        binding = sequence.toString(
            QKeySequence.SequenceFormat.PortableText
        ).strip()

        if not binding:
            return False

        normalized = self.shortcut_manager._normalize(binding)

        for action in self.shortcut_manager.all_actions():
            if not any(
                self.shortcut_manager._normalize(value) == normalized
                for value in action["bindings"]
            ):
                continue

            if self._execute_playback_shortcut(
                action["id"],
                binding
            ):
                event.accept()
                return True

        return False

    def _get_shortcut_selected_track(self):
        page = self.pages.currentWidget()

        if page is self.favorites_view:
            panel = self.favorites_view.tracks_table
            tracks = self.favorites_view.tracks
            index = panel.currentRow()
            if 0 <= index < len(tracks):
                return tracks[index], tracks, "favorites"
            return None, None, None

        if page is self.album_detail:
            panel = self.album_detail.tracks_table
            tracks = self.album_detail.tracks
            index = panel.currentRow()
            if 0 <= index < len(tracks):
                return tracks[index], tracks, "album"
            return None, None, None

        if page is self.library_view:
            tab_index = self.library_view.tabs.currentIndex()

            if tab_index == 3:
                tracks = self.library_view.tracks
                index = self.library_view.tracks_table.currentRow()
                if 0 <= index < len(tracks):
                    return tracks[index], tracks, "library"

            if (
                tab_index == 2
                and self.library_view.playlist_stack.currentIndex() == 2
            ):
                tracks = self.library_view.playlist_tracks
                index = self.library_view.playlist_tracks_table.currentRow()
                if 0 <= index < len(tracks):
                    return tracks[index], tracks, "playlist"

        return None, None, None

    def _play_favorites_from_shortcut(self):
        if not self.library_access_ready:
            return False

        self.favorites_view.refresh_if_needed()
        tracks = list(self.favorites_view.tracks)

        if not tracks:
            return False

        self.play_track_data(tracks[0], tracks)
        return True

    def _remove_selected_playlist_track(self):
        if (
            self.pages.currentWidget() is not self.library_view
            or self.library_view.tabs.currentIndex() != 2
            or self.library_view.playlist_stack.currentIndex() != 2
        ):
            return False

        table = self.library_view.playlist_tracks_table
        index = table.currentRow()
        tracks = self.library_view.playlist_tracks

        if index < 0:
            return False

        if not 0 <= index < len(tracks):
            return False

        entry_id = tracks[index].get("playlist_entry_id")

        if entry_id is None:
            return False

        self.library_view.remove_playlist_track_from_context(entry_id)
        return True

    def _execute_playback_shortcut(self, action_id, binding):

        if action_id == "next_track":
            self.play_next_track()

        elif action_id == "play_pause":
            self.toggle_playback()

        elif action_id == "previous_or_restart":
            self.play_previous_track()

        elif action_id == "restart_track":
            if self.audio_player.current_path is None:
                return True

            self._request_seek(
                0,
                self.audio_player.get_duration()
            )

        elif action_id == "volume_up":
            current = self.player.volume_slider.value()
            self.player.volume_slider.setValue(
                min(100, current + 5)
            )

        elif action_id == "volume_down":
            current = self.player.volume_slider.value()
            self.player.volume_slider.setValue(
                max(0, current - 5)
            )

        elif action_id == "shuffle":
            self.toggle_shuffle()

        elif action_id == "repeat":
            self.cycle_repeat()

        elif action_id == "infinite_play":
            self.toggle_infinity_play()

        elif action_id in (
            "seek_back_5",
            "seek_forward_5",
            "seek_back_10",
            "seek_forward_10"
        ):
            if self.audio_player.current_path is None:
                return True

            offsets = {
                "seek_back_5": -5,
                "seek_forward_5": 5,
                "seek_back_10": -10,
                "seek_forward_10": 10,
            }

            self._request_seek(
                self.audio_player.get_position() + offsets[action_id],
                self.audio_player.get_duration()
            )

        elif action_id == "seek_percentage":
            if binding.isdigit():
                self.seek_to_percentage(int(binding) * 10)

        elif action_id == "mute":
            self.toggle_mute()

        elif action_id == "home":
            self.show_home()

        elif action_id == "favorites":
            self.show_favorites()

        elif action_id == "global_search":
            if self.global_search_overlay.isVisible():
                self.global_search_overlay.input.setFocus()
                self.global_search_overlay.input.selectAll()
            else:
                self.open_global_search()

        elif action_id == "import":
            self.show_library_settings()

        elif action_id == "fullscreen":
            if self.fullscreen_player.isVisible():
                self.fullscreen_player.close()
            else:
                self.show_fullscreen_player()

        elif action_id == "queue_panel":
            self.toggle_queue_panel()

        elif action_id == "equalizer":
            if self.equalizer_dialog.isVisible():
                self.equalizer_dialog.hide()
            else:
                self.show_equalizer()

        elif action_id == "next_preview":
            self.set_next_track_preview_enabled(
                not self.next_track_preview_enabled
            )

        elif action_id == "settings":
            self.show_settings()

        elif action_id == "about":
            self.show_settings()
            self.settings_dialog.show_section(4)

        elif action_id == "context_escape":
            if self.fullscreen_player.isVisible():
                self.fullscreen_player.close()
            elif self.global_search_overlay.isVisible():
                self.global_search_overlay.close_overlay()
            else:
                return False

        elif action_id == "search_up":
            if not self.global_search_overlay.isVisible():
                return False

            self.global_search_overlay.move_selection(-1)

        elif action_id == "search_down":
            if not self.global_search_overlay.isVisible():
                return False

            self.global_search_overlay.move_selection(1)

        elif action_id == "favorite_selected":
            track, _, _ = self._get_shortcut_selected_track()
            if not track:
                return False
            self.toggle_track_favorite(track.get("id"))

        elif action_id == "favorite_current":
            if not self.current_track:
                return False
            self.toggle_current_favorite()

        elif action_id == "play_favorites":
            if not self._play_favorites_from_shortcut():
                return False

        elif action_id == "remove_playlist_track":
            if not self._remove_selected_playlist_track():
                return False

        elif action_id == "remove_queue_track":
            entry_id = getattr(self, "selected_queue_entry_id", None)
            if not entry_id:
                return False
            self.remove_queue_entry(entry_id)

        elif action_id == "new_playlist":
            self.library_view.create_playlist_dialog()

        elif action_id == "play_selected":
            queue_entry_id = getattr(
                self, "selected_queue_entry_id", None
            )
            if self.queue_panel_open and queue_entry_id:
                self.play_queue_entry(queue_entry_id)
            else:
                track, context, _ = self._get_shortcut_selected_track()
                if not track:
                    return False
                self.play_track_data(track, context)

        else:
            return False

        return True

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.KeyPress:
            active_modal = QApplication.activeModalWidget()

            if isinstance(active_modal, ShortcutCaptureDialog):
                active_modal.handle_key_event(event)
                return True

        if event.type() == QEvent.Type.KeyPress:
            active_modal = QApplication.activeModalWidget()

            if isinstance(active_modal, ShortcutCaptureDialog):
                active_modal.handle_key_event(event)
                return True

            if self._handle_shortcut_key_event(event):
                return True

        if (
            getattr(self, "queue_panel_open", False)
            and not getattr(self, "queue_panel_pinned", False)
            and event.type() == QEvent.Type.MouseButtonPress
            and event.button() == Qt.MouseButton.LeftButton
        ):
            position = event.globalPosition().toPoint()

            panel_host = getattr(
                self,
                "queue_panel_host",
                None
            )
            player_queue_button = getattr(
                getattr(self, "player", None),
                "queue_button",
                None
            )

            clicked_inside_queue = False

            if panel_host is not None:
                panel_rect = QRect(
                    panel_host.mapToGlobal(
                        panel_host.rect().topLeft()
                    ),
                    panel_host.size()
                )
                clicked_inside_queue = panel_rect.contains(
                    position
                )

            clicked_queue_control = False

            if player_queue_button is not None:
                button_rect = QRect(
                    player_queue_button.mapToGlobal(
                        player_queue_button.rect().topLeft()
                    ),
                    player_queue_button.size()
                )
                clicked_queue_control = button_rect.contains(
                    position
                )

            if (
                not clicked_inside_queue
                and not clicked_queue_control
            ):
                self.set_queue_panel_open(False)

        return super().eventFilter(watched, event)

    def toggle_queue_panel(self):
        if self.queue_panel_open and self.active_right_panel == "queue":
            self.set_right_panel_open(None, False)
        else:
            self.set_right_panel_open("queue", True)

    def toggle_usage_panel(self):
        if self.queue_panel_open and self.active_right_panel == "usage":
            self.set_right_panel_open(None, False)
        else:
            self.set_right_panel_open("usage", True)

    def refresh_usage_panel(self, *_):
        if not hasattr(self, "usage_month_selector"):
            return

        english = self.interface_language == "en"
        names = (
            ["January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November",
             "December"]
            if english else
            ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro",
             "Dezembro"]
        )

        today = datetime.now()
        self.usage_year_playlist_button.setVisible(today.month == 12)

        display_name = self.get_display_name()
        self.usage_period_label.setText(
            f"{display_name}, your summary is here:"
            if english and display_name else
            f"{display_name}, seu resumo está aqui:"
            if display_name else
            "Your summary is here:" if english else "Seu resumo está aqui:"
        )

        current = today.strftime("%Y-%m")
        previous = (
            f"{today.year - 1}-12" if today.month == 1
            else f"{today.year}-{today.month - 1:02d}"
        )

        def set_cover(label, path, circular=False, fallback_title=None):
            label.clear()
            _set_cover_initial(label, fallback_title)
            if not path or not Path(str(path)).is_file():
                return

            pixmap = QPixmap(str(path))
            if pixmap.isNull():
                return

            size = label.width()
            scaled = pixmap.scaled(
                QSize(size, size),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            x = max(0, (scaled.width() - size) // 2)
            y = max(0, (scaled.height() - size) // 2)
            cropped = scaled.copy(x, y, size, size)

            result = QPixmap(size, size)
            result.fill(Qt.GlobalColor.transparent)
            painter = QPainter(result)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(
                QPainter.RenderHint.SmoothPixmapTransform
            )

            shape = QPainterPath()
            rect = QRectF(0, 0, size, size)
            if circular:
                shape.addEllipse(rect)
            else:
                shape.addRoundedRect(rect, 12, 12)

            painter.setClipPath(shape)
            painter.drawPixmap(0, 0, cropped)
            painter.end()

            label.setText("")
            label.setPixmap(result)

        def clear_summary(message=""):
            self.usage_hours_value.setText("—")
            self.usage_top_artist_value.setText("—")
            self.usage_top_track_value.setText("—")
            self.usage_top_track_artist_value.setText("")
            set_cover(self.usage_artist_cover, None, True)
            set_cover(self.usage_track_cover, None)
            self.usage_status_label.setText(message)

        try:
            available = self.scanner.get_usage_months()
            months = {
                item["month"]: item for item in available
                if item.get("month")
            }
            months.setdefault(current, {})
            months.setdefault(previous, {})

            selector = self.usage_month_selector
            old_selection = selector.currentData()
            selector.blockSignals(True)
            selector.clear()

            for month in sorted(months, reverse=True):
                year, number = map(int, month.split("-"))
                selector.addItem(
                    f"{names[number - 1]} {year}", month
                )

            target = old_selection if old_selection in months else previous
            selector.setCurrentIndex(max(0, selector.findData(target)))
            selector.blockSignals(False)

            selected = selector.currentData()
            if not selected:
                return

            year, number = map(int, selected.split("-"))
            if selected == current and today.day > 5:
                clear_summary(
                    "Your recap is being prepared.\n"
                    "Last month's data will be available from the 1st "
                    "to the 5th."
                    if english else
                    "Sua retrospectiva está em preparação.\n"
                    "Os dados do mês anterior estarão disponíveis "
                    "de 1 a 5."
                )
                return

            start = f"{selected}-01 00:00:00"
            next_month = (
                f"{year + 1}-01" if number == 12
                else f"{year}-{number + 1:02d}"
            )
            end = f"{next_month}-01 00:00:00"

            summary = self.scanner.get_usage_summary(start, end)

            if int(summary.get("sessions", 0)) == 0:
                clear_summary(
                    "There is no data for this month."
                    if english else "Não há dados para este mês."
                )
                return

            seconds = max(0, int(summary.get("listened_seconds", 0)))
            hours, remainder = divmod(seconds, 3600)
            minutes = remainder // 60
            self.usage_hours_value.setText(f"{hours}h{minutes:02d}")

            artist = summary.get("top_artist")
            if artist:
                artist_name = str(artist.get("artist") or "—").strip()
                self.usage_top_artist_value.setText(artist_name)

                artist_cover = artist.get("cover_path")
                custom = self.scanner.get_entity_cover(
                    "artist", artist_name.casefold()
                )
                if custom:
                    artist_cover = custom
                set_cover(self.usage_artist_cover, artist_cover, True)
            else:
                self.usage_top_artist_value.setText("—")
                set_cover(self.usage_artist_cover, None, True)

            track = summary.get("top_track")
            if track:
                title = str(track.get("title") or "—")
                artist_name = str(track.get("artist") or "")
                album = str(track.get("album") or "")

                self.usage_top_track_value.setText(title)
                self.usage_top_track_artist_value.setText(artist_name)

                cover = track.get("cover_path")
                if album and artist_name:
                    key = json.dumps(
                        [album.casefold(), artist_name.casefold()],
                        ensure_ascii=False,
                        separators=(",", ":")
                    )
                    custom = self.scanner.get_entity_cover("album", key)
                    if custom:
                        cover = custom
                set_cover(self.usage_track_cover, cover, fallback_title=title)
            else:
                self.usage_top_track_value.setText("—")
                self.usage_top_track_artist_value.setText("")
                set_cover(self.usage_track_cover, None)

            self.usage_status_label.setText("")

        except Exception as exc:
            self.usage_status_label.setText(
                f"Could not load summary: {exc}" if english
                else f"Não foi possível carregar o resumo: {exc}"
            )


    def create_yearly_usage_playlist(self):
        today = datetime.now()

        if today.month != 12:
            return

        year = today.year
        start = f"{year}-01-01 00:00:00"
        end = f"{year + 1}-01-01 00:00:00"
        name = f"Retrospectiva {year}"

        try:
            ranking = self.scanner.get_usage_top_tracks(
                start, end, 100
            )

            track_ids = []
            for row in ranking:
                track_id = row.get("track_id")
                if track_id is not None:
                    track_ids.append(int(track_id))

            if not track_ids:
                self.usage_status_label.setText(
                    "Ainda não há reproduções suficientes para criar "
                    "a playlist do ano."
                    if self.interface_language != "en"
                    else "There are no qualifying plays for this year's playlist yet."
                )
                return

            existing = next(
                (
                    item for item in self.scanner.list_playlists()
                    if (item.get("name") or "").casefold()
                    == name.casefold()
                ),
                None
            )

            if existing:
                playlist_id = int(existing["id"])
            else:
                created = self.scanner.create_playlist(name)
                playlist_id = int(created["id"])

            total = self.scanner.replace_playlist_tracks(
                playlist_id, track_ids
            )

            self.show_playlists()
            self.library_view.open_playlist(playlist_id)

            self.usage_status_label.setText(
                f"{name} atualizada com {total} músicas."
                if self.interface_language != "en"
                else f"{name} updated with {total} tracks."
            )

        except Exception as exc:
            self.usage_status_label.setText(
                f"Não foi possível criar a playlist: {exc}"
                if self.interface_language != "en"
                else f"Could not create the playlist: {exc}"
            )

    def refresh_queue_panel(self):
        current_entry = self.playback_queue.get_current_entry()
        current_track = (
            current_entry.get("track")
            if current_entry else self.current_track
        )

        if current_track:
            title = (
                current_track.get("title")
                or Path(current_track.get("path", "")).stem
                or tr("queue.unknown_track", self.interface_language)
            )

            duration = current_track.get("duration") or 0

            try:
                duration_text = self.format_time(float(duration))
            except (TypeError, ValueError):
                duration_text = "0:00"

            self.queue_current_title.setText(title)
            self.queue_current_title.setToolTip(title)
            self.queue_current_duration.setText(duration_text)
            self.queue_current_cover.set_cover(
                current_track.get("cover_path"), title
            )
        else:
            self.queue_current_title.setText(tr("queue.no_track", self.interface_language))
            self.queue_current_title.setToolTip("")
            self.queue_current_duration.clear()
            self.queue_current_cover.set_cover(None)

        self.refresh_queue_upcoming()

    def refresh_queue_upcoming(self):
        if getattr(self, "queue_panel_open", False):
            while self.queue_list_layout.count():
                item = self.queue_list_layout.takeAt(0)
                widget = item.widget()

                if widget is not None and widget is not self.queue_empty_label:
                    widget.deleteLater()

            entries = self.playback_queue.get_upcoming_entries()

            if not entries:
                self.queue_list_layout.addWidget(
                    self.queue_empty_label
                )
                self.queue_empty_label.show()
            else:
                self.queue_empty_label.hide()

                for entry in entries:
                    track = entry["track"]
                    duration = track.get("duration") or 0

                    try:
                        duration_text = self.format_time(float(duration))
                    except (TypeError, ValueError):
                        duration_text = "0:00"

                    row = QueueTrackRow(
                        entry["id"],
                        track,
                        duration_text, language=self.interface_language
                    )

                    row.indicator.setVisible(False)
                    row.clicked.connect(self.select_queue_entry)
                    row.double_clicked.connect(self.play_queue_entry)
                    row.remove_requested.connect(self.remove_queue_entry)
                    row.set_selected(
                        row.entry_id == getattr(
                            self, "selected_queue_entry_id", None
                        )
                    )

                    self.queue_list_layout.addWidget(row)

        if (
            hasattr(self, "fullscreen_player")
            and getattr(
                self.fullscreen_player,
                "queue_panel_open",
                False
            )
        ):
            self.fullscreen_player.refresh_queue()

    def add_library_drag_to_queue(
        self,
        mime_type,
        payload,
        position
    ):
        if not self.library_access_ready:
            return

        try:
            data = json.loads(payload)
        except (TypeError, ValueError, json.JSONDecodeError):
            return

        tracks = []

        if mime_type == SERIFA_TRACK_MIME:
            try:
                track_id = int(data.get("id"))
            except (TypeError, ValueError):
                return

            library_tracks = getattr(
                self.library_view,
                "tracks",
                []
            )

            track = next(
                (
                    item for item in library_tracks
                    if int(item.get("id") or -1) == track_id
                ),
                None
            )

            if track is None:
                track = next(
                    (
                        item for item in self.scanner.list_tracks(limit=None)
                        if int(item.get("id") or -1) == track_id
                    ),
                    None
                )

            if track:
                tracks = [track]

        elif mime_type == SERIFA_ALBUM_MIME:
            title = str(data.get("title") or "").strip()
            artist = str(data.get("artist") or "").strip()

            if title:
                tracks = self._get_album_tracks_for_context(
                    title,
                    artist
                )

        elif mime_type == SERIFA_PLAYLIST_MIME:
            try:
                playlist_id = int(data.get("id"))
            except (TypeError, ValueError):
                return

            tracks = self.scanner.list_playlist_tracks(
                playlist_id
            )

        else:
            return

        tracks = [
            track for track in tracks
            if track and self._track_is_available(track)
        ]

        if not tracks:
            return

        self._add_manual_tracks_to_queue(
            tracks,
            position=position
        )

        self.refresh_queue_upcoming()

    def reorder_queue_entry(self, entry_id, new_position):
        moved = self.playback_queue.move_entry(
            entry_id,
            new_position
        )

        if moved:
            self.refresh_queue_upcoming()

    def select_queue_entry(self, entry_id):
        self.selected_queue_entry_id = entry_id

        for index in range(self.queue_list_layout.count()):
            item = self.queue_list_layout.itemAt(index)
            row = item.widget()

            if isinstance(row, QueueTrackRow):
                row.set_selected(row.entry_id == entry_id)

    def remove_queue_entry(self, entry_id):
        removed = self.playback_queue.remove_entry(entry_id)

        if removed is not None:
            if getattr(self, "selected_queue_entry_id", None) == entry_id:
                self.selected_queue_entry_id = None
            self.refresh_queue_upcoming()

    def set_queue_panel_open(self, opened):
        if opened:
            self.set_right_panel_open("queue", True)
        else:
            self.set_right_panel_open(None, False)

    def set_usage_panel_open(self, opened):
        if opened:
            self.set_right_panel_open("usage", True)
        else:
            self.set_right_panel_open(None, False)

    def set_right_panel_open(self, panel_name, opened):
        self.queue_panel_animation.stop()
        self.queue_panel_open = bool(opened)

        if opened:
            if panel_name not in ("queue", "usage"):
                panel_name = "queue"

            self.active_right_panel = panel_name

            if panel_name == "queue":
                self.right_panel_stack.setCurrentWidget(
                    self.queue_content
                )
                self.right_panel_title.setText(
                    tr("queue.title", self.interface_language)
                )
                self.refresh_queue_panel()
            else:
                self.right_panel_stack.setCurrentWidget(
                    self.usage_content
                )
                self.right_panel_title.setText(
                    "Summary" if self.interface_language == "en"
                    else "Resumo"
                )
                refresh_usage = getattr(
                    self, "refresh_usage_panel", None
                )
                if callable(refresh_usage):
                    refresh_usage()

        start_width = self.queue_panel.width()
        end_width = 340 if opened else 0

        self.queue_panel_animation.setStartValue(start_width)
        self.queue_panel_animation.setEndValue(end_width)
        self.queue_panel_animation.start()

        self.player.queue_button.set_active(
            bool(opened and self.active_right_panel == "queue")
        )

        self._set_right_panel_tab_active(
            self.queue_tab_button,
            bool(opened and self.active_right_panel == "queue")
        )
        self._set_right_panel_tab_active(
            self.usage_tab_button,
            bool(opened and self.active_right_panel == "usage")
        )

    @staticmethod
    def _set_right_panel_tab_active(button, active):
        button.setProperty("active", active)
        button.style().unpolish(button)
        button.style().polish(button)
        button.update()

    def finish_queue_panel_animation(self):
        width = 340 if self.queue_panel_open else 0
        self.queue_panel.setMinimumWidth(width)
        self.queue_panel.setMaximumWidth(width)

    def toggle_queue_panel_pin(self):
        self.queue_panel_pinned = not self.queue_panel_pinned

        if self.queue_panel_pinned:
            self.queue_pin_button.setText("⌖")
            self.queue_pin_button.setToolTip(tr("queue.unpin", self.interface_language))
        else:
            self.queue_pin_button.setText("⌁")
            self.queue_pin_button.setToolTip(tr("queue.pin", self.interface_language))

    # --------------------------------------------------
    # GERENCIAMENTO DA BIBLIOTECA
    # --------------------------------------------------

    def load_library_volume_registry(self):
        if not self.library_volume_file.exists():
            return {"version": 1, "folders": []}

        try:
            data = json.loads(
                self.library_volume_file.read_text(encoding="utf-8")
            )

            if (
                not isinstance(data, dict)
                or not isinstance(data.get("folders"), list)
            ):
                raise ValueError("Estrutura inválida no cadastro de volumes.")

            return data

        except Exception as error:
            self.library_volume_registry_error = str(error)
            print(
                "ERRO ao carregar library_volumes.json:",
                self.library_volume_registry_error
            )
            return {"version": 1, "folders": []}

    def save_library_volume_registry(self):
        if self.library_volume_registry_error:
            raise RuntimeError(
                "O cadastro de volumes apresentou erro na leitura. "
                "O salvamento foi bloqueado para preservar o arquivo original."
            )

        self.data_dir.mkdir(parents=True, exist_ok=True)

        temporary = self.library_volume_file.with_suffix(".tmp")

        if self.library_volume_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = self.library_volume_file.with_name(
                f"library_volumes.json.bak.{timestamp}"
            )
            shutil.copy2(self.library_volume_file, backup)

        temporary.write_text(
            json.dumps(
                self.library_volume_registry,
                ensure_ascii=False,
                indent=4
            ),
            encoding="utf-8"
        )

        temporary.replace(self.library_volume_file)

    def build_library_volume_entry(self, folder):
        path = Path(folder).expanduser().resolve()

        if not path.is_dir():
            raise StorageError(
                f"A pasta não está acessível: {path}"
            )

        partition, mountpoint = (
            self.storage_manager.find_partition_for_path(path)
        )

        mount_root = Path(mountpoint).resolve()

        # O /home é armazenamento local do sistema.
        if mount_root == Path("/home"):
            return {
                "path": str(path),
                "kind": "local",
                "absolute_path": str(path)
            }

        # Volumes externos só podem entrar na biblioteca em modo RO.
        if partition.read_only is not True:
            raise StorageError(
                f"O volume de {path} não está confirmado "
                "como somente leitura. A pasta não foi adicionada."
            )

        if not partition.uuid:
            raise StorageError(
                f"O volume de {path} não possui UUID identificável."
            )

        try:
            relative_path = path.relative_to(mount_root)
        except ValueError as error:
            raise StorageError(
                "A pasta não está dentro do ponto de montagem identificado."
            ) from error

        return {
            "path": str(path),
            "kind": "volume",
            "uuid": partition.uuid,
            "relative_path": relative_path.as_posix(),
            "registered_mountpoint": str(mount_root)
        }

    def registry_path_key(self, path):
        return os.path.normcase(
            str(Path(path).expanduser().resolve())
        )

    def load_library_folders(self):

        if not self.library_file.exists():
            return []

        try:
            with open(
                self.library_file,
                "r",
                encoding="utf-8"
            ) as file:
                data = json.load(file)

            return data if isinstance(data, list) else []

        except (OSError, json.JSONDecodeError):
            return []

    def save_library_folders(self):
        self.data_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        temporary = self.library_file.with_suffix(".tmp")

        with open(
            temporary,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                self.library_folders,
                file,
                ensure_ascii=False,
                indent=4
            )

        temporary.replace(self.library_file)

    def save_library_configuration_transactionally(self):
        if self.library_volume_registry_error:
            raise RuntimeError(
                "O cadastro de volumes apresentou erro de leitura. "
                "A configuração não será sobrescrita."
            )

        self.data_dir.mkdir(parents=True, exist_ok=True)

        files = {
            self.library_file: json.dumps(
                self.library_folders,
                ensure_ascii=False,
                indent=4
            ),
            self.library_volume_file: json.dumps(
                self.library_volume_registry,
                ensure_ascii=False,
                indent=4
            )
        }

        snapshots = {
            path: path.read_bytes() if path.exists() else None
            for path in files
        }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            for path, content in files.items():
                if snapshots[path] is not None:
                    backup = path.with_name(
                        f"{path.name}.bak.{timestamp}"
                    )
                    shutil.copy2(path, backup)

            for path, content in files.items():
                temporary = path.with_name(path.name + ".tmp")
                temporary.write_text(content, encoding="utf-8")
                temporary.replace(path)

        except Exception as error:
            rollback_errors = []

            for path, original in snapshots.items():
                try:
                    if original is None:
                        path.unlink(missing_ok=True)
                    else:
                        temporary = path.with_name(
                            path.name + ".rollback.tmp"
                        )
                        temporary.write_bytes(original)
                        temporary.replace(path)
                except Exception as rollback_error:
                    rollback_errors.append(
                        f"{path.name}: {rollback_error}"
                    )

            if rollback_errors:
                raise RuntimeError(
                    f"Falha ao salvar: {error}. "
                    "Também houve falha na restauração: "
                    + "; ".join(rollback_errors)
                ) from error

            raise

        finally:
            for path in files:
                path.with_name(path.name + ".tmp").unlink(
                    missing_ok=True
                )
                path.with_name(path.name + ".rollback.tmp").unlink(
                    missing_ok=True
                )

    def add_library_folders(self, folders):
        added = []
        duplicates = []

        existing = {
            os.path.normcase(os.path.abspath(path))
            for path in self.library_folders
        }

        for folder in folders:
            folder = os.path.abspath(folder)
            normalized = os.path.normcase(folder)

            if normalized in existing:
                duplicates.append(folder)
                continue

            added.append(folder)
            existing.add(normalized)

        if not added:
            self.library_settings.refresh(self.library_folders)
            self.show_library_settings()
            return

        previous_folders = list(self.library_folders)
        previous_registry = json.loads(
            json.dumps(self.library_volume_registry)
        )

        try:
            new_entries = [
                self.build_library_volume_entry(folder)
                for folder in added
            ]

            registered = {
                self.registry_path_key(entry["path"])
                for entry in self.library_volume_registry["folders"]
            }

            for entry in new_entries:
                key = self.registry_path_key(entry["path"])

                if key not in registered:
                    self.library_volume_registry["folders"].append(entry)
                    registered.add(key)

            self.library_folders.extend(added)

            self.save_library_configuration_transactionally()

        except Exception as error:
            self.library_folders = previous_folders
            self.library_volume_registry = previous_registry

            QMessageBox.critical(
                self,
                "Erro ao adicionar pastas",
                (
                    "Não foi possível concluir a inclusão. "
                    "A lista anterior foi restaurada.\n\n"
                    f"Detalhes: {error}"
                )
            )
            return

        if self.library_access_ready:
            self.available_library_folders.extend(added)
            self.available_library_folders = list(dict.fromkeys(
                self.available_library_folders
            ))

            self.library_settings.scan_button.setEnabled(
                bool(self.available_library_folders)
            )

            self.update_library_status()

        self.library_settings.refresh(self.library_folders)
        self.library_view.refresh()
        self.home.refresh()
        self.show_library_settings()

    def add_library_folder(self, folder):
        folder = os.path.abspath(folder)

        if folder in self.library_folders:
            QMessageBox.information(
                self,
                "Pasta já adicionada",
                "Esta pasta já faz parte da biblioteca."
            )
            self.show_library_settings()
            return

        self.add_library_folders([folder])
    def remove_selected_folder(self):
        selected_items = (
            self.library_settings.folder_list.selectedItems()
        )

        if not selected_items:
            return

        folders = [item.text() for item in selected_items]

        if len(folders) == 1:
            title = "Remover pasta"
            message = (
                "Deseja remover esta pasta da biblioteca?\n\n"
                f"{folders[0]}\n\n"
                "As músicas indexadas exclusivamente nesta pasta "
                "serão removidas da biblioteca. "
                "Os arquivos originais continuarão no disco."
            )
        else:
            title = "Remover pastas"
            folder_list = "\n".join(
                f"• {folder}" for folder in folders
            )
            message = (
                f"Deseja remover estas {len(folders)} pastas "
                "da biblioteca?\n\n"
                f"{folder_list}\n\n"
                "As músicas indexadas exclusivamente nessas pastas "
                "serão removidas da biblioteca. "
                "Os arquivos originais continuarão no disco."
            )

        answer = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        previous_folders = list(self.library_folders)
        previous_registry = json.loads(
            json.dumps(self.library_volume_registry)
        )

        removed_paths = {
            self.registry_path_key(folder)
            for folder in folders
        }

        remaining_folders = [
            path
            for path in previous_folders
            if self.registry_path_key(path) not in removed_paths
        ]

        try:
            self.library_folders = remaining_folders

            self.library_volume_registry["folders"] = [
                entry
                for entry in self.library_volume_registry["folders"]
                if self.registry_path_key(entry["path"])
                not in removed_paths
            ]

            self.save_library_configuration_transactionally()

            removed_count = self.scanner.remove_folders(
                folders,
                protected_folders=remaining_folders
            )

        except Exception as error:
            self.library_folders = previous_folders
            self.library_volume_registry = previous_registry

            try:
                self.save_library_configuration_transactionally()
            except Exception as rollback_error:
                error = RuntimeError(
                    f"{error}. Falha ao restaurar a configuração: "
                    f"{rollback_error}"
                )

            QMessageBox.critical(
                self,
                "Erro ao remover pastas",
                (
                    "Não foi possível concluir a remoção. "
                    "A lista anterior foi restaurada.\n\n"
                    f"Detalhes: {error}"
                )
            )
            return

        removed_keys = {
            self.registry_path_key(folder)
            for folder in folders
        }

        self.available_library_folders = [
            path for path in self.available_library_folders
            if self.registry_path_key(path) not in removed_keys
        ]

        self.library_settings.refresh(self.library_folders)
        self.library_view.refresh()
        self.home.refresh()

        QMessageBox.information(
            self,
            "Pastas removidas",
            (
                f"{len(folders)} pasta(s) removida(s) "
                "com sucesso.\n\n"
                f"{removed_count} música(s) removida(s) "
                "da biblioteca.\n\n"
                "Os arquivos originais foram preservados."
            )
        )
    def set_active_navigation(self, active_button):
        buttons = (
            self.sidebar.buttons
            + [
                self.sidebar.import_button,
                self.sidebar.settings_button
            ]
        )

        for button in buttons:
            button.setProperty(
                "active",
                button is active_button
            )

            button.style().unpolish(button)
            button.style().polish(button)


    def _add_manual_tracks_to_queue(self, tracks, position=None):
        tracks = [track for track in (tracks or []) if track]
        if not tracks:
            return []

        upcoming = self.playback_queue.upcoming
        first_auto = next(
            (
                i for i, entry in enumerate(upcoming)
                if entry.get("id") in self._infinity_queue_entry_ids
            ),
            len(upcoming)
        )

        if position is None:
            position = first_auto
        else:
            position = min(int(position), first_auto)

        return self.playback_queue.add_tracks(
            tracks,
            position=position
        )

    def _infinity_track_key(self, track):
        if not track:
            return None

        path = track.get("path")
        if path:
            return str(path).strip().casefold()

        track_id = track.get("id")
        return f"id:{track_id}" if track_id is not None else None

    def _get_infinity_library_tracks(self):
        if not self.library_access_ready:
            return []

        return [
            track
            for track in self.scanner.list_tracks(limit=None)
            if self._track_is_available(track)
        ]

    def _infinity_track_sort_key(self, track):
        def number(value):
            try:
                return int(value or 0)
            except (TypeError, ValueError):
                return 0

        return (
            (track.get("album") or "").strip().casefold(),
            number(track.get("disc_number")),
            number(track.get("track_number")),
            (track.get("title") or "").strip().casefold(),
            self._infinity_track_key(track) or ""
        )

    def _next_infinity_random_track(self, tracks=None):
        if tracks is None:
            tracks = self._get_infinity_library_tracks()
        if not tracks:
            return None

        current = self.current_track
        if not current:
            return None

        keyed_tracks = {}

        for track in tracks:
            key = self._infinity_track_key(track)
            if key:
                keyed_tracks[key] = track

        if not keyed_tracks:
            return None

        available_keys = set(keyed_tracks)
        queued_keys = {
            self._infinity_track_key(entry.get("track"))
            for entry in self.playback_queue.upcoming
            if isinstance(entry, dict) and entry.get("track")
        }
        self._infinity_cycle_seen.intersection_update(
            available_keys
        )

        if not self._infinity_cycle_seen:
            queue_history = getattr(
                self.playback_queue,
                "history",
                []
            )

            for entry in queue_history:
                if isinstance(entry, dict):
                    previous = entry.get("track")
                    key = self._infinity_track_key(previous)

                    if key:
                        self._infinity_cycle_seen.add(key)

            current_entry = getattr(
                self.playback_queue,
                "current_entry",
                None
            )

            if isinstance(current_entry, dict):
                previous = current_entry.get("track")
                key = self._infinity_track_key(previous)

                if key:
                    self._infinity_cycle_seen.add(key)

            current_key = self._infinity_track_key(current)

            if current_key:
                self._infinity_cycle_seen.add(current_key)

        if len(self._infinity_cycle_seen) >= len(available_keys):
            self._infinity_cycle_seen.clear()

            current_key = self._infinity_track_key(current)

            if current_key in available_keys:
                self._infinity_cycle_seen.add(current_key)

        unseen_tracks = [
            track
            for key, track in keyed_tracks.items()
            if key not in self._infinity_cycle_seen
            and key not in queued_keys
        ]

        if not unseen_tracks:
            return None

        selected_track = random.choice(unseen_tracks)
        selected_key = self._infinity_track_key(selected_track)

        if selected_key:
            self._infinity_cycle_seen.add(selected_key)

        return selected_track

    def _next_infinity_sequential_track(self, tracks=None):
        if tracks is None:
            tracks = self._get_infinity_library_tracks()
        if not tracks:
            return None

        current = self.current_track
        if not current:
            return None

        keyed_tracks = {}
        for track in tracks:
            key = self._infinity_track_key(track)
            if key:
                keyed_tracks[key] = track

        if not keyed_tracks:
            return None

        available_keys = set(keyed_tracks)
        queued_keys = {
            self._infinity_track_key(entry.get("track"))
            for entry in self.playback_queue.upcoming
            if isinstance(entry, dict) and entry.get("track")
        }
        self._infinity_cycle_seen.intersection_update(available_keys)

        if not self._infinity_cycle_seen:
            queue_history = getattr(
                self.playback_queue,
                "history",
                []
            )

            for entry in queue_history:
                if isinstance(entry, dict):
                    previous = entry.get("track")
                    key = self._infinity_track_key(previous)
                    if key:
                        self._infinity_cycle_seen.add(key)

            current_entry = getattr(
                self.playback_queue,
                "current_entry",
                None
            )

            if isinstance(current_entry, dict):
                previous = current_entry.get("track")
                key = self._infinity_track_key(previous)
                if key:
                    self._infinity_cycle_seen.add(key)

            current_key = self._infinity_track_key(current)
            if current_key:
                self._infinity_cycle_seen.add(current_key)

        if len(self._infinity_cycle_seen) >= len(available_keys):
            self._infinity_cycle_seen.clear()

            current_key = self._infinity_track_key(current)
            if current_key in available_keys:
                self._infinity_cycle_seen.add(current_key)

        groups = {}

        for track in tracks:
            artist = (
                (track.get("artist") or "").strip()
                or (track.get("album_artist") or "").strip()
                or "Artista desconhecido"
            )

            artist_key = artist.casefold()
            groups.setdefault(artist_key, []).append(track)

        for artist_tracks in groups.values():
            artist_tracks.sort(
                key=self._infinity_track_sort_key
            )

        current_artist = (
            (current.get("artist") or "").strip()
            or (current.get("album_artist") or "").strip()
            or "Artista desconhecido"
        ).casefold()

        artist_order = sorted(groups)
        ordered_tracks = []

        if current_artist in groups:
            current_artist_tracks = groups[current_artist]
            current_key = self._infinity_track_key(current)

            current_index = next(
                (
                    index
                    for index, track in enumerate(current_artist_tracks)
                    if self._infinity_track_key(track) == current_key
                ),
                -1
            )

            if current_index >= 0:
                ordered_tracks.extend(
                    current_artist_tracks[current_index + 1:]
                )

                remaining_artists = [
                    artist
                    for artist in artist_order
                    if artist != current_artist
                ]

                artists_after = [
                    artist
                    for artist in remaining_artists
                    if artist > current_artist
                ]
                artists_before = [
                    artist
                    for artist in remaining_artists
                    if artist < current_artist
                ]

                for artist in artists_after + artists_before:
                    ordered_tracks.extend(groups[artist])

                ordered_tracks.extend(
                    current_artist_tracks[:current_index]
                )
            else:
                start = artist_order.index(current_artist)
                rotated = (
                    artist_order[start:]
                    + artist_order[:start]
                )

                for artist in rotated:
                    ordered_tracks.extend(groups[artist])
        else:
            for artist in artist_order:
                ordered_tracks.extend(groups[artist])

        for track in ordered_tracks:
            key = self._infinity_track_key(track)

            if (
                not key
                or key in self._infinity_cycle_seen
                or key in queued_keys
            ):
                continue

            self._infinity_cycle_seen.add(key)
            return track

        return None

    def _maintain_infinity_queue(self):
        if (
            not self.infinity_play_enabled
            or self.playback_queue.repeat_mode != "off"
            or not self.library_access_ready
            or not self.current_track
        ):
            return

        upcoming_ids = {
            entry.get("id")
            for entry in self.playback_queue.upcoming
            if isinstance(entry, dict)
        }
        self._infinity_queue_entry_ids.intersection_update(
            upcoming_ids
        )

        missing = (
            self._infinity_queue_target
            - len(self.playback_queue.upcoming)
        )
        if missing <= 0:
            return

        library_tracks = self._get_infinity_library_tracks()
        if not library_tracks:
            return

        added = False

        for _ in range(missing):
            if self.playback_queue.shuffle_enabled:
                track = self._next_infinity_random_track(
                    library_tracks
                )
            else:
                track = self._next_infinity_sequential_track(
                    library_tracks
                )

            if track is None:
                break

            entry_id = self.playback_queue.add_to_end(track)
            if entry_id:
                self._infinity_queue_entry_ids.add(entry_id)
                added = True

        if added:
            self.refresh_queue_upcoming()

    def _artist_tracks(self, artist_name):
        if not self.library_access_ready:
            return []

        target = artist_name.strip().casefold()

        return [
            track
            for track in self.scanner.list_tracks(limit=None)
            if self._track_is_available(track)
            and (
                (track.get("artist") or "").strip().casefold() == target
                or
                (track.get("album_artist") or "").strip().casefold() == target
            )
        ]


    def _refresh_entity_cover_page(self, entity_type, entity_key):
        if entity_type == "artist":
            self.open_artist_page(self.artist_profile.artist_name)
            return

        if entity_type == "album":
            try:
                album_title, artist_name = json.loads(entity_key)
            except (TypeError, ValueError):
                return

            self.open_album_page(album_title, artist_name)

    def choose_entity_cover(self, entity_type, entity_key):
        if entity_type not in ("artist", "album") or not entity_key:
            return

        if self.interface_language == "en":
            title = "Choose cover"
            file_filter = "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
            invalid_title = "Invalid image"
            invalid_message = "The selected file is not a valid image."
            error_title = "Could not change cover"
        else:
            title = "Escolher capa"
            file_filter = "Imagens (*.png *.jpg *.jpeg *.webp *.bmp)"
            invalid_title = "Imagem inválida"
            invalid_message = "O arquivo selecionado não é uma imagem válida."
            error_title = "Não foi possível alterar a capa"

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            title,
            str(Path.home()),
            file_filter
        )

        if not file_path:
            return

        image = QPixmap(file_path)

        if image.isNull():
            QMessageBox.warning(
                self,
                invalid_title,
                invalid_message
            )
            return

        try:
            self.scanner.set_entity_cover(
                entity_type,
                entity_key,
                file_path
            )
        except Exception as error:
            QMessageBox.warning(
                self,
                error_title,
                str(error)
            )
            return

        self._refresh_entity_cover_page(
            entity_type,
            entity_key
        )

    def reset_entity_cover(self, entity_type, entity_key):
        if entity_type not in ("artist", "album") or not entity_key:
            return

        try:
            self.scanner.reset_entity_cover(
                entity_type,
                entity_key
            )
        except Exception as error:
            title = (
                "Could not restore cover"
                if self.interface_language == "en"
                else "Não foi possível restaurar a capa"
            )
            QMessageBox.warning(self, title, str(error))
            return

        self._refresh_entity_cover_page(
            entity_type,
            entity_key
        )

    def open_artist_page(self, artist_name):
        if not self.library_access_ready:
            return

        tracks = self._artist_tracks(artist_name)

        if not tracks:
            QMessageBox.information(
                self,
                tr("message.artist_not_found.title", self.interface_language),
                tr("message.artist_not_found.body", self.interface_language)
            )
            return

        albums = self.scanner.list_albums()
        album_names = {
            (track.get("album") or "").strip().casefold()
            for track in tracks
        }

        artist_key = artist_name.strip().casefold()

        artist_albums = [
            album
            for album in albums
            if (
                (album.get("artist") or "").strip().casefold() == artist_key
                or
                (album.get("album") or "").strip().casefold() in album_names
            )
        ]

        cover_path = next(
            (
                track.get("cover_path")
                for track in tracks
                if (
                    track.get("cover_path")
                    and Path(track["cover_path"]).is_file()
                )
            ),
            None
        )

        custom_artist_cover = self.scanner.get_entity_cover(
            "artist", artist_key
        )
        if custom_artist_cover:
            cover_path = custom_artist_cover

        for album in artist_albums:
            album_title = (album.get("album") or "").strip()
            album_artist = (album.get("artist") or artist_name).strip()
            album_entity_key = json.dumps(
                [
                    album_title.casefold(),
                    album_artist.casefold()
                ],
                ensure_ascii=False,
                separators=(",", ":")
            )
            custom_album_cover = self.scanner.get_entity_cover(
                "album", album_entity_key
            )
            if custom_album_cover:
                album["cover_path"] = custom_album_cover

        genres = sorted({
            str(track.get("genre")).strip()
            for track in tracks
            if track.get("genre")
        }, key=str.casefold)

        years = sorted({
            str(track.get("year")).strip()
            for track in tracks
            if track.get("year")
        })

        track_count = len(tracks)
        album_count = len(artist_albums)
        track_key = "artist.count.one" if track_count == 1 else "artist.count.many"
        album_key = "artist.albums.one" if album_count == 1 else "artist.albums.many"

        description_parts = [
            tr(track_key, self.interface_language).format(count=track_count),
            tr(album_key, self.interface_language).format(count=album_count)
        ]

        if genres:
            description_parts.append(
                tr("artist.genres", self.interface_language) + ", ".join(genres[:4])
            )

        if years:
            period = years[0] if len(years) == 1 else (
                f"{years[0]} – {years[-1]}"
            )
            description_parts.append(tr("artist.period", self.interface_language) + period)

        description = "  •  ".join(description_parts)

        self.artist_profile.set_artist(
            artist_name,
            cover_path,
            description,
            artist_albums
        )

        self.pages.setCurrentWidget(self.artist_profile)

        self.set_active_navigation(
            self.sidebar.buttons[3]
        )

    def _get_album_tracks_for_context(self, album_title, artist_name):
        if not self.library_access_ready:
            return []

        title_key = (album_title or "").strip().casefold()
        artist_key = (artist_name or "").strip().casefold()

        tracks = [
            track
            for track in self.scanner.list_tracks(limit=None)
            if (
                self._track_is_available(track)
                and (track.get("album") or "").strip().casefold()
                    == title_key
                and (
                    (track.get("album_artist") or "").strip().casefold()
                        == artist_key
                    or
                    (track.get("artist") or "").strip().casefold()
                        == artist_key
                )
            )
        ]

        if not tracks:
            tracks = [
                track
                for track in self.scanner.list_tracks(limit=None)
                if (
                    self._track_is_available(track)
                    and (track.get("album") or "").strip().casefold()
                        == title_key
                )
            ]

        def track_number(track, field):
            try:
                return int(
                    str(track.get(field) or "0").split("/")[0]
                )
            except (ValueError, TypeError):
                return 0

        tracks.sort(
            key=lambda track: (
                track_number(track, "disc_number"),
                track_number(track, "track_number"),
                (track.get("title") or "").casefold()
            )
        )

        return tracks

    def show_album_context_menu(
        self,
        album_title,
        artist_name,
        global_position
    ):
        tracks = self._get_album_tracks_for_context(
            album_title,
            artist_name
        )

        if not tracks:
            return

        self.show_context_actions(
            tracks,
            global_position
        )

    def open_album_page(self, album_title, artist_name):
        if not self.library_access_ready:
            return

        all_tracks = [
            track
            for track in self.scanner.list_tracks(limit=None)
            if self._track_is_available(track)
        ]

        title_key = album_title.strip().casefold()
        artist_key = artist_name.strip().casefold()

        album_tracks = [
            track
            for track in all_tracks
            if (
                (track.get("album") or "").strip().casefold() == title_key
                and (
                    (track.get("album_artist") or "").strip().casefold() == artist_key
                    or
                    (track.get("artist") or "").strip().casefold() == artist_key
                )
            )
        ]

        if not album_tracks:
            album_tracks = [
                track
                for track in all_tracks
                if (
                    (track.get("album") or "").strip().casefold() == title_key
                )
            ]

        if not album_tracks:
            QMessageBox.information(
                self,
                tr("message.album_not_found.title", self.interface_language),
                tr("message.album_not_found.body", self.interface_language)
            )
            return

        cover_path = next(
            (
                track.get("cover_path")
                for track in album_tracks
                if (
                    track.get("cover_path")
                    and Path(track["cover_path"]).is_file()
                )
            ),
            None
        )

        album_entity_key = json.dumps(
            [title_key, artist_key],
            ensure_ascii=False,
            separators=(",", ":")
        )
        custom_album_cover = self.scanner.get_entity_cover(
            "album", album_entity_key
        )
        if custom_album_cover:
            cover_path = custom_album_cover

        if self.pages.currentWidget() is not self.album_detail:
            self.album_return_page = self.pages.currentWidget()

        self.album_detail.set_album(
            album_title,
            artist_name,
            album_tracks,
            cover_path
        )

        self.pages.setCurrentWidget(self.album_detail)

        self.set_active_navigation(
            self.sidebar.buttons[4]
        )

    def return_from_album_page(self):
        if self.album_return_page is not None:
            return_page = self.album_return_page
            self.pages.setCurrentWidget(return_page)

            if return_page is self.artist_profile:
                active_index = 3
            elif return_page is self.favorites_view:
                active_index = 1
            elif return_page is self.home:
                active_index = 0
            elif return_page is self.library_view:
                active_index = {
                    0: 3,
                    1: 4,
                    2: 2,
                    3: 5
                }.get(
                    self.library_view.tabs.currentIndex(),
                    5
                )
            else:
                return

            self.set_active_navigation(
                self.sidebar.buttons[active_index]
            )
        else:
            self.show_library()

    def update_favorite_button(self):
        track = self.current_track

        if not track or not track.get("id"):
            self.player.favorite_button.setEnabled(False)
            self.player.favorite_button.set_active(False)
            self.player.favorite_button.setToolTip(
                tr("controls.no_favorite_track", self.interface_language)
            )
            _set_theme_stylesheet(self.player.favorite_button, "")
            return

        is_favorite = self.scanner.is_track_favorite(
            track["id"]
        )
        track["is_favorite"] = int(is_favorite)


        button = self.player.favorite_button
        button.setEnabled(True)
        button.set_active(is_favorite)
        button.setToolTip(
            tr("controls.remove_favorite", self.interface_language)
            if is_favorite
            else tr("controls.add_favorite", self.interface_language)
        )
        _set_theme_stylesheet(button, "color: #B6F23A;" if is_favorite else ""
        )

    def toggle_album_track_favorite(self, track):
        track_id = track.get("id") if track else None
        if not track_id:
            return

        self.toggle_track_favorite(track_id)

    def toggle_track_favorite(self, track_id):
        if not track_id:
            return

        current_state = self.scanner.is_track_favorite(track_id)
        new_state = not current_state

        updated = self.scanner.set_track_favorite(
            track_id,
            new_state
        )

        if not updated:
            return

        if (
            self.current_track
            and self.current_track.get("id") == track_id
        ):
            self.current_track["is_favorite"] = int(new_state)
            self.update_favorite_button()

        self.library_view._available_tracks_cache = None

        self.library_view.tracks_table.update_track_favorite(
            track_id,
            new_state
        )

        for album_track in self.album_detail.tracks:
            if album_track.get("id") == track_id:
                album_track["is_favorite"] = int(new_state)

        self.album_detail.tracks_table.update_track_favorite(
            track_id,
            new_state
        )

        self.favorites_view.update_track(track_id, new_state)

    def toggle_current_favorite(self):
        track = self.current_track

        if not track or not track.get("id"):
            return

        self.toggle_track_favorite(track["id"])

    def show_add_to_playlist_menu(self, button=None):

        track = self.current_track

        if not track or not track.get("id"):
            QMessageBox.information(
                self,
                tr("playlist.dialog.add_title", self.interface_language),
                tr("playlist.dialog.no_current_track", self.interface_language)
            )
            return

        playlists = self.scanner.list_playlists()

        menu = QMenu(button or self)

        create_action = menu.addAction(
            tr("playlist.menu.create", self.interface_language)
        )

        menu.addSeparator()

        playlist_actions = {}

        if not playlists:
            empty_action = menu.addAction(
                tr("playlist.menu.empty", self.interface_language)
            )
            empty_action.setEnabled(False)

        else:
            for playlist in playlists:

                count = playlist.get("track_count", 0)

                action = menu.addAction(
                    f"{playlist['name']}  ·  {count} música(s)"
                )

                action.setData(playlist["id"])
                playlist_actions[action] = playlist["id"]

        button = button or self.player.add_playlist_button

        selected = menu.exec(
            button.mapToGlobal(
                button.rect().bottomLeft()
            )
        )

        if selected is None:
            return

        if selected == create_action:
            self.create_playlist_and_add_current_track()
            return

        playlist_id = playlist_actions.get(selected)

        if playlist_id is not None:
            self.add_current_track_to_playlist(playlist_id)

    def create_playlist_and_add_current_track(self):

        track = self.current_track

        if not track or not track.get("id"):
            return

        name, accepted = QInputDialog.getText(
            self,
            tr("playlist.dialog.new_title", self.interface_language),
            tr("playlist.dialog.name_label", self.interface_language)
        )

        if not accepted:
            return

        name = name.strip()

        if not name:
            return

        try:
            playlist = self.scanner.create_playlist(name)

            self.add_current_track_to_playlist(
                playlist["id"],
                show_confirmation=False
            )

        except Exception as error:
            QMessageBox.warning(
                self,
                tr("playlist.dialog.create_error", self.interface_language),
                str(error)
            )

    def add_current_track_to_playlist(
        self,
        playlist_id,
        show_confirmation=True
    ):

        track = self.current_track

        if not track or not track.get("id"):
            return

        try:
            playlist_tracks = self.scanner.list_playlist_tracks(
                playlist_id
            )

            already_added = any(
                int(item["id"]) == int(track["id"])
                for item in playlist_tracks
            )

            if already_added:
                answer = QMessageBox.question(
                    self,
                    tr("playlist.dialog.duplicate_title", self.interface_language),
                    (
                        tr("playlist.dialog.duplicate_body", self.interface_language).format(
                            name=track.get("title") or tr("controls.unknown_track", self.interface_language)
                        )
                    ),
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if answer != QMessageBox.StandardButton.Yes:
                    return

            added = self.scanner.add_tracks_to_playlist(
                playlist_id,
                [track["id"]]
            )

            if not added:
                return

            self.library_view.refresh_playlists()

            if (
                self.library_view.current_playlist_id
                == playlist_id
            ):
                self.library_view.refresh_playlist_detail()

        except Exception as error:
            QMessageBox.warning(
                self,
                tr("playlist.dialog.add_error", self.interface_language),
                str(error)
            )

    def show_library_track_context_menu(self, position):
        table = self.library_view.tracks_table
        row = table.rowAt(position.y())

        if row < 0 or row >= len(self.library_view.tracks):
            return

        table.setCurrentCell(row, 0)

        self.show_context_actions(
            [self.library_view.tracks[row]],
            table.mapToGlobal(position)
        )

    def show_album_track_context_menu(self, position):
        table = self.album_detail.tracks_table
        row = table.rowAt(position.y())

        if row < 0 or row >= len(self.album_detail.tracks):
            return

        table.setCurrentCell(row, 1)

        self.show_context_actions(
            [self.album_detail.tracks[row]],
            table.mapToGlobal(position)
        )

    def show_context_actions(
        self,
        tracks,
        global_position,
        extra_actions=None,
        extra_submenus=None,
        include_playlist_menu=True
    ):
        """Exibe ações comuns e ações adicionais de contexto."""

        tracks = [
            track for track in (tracks or [])
            if track and self._track_is_available(track)
        ]

        extra_actions = list(extra_actions or [])
        extra_submenus = list(extra_submenus or [])

        if not tracks and not extra_actions:
            return

        menu = QMenu(self)

        play_action = menu.addAction(tr("context.play", self.interface_language))
        next_action = menu.addAction(tr("context.play_next", self.interface_language))
        queue_action = menu.addAction(tr("context.add_queue", self.interface_language))

        play_action.setEnabled(bool(tracks))
        next_action.setEnabled(bool(tracks))
        queue_action.setEnabled(bool(tracks))

        menu.addSeparator()

        favorite_action = menu.addAction(
            tr("context.add_favorites", self.interface_language)
        )
        favorite_action.setEnabled(bool(tracks))

        playlist_actions = {}
        create_playlist_action = None

        if include_playlist_menu:
            playlist_menu = menu.addMenu(
                tr("context.add_playlist", self.interface_language)
            )
            playlist_menu.setEnabled(bool(tracks))

            create_playlist_action = playlist_menu.addAction(
                tr("context.create_playlist", self.interface_language)
            )

            playlist_menu.addSeparator()

            playlists = self.scanner.list_playlists()

            if not playlists:
                empty_action = playlist_menu.addAction(
                    tr("context.no_playlists", self.interface_language)
                )
                empty_action.setEnabled(False)

            else:
                for playlist in playlists:
                    count = playlist.get("track_count", 0)

                    action = playlist_menu.addAction(
                        f"{playlist['name']}  ·  {count} música(s)"
                    )

                    playlist_actions[action] = playlist["id"]

        extra_action_callbacks = {}

        if extra_actions:
            menu.addSeparator()

            for label, callback in extra_actions:
                action = menu.addAction(label)
                extra_action_callbacks[action] = callback

        for submenu_label, submenu_items in extra_submenus:
            submenu = menu.addMenu(submenu_label)

            if not submenu_items:
                empty_action = submenu.addAction(
                    tr("playlist.folder.empty", self.interface_language)
                )
                empty_action.setEnabled(False)
                continue

            for item_label, callback in submenu_items:
                action = submenu.addAction(item_label)
                action.triggered.connect(callback)

        selected = menu.exec(global_position)

        if selected is None:
            return

        if selected == play_action:
            self.context_play_tracks(tracks)

        elif selected == next_action:
            self.context_add_next(tracks)

        elif selected == queue_action:
            self.context_add_to_queue(tracks)

        elif selected == favorite_action:
            self.context_add_favorites(tracks)

        elif (
            create_playlist_action is not None
            and selected == create_playlist_action
        ):
            self.context_create_playlist(tracks)

        elif selected in playlist_actions:
            self.context_add_to_playlist(
                tracks,
                playlist_actions[selected]
            )

        elif selected in extra_action_callbacks:
            extra_action_callbacks[selected]()
    def context_play_tracks(self, tracks):
        tracks = list(tracks or [])

        if not tracks:
            return

        if len(tracks) == 1:
            self.playback_queue.play_immediately(tracks[0])
        else:
            self.playback_queue.start_group(tracks)

        self.play_track_data(tracks[0])
        self.refresh_queue_panel()

    def context_add_next(self, tracks):
        tracks = list(tracks or [])

        if not tracks:
            return

        self._add_manual_tracks_to_queue(
            tracks,
            position=0
        )

        self.refresh_queue_panel()

    def context_add_to_queue(self, tracks):
        tracks = list(tracks or [])

        if not tracks:
            return

        self._add_manual_tracks_to_queue(tracks)

        self.refresh_queue_panel()

    def context_add_favorites(self, tracks):
        tracks = [
            track for track in (tracks or [])
            if track and track.get("id")
        ]

        if not tracks:
            return

        updated_ids = set()

        try:
            for track in tracks:
                track_id = track["id"]

                if self.scanner.is_track_favorite(track_id):
                    track["is_favorite"] = 1
                    continue

                if self.scanner.set_track_favorite(
                    track_id,
                    True
                ):
                    track["is_favorite"] = 1
                    updated_ids.add(track_id)

            if (
                self.current_track
                and self.current_track.get("id") in updated_ids
            ):
                self.current_track["is_favorite"] = 1
                self.update_favorite_button()

            self.library_view.refresh_tracks()
            self.favorites_view.refresh()

        except Exception as error:
            QMessageBox.warning(
                self,
                "Erro ao adicionar favoritas",
                str(error)
            )

    def context_add_to_playlist(self, tracks, playlist_id):
        tracks = [
            track for track in (tracks or [])
            if track and track.get("id")
        ]

        if not tracks:
            return

        try:
            playlist_tracks = self.scanner.list_playlist_tracks(
                playlist_id
            )

            existing_ids = {
                int(track["id"])
                for track in playlist_tracks
            }

            duplicate_ids = {
                int(track["id"])
                for track in tracks
                if int(track["id"]) in existing_ids
            }

            if duplicate_ids:
                answer = QMessageBox.question(
                    self,
                    tr("playlist.dialog.duplicates_title", self.interface_language),
                    (
                        tr("playlist.dialog.duplicates_body", self.interface_language).format(
                            count=len(duplicate_ids)
                        )
                    ),
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if answer != QMessageBox.StandardButton.Yes:
                    return

            added = self.scanner.add_tracks_to_playlist(
                playlist_id,
                [track["id"] for track in tracks]
            )

            if not added:
                return

            self.library_view.refresh_playlists()

            if self.library_view.current_playlist_id == playlist_id:
                self.library_view.refresh_playlist_detail()

        except Exception as error:
            QMessageBox.warning(
                self,
                tr("playlist.dialog.add_many_error", self.interface_language),
                str(error)
            )

    def context_create_playlist(self, tracks):
        tracks = [
            track for track in (tracks or [])
            if track and track.get("id")
        ]

        if not tracks:
            return

        name, accepted = QInputDialog.getText(
            self,
            tr("playlist.dialog.new_title", self.interface_language),
            tr("playlist.dialog.name_label", self.interface_language)
        )

        if not accepted:
            return

        name = name.strip()

        if not name:
            return

        try:
            playlist = self.scanner.create_playlist(name)

            self.scanner.add_tracks_to_playlist(
                playlist["id"],
                [track["id"] for track in tracks]
            )

            self.library_view.refresh_playlists()

        except Exception as error:
            QMessageBox.warning(
                self,
                tr("playlist.dialog.create_error", self.interface_language),
                str(error)
            )

    def _usage_start_session(self, track, deck):
        if not isinstance(track, dict):
            return

        if deck in self._usage_sessions:
            self._usage_finalize_session(deck)

        try:
            session_id = self.scanner.start_play_session(track)
            if not session_id:
                return

            position = self.audio_player.get_position(deck)
            duration = self.audio_player.get_duration(deck)

            self._usage_sessions[deck] = {
                "id": session_id,
                "track": dict(track),
                "listened": 0.0,
                "duration": max(
                    0.0,
                    float(duration or track.get("duration") or 0)
                ),
                "last_position": max(0.0, float(position or 0)),
                "last_tick": time.monotonic(),
                "last_checkpoint": time.monotonic()
            }

        except Exception as error:
            print(f"[Usage] Falha ao iniciar sessão: {error}", flush=True)

    def _usage_is_qualified(self, session):
        duration = session["duration"]
        threshold = min(30.0, duration * 0.5) if duration > 0 else 30.0
        return session["listened"] >= threshold

    def _usage_save_session(self, session, finished=False):
        try:
            self.scanner.update_play_session(
                session["id"],
                session["listened"],
                duration_seconds=session["duration"],
                qualified=self._usage_is_qualified(session),
                finished=finished
            )
        except Exception as error:
            print(f"[Usage] Falha ao salvar sessão: {error}", flush=True)

    def _usage_finalize_session(self, deck, finished=False):
        session = self._usage_sessions.pop(deck, None)
        if session is not None:
            self._usage_save_session(session, finished)

    def _usage_flush_sessions(self):
        for session in self._usage_sessions.values():
            self._usage_save_session(session)

    def _usage_finalize_all(self):
        self._usage_flush_sessions()
        for deck in list(self._usage_sessions):
            self._usage_finalize_session(deck)

    def _usage_reset_session_positions(self):
        now = time.monotonic()

        for deck, session in self._usage_sessions.items():
            try:
                session["last_position"] = max(
                    0.0,
                    float(self.audio_player.get_position(deck) or 0)
                )
                session["last_tick"] = now
            except Exception:
                pass

    def _usage_update_sessions(self):
        audio = self.audio_player

        if not audio.is_playing or audio.is_paused:
            return

        if audio.crossfade_active:
            active_decks = {
                audio.crossfade_from,
                audio.crossfade_to
            }
        else:
            active_decks = {audio.active_deck}

        # Finaliza sessões de decks que já saíram da reprodução.
        for deck in list(self._usage_sessions):
            if deck not in active_decks:
                self._usage_finalize_session(deck)

        now = time.monotonic()

        for deck in active_decks:
            session = self._usage_sessions.get(deck)
            if session is None:
                continue

            try:
                position = max(
                    0.0,
                    float(audio.get_position(deck) or 0)
                )
                duration = float(audio.get_duration(deck) or 0)

                if duration > 0:
                    session["duration"] = duration

                elapsed = max(0.0, now - session["last_tick"])
                delta = position - session["last_position"]

                # Saltos de posição são tratados como seeks, não como
                # tempo efetivamente ouvido.
                maximum_delta = elapsed * 2.5 + 0.5

                if 0 < delta <= maximum_delta:
                    session["listened"] += delta

                session["last_position"] = position
                session["last_tick"] = now

                if (
                    now - session["last_checkpoint"]
                    >= self._usage_checkpoint_interval
                ):
                    self._usage_save_session(session)
                    session["last_checkpoint"] = now

            except Exception as error:
                print(
                    f"[Usage] Falha ao medir deck {deck}: {error}",
                    flush=True
                )

    def play_track_data(
        self,
        track,
        context_tracks=None,
        cover_transition="fade",
        automatic_transition=False,
        crossfade_transition=False
    ):
        _timing_start = time.perf_counter()
        if not self._track_is_available(track):
            return

        if automatic_transition:
            if not crossfade_transition:
                self._finish_next_track_preview()
        else:
            self._hide_next_track_preview()

        if crossfade_transition:
            self._crossfade_preview_track = track

        if context_tracks is not None:
            self.playback_queue.set_context(
                context_tracks,
                track
            )
        else:
            queue_current_track = self.playback_queue.current_track

            if (
                queue_current_track is None
                or self.playback_queue._path(queue_current_track)
                != self.playback_queue._path(track)
            ):
                self.playback_queue.play_immediately(track)

        self.current_track = track
        self.player.set_track(track)
        self.fullscreen_player.set_track(
            track,
            transition=cover_transition
        )
        self.update_favorite_button()
        self.refresh_queue_panel()

        try:
            selected_path = Path(
                track["path"]
            ).expanduser().resolve()

            crossfade_started = False

            if crossfade_transition:
                crossfade_started = self.audio_player.start_crossfade(
                    selected_path,
                    self.crossfade_duration
                )

            if not crossfade_started:
                self._usage_finalize_all()
                self.audio_player.play(selected_path)

            self._usage_start_session(
                track,
                self.audio_player.active_deck
            )

            self._crossfade_transition_started = crossfade_started
            self._crossfade_checked_path = None


            self.home.invalidate()

            if self.pages.currentIndex() == 0:
                self.home.refresh()

            self.player.set_playing(True)
            self.fullscreen_player.set_playing(True)

        except Exception as error:
            self._crossfade_transition_started = False
            self.player.set_playing(False)
            self.fullscreen_player.set_playing(False)

            QMessageBox.warning(
                self,
                "Erro de reprodução",
                str(error)
            )

        _elapsed = (time.perf_counter() - _timing_start) * 1000
        if _elapsed >= 20:
            print(f"[Track Switch] play_track_data: {_elapsed:.1f} ms", flush=True)


    def play_album(self, album_title, artist_name):
        if not self.library_access_ready:
            return

        title_key = album_title.strip().casefold()
        artist_key = artist_name.strip().casefold()

        tracks = [
            track
            for track in self.scanner.list_tracks(limit=None)
            if (
                self._track_is_available(track)
                and (track.get("album") or "").strip().casefold() == title_key
                and (
                    (track.get("album_artist") or "").strip().casefold() == artist_key
                    or
                    (track.get("artist") or "").strip().casefold() == artist_key
                )
            )
        ]

        if not tracks:
            return

        def track_number(track, field):
            try:
                return int(str(track.get(field) or "0").split("/")[0])
            except (ValueError, TypeError):
                return 0

        tracks.sort(
            key=lambda track: (
                track_number(track, "disc_number"),
                track_number(track, "track_number")
            )
        )

        self.play_track_data(tracks[0], tracks)

    def play_artist(self, artist_name):
        if not self.library_access_ready:
            return

        tracks = self._artist_tracks(artist_name)

        if not tracks:
            return

        def track_number(track, field):
            try:
                return int(str(track.get(field) or "0").split("/")[0])
            except (ValueError, TypeError):
                return 0

        tracks.sort(
            key=lambda track: (
                (track.get("album") or "").casefold(),
                track_number(track, "disc_number"),
                track_number(track, "track_number")
            )
        )

        self.play_track_data(tracks[0], tracks)

    def show_favorites(self):
        if not self.library_access_ready:
            self.library_settings.scan_status.setText(
                "Aguarde a verificação dos discos da biblioteca."
            )
            return

        self.favorites_view.refresh_if_needed()
        self.pages.setCurrentWidget(self.favorites_view)

        self.set_active_navigation(
            self.sidebar.buttons[1]
        )

    def update_favorite_selection(self, track=None, index=None):
        if track is None:
            row = self.favorites_view.tracks_table.currentRow()

            if row < 0 or row >= len(self.favorites_view.tracks):
                return

            track = self.favorites_view.tracks[row]

        self.current_track = track
        self.player.set_track(self.current_track)
        self.update_favorite_button()

    def play_favorite_track_from_row(self, row, column):
        if column != 0:
            return

        tracks = self.favorites_view.tracks

        if row < 0 or row >= len(tracks):
            return

        self.play_track_data(
            tracks[row],
            tracks
        )

    def show_settings(self):
        if not hasattr(self, "settings_dialog"):
            self.settings_dialog = SettingsDialog(self)

        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

    def show_home(self):
        self.home.refresh_if_needed()
        self.pages.setCurrentIndex(0)

        self.set_active_navigation(
            self.sidebar.buttons[0]
        )

    def update_player_selection(self, track=None, index=None):
        if track is None:
            row = self.library_view.tracks_table.currentRow()

            if row < 0 or row >= len(self.library_view.tracks):
                return

            track = self.library_view.tracks[row]

        self.current_track = track
        self.player.set_track(self.current_track)
        self.update_favorite_button()

    def play_track_from_row(self, row, column):
        if column != 0:
            return

        tracks = self.library_view.tracks

        if row < 0 or row >= len(tracks):
            return

        self.play_track_data(
            tracks[row],
            tracks
        )

    def play_queue_entry(self, entry_id):
        """Reproduz uma ocorrência específica sem reiniciar o contexto."""

        entry = next(
            (
                item
                for item in self.playback_queue.get_upcoming_entries()
                if item["id"] == entry_id
            ),
            None
        )

        if entry is None:
            return

        track = entry["track"]

        if not self._track_is_available(track):
            return

        selected_track = self.playback_queue.play_entry(entry_id)

        if selected_track is not None:
            self.play_track_data(selected_track)

    def toggle_infinity_play(self):
        self._hide_next_track_preview()
        self.infinity_play_enabled = not self.infinity_play_enabled
        self._infinity_cycle_seen.clear()

        self.settings.setValue(
            "infinity_play_enabled",
            self.infinity_play_enabled
        )
        self.settings.sync()

        if self.infinity_play_enabled:
            self._maintain_infinity_queue()

        self._refresh_playback_controls()

        return self.infinity_play_enabled

    def toggle_shuffle(self):
        self._hide_next_track_preview()
        enabled = self.playback_queue.toggle_shuffle()

        self._refresh_playback_controls()

        return enabled

    def cycle_repeat(self):
        self._hide_next_track_preview()
        mode = self.playback_queue.cycle_repeat()

        self._refresh_playback_controls()

        return mode

    def _refresh_playback_controls(self):
        shuffle_enabled = self.playback_queue.shuffle_enabled
        repeat_mode = self.playback_queue.repeat_mode

        self.player.shuffle_button.set_active(shuffle_enabled)
        self.fullscreen_player.shuffle_button.set_active(shuffle_enabled)
        _set_theme_stylesheet(self.player.shuffle_button, "color: #B6F23A;" if shuffle_enabled else ""
        )
        self.player.shuffle_button.setToolTip(
            tr("playback.shuffle.active", self.interface_language)
            if shuffle_enabled
            else tr("playback.shuffle.inactive", self.interface_language)
        )

        repeat_tooltips = {
            "off": tr("playback.repeat.off", self.interface_language),
            "queue": tr("playback.repeat.queue", self.interface_language),
            "track": tr("playback.repeat.track", self.interface_language),
        }

        self.player.repeat_button.set_active(repeat_mode != "off")
        self.fullscreen_player.repeat_button.set_active(repeat_mode != "off")
        _set_theme_stylesheet(self.player.repeat_button, "color: #B6F23A;" if repeat_mode != "off" else ""
        )
        self.player.repeat_button.setToolTip(
            repeat_tooltips.get(
                repeat_mode,
                tr("playback.repeat.mode", self.interface_language)
            )
        )

        infinity_enabled = self.infinity_play_enabled

        for button in (
            self.player.infinity_button,
            self.fullscreen_player.infinity_button
        ):
            button.setEnabled(True)
            button.set_active(infinity_enabled)

            if button is self.fullscreen_player.infinity_button:
                infinity_style = """
                    QPushButton {
                        background: transparent;
                        border: none;
                    }
                """
                if infinity_enabled:
                    infinity_style = """
                        QPushButton {
                            background: transparent;
                            border: none;
                            color: #B6F23A;
                        }
                    """
                _set_theme_stylesheet(button, infinity_style)
            else:
                _set_theme_stylesheet(
                    button,
                    "color: #B6F23A;" if infinity_enabled else ""
                )

            button.setToolTip(
                tr("playback.infinite.on", self.interface_language)
                if infinity_enabled
                else tr("playback.infinite.off", self.interface_language)
            )

    def get_system_display_name(self):
        name = getpass.getuser().strip()

        if not name:
            return ""

        return name[:1].upper() + name[1:]

    def get_display_name(self):
        custom_name = str(
            self.settings.value("display_name", "")
        ).strip()

        return custom_name or self.get_system_display_name()

    def set_display_name(self, name):
        name = str(name).strip()

        if name:
            self.settings.setValue("display_name", name)
        else:
            self.settings.remove("display_name")

        self.settings.sync()

        if hasattr(self, "home"):
            self.home.update_greeting()

    def set_next_track_preview_enabled(self, enabled):
        enabled = bool(enabled)

        self.next_track_preview_enabled = enabled
        self.settings.setValue(
            "next_track_preview_enabled",
            enabled
        )

        if not enabled:
            for preview in (
                getattr(self, "next_track_preview", None),
                getattr(
                    self.fullscreen_player,
                    "next_track_preview",
                    None
                )
            ):
                if preview is not None:
                    preview.hide_preview()


    def set_crossfade_enabled(self, enabled):
        self.crossfade_enabled = bool(enabled)

        self.settings.setValue(
            "crossfade_enabled",
            self.crossfade_enabled
        )

    def set_crossfade_duration(self, duration):
        self.crossfade_duration = max(
            1,
            min(12, int(duration))
        )

        self.settings.setValue(
            "crossfade_duration",
            self.crossfade_duration
        )

    def _hide_next_track_preview(self):
        self._next_preview_data = None

        for preview in (
            getattr(self, "next_track_preview", None),
            getattr(
                self.fullscreen_player,
                "next_track_preview",
                None
            )
        ):
            if preview is not None:
                preview.hide_preview()


    def _finish_next_track_preview(self):
        had_preview = self._next_preview_data is not None
        self._next_preview_data = None

        previews = (
            getattr(self, "next_track_preview", None),
            getattr(
                self.fullscreen_player,
                "next_track_preview",
                None
            )
        )

        for preview in previews:
            if preview is None:
                continue

            if had_preview and self.next_track_preview_enabled:
                preview.finish()
            else:
                preview.hide_preview()


    def _next_preview_signature(self):
        queue = self.playback_queue

        current_entry = queue.current_entry

        return (
            current_entry["id"] if current_entry else None,
            tuple(entry["id"] for entry in queue.upcoming),
            tuple(entry["id"] for entry in queue._context_entries),
            queue.repeat_mode,
            queue.shuffle_enabled,
            self.infinity_play_enabled,
            tuple(sorted(self._infinity_cycle_seen))
        )


    def _build_next_preview_data(self):
        queue = self.playback_queue
        signature = self._next_preview_signature()

        random_state = random.getstate()

        try:
            queue_copy = copy.deepcopy(queue)
            candidate = queue_copy.next_track(on_end=True)
        finally:
            random.setstate(random_state)

        if candidate is not None:
            kind = (
                "repeat"
                if queue.repeat_mode == "track"
                else "queue"
            )

            entry = queue_copy.current_entry

            return {
                "track": candidate,
                "kind": kind,
                "entry_id": (
                    entry["id"]
                    if kind == "queue" and entry
                    else None
                ),
                "signature": signature,
                "infinity_seen": None
            }

        if (
            not self.infinity_play_enabled
            or queue.repeat_mode != "off"
        ):
            return None

        seen_before = set(self._infinity_cycle_seen)
        random_state = random.getstate()

        try:
            if queue.shuffle_enabled:
                candidate = self._next_infinity_random_track()
            else:
                candidate = self._next_infinity_sequential_track()

            seen_after = set(self._infinity_cycle_seen)

        finally:
            self._infinity_cycle_seen = seen_before
            random.setstate(random_state)

        if candidate is None:
            return None

        return {
            "track": candidate,
            "kind": "infinity",
            "entry_id": None,
            "signature": signature,
            "infinity_seen": seen_after
        }


    def _update_next_track_preview(self, position, duration):
        if not self.audio_player.is_playing:
            return

        remaining = duration - position

        if remaining <= 0 or remaining > 5.0:
            return

        crossfade_in_progress = (
            self.audio_player.crossfade_active
            or self._crossfade_transition_started
        )

        if crossfade_in_progress:
            track = getattr(
                self,
                "_crossfade_preview_track",
                None
            )

            if track is None or not self.next_track_preview_enabled:
                return

            for preview in (
                self.next_track_preview,
                self.fullscreen_player.next_track_preview
            ):
                if not getattr(preview, "_visible", False):
                    preview.show_track(track)

            return

        signature = self._next_preview_signature()
        preview_data = self._next_preview_data

        if (
            preview_data is not None
            and preview_data["signature"] != signature
        ):
            self._hide_next_track_preview()
            preview_data = None

        if preview_data is None:
            preview_data = self._build_next_preview_data()

            if preview_data is None:
                return

            self._next_preview_data = preview_data

        if self.next_track_preview_enabled:
            track = preview_data["track"]

            for preview in (
                self.next_track_preview,
                self.fullscreen_player.next_track_preview
            ):
                if not getattr(preview, "_visible", False):
                    preview.show_track(track)

    def _has_automatic_next_track(self):
        queue = self.playback_queue

        if queue.current_track and queue.repeat_mode == "track":
            return True

        if queue.upcoming:
            return True

        if (
            queue.repeat_mode == "queue"
            and queue._context_entries
        ):
            return True

        if (
            self.infinity_play_enabled
            and queue.repeat_mode == "off"
        ):
            current_key = self._infinity_track_key(
                self.current_track
            )

            for track in self._get_infinity_library_tracks():
                key = self._infinity_track_key(track)

                if key and key != current_key:
                    return True

        return False

    def _advance_to_next_track(
        self,
        on_end=False,
        use_crossfade=False
    ):
        _timing_start = time.perf_counter()
        preview_data = (
            self._next_preview_data
            if on_end
            else None
        )

        signature_matches = (
            preview_data is not None
            and preview_data["signature"]
            == self._next_preview_signature()
        )

        if not on_end:
            self._hide_next_track_preview()

        preferred_entry_id = None

        if signature_matches and preview_data["kind"] == "queue":
            preferred_entry_id = preview_data["entry_id"]

        track = self.playback_queue.next_track(
            on_end=on_end,
            preferred_entry_id=preferred_entry_id
        )

        if (
            track is None
            and self.infinity_play_enabled
            and self.playback_queue.repeat_mode == "off"
        ):
            if (
                signature_matches
                and preview_data["kind"] == "infinity"
            ):
                track = preview_data["track"]
                self._infinity_cycle_seen = set(
                    preview_data["infinity_seen"]
                )

            else:
                if self.playback_queue.shuffle_enabled:
                    next_infinity_track = (
                        self._next_infinity_random_track()
                    )
                else:
                    next_infinity_track = (
                        self._next_infinity_sequential_track()
                    )

                track = next_infinity_track

            if track:
                self.playback_queue.add_to_end(track)
                track = self.playback_queue.next_track(
                    on_end=on_end
                )

        if track:
            self.play_track_data(
                track,
                cover_transition="next",
                automatic_transition=on_end,
                crossfade_transition=use_crossfade
            )
        else:
            self.stop_playback()

        _elapsed = (time.perf_counter() - _timing_start) * 1000
        if _elapsed >= 20:
            print(f"[Track Switch] advance_to_next_track: {_elapsed:.1f} ms", flush=True)


    def play_next_track(self):
        self._advance_to_next_track()

    def play_previous_track(self):
        self._hide_next_track_preview()
        track = self.playback_queue.previous_track()

        if track:
            self.play_track_data(
                track,
                cover_transition="previous"
            )

    def handle_track_finished(self):
        self._advance_to_next_track(on_end=True)

    def stop_playback(self):
        self._usage_finalize_all()
        self._hide_next_track_preview()
        self._crossfade_transition_started = False
        self._crossfade_checked_path = None
        self.audio_player.stop()
        self.player.set_playing(False)
        self.player.current_time_label.setText("0:00")
        self.player.duration_label.setText("0:00")

        self.player.progress_slider.blockSignals(True)
        self.player.progress_slider.setValue(0)
        self.player.progress_slider.blockSignals(False)


    def _update_playback_visualizer(self):
        audio = self.audio_player

        has_current_track = bool(
            audio.current_path
            and (audio.is_playing or audio.is_paused)
        )

        current_path = None

        if has_current_track:
            try:
                current_path = str(
                    Path(audio.current_path).expanduser().resolve()
                )
            except (OSError, RuntimeError, TypeError, ValueError):
                current_path = None

        if audio.is_playing and current_path:
            self._playback_visualizer_tick += 1

            if self._playback_visualizer_tick % 8 == 1:
                self._playback_visualizer_targets = [
                    random.uniform(0.08, 1.0)
                    for _ in range(512)
                ]

            levels = self._playback_visualizer_levels
            targets = self._playback_visualizer_targets

            for index in range(len(levels)):
                levels[index] += (
                    targets[index] - levels[index]
                ) * 0.14

        levels = self._playback_visualizer_levels

        for row in self.findChildren(HomeTrackRow):
            row.set_playback_visualizer(
                current_path,
                levels
            )

        for row in self.findChildren(TrackListRow):
            row.set_playback_visualizer(
                current_path,
                levels
            )

        for track_list in self.findChildren(VirtualTrackList):
            delegate = track_list.delegate

            delegate.playing_path = current_path
            delegate.playback_visualizer_levels = (
                list(levels) if current_path else []
            )

            track_list.view.viewport().update()

    def toggle_playback(self):
        if not self.current_track:
            QMessageBox.information(
                self,
                "SerifaPlayer",
                "Selecione uma faixa na biblioteca primeiro."
            )
            return

        try:
            selected_path = Path(
                self.current_track["path"]
            ).expanduser().resolve()

            if (
                self.audio_player.is_playing
                and self.audio_player.current_path == selected_path
            ):
                self._usage_update_sessions()
                self._usage_flush_sessions()
                self.audio_player.pause()
                self.player.set_playing(False)
                self.fullscreen_player.set_playing(False)
                return

            if (
                self.audio_player.is_paused
                and self.audio_player.current_path == selected_path
            ):
                self.audio_player.resume()
                self._usage_reset_session_positions()
            else:
                self._usage_finalize_all()
                self.audio_player.play(selected_path)
                self._usage_start_session(
                    self.current_track,
                    self.audio_player.active_deck
                )

            self.player.set_playing(True)
            self.fullscreen_player.set_playing(True)

        except Exception as error:
            self.player.set_playing(False)
            self.fullscreen_player.set_playing(False)

            QMessageBox.warning(
                self,
                "Erro de reprodução",
                str(error)
            )

    def format_time(self, seconds):
        seconds = max(0, int(seconds))

        if seconds >= 3600:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            remaining = seconds % 60
            return f"{hours}:{minutes:02d}:{remaining:02d}"

        minutes = seconds // 60
        remaining = seconds % 60
        return f"{minutes}:{remaining:02d}"

    def handle_volume_changed(self, value):
        self.audio_player.set_volume(value)
        self.settings.setValue("volume", value)

        if value > 0:
            self._last_nonzero_volume = value
            self.settings.setValue(
                "last_nonzero_volume", value
            )

        self.update_volume_button()

    def update_volume_button(self):
        muted = self.player.volume_slider.value() == 0

        self.player.volume_button.set_active(muted)
        self.player.volume_button.setToolTip(
            tr("controls.unmute", self.interface_language) if muted else tr("controls.mute", self.interface_language)
        )

    def toggle_mute(self):
        current_volume = self.player.volume_slider.value()

        if current_volume > 0:
            self._last_nonzero_volume = current_volume
            self.settings.setValue(
                "last_nonzero_volume", current_volume
            )
            self.player.volume_slider.setValue(0)
        else:
            restore_volume = max(
                1, min(100, self._last_nonzero_volume)
            )
            self.player.volume_slider.setValue(restore_volume)

    def start_seeking(self):
        self._hide_next_track_preview()
        self.seeking = True

    def _request_seek(self, position, duration):
        self._hide_next_track_preview()
        target = max(0.0, min(float(position), duration))

        success = self.audio_player.seek(target)

        if not success:
            self._pending_seek_position = None
            self._pending_seek_deadline = 0.0
            return False

        self._pending_seek_position = target
        self._pending_seek_deadline = time.monotonic() + 2.0

        self.player.current_time_label.setText(
            self.format_time(target)
        )
        self.player.duration_label.setText(
            self.format_time(duration)
        )

        return True

    def seek_from_slider(self):
        self.seeking = False

        if self.audio_player.current_path is None:
            return

        duration = self.audio_player.get_duration()

        if duration <= 0:
            return

        percentage = (
            self.player.progress_slider.value() / 1000
        )

        self._request_seek(duration * percentage, duration)

    def seek_to_percentage(self, percentage):
        if self.audio_player.current_path is None:
            return

        duration = self.audio_player.get_duration()

        if duration <= 0:
            return

        position = duration * (percentage / 100)
        self._request_seek(position, duration)

    def _mpris_play(self):
        if not self.current_track:
            return

        if (
            self.audio_player.is_paused
            or not self.audio_player.is_playing
        ):
            self.toggle_playback()

    def _mpris_pause(self):
        if (
            self.audio_player.is_playing
            and not self.audio_player.is_paused
        ):
            self.toggle_playback()

    def _mpris_set_volume(self, value):
        self.handle_volume_changed(
            round(value * 100)
        )

    def _mpris_seek_relative(self, offset):
        if self.audio_player.current_path is None:
            return

        duration = self.audio_player.get_duration()
        position = self.audio_player.get_position()

        if duration > 0:
            self._request_seek(
                position + offset / 1_000_000,
                duration
            )

    def _mpris_seek_absolute(self, position):
        if self.audio_player.current_path is None:
            return

        duration = self.audio_player.get_duration()

        if duration > 0:
            self._request_seek(
                position / 1_000_000,
                duration
            )

    def _update_mpris_state(self):
        if not hasattr(self, "mpris_service"):
            return

        audio = self.audio_player
        track = self.current_track

        if track and audio.is_paused:
            status = "Paused"
        elif track and audio.is_playing:
            status = "Playing"
        else:
            status = "Stopped"

        position = 0.0

        if audio.current_path is not None:
            try:
                position = max(
                    0.0,
                    float(audio.get_position())
                )
            except Exception:
                position = 0.0

        volume = self.player.volume_slider.value() / 100.0

        self.mpris_service.update(
            track,
            status,
            position,
            volume,
            bool(track and self._has_automatic_next_track()),
            bool(track and self.playback_queue.history)
        )

    def update_progress(self):
        started = time.perf_counter()
        try:
            self._update_progress_impl()
        finally:
            self._update_mpris_state()

            elapsed = (time.perf_counter() - started) * 1000
            if elapsed >= 30:
                print(
                    f"[Progress Timer] update_progress: "
                    f"{elapsed:.1f} ms",
                    flush=True
                )

    def _update_progress_impl(self):
        self._usage_update_sessions()

        if self.audio_player.crossfade_active:
            started = time.perf_counter()
            self.audio_player.update_crossfade()
            elapsed = (time.perf_counter() - started) * 1000
            if elapsed >= 20:
                print(f"[Progress Detail] update_crossfade: {elapsed:.1f} ms", flush=True)

        elif self._crossfade_transition_started:
            self._crossfade_transition_started = False
            self._crossfade_checked_path = None

            self._finish_next_track_preview()
            self._crossfade_preview_track = None

        started = time.perf_counter()
        messages = self.audio_player.poll_bus()
        elapsed = (time.perf_counter() - started) * 1000
        if elapsed >= 20:
            print(f"[Progress Detail] poll_bus: {elapsed:.1f} ms", flush=True)

        for message in messages:
            if message["type"] == "error":
                self.player.set_playing(False)

                self._pending_seek_position = None
                self._pending_seek_deadline = 0.0

                QMessageBox.warning(
                    self,
                    "Erro de reprodução",
                    message["message"]
                )

            elif message["type"] == "eos":
                self.handle_track_finished()

        if self.audio_player.current_path is None:
            self._pending_seek_position = None
            self._pending_seek_deadline = 0.0
            return

        progress_deck = (
            self.audio_player.crossfade_from
            if (
                self.audio_player.crossfade_active
                and not self.audio_player.crossfade_outgoing_finished
            )
            else None
        )

        started = time.perf_counter()
        duration = self.audio_player.get_duration(progress_deck)
        elapsed = (time.perf_counter() - started) * 1000
        if elapsed >= 20:
            print(f"[Progress Detail] get_duration: {elapsed:.1f} ms", flush=True)

        started = time.perf_counter()
        position = self.audio_player.get_position(progress_deck)
        elapsed = (time.perf_counter() - started) * 1000
        if elapsed >= 20:
            print(f"[Progress Detail] get_position: {elapsed:.1f} ms", flush=True)

        if duration <= 0:
            return

        remaining = duration - position

        if (
            self.crossfade_enabled
            and self.audio_player.is_playing
            and not self.audio_player.is_paused
            and not self._crossfade_transition_started
        ):
            current_path = str(self.audio_player.current_path)

            if (
                self._crossfade_checked_path != current_path
                and remaining <= self.crossfade_duration / 2.0
            ):
                if (
                    duration >= self.crossfade_duration / 2.0
                    and self._has_automatic_next_track()
                ):
                    self._advance_to_next_track(
                        on_end=True,
                        use_crossfade=True
                    )
                    return

                self._crossfade_checked_path = current_path

        position = min(position, duration)

        pending_position = self._pending_seek_position

        if pending_position is not None:
            seek_confirmed = (
                abs(position - pending_position) <= 0.75
            )
            seek_timed_out = (
                time.monotonic() >= self._pending_seek_deadline
            )

            if seek_confirmed or seek_timed_out:
                self._pending_seek_position = None
                self._pending_seek_deadline = 0.0
            else:
                position = pending_position

        self.fullscreen_player.set_progress(
            position,
            duration
        )

        self.player.current_time_label.setText(
            self.format_time(position)
        )
        self.player.duration_label.setText(
            self.format_time(duration)
        )

        if not self.seeking:
            value = round((position / duration) * 1000)

            self.player.progress_slider.blockSignals(True)
            self.player.progress_slider.setValue(value)
            self.player.progress_slider.blockSignals(False)
        started = time.perf_counter()
        self._update_next_track_preview(
            position,
            duration
        )
        elapsed = (time.perf_counter() - started) * 1000
        if elapsed >= 20:
            print(f"[Progress Detail] next_track_preview: {elapsed:.1f} ms", flush=True)

    def show_fullscreen_player(self):
        if self.current_track is None:
            return

        self.fullscreen_player.showFullScreen()
        self.fullscreen_player.raise_()
        self.fullscreen_player.activateWindow()

    def closeEvent(self, event):
        if self.fullscreen_player.isVisible():
            self.fullscreen_player.close()

        self.save_playback_session()

        self.session_save_timer.stop()
        self.session_restore_timer.stop()
        self.progress_timer.stop()

        self.equalizer_dialog.save_settings()

        self._usage_update_sessions()
        self._usage_finalize_all()

        self.audio_player.stop()

        if hasattr(self, "mpris_service"):
            self.mpris_service.stop()

        event.accept()

    def show_library(self, tab_index=0):
        if not self.library_access_ready:
            self.library_settings.scan_status.setText(
                "Aguarde a verificação dos discos da biblioteca."
            )
            return

        try:
            tab_index = int(tab_index)
        except (TypeError, ValueError):
            tab_index = 0

        tab_index = max(0, min(3, tab_index))

        self.library_view.tabs.setCurrentIndex(tab_index)
        self.library_view.refresh_tab(tab_index)
        self.pages.setCurrentWidget(self.library_view)

        active_index = {
            0: 3,
            1: 4,
            2: 2,
            3: 5,
        }.get(tab_index, 5)

        self.set_active_navigation(
            self.sidebar.buttons[active_index]
        )

    def show_playlists(self):
        if not self.library_access_ready:
            self.library_settings.scan_status.setText(
                "Aguarde a verificação dos discos da biblioteca."
            )
            return

        if self.library_view.current_playlist_id is not None:
            self.library_view.close_playlist_detail()
        else:
            self.library_view.refresh_playlists()

        self.library_view.tabs.setCurrentIndex(2)
        self.pages.setCurrentIndex(1)

        self.set_active_navigation(
            self.sidebar.buttons[2]
        )

    def show_library_settings(self):
        if not self.library_access_ready:
            self.library_settings.scan_status.setText(
                "Aguarde a verificação dos discos da biblioteca."
            )
            return

        self.library_settings.refresh(
            self.library_folders
        )
        self.pages.setCurrentWidget(self.library_settings)

        self.set_active_navigation(
            self.sidebar.import_button
        )

    def open_folder_browser(self):
        self.folder_browser.start()

        self.pages.setCurrentIndex(2)

    # --------------------------------------------------
    # IMPORTAÇÃO MUSICAL
    # --------------------------------------------------

    def start_library_access_check(self):
        if self.library_access_worker is not None:
            return

        self.library_access_ready = False
        self.library_settings.scan_button.setEnabled(False)
        self.library_settings.scan_status.setText(
            "Verificando os discos e as pastas da biblioteca..."
        )

        self.library_access_worker = LibraryAccessWorker(
            self.storage_manager,
            self.library_folders,
            self.library_volume_registry,
            self.library_volume_registry_error
        )

        self.library_access_worker.progress.connect(
            self.update_library_access_progress
        )
        self.library_access_worker.completed.connect(
            self.finish_library_access_check
        )
        self.library_access_worker.finished.connect(
            self.release_library_access_worker
        )
        self.library_access_worker.start()

    def update_library_access_progress(self, message):
        self.library_settings.scan_status.setText(message)

        splash = getattr(self, "splash_screen", None)

        if splash is not None:
            splash.set_status(message)

    def finish_library_access_check(self, result):
        result = dict(result or {})
        entries = list(result.get("resolved_entries", []))
        unavailable = list(result.get("unavailable", []))
        available = list(result.get("available_folders", []))

        failed_volume_ids = set()
        grouped = {}

        for entry in entries:
            if entry.get("kind") == "volume" and entry.get("uuid"):
                grouped.setdefault(entry["uuid"], []).append(entry)

        for volume_uuid, volume_entries in grouped.items():
            roots = {
                (item.get("old_mountpoint"), item.get("new_mountpoint"))
                for item in volume_entries
            }

            try:
                root_pairs = []

                for old_root, new_root in roots:
                    if not old_root or not new_root:
                        raise RuntimeError(
                            "O caminho de montagem antigo ou atual "
                            "não foi identificado."
                        )

                    old_path = os.path.realpath(old_root)
                    new_path = os.path.realpath(new_root)

                    if old_path != new_path:
                        root_pairs.append((old_root, new_root))

                if root_pairs:
                    self.scanner.remap_volume_paths_batch(root_pairs)

            except Exception as error:
                failed_volume_ids.add(volume_uuid)

                for item in volume_entries:
                    unavailable.append({
                        "path": item["original"],
                        "reason": (
                            "Não foi possível atualizar os caminhos "
                            f"da biblioteca: {error}"
                        )
                    })

        if failed_volume_ids:
            entries = [
                item for item in entries
                if item.get("uuid") not in failed_volume_ids
            ]

            failed_resolved = {
                self.registry_path_key(item["resolved"])
                for item in result.get("resolved_entries", [])
                if item.get("uuid") in failed_volume_ids
            }

            available = [
                folder for folder in available
                if self.registry_path_key(folder) not in failed_resolved
            ]

        self.library_access_ready = True
        self.library_access_result = {
            "unavailable": unavailable,
            "warnings": list(result.get("warnings", []))
        }
        self.available_library_folders = list(dict.fromkeys(available))

        # Atualiza os caminhos persistidos somente quando o registro
        # de volumes foi carregado sem erros.
        if not self.library_volume_registry_error:
            replacements = {
                self.registry_path_key(item["original"]): item["resolved"]
                for item in entries
            }

            previous_folders = list(self.library_folders)
            previous_registry = json.loads(
                json.dumps(self.library_volume_registry)
            )

            updated_folders = [
                replacements.get(self.registry_path_key(folder), folder)
                for folder in self.library_folders
            ]

            registry_replacements = {
                self.registry_path_key(item["original"]): item
                for item in entries
            }

            updated_registry = []
            for item in self.library_volume_registry.get("folders", []):
                replacement = registry_replacements.get(
                    self.registry_path_key(item.get("path", ""))
                )

                updated = dict(item)

                if replacement:
                    updated["path"] = replacement["resolved"]

                    if replacement.get("kind") == "volume":
                        updated["registered_mountpoint"] = (
                            replacement.get("new_mountpoint")
                            or updated.get("registered_mountpoint")
                        )

                    elif updated.get("kind") == "local":
                        updated["absolute_path"] = replacement["resolved"]

                updated_registry.append(updated)

            try:
                self.library_folders = updated_folders
                self.library_volume_registry["folders"] = updated_registry

                self.save_library_configuration_transactionally()

            except Exception as error:
                self.library_folders = previous_folders
                self.library_volume_registry = previous_registry

                result.setdefault("warnings", []).append(
                    f"Não foi possível atualizar os caminhos salvos: {error}"
                )

        self.library_settings.refresh(self.library_folders)
        self.library_settings.scan_button.setEnabled(
            bool(self.available_library_folders)
        )

        self.update_library_status()
        self.home.refresh()
        self.library_view.refresh()

        if unavailable or result.get("warnings"):
            details = []

            for item in unavailable:
                details.append(
                    f"• {item.get('path')}: {item.get('reason')}"
                )

            details.extend(
                f"• {warning}" for warning in result.get("warnings", [])
            )

            QMessageBox.warning(
                self,
                "Acesso parcial à biblioteca",
                "Algumas pastas não puderam ser disponibilizadas. "
                "As demais continuam acessíveis.\n\n"
                + "\n".join(details)
            )

        if self.available_library_folders:
            self.library_settings.scan_status.setText(
                f"{len(self.available_library_folders)} pasta(s) "
                "disponível(is) para importação."
            )
        elif self.library_folders:
            self.library_settings.scan_status.setText(
                "Nenhuma pasta cadastrada está disponível no momento."
            )
        else:
            self.library_settings.scan_status.setText(
                "Adicione pastas para começar a importar músicas."
            )

        self.restore_playback_session()

        if not self.session_restore_timer.isActive():
            self.complete_startup()

    def complete_startup(self):
        if getattr(self, "_startup_completed", False):
            return
        self._startup_completed = True
        self.show()
        splash = getattr(self, "splash_screen", None)
        if splash is not None:
            splash.finish()

    def save_playback_session(self):
        track = self.current_track
        current_path = self.audio_player.current_path

        if not track or not current_path:
            return

        try:
            track_path = Path(
                track.get("path", "")
            ).expanduser().resolve()

            if track_path != current_path.resolve():
                return

            track_id = track.get("id")
            if track_id is None:
                return

            position = max(
                0.0,
                float(self.audio_player.get_position())
            )

            self.settings.setValue(
                "last_track_id",
                int(track_id)
            )
            self.settings.setValue(
                "last_track_path",
                str(current_path)
            )
            self.settings.setValue(
                "last_position",
                position
            )
            self.settings.sync()

        except (OSError, TypeError, ValueError):
            return

    def restore_playback_session(self):
        if self._session_restore_attempted:
            return

        self._session_restore_attempted = True

        if not self.library_access_ready:
            return

        saved_id = self.settings.value("last_track_id")
        saved_path = self.settings.value("last_track_path", "")
        saved_position = self.settings.value(
            "last_position",
            0.0,
            type=float
        )

        try:
            saved_id = int(saved_id) if saved_id is not None else None
        except (TypeError, ValueError):
            saved_id = None

        try:
            saved_position = max(0.0, float(saved_position))
        except (TypeError, ValueError):
            saved_position = 0.0

        if saved_id is None and not saved_path:
            return

        tracks = self.scanner.list_tracks(limit=None)

        track = None

        if saved_id is not None:
            track = next(
                (
                    item for item in tracks
                    if item.get("id") == saved_id
                ),
                None
            )

        if track is None and saved_path:
            try:
                saved_resolved = Path(
                    saved_path
                ).expanduser().resolve()

                track = next(
                    (
                        item for item in tracks
                        if Path(
                            item.get("path", "")
                        ).expanduser().resolve() == saved_resolved
                    ),
                    None
                )
            except (OSError, RuntimeError, ValueError):
                track = None

        if not track or not self._track_is_available(track):
            return

        try:
            selected_path = Path(
                track["path"]
            ).expanduser().resolve()

            self.audio_player.load_paused(selected_path)

            self.current_track = track
            self.player.set_track(track)
            self.update_favorite_button()

            self.player.set_playing(False)

            self._session_restore_position = saved_position
            self._session_restore_attempts = 0

            self.session_restore_timer.start()

        except Exception as error:
            self.current_track = None
            self.audio_player.stop()

            print(
                "Não foi possível restaurar a sessão:",
                error
            )

    def finish_session_restore(self):
        if self.audio_player.current_path is None:
            self.session_restore_timer.stop()
            self.complete_startup()
            return

        self._session_restore_attempts += 1

        duration = self.audio_player.get_duration()

        if duration <= 0:
            if self._session_restore_attempts >= 60:
                self.session_restore_timer.stop()
                print(
                    "A restauração da posição expirou: "
                    "duração indisponível."
                )
                self.complete_startup()
            return

        position = min(
            self._session_restore_position,
            max(0.0, duration - 0.5)
        )

        if position > 0:
            if not self.audio_player.seek(position):
                if self._session_restore_attempts >= 60:
                    self.session_restore_timer.stop()
                    print(
                        "Não foi possível restaurar "
                        "a posição da faixa."
                    )
                    self.complete_startup()
                return

        self.session_restore_timer.stop()

        self.audio_player.is_playing = False
        self.audio_player.is_paused = True

        self.player.set_playing(False)
        self.update_progress()

        print(
            "Sessão restaurada:",
            self.current_track.get("title", "Faixa desconhecida"),
            f"({self.format_time(position)})"
        )

        self.complete_startup()

    def release_library_access_worker(self):
        self.library_access_worker = None

    def _track_is_available(self, track):
        if not self.library_access_ready or not track:
            return False

        path = track.get("path")
        if not path:
            return False

        try:
            target = Path(path).expanduser().resolve()
            for folder in self.available_library_folders:
                root = Path(folder).expanduser().resolve()
                if target.is_relative_to(root) and target.is_file():
                    return True
        except (OSError, RuntimeError, ValueError):
            return False

        return False

    def confirm_library_reset(self):
        if self.scan_worker is not None:
            if self.scan_worker.isRunning():
                QMessageBox.warning(
                    self,
                    tr("reset.scan.title", self.interface_language),
                    tr("reset.scan.body", self.interface_language)
                )
                return

        access_worker = getattr(self, "library_access_worker", None)
        if access_worker is not None and access_worker.isRunning():
            QMessageBox.warning(
                self,
                tr("reset.access.title", self.interface_language),
                tr("reset.access.body", self.interface_language)
            )
            return

        if not self.library_access_ready:
            QMessageBox.warning(
                self,
                tr("reset.busy.title", self.interface_language),
                tr("reset.busy.body", self.interface_language)
            )
            return

        if self.library_volume_registry_error:
            QMessageBox.critical(
                self,
                tr("reset.registry.title", self.interface_language),
                tr("reset.registry.body", self.interface_language)
            )
            return

        answer = QMessageBox.warning(
            self,
            tr("reset.confirm.title", self.interface_language),
            tr("reset.confirm.body", self.interface_language),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        confirmation, accepted = QInputDialog.getText(
            self,
            tr("reset.final.title", self.interface_language),
            tr("reset.final.body", self.interface_language)
        )

        if not accepted or confirmation.strip() != "RESET":
            return

        try:
            self.reset_library_data()
        except Exception as error:
            QMessageBox.critical(
                self,
                tr("reset.failure.title", self.interface_language),
                tr("reset.failure.body", self.interface_language).format(
                    error=error
                )
            )
            return

        QMessageBox.information(
            self,
            tr("reset.success.title", self.interface_language),
            tr("reset.success.body", self.interface_language)
        )

    def reset_library_data(self):
        if self.library_volume_registry_error:
            raise RuntimeError(
                "O cadastro de volumes está com erro de leitura."
            )

        old_folders = list(self.library_folders)
        old_registry = copy.deepcopy(self.library_volume_registry)
        old_available = list(self.available_library_folders)

        config_paths = (
            self.library_file,
            self.library_volume_file
        )
        config_snapshots = {
            item: item.read_bytes() if item.exists() else None
            for item in config_paths
        }

        covers_path = Path(self.covers_dir)
        data_path = Path(self.data_dir).resolve()

        if covers_path.is_symlink():
            raise RuntimeError(
                "A pasta de capas é um link simbólico. "
                "A limpeza foi cancelada por segurança."
            )

        if covers_path.resolve().parent != data_path:
            raise RuntimeError(
                "O caminho da pasta de capas não corresponde "
                "à pasta local de dados."
            )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        covers_backup = self.data_dir / f"covers.reset.{timestamp}"
        covers_moved = False
        connection = None

        try:
            connection = self.scanner._connect()
            connection.execute("BEGIN IMMEDIATE")

            connection.execute("DELETE FROM playlist_tracks")
            connection.execute("DELETE FROM track_stats")
            connection.execute("DELETE FROM playlists")
            connection.execute("DELETE FROM playlist_folders")
            connection.execute("DELETE FROM tracks")
            connection.execute(
                "DELETE FROM sqlite_sequence "
                "WHERE name IN ('tracks', 'playlists', 'playlist_tracks', 'playlist_folders')"
            )

            if covers_path.exists():
                os.replace(covers_path, covers_backup)
                covers_moved = True

            covers_path.mkdir(parents=True, exist_ok=True)

            self.library_folders = []
            self.library_volume_registry = {
                "version": 1,
                "folders": []
            }

            self.save_library_configuration_transactionally()
            connection.commit()

        except Exception:
            if connection is not None:
                connection.rollback()

            self.library_folders = old_folders
            self.library_volume_registry = old_registry
            self.available_library_folders = old_available

            for config_path, snapshot in config_snapshots.items():
                if snapshot is None:
                    config_path.unlink(missing_ok=True)
                else:
                    temporary = config_path.with_name(
                        config_path.name + ".reset-rollback.tmp"
                    )
                    temporary.write_bytes(snapshot)
                    temporary.replace(config_path)

            if covers_moved:
                if covers_path.exists():
                    shutil.rmtree(covers_path)
                os.replace(covers_backup, covers_path)

            raise

        finally:
            if connection is not None:
                connection.close()

        if covers_backup.exists():
            try:
                shutil.rmtree(covers_backup)
            except OSError:
                pass

        self.available_library_folders = []
        self.library_access_ready = True
        self.library_access_result = None

        self.stop_playback()
        self.current_track = None
        self.playback_queue.clear()
        self._next_preview_data = None
        self._hide_next_track_preview()

        self.settings.remove("last_track_id")
        self.settings.remove("last_track_path")
        self.settings.remove("last_position")
        self.settings.sync()

        self.player.set_playing(False)
        self.player.song_label.setText("Nenhuma música selecionada")
        self.player.artist_label.clear()
        self.player.cover_widget.clear()
        _set_theme_stylesheet(self.player.cover_widget, "background: transparent; border-radius: 8px;"
        )
        self.player.favorite_button.setEnabled(False)
        self.player.favorite_button.set_active(False)
        self.player.favorite_button.setToolTip(
            "Nenhuma música selecionada"
        )

        self.fullscreen_player.set_playing(False)
        self.fullscreen_player.title_label.setText(
            "Nenhuma música selecionada"
        )
        self.fullscreen_player.artist_label.clear()
        self.fullscreen_player.cover.set_pixmap(QPixmap())
        self.fullscreen_player._current_cover_path = None
        self.fullscreen_player._track_pixmap = QPixmap()
        self.fullscreen_player._update_background()

        self.library_settings.refresh([])
        self.library_settings.scan_button.setEnabled(True)
        self.library_settings.scan_status.setText(
            "Adicione pastas para começar a importar músicas."
        )

        self.update_library_status()
        self.refresh_queue_panel()
        self.update_favorite_button()
        self.home.refresh()
        self.library_view.refresh()
        self.favorites_view.refresh()

    def update_library_status(self):
        if not self.library_access_ready:
            self.library_settings.scan_status.setText(
                "Verificando os discos e as pastas da biblioteca..."
            )
            return

        if not self.library_folders:
            self.library_settings.scan_status.setText(
                "Adicione pastas para começar a importar músicas."
            )
            return

        if not self.available_library_folders:
            self.library_settings.scan_status.setText(
                "Nenhuma pasta cadastrada está disponível no momento."
            )
            return

        total = self.scanner.count_tracks()
        available_count = len(self.available_library_folders)

        self.library_settings.scan_status.setText(
            f"{total} música(s) cadastrada(s) na biblioteca. "
            f"{available_count} pasta(s) disponível(is)."
        )

    def start_library_scan(self):
        if self.scan_worker is not None:
            if self.scan_worker.isRunning():
                return

        if not self.library_folders:
            QMessageBox.information(
                self,
                "Biblioteca vazia",
                "Adicione pelo menos uma pasta antes de importar músicas."
            )
            return

        if not self.library_access_ready:
            self.library_settings.scan_status.setText(
                "Aguarde a verificação dos discos da biblioteca."
            )
            return

        available_folders = list(self.available_library_folders)

        if not available_folders:
            QMessageBox.warning(
                self,
                "Pastas indisponíveis",
                "Nenhuma das pastas cadastradas está acessível.\n\n"
                "Verifique se os discos estão conectados e montados."
            )
            return

        self.library_settings.scan_button.setEnabled(False)
        self.set_player_busy(True)

        self.library_settings.scan_status.setText(
            "Preparando a leitura dos arquivos..."
        )

        self.scan_worker = ScanWorker(
            self.scanner,
            available_folders
        )

        self.scan_worker.progress.connect(
            self.update_scan_progress
        )

        self.scan_worker.completed.connect(
            self.finish_library_scan
        )

        self.scan_worker.failed.connect(
            self.fail_library_scan
        )

        self.scan_worker.finished.connect(
            self.release_scan_worker
        )

        self.scan_worker.start()

    def set_player_busy(self, busy):
        self.player.set_busy(busy)
        self.fullscreen_player.set_busy(busy)


    def update_scan_progress(self, filename):
        self.library_settings.scan_status.setText(
            f"Lendo arquivo:\n{filename}"
        )

    def finish_library_scan(self, result):
        self.library_settings.scan_button.setEnabled(True)
        self.set_player_busy(False)

        self.update_library_status()
        self.home.refresh()
        self.library_view.refresh()

        message = (
            "Importação concluída!\n\n"
            f"Novas músicas: {result['imported']}\n"
            f"Músicas atualizadas: {result['updated']}\n"
            f"Arquivos ignorados ou com erro: {result['errors']}\n"
            f"Total de músicas cadastradas: {result['total']}"
        )

        self.library_settings.scan_status.setText(
            f"Importação concluída. "
            f"{result['total']} música(s) cadastrada(s)."
        )

        QMessageBox.information(
            self,
            "Importação concluída",
            message
        )

    def fail_library_scan(self, error):
        self.library_settings.scan_button.setEnabled(True)
        self.set_player_busy(False)

        self.library_settings.scan_status.setText(
            "Ocorreu um erro durante a importação."
        )

        QMessageBox.critical(
            self,
            "Erro na importação",
            error
        )

    def release_scan_worker(self):
        self.scan_worker = None
    # --------------------------------------------------
    # ESTILO E NAVEGAÇÃO
    # --------------------------------------------------

    def set_active_navigation(self, active_button):
        buttons = (
            self.sidebar.buttons
            + [
                self.sidebar.import_button,
                self.sidebar.settings_button
            ]
        )

        for button in buttons:
            is_active = button is active_button

            button.setProperty(
                "active",
                is_active
            )

            self.sidebar.refresh_button_icon_state(button)

            button.style().unpolish(button)
            button.style().polish(button)


# --------------------------------------------------
# APPLICATION
# --------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Serifa Music")
    app.setDesktopFileName("com.serifa.SerifaMusic")

    icon_path = (
        Path(__file__).resolve().parent.parent
        / "customization"
        / "logos"
        / "logo_square.svg"
    )
    app.setWindowIcon(QIcon(str(icon_path)))

    appearance = AppearanceManager()
    app.setProperty("serifa_appearance_manager", appearance)

    primary_font = appearance.get_value(
        "typography", "fonts", "primary", "Inter"
    )
    fallback_font = appearance.get_value(
        "typography", "fonts", "fallback", "Noto Sans"
    )
    regular_weight = appearance.get_value(
        "typography", "weights", "regular", 400
    )

    application_font = QFont()
    application_font.setFamilies([
        primary_font,
        fallback_font
    ])
    application_font.setWeight(
        QFont.Weight(int(regular_weight))
    )
    app.setFont(application_font)

    def theme_color(section, name, fallback):
        return appearance.get_color(section, name, fallback)

    startup_settings = QSettings("SerifaPlayer", "SerifaPlayer")
    app.setProperty(
        "interface_language",
        load_language(startup_settings)
    )

    # Identidade visual independente do tema do sistema.
    class TooltipStyle(QProxyStyle):
        def drawPrimitive(self, element, option, painter, widget=None):
            if element == QStyle.PrimitiveElement.PE_PanelTipLabel:
                painter.save()
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                rect = QRectF(option.rect).adjusted(0.5, 0.5, -0.5, -0.5)
                path = QPainterPath()
                path.addRoundedRect(rect, 7, 7)
                painter.fillPath(
                    path,
                    QColor(theme_color("qt", "tooltip_background", "#211E2A"))
                )
                painter.setPen(
                    QColor(theme_color("qt", "tooltip_border", "#FFFFFF"))
                )
                painter.drawPath(path)
                painter.restore()
                return

            super().drawPrimitive(element, option, painter, widget)

    app.setStyle(TooltipStyle("Fusion"))

    palette = QPalette()

    # Cores gerais do Qt, todas editáveis em customization/colors.toml.
    colors = {
        QPalette.ColorRole.Window: theme_color("qt", "janela", "#17151e"),
        QPalette.ColorRole.WindowText: theme_color("qt", "texto_janela", "#f3edf9"),
        QPalette.ColorRole.Base: theme_color("qt", "base", "#1b1823"),
        QPalette.ColorRole.AlternateBase: theme_color("qt", "base_alternada", "#211e2a"),
        QPalette.ColorRole.ToolTipBase: theme_color("qt", "tooltip_background", "#211E2A"),
        QPalette.ColorRole.ToolTipText: theme_color("qt", "tooltip_text", "#FFFFFF"),
        QPalette.ColorRole.Text: theme_color("qt", "texto", "#f3edf9"),
        QPalette.ColorRole.Button: theme_color("qt", "botao", "#302a3b"),
        QPalette.ColorRole.ButtonText: theme_color("qt", "texto_botao", "#e9d5ff"),
        QPalette.ColorRole.BrightText: theme_color("qt", "texto_brilhante", "#ffffff"),
        QPalette.ColorRole.Highlight: theme_color("qt", "selecao", "#72558d"),
        QPalette.ColorRole.HighlightedText: theme_color("qt", "texto_selecao", "#ffffff"),
        QPalette.ColorRole.Light: theme_color("qt", "luz", "#493e58"),
        QPalette.ColorRole.Midlight: theme_color("qt", "meio_claro", "#393243"),
        QPalette.ColorRole.Mid: theme_color("qt", "meio", "#302a3b"),
        QPalette.ColorRole.Dark: theme_color("qt", "escuro", "#17151e"),
        QPalette.ColorRole.Shadow: theme_color("qt", "sombra", "#100e15"),
        QPalette.ColorRole.PlaceholderText: theme_color("qt", "texto_espaco_reservado", "#95899f"),
    }

    for role, color in colors.items():
        palette.setColor(role, QColor(color))

    disabled_colors = {
        QPalette.ColorRole.WindowText: theme_color("qt", "texto_janela", "#81798b"),
        QPalette.ColorRole.Text: theme_color("qt", "texto_desabilitado", "#81798b"),
        QPalette.ColorRole.ButtonText: theme_color("qt", "texto_desabilitado", "#81798b"),
        QPalette.ColorRole.Highlight: theme_color("qt", "selecao_desabilitada", "#493e58"),
        QPalette.ColorRole.HighlightedText: theme_color("qt", "texto_selecao_desabilitada", "#aaa3b6"),
    }

    for role, color in disabled_colors.items():
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            role,
            QColor(color)
        )

    app.setPalette(palette)

    from PySide6.QtWidgets import QToolTip

    tooltip_palette = QPalette()

    for group in (
        QPalette.ColorGroup.Active,
        QPalette.ColorGroup.Inactive,
        QPalette.ColorGroup.Disabled
    ):
        tooltip_palette.setColor(
            group,
            QPalette.ColorRole.ToolTipBase,
            QColor(theme_color("qt", "tooltip_background", "#211E2A"))
        )
        tooltip_palette.setColor(
            group,
            QPalette.ColorRole.ToolTipText,
            QColor(theme_color("qt", "tooltip_text", "#FFFFFF"))
        )

    QToolTip.setPalette(tooltip_palette)

    _set_theme_stylesheet(app, f"""
        QToolTip {{
            color: {theme_color("qt", "tooltip_text", "#FFFFFF")};
            padding: 3px 7px;
            font-size: 11px;
        }}
    """)

    splash = SplashScreen(app.property('interface_language'))
    splash.show()
    app.processEvents()

    window = SerifaPlayer()
    window.splash_screen = splash

    # Aplica o estilo inicial da interface.
    window.set_active_navigation(
        window.sidebar.buttons[0]
    )


    sys.exit(app.exec())


if __name__ == "__main__":
    main()
