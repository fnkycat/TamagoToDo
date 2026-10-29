"""Кнопка с короткой мягкой реакцией на наведение и нажатие."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QParallelAnimationGroup, QPropertyAnimation, QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QPushButton


class AnimatedButton(QPushButton):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)



        self._dark_theme = False
        self._hover_shadow: QGraphicsDropShadowEffect | None = None
        self._shadow_animation: QParallelAnimationGroup | None = None
        self._blur_animation: QPropertyAnimation | None = None
        self._offset_animation: QPropertyAnimation | None = None

    def _ensure_shadow_animation(self) -> None:
        if self._hover_shadow is not None:
            return
        shadow = QGraphicsDropShadowEffect(self)


        shadow.setBlurRadius(2)
        shadow.setOffset(0, 1)
        shadow.setColor(
            QColor(145, 174, 210, 42) if self._dark_theme else QColor(76, 70, 92, 32)
        )
        self.setGraphicsEffect(shadow)
        group = QParallelAnimationGroup(self)
        blur = QPropertyAnimation(shadow, b"blurRadius", group)
        offset = QPropertyAnimation(shadow, b"offset", group)
        group.addAnimation(blur)
        group.addAnimation(offset)
        blur.setDuration(170)
        offset.setDuration(170)
        self._hover_shadow = shadow
        self._shadow_animation = group
        self._blur_animation = blur
        self._offset_animation = offset

    def set_dark_theme(self, dark: bool) -> None:
        self._dark_theme = dark
        if self._hover_shadow is None:
            return
        tint = QColor(145, 174, 210, 42) if dark else QColor(76, 70, 92, 32)
        self._hover_shadow.setColor(tint)

    def _animate_shadow(
        self, blur: float, offset: float,
        easing: QEasingCurve.Type = QEasingCurve.Type.OutCubic,
    ) -> None:
        self._ensure_shadow_animation()
        assert self._hover_shadow is not None
        assert self._shadow_animation is not None
        assert self._blur_animation is not None
        assert self._offset_animation is not None
        self._shadow_animation.stop()
        self._blur_animation.setStartValue(self._hover_shadow.blurRadius())
        self._blur_animation.setEndValue(blur)
        self._blur_animation.setEasingCurve(easing)
        self._offset_animation.setStartValue(self._hover_shadow.offset())
        self._offset_animation.setEndValue(QPointF(0, offset))
        self._offset_animation.setEasingCurve(easing)
        self._shadow_animation.start()

    def enterEvent(self, event) -> None:
        self._animate_shadow(6, 1.5)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        if self._hover_shadow is not None:
            self._animate_shadow(2, 1, QEasingCurve.Type.InOutSine)
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        self._animate_shadow(8, 1, QEasingCurve.Type.OutCubic)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        super().mouseReleaseEvent(event)
        if self._hover_shadow is None:
            return
        if self.underMouse():
            self._animate_shadow(6, 1.5)
        else:
            self._animate_shadow(2, 1, QEasingCurve.Type.InOutSine)


class SparkleButton(AnimatedButton):
    """Кнопка добавления со звёздочками, закреплёнными у правого края."""

    @staticmethod
    def _sparkle_path(cx: float, cy: float, width: float, height: float) -> QPainterPath:
        path = QPainterPath()
        path.moveTo(cx, cy - height / 2)
        path.cubicTo(cx + width * 0.12, cy - height * 0.14, cx + width * 0.18, cy - height * 0.08, cx + width / 2, cy)
        path.cubicTo(cx + width * 0.18, cy + height * 0.08, cx + width * 0.12, cy + height * 0.14, cx, cy + height / 2)
        path.cubicTo(cx - width * 0.12, cy + height * 0.14, cx - width * 0.18, cy + height * 0.08, cx - width / 2, cy)
        path.cubicTo(cx - width * 0.18, cy - height * 0.08, cx - width * 0.12, cy - height * 0.14, cx, cy - height / 2)
        path.closeSubpath()
        return path

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#ffe69a"))
        painter.drawPath(self._sparkle_path(self.width() - 43, self.height() / 2 - 7, 30, 37))
        painter.drawPath(self._sparkle_path(self.width() - 25, self.height() / 2 + 20, 15, 19))
