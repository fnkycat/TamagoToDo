"""Встроенный настраиваемый таймер фокуса с коротким перерывом."""

from __future__ import annotations

from math import ceil
from time import monotonic

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .i18n import tr


class FocusTimerPanel(QFrame):
    """Встроенная настройка и ход фокус-сессии в панели питомца."""

    closed = Signal()
    phase_finished = Signal(str)
    session_requested = Signal(int, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("focusTimerPanel")
        self._phase = "focus"
        self._phase_duration = 0
        self._remaining = 0
        self._deadline = 0.0
        self._break_minutes = 5
        self._paused = False
        self._last_displayed_second: int | None = None
        self._task_title = ""
        self.language = "ru"
        self._session_complete = False

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(24, 24, 24, 24)
        outer_layout.setSpacing(0)
        self.pages = QStackedWidget()
        outer_layout.addWidget(self.pages)

        self.setup_page = self._build_setup_page()
        self.timer_page = self._build_timer_page()
        self.pages.addWidget(self.setup_page)
        self.pages.addWidget(self.timer_page)
        self.pages.setCurrentWidget(self.setup_page)

        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._update_countdown)

    def _build_setup_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(16)

        self.setup_eyebrow = QLabel("Настройка фокуса")
        self.setup_eyebrow.setObjectName("focusEyebrow")
        self.setup_eyebrow.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.setup_eyebrow)

        self.setup_task_title = QLabel()
        self.setup_task_title.setObjectName("focusTaskTitle")
        self.setup_task_title.setWordWrap(True)
        self.setup_task_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.setup_task_title)

        self.setup_hint = QLabel("Выбери время для работы над задачей и отдыха.")
        self.setup_hint.setObjectName("focusHint")
        self.setup_hint.setWordWrap(True)
        self.setup_hint.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.setup_hint)

        form = QFormLayout()
        form.setContentsMargins(0, 8, 0, 8)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(12)
        self.focus_spin = QSpinBox()
        self.focus_spin.setObjectName("focusDurationSpin")
        self.focus_spin.setRange(1, 180)
        self.focus_spin.setSuffix(" мин")
        self.break_spin = QSpinBox()
        self.break_spin.setObjectName("breakDurationSpin")
        self.break_spin.setRange(1, 60)
        self.break_spin.setSuffix(" мин")
        self.focus_form = form
        form.addRow("Фокус", self.focus_spin)
        form.addRow("Перерыв", self.break_spin)
        layout.addLayout(form)
        layout.addStretch(1)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        self.setup_cancel_button = QPushButton("Отмена")
        self.setup_cancel_button.setObjectName("focusSecondaryButton")
        self.setup_cancel_button.clicked.connect(self.closed.emit)
        self.setup_start_button = QPushButton("Начать")
        self.setup_start_button.setObjectName("focusPrimaryButton")
        self.setup_start_button.setDefault(True)
        self.setup_start_button.clicked.connect(
            lambda: self.session_requested.emit(self.focus_spin.value(), self.break_spin.value())
        )
        actions.addStretch(1)
        actions.addWidget(self.setup_cancel_button)
        actions.addWidget(self.setup_start_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        return page

    def _build_timer_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(16)

        self.eyebrow = QLabel("РЕЖИМ ФОКУСА")
        self.eyebrow.setObjectName("focusEyebrow")
        self.eyebrow.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.eyebrow)

        self.task_title = QLabel()
        self.task_title.setObjectName("focusTaskTitle")
        self.task_title.setWordWrap(True)
        self.task_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.task_title)

        layout.addStretch(1)
        self.time_label = QLabel("25:00")
        self.time_label.setObjectName("focusTime")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.time_label)

        self.progress = QFrame()
        self.progress.setObjectName("focusProgressTrack")
        self.progress_fill = QFrame(self.progress)
        self.progress_fill.setObjectName("focusProgressFill")
        self.progress_fill.setGeometry(0, 0, 0, 10)
        self.progress.setFixedHeight(10)
        layout.addWidget(self.progress)

        self.phase_hint = QLabel("Питомец рядом — можно спокойно заниматься делом.")
        self.phase_hint.setObjectName("focusHint")
        self.phase_hint.setWordWrap(True)
        self.phase_hint.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.phase_hint)
        layout.addStretch(2)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        self.pause_button = QPushButton("Пауза")
        self.pause_button.setObjectName("focusPrimaryButton")
        self.pause_button.clicked.connect(self.toggle_pause)
        self.break_button = QPushButton("Начать перерыв")
        self.break_button.setObjectName("focusPrimaryButton")
        self.break_button.clicked.connect(self.start_break)
        self.break_button.hide()
        self.finish_button = QPushButton("Завершить")
        self.finish_button.setObjectName("focusSecondaryButton")
        self.finish_button.clicked.connect(self.close_session)
        actions.addStretch(1)
        actions.addWidget(self.pause_button)
        actions.addWidget(self.break_button)
        actions.addWidget(self.finish_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        return page

    def prepare_session(self, title: str, focus_minutes: int, break_minutes: int) -> None:
        """Показать выбор длительности внутри панели приложения."""
        self._timer.stop()
        self.set_task_title(title)
        self.focus_spin.setValue(focus_minutes)
        self.break_spin.setValue(break_minutes)
        self.pages.setCurrentWidget(self.setup_page)

    def set_task_title(self, title: str) -> None:
        display_title = title.strip() or tr("Новая задача", self.language)
        self._task_title = display_title
        self.setup_task_title.setText(display_title)
        self.task_title.setText(display_title)

    def current_task_title(self) -> str:
        return self._task_title

    def start_session(self, title: str, focus_minutes: int, break_minutes: int) -> None:
        self._break_minutes = break_minutes
        self.set_task_title(title)
        self.pages.setCurrentWidget(self.timer_page)
        self._start_phase("focus", focus_minutes * 60)

    def _start_phase(self, phase: str, seconds: int) -> None:
        self._timer.stop()
        self._phase = phase
        self._phase_duration = seconds
        self._remaining = seconds
        self._paused = False
        self._session_complete = False
        self._last_displayed_second = None
        self._deadline = monotonic() + seconds
        self.eyebrow.setText(tr("ФОКУС" if phase == "focus" else "ПЕРЕРЫВ", self.language))
        self.phase_hint.setText(tr(
            "Питомец рядом — можно спокойно заниматься делом."
            if phase == "focus" else "Хорошая работа. Отдохни немного и возвращайся, когда будешь готова.",
            self.language,
        ))
        self.pause_button.setText(tr("Пауза", self.language))
        self.pause_button.show()
        self.break_button.hide()
        self.finish_button.setText(tr("Завершить", self.language))
        self._show_remaining(seconds)
        self._timer.start()

    def toggle_pause(self) -> None:
        if self._paused:
            self._deadline = monotonic() + self._remaining
            self._paused = False
            self.pause_button.setText(tr("Пауза", self.language))
            self._timer.start()
            return
        self._remaining = max(0, ceil(self._deadline - monotonic()))
        self._paused = True
        self._timer.stop()
        self.pause_button.setText(tr("Продолжить", self.language))
        self._show_remaining(self._remaining)

    def start_break(self) -> None:
        self._start_phase("break", self._break_minutes * 60)

    def _update_countdown(self) -> None:
        remaining = max(0, ceil(self._deadline - monotonic()))
        self._remaining = remaining
        self._show_remaining(remaining)
        if remaining:
            return
        self._timer.stop()
        self._session_complete = True
        self.pause_button.hide()
        if self._phase == "focus":
            self.eyebrow.setText(tr("ФОКУС ЗАВЕРШЁН", self.language))
            self.phase_hint.setText(tr("Отличная работа! Можно сделать небольшой перерыв.", self.language))
            self.break_button.show()
            self.finish_button.setText(tr("К задачам", self.language))
            self.phase_finished.emit("focus")
        else:
            self.eyebrow.setText(tr("ПЕРЕРЫВ ЗАВЕРШЁН", self.language))
            self.phase_hint.setText(tr("Перерыв окончен. Возвращайся к задаче, когда будешь готова.", self.language))
            self.break_button.hide()
            self.finish_button.setText(tr("К задачам", self.language))
            self.phase_finished.emit("break")

    def _show_remaining(self, seconds: int) -> None:
        if seconds != self._last_displayed_second:
            minutes, remainder = divmod(seconds, 60)
            self.time_label.setText(f"{minutes:02d}:{remainder:02d}")
            self._last_displayed_second = seconds
        elapsed = max(0, self._phase_duration - (self._deadline - monotonic())) if not self._paused else self._phase_duration - seconds
        fraction = min(1.0, max(0.0, elapsed / max(1, self._phase_duration)))
        self.progress_fill.setGeometry(
            0, 0, int(self.progress.width() * fraction), self.progress.height()
        )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._show_remaining(self._remaining)

    def close_session(self) -> None:
        self._timer.stop()
        self.closed.emit()

    def stop(self) -> None:
        self._timer.stop()

    def set_language(self, language: str) -> None:
        self.language = language if language in {"ru", "en"} else "ru"
        text = lambda value: tr(value, self.language)
        self.setup_eyebrow.setText(text("Настройка фокуса"))
        self.setup_hint.setText(text("Выбери время для работы над задачей и отдыха."))
        self.focus_form.labelForField(self.focus_spin).setText(text("Фокус"))
        self.focus_form.labelForField(self.break_spin).setText(text("Перерыв"))
        self.focus_spin.setSuffix(text(" мин"))
        self.break_spin.setSuffix(text(" мин"))
        self.setup_cancel_button.setText(text("Отмена"))
        self.setup_start_button.setText(text("Начать"))
        self.set_task_title(self._task_title)
        if self._session_complete:
            complete_key = "ФОКУС ЗАВЕРШЁН" if self._phase == "focus" else "ПЕРЕРЫВ ЗАВЕРШЁН"
            hint_key = "Отличная работа! Можно сделать небольшой перерыв." if self._phase == "focus" else "Перерыв окончен. Возвращайся к задаче, когда будешь готова."
            self.eyebrow.setText(text(complete_key))
            self.phase_hint.setText(text(hint_key))
            self.pause_button.hide()
            self.break_button.setVisible(self._phase == "focus")
            self.finish_button.setText(text("К задачам"))
        elif self._phase_duration:
            self.eyebrow.setText(text("ФОКУС" if self._phase == "focus" else "ПЕРЕРЫВ"))
            self.phase_hint.setText(text(
                "Питомец рядом — можно спокойно заниматься делом."
                if self._phase == "focus" else "Хорошая работа. Отдохни немного и возвращайся, когда будешь готова."
            ))
            self.pause_button.setText(text("Продолжить" if self._paused else "Пауза"))
            self.pause_button.show()
            self.break_button.hide()
            self.finish_button.setText(text("Завершить"))
