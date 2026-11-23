
from collections import OrderedDict
from pathlib import Path

from appearance import get_theme_color

from PySide6.QtCore import (
    Qt,
    QSize,
    QPoint,
    QRectF,
    Signal,
    QAbstractListModel,
    QModelIndex,
    QMimeData,
    QEvent,
)
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPainterPath,
    QPixmap,
    QFont,
    QDrag,
    QIcon,
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListView,
    QStyledItemDelegate,
    QStyle,
    QApplication,
    QAbstractItemView,
    QFrame,
)


class VirtualTrackModel(QAbstractListModel):

    TrackRole = Qt.ItemDataRole.UserRole + 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tracks = []

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self.tracks)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == self.TrackRole:
            return self.tracks[index.row()]

        return None

    def set_tracks(self, tracks):
        self.beginResetModel()
        self.tracks = list(tracks or [])
        self.endResetModel()


class VirtualTrackDelegate(QStyledItemDelegate):

    def __init__(self, parent=None, icon_manager=None):
        super().__init__(parent)
        self.show_favorite = True
        self.library_all_tracks_style = False
        self.playing_path = None
        self.playback_visualizer_levels = []
        self.icon_manager = icon_manager
        self.hovered_play_path = None
        self.pressed_play_path = None

        self.favorite_icons = {
            False: (
                icon_manager.icon("actions.favorite", "normal")
                if icon_manager is not None else QIcon()
            ),
            True: (
                icon_manager.icon("actions.favorite", "active")
                if icon_manager is not None else QIcon()
            ),
        }

        self.cover_cache = OrderedDict()
        self.cover_cache_limit = 160

    @staticmethod
    def track_key(track):
        if not track:
            return None
        path = track.get('path')
        if not path:
            return None
        try:
            return str(Path(path).expanduser().resolve())
        except (OSError, RuntimeError, TypeError, ValueError):
            return str(path)

    def sizeHint(self, option, index):
        return QSize(0, 66)

    @staticmethod
    def track_text(track):
        title = (
            track.get("title")
            or __import__("pathlib").Path(
                track.get("path", "")
            ).stem
            or "Faixa desconhecida"
        )

        artist = (
            track.get("artist")
            or track.get("album_artist")
            or "Artista desconhecido"
        )

        album = track.get("album") or "Álbum desconhecido"

        return title, artist, album

    @staticmethod
    def duration_text(track):
        try:
            seconds = max(
                0,
                int(float(track.get("duration") or 0))
            )
            return f"{seconds // 60}:{seconds % 60:02d}"
        except (TypeError, ValueError):
            return "--:--"

    def cover_pixmap(self, path):
        if not path:
            return None

        path = str(path)

        if path in self.cover_cache:
            self.cover_cache.move_to_end(path)
            return self.cover_cache[path]

        if not __import__("os").path.isfile(path):
            return None

        original = QPixmap(path)

        if original.isNull():
            return None

        scaled = original.scaled(
            QSize(48, 48),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        x = max(0, (scaled.width() - 48) // 2)
        y = max(0, (scaled.height() - 48) // 2)

        pixmap = scaled.copy(x, y, 48, 48)

        self.cover_cache[path] = pixmap

        if len(self.cover_cache) > self.cover_cache_limit:
            self.cover_cache.popitem(last=False)

        return pixmap

    def paint(self, painter, option, index):
        track = index.data(VirtualTrackModel.TrackRole)

        if not track:
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(
            QPainter.RenderHint.SmoothPixmapTransform
        )

        rect = QRectF(option.rect).adjusted(2, 0, -2, 0)

        track_path = track.get("path")
        try:
            track_path = (
                str(Path(track_path).expanduser().resolve())
                if track_path else None
            )
        except (OSError, RuntimeError, TypeError, ValueError):
            track_path = None

        is_playing_track = (
            track_path is not None
            and track_path == self.playing_path
        )

        selected = bool(
            option.state & QStyle.StateFlag.State_Selected
        )
        hovered = bool(
            option.state & QStyle.StateFlag.State_MouseOver
        )

        if selected:
            background = QColor(153, 112, 190, 38)
            border = QColor(153, 112, 190, 90)
        elif hovered:
            background = QColor(255, 255, 255, 19)
            border = QColor(255, 255, 255, 26)
        else:
            background = QColor(255, 255, 255, 6)
            border = QColor(255, 255, 255, 12)

        painter.setPen(border)
        painter.setBrush(background)
        painter.drawRoundedRect(rect, 9, 9)

        if is_playing_track and self.playback_visualizer_levels:
            usable_width = max(1.0, rect.width() - 12.0)
            levels = self.playback_visualizer_levels
            count = max(1, int(usable_width / 5.0))
            step = usable_width / count

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(182, 242, 58, 43))

            for bar_index in range(count):
                bar_height = 2.0 + float(levels[bar_index % len(levels)]) * 8.0
                x = rect.left() + 6.0 + bar_index * step
                bar_width = max(1.2, step * 0.55)

                painter.drawRoundedRect(
                    QRectF(
                        x,
                        rect.bottom() - bar_height - 2.0,
                        bar_width,
                        bar_height
                    ),
                    1.5,
                    1.5
                )

        cover_rect = QRectF(
            rect.left() + 8,
            rect.top() + 8,
            48,
            48
        )

        cover_path = QPainterPath()
        cover_path.addRoundedRect(cover_rect, 8, 8)

        painter.save()
        painter.setClipPath(cover_path)

        cover = self.cover_pixmap(track.get("cover_path"))

        if cover is not None:
            painter.drawPixmap(
                cover_rect.toRect(),
                cover
            )
        else:
            painter.fillPath(
                cover_path,
                QColor(get_theme_color("tons", "hex_332b40", "#332b40"))
            )
            painter.setPen(QColor(get_theme_color("tons", "hex_a99bbd", "#a99bbd")))
            painter.drawText(
                cover_rect,
                Qt.AlignmentFlag.AlignCenter,
                "♫"
            )

        painter.restore()

        title, artist, album = self.track_text(track)

        text_left = cover_rect.right() + 11
        right_limit = rect.right() - 10

        play_rect = QRectF(
            right_limit - 30,
            rect.center().y() - 15,
            30,
            30
        )

        control_gap = 10
        favorite_rect = QRectF(
            play_rect.left() - control_gap - 30,
            rect.center().y() - 15,
            30,
            30
        )

        duration = self.duration_text(track)
        duration_width = 48

        duration_right = (
            favorite_rect.left() - control_gap
            if self.show_favorite
            else play_rect.left() - control_gap
        )

        text_right = duration_right - duration_width - control_gap
        text_width = max(30, text_right - text_left)

        title_font = QFont()
        title_font.setPixelSize(
            15 if self.library_all_tracks_style else 13
        )
        title_font.setWeight(QFont.Weight.DemiBold)

        painter.setFont(title_font)
        painter.setPen(QColor(get_theme_color("tons", "hex_f2edf7", "#f2edf7")))
        painter.drawText(
            QRectF(text_left, rect.top() + 5, text_width, 22),
            Qt.AlignmentFlag.AlignVCenter,
            painter.fontMetrics().elidedText(
                title,
                Qt.TextElideMode.ElideRight,
                int(text_width)
            )
        )

        metadata_font = QFont()
        metadata_font.setPixelSize(11)
        metadata_y = rect.top() + (
            44 if self.library_all_tracks_style else 54
        )

        painter.setFont(metadata_font)
        painter.setPen(QColor(get_theme_color("tons", "hex_c9a7ef", "#c9a7ef")))

        artist_width = painter.fontMetrics().horizontalAdvance(artist)
        artist_width = min(artist_width, max(0, text_width))

        painter.drawText(
            QPoint(int(text_left), int(metadata_y)),
            painter.fontMetrics().elidedText(
                artist,
                Qt.TextElideMode.ElideRight,
                int(text_width)
            )
        )

        dot_x = text_left + artist_width + 8

        painter.setPen(QColor(get_theme_color("tons", "hex_93899d", "#93899d")))
        painter.drawText(
            QPoint(int(dot_x), int(metadata_y)),
            "·"
        )

        album_x = dot_x + 13
        album_width = max(
            0,
            text_right - album_x
        )

        painter.setPen(QColor(get_theme_color("tons", "hex_a49bad", "#a49bad")))
        painter.drawText(
            QPoint(int(album_x), int(metadata_y)),
            painter.fontMetrics().elidedText(
                album,
                Qt.TextElideMode.ElideRight,
                int(album_width)
            )
        )

        painter.setPen(QColor(get_theme_color("tons", "hex_93899d", "#93899d")))
        duration_font = QFont()
        duration_font.setPixelSize(12)
        painter.setFont(duration_font)
        painter.drawText(
            QRectF(
                duration_right - duration_width,
                rect.top(),
                duration_width,
                rect.height()
            ),
            Qt.AlignmentFlag.AlignCenter,
            duration
        )

        if self.show_favorite:
            if self.library_all_tracks_style:
                is_favorite = bool(track.get("is_favorite"))
                icon = self.favorite_icons[is_favorite]
                heart_pixmap = icon.pixmap(QSize(20, 20))
                heart_rect = QRectF(
                    favorite_rect.center().x() - 10,
                    favorite_rect.center().y() - 10,
                    20,
                    20
                )
                painter.drawPixmap(
                    heart_rect.toRect(),
                    heart_pixmap
                )
            else:
                painter.setPen(QColor(get_theme_color("tons", "hex_d9b6ff", "#d9b6ff")))
                painter.setFont(QFont("", 19))
                painter.drawText(
                    favorite_rect,
                    Qt.AlignmentFlag.AlignCenter,
                    "♥" if track.get("is_favorite") else "♡"
                )

        # Ícone de reprodução personalizado, com estados independentes.
        play_state = "normal"
        if track_path == self.pressed_play_path:
            play_state = "pressed"
        elif track_path == self.hovered_play_path:
            play_state = "hover"

        if self.icon_manager is not None:
            play_icon, _ = self.icon_manager.resolve(
                "player.play",
                play_state
            )
            if play_icon is not None and not play_icon.isNull():
                play_pixmap = play_icon.pixmap(QSize(30, 30))
                if not play_pixmap.isNull():
                    painter.drawPixmap(
                        play_rect.toRect(),
                        play_pixmap
                    )

        if is_playing_track:
            painter.setPen(QColor(182, 242, 58, 220))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect, 9, 9)

        painter.restore()

    def hit_test(self, track, position, width):
        rect = QRectF(0, 0, width, 66)

        play_left = width - 10 - 30

        if play_left <= position.x() <= play_left + 30:
            return "play"

        if self.show_favorite:
            favorite_left = play_left - 40

            if favorite_left <= position.x() <= favorite_left + 30:
                return "favorite"

        title, artist, album = self.track_text(track)

        text_left = 69
        duration_right = (
            play_left - 40 - 10
            if self.show_favorite
            else play_left - 10
        )
        text_right = duration_right - 48 - 10

        font = QFont()
        font.setPixelSize(11)

        from PySide6.QtGui import QFontMetrics
        metrics = QFontMetrics(font)

        artist_width = metrics.horizontalAdvance(artist)
        artist_end = min(text_left + artist_width, text_right)

        if text_left <= position.x() <= artist_end:
            return "artist"

        album_start = text_left + artist_width + 21

        if album_start <= position.x() <= text_right:
            return "album"

        return "row"


class VirtualTrackListView(QListView):

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.drag_start = None
        self.drag_index = QModelIndex()

        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.viewport().setAttribute(
            Qt.WidgetAttribute.WA_Hover,
            True
        )
        self.viewport().installEventFilter(self)

        self.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setUniformItemSizes(True)
        self.setSpacing(4)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            QListView {
                background: transparent;
                border: none;
                outline: none;
            }
            QListView::item {
                border: none;
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

    def eventFilter(self, watched, event):
        if (
            watched is self.viewport()
            and event.type() == QEvent.Type.Leave
            and self.owner.delegate.hovered_play_path is not None
        ):
            self.owner.delegate.hovered_play_path = None
            self.viewport().update()
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event):
        position = event.position().toPoint()

        if event.button() == Qt.MouseButton.RightButton:
            index = self.indexAt(position)

            if index.isValid():
                selection = self.selectionModel()

                if not selection.isSelected(index):
                    selection.select(
                        index,
                        selection.SelectionFlag.ClearAndSelect
                        | selection.SelectionFlag.Rows
                    )

                selection.setCurrentIndex(
                    index,
                    selection.SelectionFlag.NoUpdate
                )

                self.owner._current_row = index.row()

                tracks = self.owner.selected_tracks()
                global_position = self.viewport().mapToGlobal(position)

                self.owner.context_requested.emit(
                    tracks,
                    global_position
                )

            event.accept()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            index = self.indexAt(position)

            if index.isValid():
                track = index.data(
                    VirtualTrackModel.TrackRole
                )
                action = self.owner.delegate.hit_test(
                    track,
                    position,
                    self.viewport().width()
                )

                metadata_as_selection = (
                    action in ("artist", "album")
                    and not self.owner.metadata_clickable
                )

                if action == "play":
                    self.owner.delegate.pressed_play_path = (
                        self.owner.delegate.track_key(track)
                    )
                    self.viewport().update()

                if action != "row" and not metadata_as_selection:
                    self.drag_start = None
                    self.drag_index = QModelIndex()
                    event.accept()
                    return

            self.drag_start = position
            self.drag_index = index

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        position = event.position().toPoint()
        index_under_mouse = self.indexAt(position)
        hovered_path = None

        if index_under_mouse.isValid():
            hovered_track = index_under_mouse.data(
                VirtualTrackModel.TrackRole
            )
            if (
                hovered_track
                and self.owner.delegate.hit_test(
                    hovered_track,
                    position,
                    self.viewport().width()
                ) == "play"
            ):
                hovered_path = self.owner.delegate.track_key(
                    hovered_track
                )

        if hovered_path != self.owner.delegate.hovered_play_path:
            self.owner.delegate.hovered_play_path = hovered_path
            self.viewport().update()

        if (
            self.drag_start is None
            or not (
                event.buttons()
                & Qt.MouseButton.LeftButton
            )
            or not self.drag_index.isValid()
        ):
            super().mouseMoveEvent(event)
            return

        distance = (
            event.position().toPoint() - self.drag_start
        ).manhattanLength()

        if distance < QApplication.startDragDistance():
            return

        track = self.drag_index.data(
            VirtualTrackModel.TrackRole
        )

        track_id = track.get("id") if track else None

        if track_id is None:
            self.drag_start = None
            return

        mime_data = QMimeData()
        mime_data.setData(
            self.owner.track_mime,
            __import__("json").dumps(
                {"id": int(track_id)}
            ).encode("utf-8")
        )

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.setPixmap(
            self.owner.drag_preview(track)
        )
        drag.setHotSpot(QPoint(20, 22))

        self.drag_start = None
        self.drag_index = QModelIndex()

        drag.exec(Qt.DropAction.CopyAction)

    def mouseReleaseEvent(self, event):
        index = self.indexAt(event.position().toPoint())

        super().mouseReleaseEvent(event)

        if self.owner.delegate.pressed_play_path is not None:
            self.owner.delegate.pressed_play_path = None
            self.viewport().update()

        self.drag_start = None
        self.drag_index = QModelIndex()

        if (
            event.button() != Qt.MouseButton.LeftButton
            or not index.isValid()
        ):
            return

        track = index.data(VirtualTrackModel.TrackRole)

        if not track:
            return

        action = self.owner.delegate.hit_test(
            track,
            event.position().toPoint(),
            self.viewport().width()
        )

        row = index.row()

        if action == "play":
            self.owner.play_requested.emit(track)

        elif action == "favorite":
            # Favoritar encerra qualquer seleção múltipla.
            selection = self.selectionModel()
            if selection is not None:
                selection.clearSelection()

            self.owner.favorite_requested.emit(track)

        elif (
            action in ("artist", "album")
            and self.owner.metadata_clickable
        ):
            self.owner.metadata_requested.emit(
                track,
                action
            )

        else:
            self.owner.selection_changed.emit(
                track,
                row
            )

    def contextMenuEvent(self, event):
        event.accept()


class VirtualTrackList(QWidget):

    selection_changed = Signal(object, int)
    metadata_requested = Signal(object, str)
    play_requested = Signal(object)
    favorite_requested = Signal(object)
    context_requested = Signal(object, object)

    def __init__(
        self,
        track_mime,
        drag_preview,
        parent=None,
        icon_manager=None
    ):
        super().__init__(parent)

        self.tracks = []
        self._current_row = -1
        self.show_favorite = True
        self.metadata_clickable = True
        self.track_mime = track_mime
        self.drag_preview = drag_preview

        self.model = VirtualTrackModel(self)

        self.delegate = VirtualTrackDelegate(
            self,
            icon_manager=icon_manager
        )
        self.view = VirtualTrackListView(self)
        self.view.setModel(self.model)
        self.view.setItemDelegate(self.delegate)

        self.view.doubleClicked.connect(
            self._play_index
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.view)

    def _play_index(self, index):
        track = index.data(VirtualTrackModel.TrackRole)

        if track:
            self.play_requested.emit(track)

    def selected_tracks(self):
        selected_rows = sorted(
            index.row()
            for index in self.view.selectionModel().selectedRows()
        )
        return [
            self.tracks[row]
            for row in selected_rows
            if 0 <= row < len(self.tracks)
        ]

    def set_tracks(self, tracks, show_favorite=True):
        selected_ids = {
            track.get("id")
            for track in self.selected_tracks()
            if track.get("id") is not None
        }

        current_id = None
        if 0 <= self._current_row < len(self.tracks):
            current_id = self.tracks[self._current_row].get("id")

        self.tracks = list(tracks or [])
        self.show_favorite = show_favorite
        self.delegate.show_favorite = show_favorite

        self._current_row = -1
        self.model.set_tracks(self.tracks)

        selection = self.view.selectionModel()
        selection.clearSelection()

        for row, track in enumerate(self.tracks):
            track_id = track.get("id")

            if track_id in selected_ids:
                index = self.model.index(row, 0)
                selection.select(
                    index,
                    selection.SelectionFlag.Select
                    | selection.SelectionFlag.Rows
                )

            if current_id is not None and track_id == current_id:
                self._current_row = row
                selection.setCurrentIndex(
                    self.model.index(row, 0),
                    selection.SelectionFlag.NoUpdate
                )

        self.view.viewport().update()

    def reorder_tracks(self, tracks):
        selected_ids = {
            track.get("id")
            for track in self.selected_tracks()
            if track.get("id") is not None
        }

        current_id = None
        if 0 <= self._current_row < len(self.tracks):
            current_id = self.tracks[self._current_row].get("id")

        ordered_tracks = list(tracks or [])

        self.model.layoutAboutToBeChanged.emit()
        self.tracks = ordered_tracks
        self.model.tracks = ordered_tracks
        self.model.layoutChanged.emit()

        selection = self.view.selectionModel()
        selection.clearSelection()
        self._current_row = -1

        for row, track in enumerate(self.tracks):
            index = self.model.index(row, 0)
            track_id = track.get("id")

            if track_id in selected_ids:
                selection.select(
                    index,
                    selection.SelectionFlag.Select
                    | selection.SelectionFlag.Rows
                )

            if current_id is not None and track_id == current_id:
                self._current_row = row
                selection.setCurrentIndex(
                    index,
                    selection.SelectionFlag.NoUpdate
                )

        self.view.viewport().update()

    def update_track_favorite(self, track_id, is_favorite):
        updated_rows = set()

        for row, track in enumerate(self.tracks):
            if track.get("id") == track_id:
                track["is_favorite"] = int(is_favorite)
                updated_rows.add(row)

        for row, track in enumerate(self.model.tracks):
            if track.get("id") == track_id:
                track["is_favorite"] = int(is_favorite)
                updated_rows.add(row)

        for row in updated_rows:
            index = self.model.index(row, 0)
            self.model.dataChanged.emit(
                index,
                index,
                [VirtualTrackModel.TrackRole]
            )

    def currentRow(self):
        index = self.view.currentIndex()

        if index.isValid():
            return index.row()

        return self._current_row

    def setCurrentRow(self, index):
        if not 0 <= index < len(self.tracks):
            return

        model_index = self.model.index(index, 0)

        self.view.setCurrentIndex(model_index)
        self.view.scrollTo(
            model_index,
            QAbstractItemView.ScrollHint.EnsureVisible
        )

        self._current_row = index

        self.selection_changed.emit(
            self.tracks[index],
            index
        )
