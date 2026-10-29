"""Сцена питомца и компактный индикатор настроения."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRect, QSize, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QCursor, QPainter, QPainterPath, QPen, QPixmap, QIcon, QRegion, QScreen
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtWidgets import (
    QApplication, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QVBoxLayout, QWidget,
    QSizePolicy,
)

from .models import Mood
from .i18n import tr


ASSETS = Path(__file__).resolve().parent.parent / "assets"


class PetScene(QWidget):
    """Иллюстрация питомца и карточка его настроения."""

    overlay_drag_started = Signal()
    overlay_drag_moved = Signal()
    overlay_drag_finished = Signal()

    def __init__(self, parent: QWidget | None = None, overlay_mode: bool = False) -> None:
        super().__init__(parent)
        self.setObjectName("petScene")
        self.overlay_mode = overlay_mode
        if overlay_mode:
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
            self.setAutoFillBackground(False)
        self._image = QPixmap(str(ASSETS / "pet_room_empty.png"))
        self._fitted_image = QPixmap()
        self._fitted_image_size = QSize()
        self.background = "room"
        self._dark = False
        self._compact = False
        self._tiny = False
        layout = QVBoxLayout(self)
        if overlay_mode:
            layout.setContentsMargins(0, 0, 0, 0)
        else:
            layout.setContentsMargins(40, 22, 40, 20)
        layout.setSpacing(0)
        self._scene_layout = layout

        self.model_view = QQuickWidget(self)
        self.model_view.setObjectName("petModelView")
        self.model_view.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        self.model_view.setClearColor(QColor(0, 0, 0, 0))
        self.model_view.setAutoFillBackground(False)
        self.model_view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        if overlay_mode:
            self.model_view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.model_view.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop)
        self.model_view.rootContext().setContextProperty("tamagoOverlayMode", overlay_mode)
        self.model_view.rootContext().setContextProperty(
            "tamagoBackgroundSource",
            QUrl.fromLocalFile(str(ASSETS / "pet_room_empty.png")),
        )
        self.model_view.rootContext().setContextProperty("tamagoBackgroundColor", "#fffaf4")
        self.model_view.rootContext().setContextProperty(
            "tamagoModelSource",
            QUrl.fromLocalFile(str(ASSETS / "pet_3d" / "tamago_pet_fused.glb")),
        )
        self.model_view.rootContext().setContextProperty(
            "tamagoAngryModelSource",
            QUrl.fromLocalFile(str(ASSETS / "pet_3d" / "tamago_pet_grumpy_unified.glb")),
        )
        self.model_view.rootContext().setContextProperty(
            "tamagoTenseModelSource",
            QUrl.fromLocalFile(str(ASSETS / "pet_3d" / "tamago_pet_tense.glb")),
        )
        self.model_view.rootContext().setContextProperty("tamagoPetMood", "positive")
        self.model_view.setSource(QUrl.fromLocalFile(str(ASSETS / "pet_3d" / "view.qml")))
        if overlay_mode and self.model_view.rootObject() is not None:
            root = self.model_view.rootObject()
            root.overlayDragStarted.connect(self.overlay_drag_started.emit)
            root.overlayDragMoved.connect(self.overlay_drag_moved.emit)
            root.overlayDragFinished.connect(self.overlay_drag_finished.emit)

        self.mood_card = QFrame()
        self.mood_card.setObjectName("moodCard")
        self.mood_card.setMinimumHeight(130)
        self.mood_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.mood_shadow = QGraphicsDropShadowEffect(self.mood_card)
        self.mood_shadow.setBlurRadius(0)
        self.mood_shadow.setOffset(0, 2)
        initial_shadow_color = QColor("#70cc8c")
        initial_shadow_color.setAlpha(70)
        self.mood_shadow.setColor(initial_shadow_color)
        self.mood_card.setGraphicsEffect(self.mood_shadow)
        self._mood_animation: QPropertyAnimation | None = None
        self._current_mood = Mood.POSITIVE
        self._mood_style_key: tuple[str, ...] | None = None
        self.language = "ru"
        self._mood_colors: dict[str, str] | None = None
        card_layout = QHBoxLayout(self.mood_card)
        self._card_layout = card_layout
        card_layout.setContentsMargins(20, 14, 18, 14)
        card_layout.setSpacing(18)
        self.avatar = MoodFace()
        card_layout.addWidget(self.avatar, 0, Qt.AlignmentFlag.AlignVCenter)

        mood_text = QVBoxLayout()
        self._mood_text_layout = mood_text
        mood_text.setSpacing(8)
        top_row = QHBoxLayout()
        self._top_row = top_row
        top_row.setSpacing(8)
        self.title = QLabel()
        self.title.setObjectName("moodTitle")
        self.title.setWordWrap(True)
        top_row.addWidget(self.title, 1)
        self.heart = QLabel()
        self.heart.setObjectName("moodHeart")
        self.heart.setPixmap(QIcon(str(ASSETS / "icons" / "heart.svg")).pixmap(42, 42))
        top_row.addWidget(self.heart)
        mood_text.addLayout(top_row)

        self.segment_row = QHBoxLayout()
        self.segment_row.setSpacing(6)
        self.segments: list[QFrame] = []
        for _ in range(6):
            segment = QFrame()
            segment.setObjectName("moodSegment")
            segment.setFixedHeight(15)
            self.segments.append(segment)
            self.segment_row.addWidget(segment, 1)
        mood_text.addLayout(self.segment_row)

        card_layout.addLayout(mood_text, 1)


        if overlay_mode:
            self.mood_card.hide()
        else:
            layout.addWidget(self.mood_card, 0, Qt.AlignmentFlag.AlignTop)
        self.model_view.setGeometry(self.rect())
        self.model_view.lower()
        if not overlay_mode:
            self.mood_card.raise_()

    def resizeEvent(self, event) -> None:
        if self.overlay_mode:
            self._scene_layout.setContentsMargins(0, 0, 0, 0)
        elif self._tiny:
            self._scene_layout.setContentsMargins(8, 8, 8, 8)
        elif self._compact:
            self._scene_layout.setContentsMargins(12, 10, 12, 10)
        else:
            width = self.width()
            left = min(70, max(32, int(width * 0.15)))
            right = min(40, max(28, int(width * 0.09)))
            self._scene_layout.setContentsMargins(left, 22, right, 20)
        super().resizeEvent(event)
        self.model_view.setGeometry(self.rect())
        if self.overlay_mode:
            self.model_view.clearMask()
        else:
            clip = QPainterPath()
            clip.addRoundedRect(self.model_view.rect(), 24, 24)
            self.model_view.setMask(QRegion(clip.toFillPolygon().toPolygon()))
            self.mood_card.raise_()

    def set_compact(self, compact: bool, tiny: bool = False) -> None:
        """Подогнать карточку настроения под свободное место справа."""
        self._compact = compact
        self._tiny = tiny
        if tiny:
            face, heart, segment = 38, 24, 7
            card_margins, card_spacing = (8, 7, 8, 7), 8
            title_spacing, text_spacing = 5, 5
            card_height = 78
        elif compact:
            face, heart, segment = 48, 28, 9
            card_margins, card_spacing = (10, 9, 10, 9), 10
            title_spacing, text_spacing = 6, 6
            card_height = 92
        else:
            face, heart, segment = 72, 42, 15
            card_margins, card_spacing = (20, 14, 18, 14), 18
            title_spacing, text_spacing = 8, 8
            card_height = 130
        self.avatar.setFixedSize(face, face)
        self.heart.setFixedSize(heart, heart)
        heart_icon = "heart_slate.svg" if self._dark else "heart.svg"
        self.heart.setPixmap(QIcon(str(ASSETS / "icons" / heart_icon)).pixmap(heart, heart))
        for item in self.segments:
            item.setFixedHeight(segment)
        self._card_layout.setContentsMargins(*card_margins)
        self._card_layout.setSpacing(card_spacing)
        self._mood_text_layout.setSpacing(text_spacing)
        self._top_row.setSpacing(title_spacing)
        self.mood_card.setMinimumHeight(card_height)
        if tiny:
            self._scene_layout.setContentsMargins(8, 8, 8, 8)
        elif compact:
            self._scene_layout.setContentsMargins(12, 10, 12, 10)
        else:
            self._scene_layout.setContentsMargins(40, 22, 40, 20)

    def set_dark(self, dark: bool) -> None:
        self._dark = dark
        self.model_view.rootContext().setContextProperty(
            "tamagoBackgroundColor", "#1b2342" if dark else "#fffaf4"
        )
        self.avatar.set_dark(dark)
        heart_icon = "heart_slate.svg" if dark else "heart.svg"
        heart_size = 24 if self._tiny else (28 if self._compact else 42)
        self.heart.setPixmap(QIcon(str(ASSETS / "icons" / heart_icon)).pixmap(heart_size, heart_size))
        self.update()

    def set_background(self, background: str) -> None:
        self.background = background if background in {"room", "solid"} else "room"
        image_url = (
            QUrl.fromLocalFile(str(ASSETS / "pet_room_empty.png"))
            if self.background == "room" else QUrl()
        )
        self.model_view.rootContext().setContextProperty("tamagoBackgroundSource", image_url)
        self.model_view.rootContext().setContextProperty(
            "tamagoBackgroundColor", "#1b2342" if self._dark else "#fffaf4"
        )
        self.update()

    def paintEvent(self, event) -> None:
        if self.overlay_mode:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        rect = self.rect()
        clip = QPainterPath()
        clip.addRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), 24, 24)
        painter.setClipPath(clip)
        solid_color = QColor("#1b2342" if self._dark else "#fffaf4")
        painter.fillRect(rect, solid_color)
        if self.background == "room" and not self._image.isNull():
            if self._fitted_image_size != rect.size():
                self._fitted_image = self._image.scaled(
                    rect.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._fitted_image_size = rect.size()
            x = (rect.width() - self._fitted_image.width()) // 2
            y = (rect.height() - self._fitted_image.height()) // 2
            painter.drawPixmap(x, y, self._fitted_image)
        if self._dark:

            painter.fillRect(rect, QColor(24, 30, 62, 42))
        painter.end()

    def set_mood_card_visible(self, visible: bool) -> None:
        current = getattr(self, "_visibility_animation", None)
        if current is not None:
            current.stop()
        if visible:
            start_height = 0 if self.mood_card.isHidden() else self.mood_card.height()
            self.mood_card.show()
            self.mood_card.setMaximumHeight(max(1, start_height))
            end_height = max(1, self.mood_card.sizeHint().height())
        else:
            if self.mood_card.isHidden():
                return
            start_height = self.mood_card.height()
            self.mood_card.setMaximumHeight(16_777_215)
            self.mood_card.setMaximumHeight(max(1, start_height))
            end_height = 0
        animation = QPropertyAnimation(self.mood_card, b"maximumHeight", self)
        animation.setDuration(280)
        animation.setStartValue(start_height)
        animation.setEndValue(end_height)
        animation.setEasingCurve(
            QEasingCurve.Type.OutCubic if visible else QEasingCurve.Type.InCubic
        )
        if not visible:
            animation.finished.connect(self.mood_card.hide)
        else:
            animation.finished.connect(lambda: self.mood_card.setMaximumHeight(16_777_215))
        self._visibility_animation = animation
        animation.start()

    def _pulse_mood_card(self, color: str) -> None:
        if self._mood_animation is not None:
            self._mood_animation.stop()
        shadow_color = QColor(color)
        shadow_color.setAlpha(42)
        self.mood_shadow.setColor(shadow_color)
        animation = QPropertyAnimation(self.mood_shadow, b"blurRadius", self)
        animation.setDuration(560)
        animation.setStartValue(self.mood_shadow.blurRadius())
        animation.setKeyValueAt(0.42, 9.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._mood_animation = animation
        animation.start()

    def set_mood(self, mood: Mood, colors: dict[str, str]) -> None:
        mood_changed = mood != self._current_mood
        self._current_mood = mood
        self.model_view.rootContext().setContextProperty("tamagoPetMood", mood.name.lower())
        self._mood_colors = colors
        mood_title = tr(mood.title, self.language)
        if self.title.text() != mood_title:
            self.title.setText(mood_title)
        self.avatar.set_mood(mood)
        mood_message = tr(mood.message, self.language)
        if self.mood_card.toolTip() != mood_message:
            self.mood_card.setToolTip(mood_message)
        mood_key = {
            Mood.POSITIVE: "positive", Mood.TENSE: "tense", Mood.ANGRY: "angry",
        }[mood]
        background = colors[f"{mood_key}_bg"]
        foreground = colors[f"{mood_key}_fg"]
        fill = colors[f"{mood_key}_fill"]
        if mood_changed:
            self._pulse_mood_card(fill)
        style_key = (
            mood_key, background, foreground, fill,
            colors[f"{mood_key}_border"], colors["meter_empty"],
        )
        if style_key == self._mood_style_key:
            return
        self._mood_style_key = style_key
        self.mood_card.setStyleSheet(
            f"QFrame#moodCard {{ background: {background}; border: 3px solid {colors[f'{mood_key}_border']}; }}\n"
            f"QLabel#moodTitle {{ color: {foreground}; }}"
        )
        active_segments = {Mood.POSITIVE: 4, Mood.TENSE: 2, Mood.ANGRY: 1}[mood]
        for index, segment in enumerate(self.segments):
            color = fill if index < active_segments else colors["meter_empty"]
            segment.setStyleSheet(f"background: {color}; border-radius: 7px;")

    def set_language(self, language: str) -> None:
        self.language = language if language in {"ru", "en"} else "ru"
        if self._mood_colors is not None:
            self.set_mood(self._current_mood, self._mood_colors)


class PetOverlayWindow(QWidget):
    def __init__(self, screen: QScreen | None = None) -> None:
        flags = (
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        super().__init__(None, flags)
        self.setObjectName("petOverlayWindow")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAutoFillBackground(False)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.resize(280, 310)
        self._target_screen = screen
        self._position_initialized = False
        self._drag_cursor_origin = None
        self._drag_window_origin = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.pet_scene = PetScene(self, overlay_mode=True)
        layout.addWidget(self.pet_scene)
        self.pet_scene.overlay_drag_started.connect(self._start_drag)
        self.pet_scene.overlay_drag_moved.connect(self._continue_drag)
        self.pet_scene.overlay_drag_finished.connect(self._finish_drag)
        self._update_input_shape()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_input_shape()

    def _update_input_shape(self) -> None:
        width = self.width()
        height = self.height()
        shape = QRegion()
        ellipses = (
            (0.12, 0.28, 0.76, 0.62),
            (0.14, 0.02, 0.43, 0.34),
            (0.43, 0.02, 0.43, 0.34),
            (0.29, 0.77, 0.23, 0.18),
            (0.49, 0.77, 0.23, 0.18),
        )
        for x, y, w, h in ellipses:
            rect = QRect(int(x * width), int(y * height), int(w * width), int(h * height))
            shape = shape.united(QRegion(rect, QRegion.RegionType.Ellipse))
        stem = QRect(int(width * 0.44), int(height * 0.22), int(width * 0.12), int(height * 0.23))
        self.setMask(shape.united(QRegion(stem)))

    def show_overlay(self) -> None:
        if not self._position_initialized:
            screen = self._target_screen or QApplication.primaryScreen()
            if screen is not None:
                bounds = screen.availableGeometry()
                self.move(bounds.right() - self.width() - 24, bounds.bottom() - self.height() - 16)
            self._position_initialized = True
        self.show()
        self.raise_()

    def _start_drag(self) -> None:
        self._drag_cursor_origin = QCursor.pos()
        self._drag_window_origin = self.pos()

    def _continue_drag(self) -> None:
        if self._drag_cursor_origin is None or self._drag_window_origin is None:
            return
        cursor = QCursor.pos()
        target = self._drag_window_origin + cursor - self._drag_cursor_origin
        screen = QApplication.screenAt(cursor) or QApplication.primaryScreen()
        if screen is not None:
            bounds = screen.availableGeometry()
            target.setX(max(bounds.left(), min(target.x(), bounds.right() - self.width() + 1)))
            target.setY(max(bounds.top(), min(target.y(), bounds.bottom() - self.height() + 1)))
        self.move(target)

    def _finish_drag(self) -> None:
        self._drag_cursor_origin = None
        self._drag_window_origin = None


class MoodFace(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(72, 72)
        self.mood = Mood.POSITIVE
        self._dark = False

    def set_mood(self, mood: Mood) -> None:
        if mood == self.mood:
            return
        self.mood = mood
        self.update()

    def set_dark(self, dark: bool) -> None:
        if dark == self._dark:
            return
        self._dark = dark
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(self.width() / 76, self.height() / 76)
        if self._dark:
            palettes = {
                Mood.POSITIVE: ("#91b9d2", "#385b76"),
                Mood.TENSE: ("#a6b9dc", "#455c82"),
                Mood.ANGRY: ("#c0acd9", "#5b4d77"),
            }
        else:
            palettes = {
                Mood.POSITIVE: ("#a9dfb1", "#377c59"),
                Mood.TENSE: ("#ffe0a0", "#9a6818"),
                Mood.ANGRY: ("#ffc1b8", "#ab5055"),
            }
        fill, ink = palettes[self.mood]
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(fill))
        painter.drawEllipse(2, 2, 72, 72)
        painter.setPen(QPen(QColor(ink), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawPoint(27, 31)
        painter.drawPoint(49, 31)
        mouth = QPainterPath()
        if self.mood == Mood.POSITIVE:
            mouth.moveTo(25, 43)
            mouth.quadTo(38, 58, 51, 43)
        elif self.mood == Mood.TENSE:
            mouth.moveTo(29, 49)
            mouth.quadTo(38, 44, 47, 49)
        else:
            mouth.moveTo(27, 52)
            mouth.quadTo(38, 39, 49, 52)
        painter.drawPath(mouth)
        painter.end()
