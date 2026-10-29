"""Компактная шапка окна и ручки изменения его размера."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QPushButton, QWidget

from .i18n import tr
from .typography import StrokeLabel

ASSETS = Path(__file__).resolve().parent.parent / "assets"


class TitleBar(QWidget):
    def __init__(self, window: QMainWindow) -> None:
        super().__init__(window)
        self.window = window
        self.setObjectName("titleBar")
        self.setFixedHeight(72)
        self._drag_position = None
        self._dark = False
        self._language = "ru"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 7, 16, 7)
        layout.setSpacing(14)

        self.app_icon = QLabel()
        self.app_icon.setObjectName("appIcon")
        self.app_icon.setPixmap(QIcon(str(ASSETS / "app_icon.png")).pixmap(52, 52))
        layout.addWidget(self.app_icon)

        self.title = StrokeLabel("TamagoToDo", stroke_width=0.7)
        self.title.setObjectName("appTitle")
        layout.addWidget(self.title)
        self.language_button = QPushButton()
        self.language_button.setObjectName("languageButton")
        self.language_button.setIconSize(QSize(28, 28))
        self.language_button.setFixedSize(42, 42)
        self.language_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.language_button.setAutoDefault(False)
        self.language_button.setDefault(False)
        layout.addWidget(self.language_button)
        layout.addStretch(1)

        self.minimize_button = self._window_button("minimize.svg", "Свернуть")
        self.minimize_button.clicked.connect(window.showMinimized)
        self.maximize_button = self._window_button("maximize.svg", "Развернуть")
        self.maximize_button.clicked.connect(self.toggle_maximized)
        self.close_button = self._window_button("close.svg", "Закрыть")
        self.close_button.setObjectName("closeWindowButton")
        self.close_button.clicked.connect(window.close)
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(self.close_button)

    @staticmethod
    def _window_button(icon_name: str, tooltip: str) -> QPushButton:
        button = QPushButton()
        button.setObjectName("windowButton")
        button.setIcon(QIcon(str(ASSETS / "icons" / icon_name)))
        button.setIconSize(QSize(23, 23))
        button.setFixedSize(42, 42)
        button.setToolTip(tooltip)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setAutoDefault(False)
        button.setDefault(False)
        return button

    def toggle_maximized(self) -> None:
        if self.window.isMaximized():
            self.window.showNormal()
        else:
            self.window.showMaximized()
        self.refresh_window_icons()

    def set_dark(self, dark: bool) -> None:
        self._dark = dark
        self.refresh_window_icons()

    def set_language(self, language: str) -> None:
        self._language = language
        suffix = "_slate" if self._dark else ""
        self.language_button.setIcon(
            QIcon(str(ASSETS / "icons" / f"language{suffix}.svg"))
        )
        tooltip = tr(
            "Сменить язык на английский" if language == "ru" else "Сменить язык на русский",
            language,
        )
        self.language_button.setToolTip(tooltip)
        self.language_button.setAccessibleName(tooltip)
        self.minimize_button.setToolTip(tr("Свернуть", language))
        self.close_button.setToolTip(tr("Закрыть", language))
        self.refresh_window_icons()

    def refresh_window_icons(self) -> None:
        suffix = "_slate" if self._dark else ""
        self.language_button.setIcon(
            QIcon(str(ASSETS / "icons" / f"language{suffix}.svg"))
        )
        self.minimize_button.setIcon(QIcon(str(ASSETS / "icons" / f"minimize{suffix}.svg")))
        self.close_button.setIcon(QIcon(str(ASSETS / "icons" / f"close{suffix}.svg")))
        if self.window.isMaximized():
            self.maximize_button.setIcon(QIcon(str(ASSETS / "icons" / f"restore{suffix}.svg")))
            self.maximize_button.setToolTip(tr("Восстановить размер", self._language))
        else:
            self.maximize_button.setIcon(QIcon(str(ASSETS / "icons" / f"maximize{suffix}.svg")))
            self.maximize_button.setToolTip(tr("Развернуть", self._language))

    def set_compact(self, compact: bool, tiny: bool = False) -> None:
        """Уменьшить шапку и системные кнопки вместе с окном."""
        height = 48 if tiny else (56 if compact else 72)
        icon_size = 32 if tiny else (38 if compact else 52)
        button_size = 30 if tiny else (34 if compact else 42)
        button_icon = 16 if tiny else (18 if compact else 23)
        self.setFixedHeight(height)
        self.layout().setContentsMargins(12 if compact else 20, 4, 10 if compact else 16, 4)
        self.layout().setSpacing(8 if compact else 14)
        self.app_icon.setFixedSize(icon_size, icon_size)
        self.app_icon.setPixmap(QIcon(str(ASSETS / "app_icon.png")).pixmap(icon_size, icon_size))
        for button in (self.minimize_button, self.maximize_button, self.close_button):
            button.setFixedSize(button_size, button_size)
            button.setIconSize(QSize(button_icon, button_icon))
        self.language_button.setFixedSize(28 if tiny else (30 if compact else 34),
                                          28 if tiny else (30 if compact else 34))
        self.language_button.setIconSize(QSize(18 if tiny else (19 if compact else 22),
                                               18 if tiny else (19 if compact else 22)))

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.window.windowHandle()
            if handle is not None and handle.startSystemMove():
                event.accept()
                return
            self._drag_position = event.globalPosition().toPoint() - self.window.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_position is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.window.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_position = None
        self._dark = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximized()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class ResizeHandle(QWidget):
    """Невидимая ручка по краям frameless окна с нативным resize в Windows."""

    def __init__(self, window: QMainWindow, edges: Qt.Edges, cursor: Qt.CursorShape) -> None:
        super().__init__(window)
        self.window = window
        self.edges = edges
        self.setCursor(cursor)
        self.setStyleSheet("background: transparent;")
        self._fallback = False
        self._origin = None
        self._initial_geometry = None

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        handle = self.window.windowHandle()
        if handle is not None and handle.startSystemResize(self.edges):
            event.accept()
            return
        self._fallback = True
        self._origin = event.globalPosition().toPoint()
        self._initial_geometry = self.window.geometry()
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        if not self._fallback or self._origin is None or self._initial_geometry is None:
            return super().mouseMoveEvent(event)
        delta = event.globalPosition().toPoint() - self._origin
        rect = self._initial_geometry
        left, top, right, bottom = rect.left(), rect.top(), rect.right(), rect.bottom()
        if self.edges & Qt.Edge.LeftEdge:
            left += delta.x()
        if self.edges & Qt.Edge.RightEdge:
            right += delta.x()
        if self.edges & Qt.Edge.TopEdge:
            top += delta.y()
        if self.edges & Qt.Edge.BottomEdge:
            bottom += delta.y()
        min_width, min_height = self.window.minimumWidth(), self.window.minimumHeight()
        if right - left + 1 < min_width:
            left = right - min_width + 1 if self.edges & Qt.Edge.LeftEdge else left
            right = left + min_width - 1 if self.edges & Qt.Edge.RightEdge else right
        if bottom - top + 1 < min_height:
            top = bottom - min_height + 1 if self.edges & Qt.Edge.TopEdge else top
            bottom = top + min_height - 1 if self.edges & Qt.Edge.BottomEdge else bottom
        self.window.setGeometry(left, top, right - left + 1, bottom - top + 1)
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        self._fallback = False
        self._origin = None
        self._initial_geometry = None
        super().mouseReleaseEvent(event)

