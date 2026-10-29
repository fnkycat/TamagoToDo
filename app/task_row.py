"""Карточка задачи и встроенный редактор."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .animated_button import AnimatedButton
from .i18n import tr
from .models import MONTHS_SHORT, Task, to_qdatetime
from .typography import StrokeLabel


ASSETS = Path(__file__).resolve().parent.parent / "assets"
TASK_ICONS = {
    "document": ("Документ", "task_document.svg"),
    "shopping": ("Покупки", "task_cart.svg"),
    "phone": ("Звонок", "task_phone.svg"),
    "mail": ("Почта", "task_mail.svg"),
    "idea": ("Идея", "task_idea.svg"),
    "home": ("Дом", "task_home.svg"),
}


class TaskRow(QFrame):
    changed = Signal()
    content_changed = Signal()
    delete_requested = Signal(str)
    focus_requested = Signal(str)
    selection_requested = Signal(str, bool)
    title_preview_changed = Signal(str, str)

    def __init__(self, task: Task, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.task = task
        self.language = "ru"
        self.dark_theme = False
        self.selection_mode = False
        self.setObjectName("taskRow")
        self._compact = False
        self._tiny = False
        self._base_min_height = 126
        self.setMinimumHeight(126)
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setOffset(0, 4)
        self.shadow.setColor(QColor(67, 54, 79, 28))
        self.setGraphicsEffect(self.shadow)

        self.card_layout = QVBoxLayout(self)
        self.card_layout.setContentsMargins(24, 18, 20, 17)
        self.card_layout.setSpacing(8)
        self._build_display()
        self._build_editor()
        self.editor_page.hide()
        self.update_display()

    def _build_display(self) -> None:
        """Сохранённая карточка текущего мягкого оформления."""
        self.display_page = QWidget()
        display_layout = QVBoxLayout(self.display_page)
        display_layout.setContentsMargins(0, 0, 0, 0)
        display_layout.setSpacing(10)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(16)
        self.header_layout = header
        self.done_box = QCheckBox()
        self.done_box.setFixedSize(44, 44)
        self.done_box.setToolTip("Отметить задачу выполненной")
        self.done_box.toggled.connect(self._set_completed)
        self.selection_box = QCheckBox()
        self.selection_box.setFixedSize(44, 44)
        self.selection_box.setToolTip("Выбрать задачу")
        self.selection_box.hide()
        self.selection_box.toggled.connect(
            lambda checked: self.selection_requested.emit(self.task.task_id, checked)
        )

        self.display_icon_button = AnimatedButton()
        self.display_icon_button.setObjectName("taskIconButton")
        self.display_icon_button.setFixedSize(38, 38)
        self.display_icon_button.setIconSize(QSize(28, 28))
        self.display_icon_button.setToolTip("Изменить значок задачи")
        self.display_icon_button.clicked.connect(
            lambda: self._show_icon_menu(self.display_icon_button)
        )

        self.title_label = StrokeLabel(stroke_width=0.75)
        self.title_label.setObjectName("taskTitle")
        self.title_label.setWordWrap(True)

        text_column = QWidget(self.display_page)
        text_layout = QVBoxLayout(text_column)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)

        self.deadline_pill = self._make_deadline_pill()
        self.more_button = self._make_more_button()
        text_layout.addWidget(self.title_label)

        self.description_label = QLabel()
        self.description_label.setObjectName("taskDescription")
        self.description_label.setWordWrap(True)
        text_layout.addWidget(self.description_label)

        header.addWidget(self.done_box)
        header.addWidget(self.selection_box)
        header.addWidget(self.display_icon_button)
        header.addWidget(text_column, 1, Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(self.deadline_pill, 0, Qt.AlignmentFlag.AlignRight)
        header.addWidget(self.more_button)
        display_layout.addStretch(1)
        display_layout.addLayout(header)
        display_layout.addStretch(1)
        self.card_layout.addWidget(self.display_page, 1)

    def _make_deadline_pill(self) -> QFrame:
        pill = QFrame()
        pill.setObjectName("deadlinePill")
        pill_layout = QHBoxLayout(pill)
        pill_layout.setContentsMargins(15, 8, 16, 8)
        pill_layout.setSpacing(8)
        icon = QLabel()
        icon.setObjectName("deadlineIcon")
        label = QLabel()
        label.setObjectName("deadlineText")
        label.setWordWrap(True)
        pill_layout.addWidget(icon)
        pill_layout.addWidget(label)
        pill.setMinimumHeight(44)
        pill.setMinimumWidth(172)
        pill._icon_label = icon
        pill._text_label = label
        pill._layout = pill_layout
        return pill

    @staticmethod
    def _make_more_button() -> QPushButton:
        button = AnimatedButton()
        button.setObjectName("moreButton")
        button.setIcon(QIcon(str(ASSETS / "icons" / "more.svg")))
        button.setIconSize(QSize(26, 26))
        button.setFixedSize(42, 42)
        button.setToolTip("Редактировать, изменить статус или удалить задачу")
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return button

    def _build_editor(self) -> None:
        self.editor_page = QWidget()
        editor_layout = QVBoxLayout(self.editor_page)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(8)

        self.title_edit = QLineEdit(self.task.title)
        self.title_edit.setObjectName("taskTitleEdit")
        self.title_edit.setPlaceholderText("Название задачи")
        self.title_edit.setMaxLength(120)
        self.title_edit.textEdited.connect(
            lambda title: self.title_preview_changed.emit(self.task.task_id, title)
        )
        self.title_edit.returnPressed.connect(self.save_edit)

        self.description_edit = QPlainTextEdit(self.task.description)
        self.description_edit.setObjectName("taskDescriptionEdit")
        self.description_edit.setPlaceholderText("Описание (необязательно)")
        self.description_edit.setTabChangesFocus(True)
        self.description_edit.setMaximumHeight(76)

        self.deadline_edit = QDateTimeEdit()
        self.deadline_edit.setObjectName("deadlineEdit")
        self.deadline_edit.setCalendarPopup(True)
        self.deadline_edit.setDisplayFormat("dd.MM.yyyy  HH:mm")
        self.deadline_edit.setDateTime(to_qdatetime(self.task.deadline))
        self.deadline_edit.lineEdit().returnPressed.connect(self.save_edit)

        reminder_row = QHBoxLayout()
        self.reminder_label = QLabel("Напоминание")
        self.reminder_label.setObjectName("reminderLabel")
        self.reminder_combo = QComboBox()
        self.reminder_combo.setObjectName("reminderCombo")
        for label, minutes in (
            ("Без напоминания", None),
            ("В момент дедлайна", 0),
            ("За 15 минут", 15),
            ("За час", 60),
            ("За день", 1440),
        ):
            self.reminder_combo.addItem(label, minutes)
        self.reminder_combo.setCurrentIndex(self.reminder_combo.findData(self.task.reminder_minutes))
        reminder_row.addWidget(self.reminder_label)
        reminder_row.addWidget(self.reminder_combo, 1)

        editor_actions = QHBoxLayout()
        editor_actions.addWidget(self.deadline_edit, 1)
        self.edit_icon_button = AnimatedButton("Значок")
        self.edit_icon_button.setObjectName("secondaryButton")
        self.edit_icon_button.setMinimumWidth(96)
        self.edit_icon_button.setToolTip("Выбрать значок задачи")
        self.edit_icon_button.clicked.connect(
            lambda: self._show_icon_menu(self.edit_icon_button, draft=True)
        )
        editor_actions.addWidget(self.edit_icon_button)
        editor_actions.addStretch(1)
        self.cancel_edit_button = AnimatedButton("Отмена")
        self.cancel_edit_button.setObjectName("secondaryButton")
        self.cancel_edit_button.setMinimumWidth(86)
        self.cancel_edit_button.clicked.connect(self.cancel_edit)
        self.save_edit_button = AnimatedButton("Сохранить")
        self.save_edit_button.setObjectName("saveEditButton")
        self.save_edit_button.setMinimumWidth(104)
        self.save_edit_button.clicked.connect(self.save_edit)
        editor_actions.addWidget(self.cancel_edit_button)
        editor_actions.addWidget(self.save_edit_button)
        self.editor_actions_layout = editor_actions

        editor_layout.addWidget(self.title_edit)
        editor_layout.addWidget(self.description_edit)
        editor_layout.addLayout(reminder_row)
        editor_layout.addLayout(editor_actions)
        self.card_layout.addWidget(self.editor_page)

        self.icon_chooser = QFrame()
        self.icon_chooser.setObjectName("taskIconChooser")
        icon_layout = QHBoxLayout(self.icon_chooser)
        icon_layout.setContentsMargins(8, 6, 8, 6)
        icon_layout.setSpacing(6)
        self.icon_choice_buttons: dict[str, AnimatedButton] = {}
        for icon_id, (label, filename) in TASK_ICONS.items():
            icon_path = filename.replace(".svg", "_slate.svg") if self.dark_theme else filename
            button = AnimatedButton()
            button.setObjectName("taskIconChoiceButton")
            button.setIcon(QIcon(str(ASSETS / "icons" / icon_path)))
            button.setIconSize(QSize(24, 24))
            button.setFixedSize(38, 38)
            button.setToolTip(label)
            button.clicked.connect(
                lambda checked=False, value=icon_id: self._choose_icon(
                    value, getattr(self, "_icon_chooser_draft", False)
                )
            )
            icon_layout.addWidget(button)
            self.icon_choice_buttons[icon_id] = button
        icon_layout.addStretch(1)
        self.icon_chooser.hide()
        self.card_layout.addWidget(self.icon_chooser)

        self.task_action_panel = QFrame()
        self.task_action_panel.setObjectName("inlineTaskTools")
        actions_layout = QGridLayout(self.task_action_panel)
        actions_layout.setContentsMargins(8, 2, 8, 2)
        actions_layout.setSpacing(6)
        self.action_buttons_layout = actions_layout
        self.action_edit_button = QPushButton("Редактировать", self.task_action_panel)
        self.action_edit_button.setObjectName("taskEditActionButton")
        self.action_status_button = QPushButton(self.task_action_panel)
        self.action_status_button.setObjectName("taskDoneActionButton")
        self.action_focus_button = QPushButton("Фокус", self.task_action_panel)
        self.action_focus_button.setObjectName("taskFocusActionButton")
        self.action_delete_button = QPushButton("Удалить", self.task_action_panel)
        self.action_delete_button.setObjectName("taskDeleteButton")
        self.action_buttons = (
            self.action_edit_button, self.action_status_button,
            self.action_focus_button, self.action_delete_button,
        )
        self._action_columns = 0
        for button in self.action_buttons:
            if button.objectName() == "QPushButton":
                button.setObjectName("taskActionButton")
            button.setMinimumSize(0, 34)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._layout_action_buttons()
        self.action_edit_button.clicked.connect(self._edit_from_inline_tools)
        self.action_status_button.clicked.connect(self._toggle_status_from_inline_tools)
        self.action_focus_button.clicked.connect(self._focus_from_inline_tools)
        self.action_delete_button.clicked.connect(self._delete_from_inline_tools)
        self.task_action_panel.hide()
        self.card_layout.addWidget(self.task_action_panel)

        self.more_button.clicked.connect(lambda: self._show_task_menu(self.more_button))

    def set_compact(self, compact: bool, tiny: bool = False) -> None:
        """Согласованно уменьшить карточку и элементы формы при узком окне."""
        self._compact = compact
        self._tiny = tiny
        if tiny:
            margins, spacing = (12, 10, 12, 10), 6
            checkbox_size, more_size, more_icon = 28, 30, 18
            pill_width, pill_height = 108, 34
            pill_margins, pill_spacing, deadline_icon = (6, 3, 6, 3), 4, 16
            min_height = 88
            date_width, icon_width, cancel_width, save_width = 160, 48, 52, 68
        elif compact:
            margins, spacing = (16, 12, 14, 12), 7
            checkbox_size, more_size, more_icon = 34, 34, 20
            pill_width, pill_height = 128, 38
            pill_margins, pill_spacing, deadline_icon = (8, 4, 8, 4), 5, 18
            min_height = 100
            date_width, icon_width, cancel_width, save_width = 176, 64, 68, 78
        else:
            margins, spacing = (24, 18, 20, 17), 8
            checkbox_size, more_size, more_icon = 44, 42, 26
            pill_width, pill_height = 172, 44
            pill_margins, pill_spacing, deadline_icon = (15, 8, 16, 8), 8, 22
            min_height = 126
            date_width, icon_width, cancel_width, save_width = 0, 96, 86, 104

        self.card_layout.setContentsMargins(*margins)
        self.card_layout.setSpacing(spacing)
        self.setMinimumHeight(min_height)
        self._base_min_height = min_height
        self.header_layout.setSpacing(8 if tiny else (12 if compact else 16))
        for checkbox in (self.done_box, self.selection_box):
            checkbox.setFixedSize(checkbox_size, checkbox_size)
        self.more_button.setFixedSize(more_size, more_size)
        self.more_button.setIconSize(QSize(more_icon, more_icon))
        self.display_icon_button.setFixedSize(30 if tiny else (34 if compact else 38),
                                              30 if tiny else (34 if compact else 38))
        self.display_icon_button.setIconSize(
            QSize(22, 22) if tiny else (QSize(24, 24) if compact else QSize(28, 28))
        )
        self.deadline_pill.setMinimumWidth(pill_width)
        self.deadline_pill.setMaximumWidth(230 if not compact else (164 if tiny else 190))
        self.deadline_pill.setMinimumHeight(pill_height)
        self.deadline_pill._layout.setContentsMargins(*pill_margins)
        self.deadline_pill._layout.setSpacing(pill_spacing)
        self.deadline_pill._icon_label.setFixedSize(deadline_icon, deadline_icon)
        self.deadline_edit.setMinimumWidth(date_width)
        self.edit_icon_button.setMinimumWidth(icon_width)
        self.cancel_edit_button.setMinimumWidth(cancel_width)
        self.save_edit_button.setMinimumWidth(save_width)
        self.editor_actions_layout.setSpacing(5 if compact else 8)
        self._update_deadline_pill()
        self._refresh_expanded_geometry()

    def _layout_action_buttons(self) -> bool:
        """Lay out action buttons evenly, wrapping to two rows when the card is narrow."""
        layout = self.action_buttons_layout
        margins = layout.contentsMargins()
        card_margins = self.card_layout.contentsMargins()
        available_width = max(
            0,
            self.width() - card_margins.left() - card_margins.right()
            - margins.left() - margins.right(),
        )
        visible_buttons = [
            button for button in self.action_buttons
            if button is not self.action_focus_button or not self.task.completed
        ]
        columns = 2 if available_width < 560 else max(1, len(visible_buttons))
        if columns == self._action_columns:
            return False
        self._action_columns = columns
        while layout.count():
            layout.takeAt(0)
        for index, button in enumerate(visible_buttons):
            row, column = divmod(index, columns)
            if columns == 2 and len(visible_buttons) % 2 and index == len(visible_buttons) - 1:
                layout.addWidget(button, row, 0, 1, 2)
            else:
                layout.addWidget(button, row, column)
        for column in range(4):
            layout.setColumnStretch(column, 1 if column < columns else 0)
        row_count = (len(visible_buttons) + columns - 1) // columns
        for row in range(2):
            layout.setRowStretch(row, 1 if row < row_count else 0)
        return True

    def _refresh_expanded_geometry(self) -> None:
        extra = 0
        if self.task_action_panel.isVisible():
            self._layout_action_buttons()

            extra = self.task_action_panel.sizeHint().height() + self.card_layout.spacing() + 8
        self.setMinimumHeight(self._base_min_height + extra)
        self.card_layout.invalidate()
        self.card_layout.activate()
        self.updateGeometry()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "task_action_panel") and self.task_action_panel.isVisible() and self._layout_action_buttons():
            self._refresh_expanded_geometry()

    def animate_appearance(self) -> None:
        """Подсветить появление карточки лёгким движением её тени."""
        self._animate_shadow(22.0, 20.0)

    def _animate_completion(self) -> None:
        """Коротко подчеркнуть смену статуса мягкой тенью карточки."""
        self._animate_shadow(22.0, 20.0)

    def _animate_shadow(self, start: float, end: float) -> None:
        previous = getattr(self, "_shadow_animation", None)
        if previous is not None and previous.state() == QPropertyAnimation.State.Running:
            previous.stop()
        current = self.shadow.blurRadius()
        animation = QPropertyAnimation(self.shadow, b"blurRadius", self)
        animation.setDuration(380)
        animation.setStartValue(current)


        animation.setKeyValueAt(0.32, max(start, end) + 2.0)
        animation.setEndValue(end)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._shadow_animation = animation
        animation.start()

    def set_dark_theme(self, dark: bool) -> None:
        self.dark_theme = dark
        for icon_id, button in self.icon_choice_buttons.items():
            button.setIcon(QIcon(str(self._task_icon_path(icon_id))))
        icon_name = "more_slate.svg" if dark else "more.svg"
        self.more_button.setIcon(QIcon(str(ASSETS / "icons" / icon_name)))
        for button in self.findChildren(AnimatedButton):
            button.set_dark_theme(dark)
        self.update_display()

    def set_language(self, language: str) -> None:
        self.language = language if language in {"ru", "en"} else "ru"
        text = lambda value: tr(value, self.language)
        self.done_box.setToolTip(text("Отметить задачу выполненной"))
        self.selection_box.setToolTip(text("Выбрать задачу"))
        self.display_icon_button.setToolTip(text("Изменить значок задачи"))
        self.more_button.setToolTip(text("Редактировать, изменить статус или удалить задачу"))
        self.title_edit.setPlaceholderText(text("Название задачи"))
        self.description_edit.setPlaceholderText(text("Описание (необязательно)"))
        self.reminder_label.setText(text("Напоминание"))
        for index, source in enumerate(("Без напоминания", "В момент дедлайна", "За 15 минут", "За час", "За день")):
            self.reminder_combo.setItemText(index, text(source))
        self.edit_icon_button.setText(text("Значок"))
        self.edit_icon_button.setToolTip(text("Выбрать значок задачи"))
        self.cancel_edit_button.setText(text("Отмена"))
        self.save_edit_button.setText(text("Сохранить"))
        self.action_edit_button.setText(text("Редактировать"))
        self.action_focus_button.setText(text("Фокус"))
        self.action_delete_button.setText(text("Удалить"))
        for icon_id, button in self.icon_choice_buttons.items():
            button.setToolTip(text(TASK_ICONS[icon_id][0]))
        self.action_status_button.setText(text("В активные" if self.task.completed else "Готово"))
        default_titles = {tr("Новая задача", "ru"), tr("Новая задача", "en")}
        if self.is_editing() and self.title_edit.text() in default_titles:
            self.title_edit.setText(text("Новая задача"))
        self.update_display()

    def set_selection_mode(self, enabled: bool) -> None:
        self.selection_mode = enabled
        self.done_box.setVisible(not enabled)
        self.selection_box.setVisible(enabled and not self.editor_page.isVisible())

    def set_selected(self, selected: bool) -> None:
        self.selection_box.blockSignals(True)
        self.selection_box.setChecked(selected)
        self.selection_box.blockSignals(False)
        if bool(self.property("selected")) != selected:
            self.setProperty("selected", selected)
            self.style().unpolish(self)
            self.style().polish(self)

    def _task_icon_path(self, icon_id: str) -> Path:
        filename = TASK_ICONS.get(icon_id, TASK_ICONS["document"])[1]
        if self.dark_theme:
            filename = filename.replace(".svg", "_slate.svg")
        return ASSETS / "icons" / filename

    def update_display(self) -> None:
        title = (
            tr("Новая задача", self.language)
            if self.task.title in {"", tr("Новая задача", "ru"), tr("Новая задача", "en")}
            else self.task.title
        )
        self.title_label.setText(title)
        self.title_label.setProperty("completed", self.task.completed)
        font = self.title_label.font()
        font.setStrikeOut(self.task.completed)
        self.title_label.setFont(font)
        self.title_label.style().unpolish(self.title_label)
        self.title_label.style().polish(self.title_label)
        self.description_label.setText(self.task.description)
        self.description_label.setVisible(bool(self.task.description.strip()))
        self.done_box.blockSignals(True)
        self.done_box.setChecked(self.task.completed)
        self.done_box.blockSignals(False)
        self.set_selected(self.selection_box.isChecked())
        icon = QIcon(str(self._task_icon_path(self.task.icon)))
        self.display_icon_button.setIcon(icon)
        self.edit_icon_button.setIcon(icon)
        self.edit_icon_button.setIconSize(QSize(20, 20))

        self.setProperty("completed", self.task.completed)
        self.style().unpolish(self)
        self.style().polish(self)
        self._update_deadline_pill()

    def _update_deadline_pill(self) -> None:
        now = datetime.now()
        deadline = self.task.deadline
        if deadline < now:
            text = f"{tr('Просрочено', self.language)}\n{self._format_date(deadline)}"
            tone = "overdue"
        elif deadline.date() == now.date():
            text = tr("Сегодня, {time}", self.language).format(time=f"{deadline:%H:%M}")
            tone = "urgent"
        elif deadline.date() == (now + timedelta(days=1)).date():
            text = tr("Завтра, {time}", self.language).format(time=f"{deadline:%H:%M}")
            tone = "soon" if deadline - now <= timedelta(hours=24) else "normal"
        else:
            text = self._format_date(deadline)
            tone = "normal"
        if self.task.completed:
            tone = "completed"

        icon_names = {
            "normal": "calendar_green.svg", "soon": "calendar_amber.svg",
            "urgent": "calendar_red.svg", "overdue": "calendar_red.svg",
            "completed": "calendar_muted.svg",
        }
        pill = self.deadline_pill
        if pill._text_label.text() != text:
            pill._text_label.setText(text)
        word_wrap = tone != "overdue"
        if pill._text_label.wordWrap() != word_wrap:
            pill._text_label.setWordWrap(word_wrap)
        alignment = (
            Qt.AlignmentFlag.AlignCenter if tone == "overdue"
            else Qt.AlignmentFlag.AlignVCenter
        )
        if pill._text_label.alignment() != alignment:
            pill._text_label.setAlignment(alignment)
        minimum_height = 54 if tone == "overdue" else 44
        minimum_width = 198 if tone == "overdue" else 172
        if pill.minimumHeight() != minimum_height:
            pill.setMinimumHeight(minimum_height)
        if pill.minimumWidth() != minimum_width:
            pill.setMinimumWidth(minimum_width)
        icon_name = "calendar_slate.svg" if self.dark_theme else icon_names[tone]
        icon_size = pill._icon_label.width() or (16 if self._tiny else (18 if self._compact else 22))
        icon_key = (icon_name, icon_size)
        if getattr(pill, "_icon_cache_key", None) != icon_key:
            pill._icon_label.setPixmap(
                QIcon(str(ASSETS / "icons" / icon_name)).pixmap(icon_size, icon_size)
            )
            pill._icon_cache_key = icon_key
        if pill.property("tone") != tone:
            pill.setProperty("tone", tone)
            pill.style().unpolish(pill)
            pill.style().polish(pill)
        if pill._text_label.property("tone") != tone:
            pill._text_label.setProperty("tone", tone)
            label_style = pill._text_label.style()
            label_style.unpolish(pill._text_label)
            label_style.polish(pill._text_label)
            pill._text_label.update()
        pill.update()

    def _format_date(self, value: datetime) -> str:
        months_en = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
        month = MONTHS_SHORT[value.month - 1] if self.language == "ru" else months_en[value.month - 1]
        return f"{value.day} {month}, {value:%H:%M}"

    def _show_icon_menu(self, anchor: QPushButton, draft: bool = False) -> None:
        if self.icon_chooser.isVisible() and self._icon_chooser_draft == draft:
            self.icon_chooser.hide()
            return
        self.task_action_panel.hide()
        self._refresh_expanded_geometry()
        self._icon_chooser_draft = draft
        selected_icon = getattr(self, "_edit_icon", self.task.icon) if draft else self.task.icon
        for icon_id, button in self.icon_choice_buttons.items():
            button.setProperty("selected", icon_id == selected_icon)
            button.style().unpolish(button)
            button.style().polish(button)
        self.icon_chooser.show()

    def _choose_icon(self, icon_id: str, draft: bool) -> None:
        self.icon_chooser.hide()
        if draft:
            self._edit_icon = icon_id
            self.edit_icon_button.setIcon(QIcon(str(self._task_icon_path(icon_id))))
            return
        self._set_icon(icon_id)

    def _set_icon(self, icon_id: str) -> None:
        self.icon_chooser.hide()
        self.task.icon = icon_id if icon_id in TASK_ICONS else "document"
        self.update_display()
        self.content_changed.emit()

    def _show_task_menu(self, anchor: QPushButton) -> None:
        if self.task_action_panel.isVisible():
            self.task_action_panel.hide()
            self._refresh_expanded_geometry()
            return
        self.icon_chooser.hide()
        self.action_status_button.setText(
            tr("В активные" if self.task.completed else "Готово", self.language)
        )
        for button in self.action_buttons:
            button.setVisible(button is not self.action_focus_button or not self.task.completed)
        self._action_columns = 0
        self.task_action_panel.show()
        self._refresh_expanded_geometry()

    def _edit_from_inline_tools(self) -> None:
        self.task_action_panel.hide()
        self._refresh_expanded_geometry()
        self.enter_edit_mode()

    def _toggle_status_from_inline_tools(self) -> None:
        self.task_action_panel.hide()
        self._refresh_expanded_geometry()
        self._set_completed(not self.task.completed)

    def _focus_from_inline_tools(self) -> None:
        self.task_action_panel.hide()
        self._refresh_expanded_geometry()
        if not self.task.completed:
            self.focus_requested.emit(self.task.task_id)

    def _delete_from_inline_tools(self) -> None:
        self.task_action_panel.hide()
        self._refresh_expanded_geometry()
        self.delete_requested.emit(self.task.task_id)

    def is_editing(self) -> bool:
        """Проверить, открыта ли форма, даже если сама карточка сейчас скрыта фильтром."""
        return not self.editor_page.isHidden()

    def enter_edit_mode(self) -> None:
        self.task_action_panel.hide()
        self._refresh_expanded_geometry()
        self.icon_chooser.hide()
        self._edit_icon = self.task.icon
        title = self.task.title
        if title in {tr("Новая задача", "ru"), tr("Новая задача", "en")}:
            title = tr("Новая задача", self.language)
        self.title_edit.setText(title)
        self.description_edit.setPlainText(self.task.description)
        self.deadline_edit.setDateTime(to_qdatetime(self.task.deadline))
        self.reminder_combo.setCurrentIndex(self.reminder_combo.findData(self.task.reminder_minutes))
        self.selection_box.hide()
        self.display_page.hide()
        self.editor_page.show()
        QTimer.singleShot(0, self._focus_title_edit)

    def _focus_title_edit(self) -> None:
        if self.editor_page.isVisible():
            self.title_edit.setFocus(Qt.FocusReason.OtherFocusReason)
            self.title_edit.selectAll()

    def save_edit(self) -> None:
        if self.editor_page.isHidden():
            return
        previous_deadline = self.task.deadline
        previous_reminder = self.task.reminder_minutes
        self.task.title = self.title_edit.text().strip() or tr("Новая задача", self.language)
        self.title_preview_changed.emit(self.task.task_id, self.task.title)
        self.task.description = self.description_edit.toPlainText().strip()
        self.task.deadline = self.deadline_edit.dateTime().toPython()
        self.task.icon = getattr(self, "_edit_icon", self.task.icon)
        self.task.reminder_minutes = self.reminder_combo.currentData()
        if self.task.deadline != previous_deadline or self.task.reminder_minutes != previous_reminder:
            self.task.reminded_deadline = None
        self.editor_page.hide()
        self.icon_chooser.hide()
        self.update_display()
        self._show_current_page()
        self.animate_appearance()
        self.content_changed.emit()
        self.changed.emit()

    def cancel_edit(self) -> None:
        self._edit_icon = self.task.icon
        self.title_preview_changed.emit(self.task.task_id, self.task.title)
        self.editor_page.hide()
        self.icon_chooser.hide()
        self.update_display()
        self._show_current_page()

    def _show_current_page(self) -> None:
        self.display_page.show()
        if self.selection_mode:
            self.done_box.hide()
            self.selection_box.show()
        else:
            self.done_box.show()
            self.selection_box.hide()

    def _set_completed(self, completed: bool) -> None:
        if completed == self.task.completed:
            return
        self.task.completed = completed
        self.task.completed_at = datetime.now() if completed else None
        self.action_status_button.setText(
            tr("В активные" if completed else "Готово", self.language)
        )
        self.action_focus_button.setVisible(not completed)
        if self.task_action_panel.isVisible():
            self._action_columns = 0
            self._layout_action_buttons()
            self._refresh_expanded_geometry()
        self.update_display()
        self._animate_completion()
        self.changed.emit()
