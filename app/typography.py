"""Небольшое управляемое утолщение текста в крупных заголовках."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QFontMetricsF, QPainter, QPainterPath, QPen, QPalette
from PySide6.QtWidgets import QLabel


class StrokeLabel(QLabel):
    """Рисует обычный текст QLabel с тонкой обводкой того же цвета."""

    def __init__(self, text: str = "", parent=None, stroke_width: float = 0.7) -> None:
        super().__init__(text, parent)
        self.stroke_width = stroke_width
        self.setTextFormat(Qt.TextFormat.PlainText)

    def paintEvent(self, event) -> None:
        text = self.text()
        if not text:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setFont(self.font())
        color = self.palette().color(QPalette.ColorRole.WindowText)
        painter.setPen(QPen(
            color,
            self.stroke_width,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        ))
        painter.setBrush(color)

        bounds = QRectF(self.contentsRect())
        metrics = QFontMetricsF(self.font())
        lines = self._wrap_lines(text, metrics, bounds.width()) if self.wordWrap() else text.splitlines()
        if not lines:
            lines = [text]

        line_height = metrics.lineSpacing()
        total_height = line_height * len(lines)
        alignment = self.alignment()
        if alignment & Qt.AlignmentFlag.AlignVCenter:
            first_baseline = bounds.top() + (bounds.height() - total_height) / 2 + metrics.ascent()
        elif alignment & Qt.AlignmentFlag.AlignBottom:
            first_baseline = bounds.bottom() - total_height + metrics.ascent()
        else:
            first_baseline = bounds.top() + metrics.ascent()

        for index, line in enumerate(lines):
            width = metrics.horizontalAdvance(line)
            if alignment & Qt.AlignmentFlag.AlignHCenter:
                x = bounds.left() + (bounds.width() - width) / 2
            elif alignment & Qt.AlignmentFlag.AlignRight:
                x = bounds.right() - width
            else:
                x = bounds.left()
            baseline = first_baseline + index * line_height
            path = QPainterPath()
            path.addText(x, baseline, self.font(), line)
            painter.drawPath(path)

            if self.property("completed") == "true" or self.property("completed") is True:
                strike_y = baseline - metrics.ascent() * 0.34
                painter.drawLine(int(x), int(strike_y), int(x + width), int(strike_y))

        painter.end()

    @staticmethod
    def _wrap_lines(text: str, metrics: QFontMetricsF, width: float) -> list[str]:
        lines: list[str] = []
        for paragraph in text.splitlines() or [text]:
            words = paragraph.split()
            if not words:
                lines.append("")
                continue
            line = ""
            for word in words:
                candidate = f"{line} {word}" if line else word
                if line and metrics.horizontalAdvance(candidate) > width:
                    lines.append(line)
                    line = word
                elif not line and metrics.horizontalAdvance(word) > width:
                    chunk = ""
                    for character in word:
                        candidate_chunk = chunk + character
                        if chunk and metrics.horizontalAdvance(candidate_chunk) > width:
                            lines.append(chunk)
                            chunk = character
                        else:
                            chunk = candidate_chunk
                    line = chunk
                else:
                    line = candidate
            lines.append(line)
        return lines


class ClickableStrokeLabel(StrokeLabel):
    """Надпись имени питомца, которая открывает поле редактирования по клику."""

    clicked = Signal()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)
