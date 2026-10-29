"""Главное окно: экран задач и панель питомца."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QEvent, QSize, Qt, QTimer, QVariantAnimation
from PySide6.QtGui import QAction, QFontDatabase, QFontMetricsF, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QFileDialog,
    QHBoxLayout,
    QApplication,
    QComboBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .animated_button import AnimatedButton, SparkleButton
from .focus_timer import FocusTimerPanel
from .i18n import tr
from .models import Task, evaluate_mood
from .pet_scene import PetOverlayWindow, PetScene
from .storage import TaskStorage, TaskStorageError
from .styles import THEMES, build_stylesheet
from .task_row import TaskRow
from .title_bar import ResizeHandle, TitleBar
from .typography import ClickableStrokeLabel, StrokeLabel


ASSETS = Path(__file__).resolve().parent.parent / "assets"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        QFontDatabase.addApplicationFont(str(ASSETS / "fonts" / "Comfortaa-VariableFont_wght.ttf"))
        self.setObjectName("appWindow")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("TamagoToDo")
        self.setWindowIcon(QIcon(str(ASSETS / "app_icon.png")))
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry() if screen is not None else None
        if available is not None:
            initial_width = int(available.width() * 0.82)
            initial_height = int(available.height() * 0.94)
        else:
            initial_width, initial_height = 1280, 780
        self.resize(initial_width, initial_height)
        self.setMinimumSize(760, 500)
        if available is not None:
            self.move(
                available.x() + (available.width() - initial_width) // 2,
                available.y() + (available.height() - initial_height) // 2,
            )
        self.status_bar = self.statusBar()
        self.status_bar.setSizeGripEnabled(False)
        self.status_bar.setFixedHeight(22)
        self.status_bar.hide()
        self.status_timer = QTimer(self)
        self.status_timer.setSingleShot(True)
        self.status_timer.setInterval(5000)
        self.status_timer.timeout.connect(self._hide_status_bar)
        self.undo_delete_button = AnimatedButton("Отменить")
        self.undo_delete_button.setObjectName("undoDeleteButton")
        self.undo_delete_button.clicked.connect(self.undo_bulk_delete)
        self.undo_delete_button.hide()
        self.status_bar.addPermanentWidget(self.undo_delete_button)

        self.tasks: list[Task] = []
        self.task_rows: dict[str, TaskRow] = {}
        self.language = "ru"
        self.theme = "light"
        self.pet_name = "Тамагочи"
        self.current_filter = "all"
        self.show_mood_status = True
        self.show_pet_panel = True
        self.pet_overlay: PetOverlayWindow | None = None
        self.pet_background = "room"
        self.focus_minutes = 25
        self.break_minutes = 5
        self._focus_task_id: str | None = None
        self.selection_mode = False
        self.selected_task_ids: set[str] = set()
        self._undo_deleted_tasks: list[Task] = []
        self.search_query = ""
        self.storage = TaskStorage()
        self.storage_ready = True
        self._load_tasks()
        self._sort_rows()

        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(500)
        self.save_timer.timeout.connect(self._save_tasks)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(10)
        self.task_panel = self._build_task_panel()
        self.pet_panel = self._build_pet_panel()
        self.task_panel.setMinimumWidth(0)
        self.pet_panel.setMinimumWidth(0)
        self.splitter.addWidget(self.task_panel)
        self.splitter.addWidget(self.pet_panel)
        divider = self.splitter.handle(1)
        divider.setEnabled(False)
        divider.setCursor(Qt.CursorShape.ArrowCursor)
        self.splitter.setStretchFactor(0, 6)
        self.splitter.setStretchFactor(1, 4)
        self.splitter.setSizes([900, 600])
        self._saved_splitter_sizes = self.splitter.sizes()
        self._pet_panel_animation: QVariantAnimation | None = None

        app_frame = QFrame()
        app_frame.setObjectName("appFrame")
        app_layout = QVBoxLayout(app_frame)
        app_layout.setContentsMargins(3, 3, 3, 3)
        app_layout.setSpacing(0)
        self.title_bar = TitleBar(self)
        self.title_bar.language_button.clicked.connect(self.toggle_language)
        app_layout.addWidget(self.title_bar)
        app_layout.addWidget(self.splitter, 1)

        central = QWidget()
        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(4, 4, 4, 4)
        outer_layout.setSpacing(0)
        outer_layout.addWidget(app_frame)
        self.setCentralWidget(central)
        self._create_resize_handles()


        self.finish_selection_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Return), self)
        self.finish_selection_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.finish_selection_shortcut.setEnabled(False)
        self.finish_selection_shortcut.activated.connect(self._finish_selection_from_enter)
        self.finish_selection_enter_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Enter), self)
        self.finish_selection_enter_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.finish_selection_enter_shortcut.setEnabled(False)
        self.finish_selection_enter_shortcut.activated.connect(self._finish_selection_from_enter)
        self.cancel_task_edit_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self.cancel_task_edit_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.cancel_task_edit_shortcut.activated.connect(self._cancel_active_task_edit)

        for task in self.tasks:
            self._create_task_row(task)

        self.mood_timer = QTimer(self)
        self.mood_timer.setInterval(60_000)
        self.mood_timer.timeout.connect(self._update_mood)
        self.mood_timer.start()

        background_index = self.pet_background_combo.findData(self.pet_background)
        self.pet_background_combo.blockSignals(True)
        self.pet_background_combo.setCurrentIndex(background_index)
        self.pet_background_combo.blockSignals(False)
        self.pet_scene.set_background(self.pet_background)
        self._apply_theme()
        self._apply_saved_visibility()
        self._refresh_task_list_state()
        self._setup_reminders()
        self._compact_layout: bool | None = None
        self._tiny_layout = False
        self._update_responsive_layout(force=True)
        self._apply_language()

    def _build_task_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("taskPanel")
        layout = QVBoxLayout(panel)
        self.task_panel_layout = layout
        layout.setContentsMargins(22, 18, 22, 19)
        layout.setSpacing(14)

        header_frame = QFrame()
        header_frame.setObjectName("sectionHeader")
        header = QVBoxLayout(header_frame)
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)
        self.task_header_frame = header_frame
        self.task_header_layout = header
        heading_row = QHBoxLayout()
        heading_row.setContentsMargins(0, 0, 0, 0)
        heading_row.setSpacing(10)
        self.task_heading_row = heading_row
        heading = StrokeLabel("МОИ ЗАДАЧИ", stroke_width=1.0)
        self.task_heading = heading
        heading.setWordWrap(False)
        heading.setObjectName("sectionHeading")
        heading_row.addWidget(heading)

        self.restore_pet_button = AnimatedButton("Показать питомца")
        self.restore_pet_button.setObjectName("restorePetButton")
        self.restore_pet_button.setMinimumHeight(48)
        self.restore_pet_button.setToolTip("Вернуть правую панель")
        self.restore_pet_button.clicked.connect(self.show_pet_panel_again)
        self.restore_pet_button.hide()
        heading_row.addWidget(self.restore_pet_button)
        heading_row.addStretch(1)

        self.filter_bar = QWidget()
        filter_layout = QHBoxLayout(self.filter_bar)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(8)
        filter_layout.addStretch(1)
        self.filter_buttons: dict[str, QPushButton] = {}
        for key, label in (
            ("all", "Все"),
            ("active", "Активные"),
            ("completed", "Выполненные"),
        ):
            button = AnimatedButton(label)
            button.setObjectName("filterButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, value=key: self.set_filter(value))
            self.filter_buttons[key] = button
            filter_layout.addWidget(button)
        self.filter_buttons["all"].setChecked(True)
        heading_row.addWidget(self.filter_bar)
        header.addLayout(heading_row)
        layout.addWidget(header_frame)

        search_row = QHBoxLayout()
        search_row.setSpacing(10)
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchTasksInput")
        self.search_input.setPlaceholderText("Поиск по задачам…")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.set_search_query)
        search_row.addWidget(self.search_input, 1)
        self.selection_mode_button = AnimatedButton("Выбрать")
        self.selection_mode_button.setObjectName("selectionModeButton")
        self.selection_mode_button.setCheckable(True)
        self.selection_mode_button.setMinimumHeight(44)
        self.selection_mode_button.clicked.connect(self.toggle_selection_mode)
        search_row.addWidget(self.selection_mode_button)
        layout.addLayout(search_row)

        self.task_scroll = QScrollArea()
        self.task_scroll.setObjectName("taskScroll")
        self.task_scroll.setWidgetResizable(True)
        self.task_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.task_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        list_content = QWidget()
        list_content.setObjectName("taskListContent")
        self.rows_layout = QVBoxLayout(list_content)
        self.rows_layout.setContentsMargins(5, 5, 12, 5)
        self.rows_layout.setSpacing(17)

        self.empty_state = QLabel()
        self.empty_state.setObjectName("emptyState")
        self.empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_state.setWordWrap(True)
        self.empty_state.setMinimumHeight(200)
        self.task_scroll.setWidget(list_content)
        layout.addWidget(self.task_scroll, 1)

        self.quick_add_bar = QWidget()
        quick_layout = QHBoxLayout(self.quick_add_bar)
        quick_layout.setContentsMargins(0, 0, 0, 0)
        quick_layout.setSpacing(10)
        self.quick_add_input = QLineEdit()
        self.quick_add_input.setObjectName("quickAddInput")
        self.quick_add_input.setPlaceholderText("Быстро добавить задачу…")
        self.quick_add_input.setClearButtonEnabled(True)
        self.quick_add_input.returnPressed.connect(self.quick_add_task)
        quick_layout.addWidget(self.quick_add_input, 1)
        self.quick_add_button = AnimatedButton("Добавить")
        self.quick_add_button.setObjectName("quickAddButton")
        self.quick_add_button.clicked.connect(self.quick_add_task)
        quick_layout.addWidget(self.quick_add_button)
        layout.addWidget(self.quick_add_bar)

        self.bulk_bar = QWidget()
        bulk_layout = QHBoxLayout(self.bulk_bar)
        bulk_layout.setContentsMargins(0, 0, 0, 0)
        bulk_layout.setSpacing(10)
        self.selected_count_label = QLabel("Выбрано: 0")
        self.selected_count_label.setObjectName("bulkCountLabel")
        bulk_layout.addWidget(self.selected_count_label, 1)
        self.select_all_button = AnimatedButton("Выбрать все")
        self.select_all_button.setObjectName("bulkActionButton")
        self.select_all_button.clicked.connect(self.select_all_visible_tasks)
        bulk_layout.addWidget(self.select_all_button)
        self.bulk_delete_button = AnimatedButton("Удалить выбранные")
        self.bulk_delete_button.setObjectName("bulkDeleteButton")
        self.bulk_delete_button.clicked.connect(self.delete_selected_tasks)
        bulk_layout.addWidget(self.bulk_delete_button)
        self.cancel_selection_button = AnimatedButton("Готово")
        self.cancel_selection_button.setObjectName("finishSelectionButton")
        self.cancel_selection_button.clicked.connect(lambda: self.set_selection_mode(False))
        bulk_layout.addWidget(self.cancel_selection_button)
        self.bulk_bar.hide()
        layout.addWidget(self.bulk_bar)

        self.add_button = SparkleButton("\u2002Добавить задачу")
        self.add_button.setObjectName("addTaskButton")
        self.add_button.setAccessibleName("Добавить задачу")
        self.add_button.setIcon(QIcon(str(ASSETS / "icons" / "add_circle.svg")))
        self.add_button.setIconSize(QSize(50, 50))
        self.add_button.clicked.connect(self.add_task)
        layout.addWidget(self.add_button)
        return panel

    def _build_pet_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("petPanel")
        layout = QVBoxLayout(panel)
        self.pet_panel_layout = layout
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        header_frame = QFrame()
        header_frame.setObjectName("sectionHeader")
        header = QHBoxLayout(header_frame)
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(12)
        self.pet_header_frame = header_frame
        self.pet_header_layout = header
        self.pet_name_stack = QStackedWidget()
        self.pet_name_stack.setObjectName("petNameStack")
        self.pet_name_stack.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.pet_name_label = ClickableStrokeLabel(self.pet_name.upper(), stroke_width=0.9)
        self.pet_name_label.setObjectName("petNameDisplay")
        self.pet_name_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pet_name_label.setToolTip("Нажми, чтобы изменить имя")
        self.pet_name_label.clicked.connect(self._focus_pet_name)
        self.pet_name_edit = QLineEdit(self.pet_name.upper())
        self.pet_name_edit.setObjectName("petNameEdit")
        self.pet_name_edit.setMaxLength(9)
        self.pet_name_edit.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.pet_name_edit.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.pet_name_edit.setPlaceholderText("Имя питомца")
        self.pet_name_edit.setToolTip("Нажми, чтобы изменить имя")
        self.pet_name_edit.textEdited.connect(self._set_pet_name)
        self.pet_name_edit.editingFinished.connect(self._commit_pet_name)
        self.pet_name_stack.addWidget(self.pet_name_label)
        self.pet_name_stack.addWidget(self.pet_name_edit)
        self.pet_name_stack.setCurrentWidget(self.pet_name_label)
        header.addWidget(self.pet_name_stack, 1)

        self.theme_button = self._toolbar_button("sun.svg", "Переключить тему", self.toggle_theme)
        self.status_button = self._toolbar_button("chart.svg", "Показать или скрыть состояние", self.toggle_mood_status)
        self.status_button.setCheckable(True)
        self.settings_button = self._toolbar_button("gear.svg", "Настройки", self.show_settings_menu)
        self.settings_button.setCheckable(True)
        for button in (self.theme_button, self.status_button, self.settings_button):
            header.addWidget(button)
        layout.addWidget(header_frame)

        self.settings_panel = QFrame()
        self.settings_panel.setParent(panel)
        self.settings_panel.setObjectName("inlineSettingsPanel")
        settings_layout = QVBoxLayout(self.settings_panel)
        settings_layout.setContentsMargins(10, 8, 10, 8)
        settings_layout.setSpacing(6)
        settings_buttons = QHBoxLayout()
        settings_buttons.setSpacing(8)
        self.mood_setting_button = QPushButton("Статус")
        self.mood_setting_button.setObjectName("inlineSettingButton")
        self.mood_setting_button.setToolTip("Показывать состояние питомца")
        self.mood_setting_button.setCheckable(True)
        self.mood_setting_button.setChecked(self.show_mood_status)
        self.mood_setting_button.clicked.connect(self.set_mood_status_visible)
        settings_buttons.addWidget(self.mood_setting_button)
        self.pet_setting_button = QPushButton("Питомец")
        self.pet_setting_button.setObjectName("inlineSettingButton")
        self.pet_setting_button.setToolTip("Показывать панель питомца")
        self.pet_setting_button.setCheckable(True)
        self.pet_setting_button.setChecked(self.show_pet_panel)
        self.pet_setting_button.clicked.connect(self.set_pet_panel_visible)
        settings_buttons.addWidget(self.pet_setting_button)
        self.rename_pet_button = QPushButton("Имя")
        self.rename_pet_button.setObjectName("inlineSettingButton")
        self.rename_pet_button.setToolTip("Изменить имя питомца")
        self.rename_pet_button.clicked.connect(self._focus_pet_name)
        settings_buttons.addWidget(self.rename_pet_button)
        settings_layout.addLayout(settings_buttons)
        background_row = QHBoxLayout()
        background_label = QLabel("Фон питомца")
        self.pet_background_label = background_label
        background_label.setObjectName("petBackgroundLabel")
        self.pet_background_combo = QComboBox()
        self.pet_background_combo.setObjectName("petBackgroundCombo")
        self.pet_background_combo.addItem("Комната", "room")
        self.pet_background_combo.addItem("Цвет приложения", "solid")
        background_row.addWidget(background_label)
        background_row.addWidget(self.pet_background_combo, 1)
        settings_layout.addLayout(background_row)

        backup_row = QHBoxLayout()
        backup_row.setSpacing(8)
        self.create_backup_button = QPushButton("Создать копию")
        self.create_backup_button.setObjectName("inlineSettingButton")
        self.create_backup_button.clicked.connect(self._create_backup)
        self.restore_backup_button = QPushButton("Восстановить")
        self.restore_backup_button.setObjectName("inlineSettingButton")
        self.restore_backup_button.clicked.connect(self._restore_backup)
        backup_row.addWidget(self.create_backup_button)
        backup_row.addWidget(self.restore_backup_button)
        settings_layout.addLayout(backup_row)
        self.pet_background_combo.currentIndexChanged.connect(self._set_pet_background)
        self.settings_panel.hide()

        self.pet_scene = PetScene()
        self.pet_scene.set_background(self.pet_background)
        self.mood_card = self.pet_scene.mood_card
        self.focus_timer_panel = FocusTimerPanel(panel)
        self.focus_timer_panel.hide()
        self.focus_timer_panel.closed.connect(self._close_focus_mode)
        self.focus_timer_panel.phase_finished.connect(self._on_focus_phase_finished)
        self.focus_timer_panel.session_requested.connect(self._begin_focus_session)
        layout.addWidget(self.focus_timer_panel, 1)
        layout.addWidget(self.pet_scene, 1)
        panel.installEventFilter(self)
        return panel

    def _position_settings_panel(self) -> None:
        if not hasattr(self, "settings_panel") or not hasattr(self, "pet_panel"):
            return
        margins = self.pet_panel_layout.contentsMargins()
        x = margins.left()
        width = max(0, self.pet_panel.width() - margins.left() - margins.right())
        y = self.pet_header_frame.geometry().bottom() + 6
        self.settings_panel.setGeometry(x, y, width, self.settings_panel.sizeHint().height())
        if self.settings_panel.isVisible():
            self.settings_panel.raise_()

    def eventFilter(self, watched, event) -> bool:
        if watched is getattr(self, "pet_panel", None) and event.type() == QEvent.Type.Resize:
            QTimer.singleShot(0, self._position_settings_panel)
        return super().eventFilter(watched, event)

    @staticmethod
    def _toolbar_button(icon_name: str, tooltip: str, callback) -> QPushButton:
        button = AnimatedButton()
        button.setObjectName("toolbarButton")
        button.setIcon(QIcon(str(ASSETS / "icons" / icon_name)))
        button.setIconSize(QSize(34, 34))
        button.setFixedSize(64, 64)
        button.setToolTip(tooltip)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.clicked.connect(callback)
        return button

    def _create_resize_handles(self) -> None:
        self.resize_handles: list[ResizeHandle] = []
        configurations = (
            (Qt.Edge.LeftEdge, Qt.CursorShape.SizeHorCursor, "left"),
            (Qt.Edge.RightEdge, Qt.CursorShape.SizeHorCursor, "right"),
            (Qt.Edge.TopEdge, Qt.CursorShape.SizeVerCursor, "top"),
            (Qt.Edge.BottomEdge, Qt.CursorShape.SizeVerCursor, "bottom"),
            (Qt.Edge.LeftEdge | Qt.Edge.TopEdge, Qt.CursorShape.SizeFDiagCursor, "top_left"),
            (Qt.Edge.RightEdge | Qt.Edge.TopEdge, Qt.CursorShape.SizeBDiagCursor, "top_right"),
            (Qt.Edge.LeftEdge | Qt.Edge.BottomEdge, Qt.CursorShape.SizeBDiagCursor, "bottom_left"),
            (Qt.Edge.RightEdge | Qt.Edge.BottomEdge, Qt.CursorShape.SizeFDiagCursor, "bottom_right"),
        )
        self._resize_edges = {}
        for edges, cursor, name in configurations:
            handle = ResizeHandle(self, edges, cursor)
            self.resize_handles.append(handle)
            self._resize_edges[name] = handle
        self._position_resize_handles()

    def _position_resize_handles(self) -> None:
        if not hasattr(self, "_resize_edges"):
            return
        width, height = self.width(), self.height()
        edge = 8
        corner = 17
        self._resize_edges["left"].setGeometry(0, corner, edge, max(0, height - 2 * corner))
        self._resize_edges["right"].setGeometry(width - edge, corner, edge, max(0, height - 2 * corner))
        self._resize_edges["top"].setGeometry(corner, 0, max(0, width - 2 * corner), edge)
        self._resize_edges["bottom"].setGeometry(corner, height - edge, max(0, width - 2 * corner), edge)
        self._resize_edges["top_left"].setGeometry(0, 0, corner, corner)
        self._resize_edges["top_right"].setGeometry(width - corner, 0, corner, corner)
        self._resize_edges["bottom_left"].setGeometry(0, height - corner, corner, corner)
        self._resize_edges["bottom_right"].setGeometry(width - corner, height - corner, corner, corner)
        for handle in self.resize_handles:
            handle.setVisible(not self.isMaximized())
            handle.raise_()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_responsive_layout()
        self._position_settings_panel()
        self._position_resize_handles()

    def _update_responsive_layout(self, force: bool = False) -> None:
        if not hasattr(self, "task_panel_layout") or not hasattr(self, "title_bar"):
            return
        compact = self.width() < 1180
        tiny = self.width() < 860
        if not force and (compact, tiny) == (
            getattr(self, "_compact_layout", None), getattr(self, "_tiny_layout", False)
        ):
            return

        self._compact_layout = compact
        self._tiny_layout = tiny
        self.setProperty("compact", compact)
        self.setProperty("tiny", tiny)

        if compact:
            self.task_heading_row.removeWidget(self.filter_bar)
            self.task_header_layout.addWidget(self.filter_bar)
            self.task_header_layout.setSpacing(5)
            self.rows_layout.setSpacing(10 if tiny else 13)
            self.rows_layout.setContentsMargins(3, 3, 7, 3)
            self.task_panel_layout.setSpacing(9 if tiny else 11)
            self.task_panel_layout.setContentsMargins(14 if not tiny else 10, 12, 14 if not tiny else 10, 12)
            self.pet_panel_layout.setContentsMargins(12 if not tiny else 8, 12, 12 if not tiny else 8, 12)
        else:
            self.task_header_layout.removeWidget(self.filter_bar)
            self.task_heading_row.addWidget(self.filter_bar)
            self.task_header_layout.setSpacing(0)
            self.rows_layout.setSpacing(17)
            self.rows_layout.setContentsMargins(5, 5, 12, 5)
            self.task_panel_layout.setSpacing(14)
            self.task_panel_layout.setContentsMargins(22, 18, 22, 19)
            self.pet_panel_layout.setContentsMargins(18, 18, 18, 18)

        control_size = 36 if tiny else (44 if compact else 64)
        icon_size = 20 if tiny else (24 if compact else 34)
        for button in (self.theme_button, self.status_button, self.settings_button):
            button.setFixedSize(control_size, control_size)
            button.setIconSize(QSize(icon_size, icon_size))
        self.pet_header_layout.setSpacing(6 if tiny else (8 if compact else 12))
        self.title_bar.set_compact(compact, tiny)
        self.add_button.setMinimumHeight(58 if tiny else (66 if compact else 78))
        self.add_button.setIconSize(QSize(32, 32) if tiny else QSize(38, 38) if compact else QSize(46, 46))
        self.selection_mode_button.setMinimumHeight(30 if tiny else (36 if compact else 44))
        self.quick_add_button.setMinimumHeight(30 if tiny else (36 if compact else 44))
        self.search_input.setMinimumWidth(0)
        self.quick_add_input.setMinimumWidth(0)
        self.pet_scene.set_compact(compact, tiny)
        for row in self.task_rows.values():
            row.set_compact(compact, tiny)

        for widget in (self, *self.findChildren(QWidget)):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

        name_metrics = QFontMetricsF(self.pet_name_label.font())


        names_to_fit = ("ТАМАГОЧИИ", self.pet_name.upper())
        name_width = max(name_metrics.horizontalAdvance(name) for name in names_to_fit) + 12
        self.pet_name_stack.setMinimumWidth(int(name_width))
        panel_margins = self.pet_panel_layout.contentsMargins()
        pet_panel_min_width = (
            int(name_width)
            + 3 * control_size
            + 3 * self.pet_header_layout.spacing()
            + panel_margins.left()
            + panel_margins.right()
            + 4
        )
        self.pet_panel.setMinimumWidth(pet_panel_min_width)
        self.setMinimumWidth(max(760, pet_panel_min_width + 360))

        if self.splitter.width() > 0:



            task_ratio = 0.62 if tiny else (0.70 if compact else 0.59)
            self.splitter.setSizes([
                int(self.splitter.width() * task_ratio),
                int(self.splitter.width() * (1 - task_ratio)),
            ])

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange and hasattr(self, "title_bar"):
            self.title_bar.refresh_window_icons()
            self._position_resize_handles()
            QTimer.singleShot(0, self._sync_pet_overlay_visibility)

    def _sync_pet_overlay_visibility(self) -> None:
        should_show = self.isMinimized() and self.show_pet_panel
        if not should_show:
            if self.pet_overlay is not None:
                self.pet_overlay.hide()
            return

        if self.pet_overlay is None:
            self.pet_overlay = PetOverlayWindow(self.screen())
            self.pet_overlay.pet_scene.set_dark(self.theme == "dark")
            self.pet_overlay.pet_scene.set_language(self.language)
            self.pet_overlay.pet_scene.set_mood(evaluate_mood(self.tasks), THEMES[self.theme])
        self.pet_overlay.show_overlay()

    def quick_add_task(self) -> None:
        title = self.quick_add_input.text().strip()
        if not title:
            self.quick_add_input.setFocus()
            return
        if self.selection_mode:
            self.set_selection_mode(False)
        if self.current_filter == "completed":
            self.set_filter("all")
        self.search_input.clear()
        task = Task(title=title)
        self.tasks.append(task)
        self._create_task_row(task)
        self._on_tasks_changed()
        self.quick_add_input.clear()
        self.quick_add_input.setFocus()
        self.task_rows[task.task_id].animate_appearance()

    def add_task(self) -> None:

        if self.selection_mode:
            self.set_selection_mode(False)
        self.search_input.clear()
        for row in list(self.task_rows.values()):
            if row.is_editing():
                row.save_edit()

        if self.current_filter == "completed":
            self.set_filter("all")
        task = Task(title=tr("Новая задача", self.language))
        self.tasks.append(task)
        self._create_task_row(task)
        self._on_tasks_changed()
        row = self.task_rows[task.task_id]
        row.enter_edit_mode()
        row.animate_appearance()

    def _create_task_row(self, task: Task) -> None:
        row = TaskRow(task)
        row.set_language(self.language)
        row.set_compact(
            getattr(self, "_compact_layout", False),
            getattr(self, "_tiny_layout", False),
        )
        row.set_dark_theme(self.theme == "dark")
        row.changed.connect(self._on_tasks_changed)
        row.content_changed.connect(self._schedule_save)
        row.delete_requested.connect(self.delete_task)
        row.focus_requested.connect(self._start_focus_for_task)
        row.title_preview_changed.connect(self._update_focus_task_title)
        row.selection_requested.connect(self._on_row_selection_requested)
        row.set_selection_mode(self.selection_mode)
        self.task_rows[task.task_id] = row

    def set_search_query(self, query: str) -> None:
        normalized = query.strip()
        if normalized != self.search_query:
            self.selected_task_ids.clear()
            for row in self.task_rows.values():
                row.set_selected(False)
        self.search_query = normalized
        self._refresh_task_list_state()

    def set_filter(self, filter_name: str) -> None:
        if filter_name not in {"all", "active", "completed"}:
            return
        if filter_name != self.current_filter:
            self.selected_task_ids.clear()
            for row in self.task_rows.values():
                row.set_selected(False)
        self.current_filter = filter_name
        for key, button in self.filter_buttons.items():
            button.setChecked(key == filter_name)
        self._refresh_task_list_state()

    def toggle_selection_mode(self) -> None:
        self.set_selection_mode(not self.selection_mode)

    def _finish_selection_from_enter(self) -> None:
        if self.selection_mode:
            self.set_selection_mode(False)

    def _cancel_active_task_edit(self) -> None:
        for row in self.task_rows.values():
            if row.is_editing():
                row.cancel_edit()
                return

    def set_selection_mode(self, enabled: bool) -> None:
        if enabled == self.selection_mode:
            return
        if enabled:
            for row in list(self.task_rows.values()):
                if row.is_editing():
                    row.save_edit()
        self.selection_mode = enabled
        self.finish_selection_shortcut.setEnabled(enabled)
        self.finish_selection_enter_shortcut.setEnabled(enabled)
        if not enabled:
            self.selected_task_ids.clear()
        for row in self.task_rows.values():
            row.set_selection_mode(enabled)
            if not enabled:
                row.set_selected(False)
        self.selection_mode_button.setText(
            tr("Выбор включён" if enabled else "Выбрать", self.language)
        )
        self.selection_mode_button.setChecked(enabled)
        self.quick_add_bar.setVisible(not enabled)
        self.add_button.setVisible(not enabled)
        self.bulk_bar.setVisible(enabled)
        self._update_bulk_controls()

    def _on_row_selection_requested(self, task_id: str, selected: bool) -> None:
        if selected:
            self.selected_task_ids.add(task_id)
        else:
            self.selected_task_ids.discard(task_id)
        self._update_bulk_controls()

    def _visible_tasks(self) -> list[Task]:
        active = [task for task in self.tasks if not task.completed]
        completed = [task for task in self.tasks if task.completed]
        tasks = {"all": active + completed, "active": active, "completed": completed}[self.current_filter]
        query = self.search_query.casefold()
        if query:
            tasks = [
                task for task in tasks
                if query in task.title.casefold() or query in task.description.casefold()
            ]
        return tasks

    def _update_bulk_controls(self) -> None:
        if not hasattr(self, "selected_count_label"):
            return
        visible_ids = {task.task_id for task in self._visible_tasks()}
        self.selected_task_ids.intersection_update(visible_ids)
        self.selected_count_label.setText(
            tr("Выбрано: {count}", self.language).format(count=len(self.selected_task_ids))
        )
        self.bulk_delete_button.setEnabled(bool(self.selected_task_ids))
        all_selected = bool(visible_ids) and visible_ids.issubset(self.selected_task_ids)
        self.select_all_button.setText(
            tr("Снять выбор" if all_selected else "Выбрать все", self.language)
        )
        self.select_all_button.setEnabled(bool(visible_ids))

    def select_all_visible_tasks(self) -> None:
        visible_ids = {task.task_id for task in self._visible_tasks()}
        if visible_ids and visible_ids.issubset(self.selected_task_ids):
            self.selected_task_ids.difference_update(visible_ids)
        else:
            self.selected_task_ids.update(visible_ids)
        for task_id, row in self.task_rows.items():
            row.set_selected(task_id in self.selected_task_ids)
        self._update_bulk_controls()

    def delete_selected_tasks(self) -> None:
        selected = set(self.selected_task_ids)
        if not selected:
            return
        if self._focus_task_id in selected:
            self._close_focus_mode()
        self._undo_deleted_tasks = [task for task in self.tasks if task.task_id in selected]
        self.tasks = [task for task in self.tasks if task.task_id not in selected]
        for task_id in selected:
            row = self.task_rows.pop(task_id, None)
            if row is not None:
                self.rows_layout.removeWidget(row)
                row.deleteLater()
        count = len(self._undo_deleted_tasks)
        self.set_selection_mode(False)
        self._on_tasks_changed()
        self.undo_delete_button.show()
        self._show_status_message(
            tr("Удалено задач: {count}", self.language).format(count=count)
        )

    def undo_bulk_delete(self) -> None:
        if not self._undo_deleted_tasks:
            self.undo_delete_button.hide()
            return
        restored = self._undo_deleted_tasks
        self._undo_deleted_tasks = []
        existing_ids = {task.task_id for task in self.tasks}
        for task in restored:
            if task.task_id not in existing_ids:
                self.tasks.append(task)
                self._create_task_row(task)
        self.undo_delete_button.hide()
        self._on_tasks_changed()
        self._show_status_message(tr("Удаление отменено", self.language))

    def _load_tasks(self) -> None:
        try:
            self.tasks, settings = self.storage.load()
            self._apply_setting_values(settings)
        except TaskStorageError as error:
            self.tasks = []
            self.storage_ready = False
            self._show_status_message(
                tr("Не удалось загрузить задачи ({error}). Автосохранение приостановлено.", self.language).format(error=error)
            )

    def _apply_setting_values(self, settings: dict[str, object]) -> None:
        saved_theme = settings.get("theme")
        if isinstance(saved_theme, str) and saved_theme in THEMES:
            self.theme = saved_theme
        saved_language = settings.get("language")
        if isinstance(saved_language, str) and saved_language in {"ru", "en"}:
            self.language = saved_language
        saved_name = settings.get("pet_name")
        if isinstance(saved_name, str) and saved_name.strip():
            self.pet_name = saved_name.strip()[:9]
        show_mood_status = settings.get("show_mood_status")
        if isinstance(show_mood_status, bool):
            self.show_mood_status = show_mood_status
        show_pet_panel = settings.get("show_pet_panel")
        if isinstance(show_pet_panel, bool):
            self.show_pet_panel = show_pet_panel
        saved_background = settings.get("pet_background", "room")
        if isinstance(saved_background, str):
            self.pet_background = saved_background if saved_background in {"room", "solid"} else "room"
        focus_minutes = settings.get("focus_minutes", 25)
        break_minutes = settings.get("break_minutes", 5)
        if type(focus_minutes) is int:
            self.focus_minutes = min(180, max(1, focus_minutes))
        if type(break_minutes) is int:
            self.break_minutes = min(60, max(1, break_minutes))

    def _show_status_message(self, message: str) -> None:
        self.status_bar.show()
        self.status_bar.showMessage(message)
        self.status_timer.start()

    def _hide_status_bar(self) -> None:
        self.status_bar.hide()
        self.undo_delete_button.hide()

    def _schedule_save(self) -> None:
        self.save_timer.start()

    def _settings_snapshot(self) -> dict[str, object]:
        return {
            "theme": self.theme,
            "language": self.language,
            "pet_name": self.pet_name,
            "show_mood_status": self.show_mood_status,
            "show_pet_panel": self.show_pet_panel,
            "pet_background": self.pet_background,
            "focus_minutes": self.focus_minutes,
            "break_minutes": self.break_minutes,
        }

    def _save_tasks(self) -> None:
        if not self.storage_ready:
            return
        try:
            self.storage.save(self.tasks, self._settings_snapshot())
        except OSError as error:
            self._show_status_message(
                tr("Не удалось сохранить: {error}", self.language).format(error=error)
            )

    def _create_backup(self) -> None:
        default_name = f"TamagoToDo backup {datetime.now():%Y-%m-%d}.json"
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("Создать резервную копию", self.language),
            default_name,
            "JSON (*.json)",
        )
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        try:
            self.storage.save_file(path, self.tasks, self._settings_snapshot())
        except OSError as error:
            QMessageBox.warning(
                self,
                tr("Ошибка резервного копирования", self.language),
                str(error),
            )
            return
        QMessageBox.information(
            self,
            tr("Резервная копия создана", self.language),
            tr("Задачи и настройки сохранены в файл.", self.language),
        )

    def _restore_backup(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("Восстановить резервную копию", self.language),
            "",
            "JSON (*.json)",
        )
        if not path:
            return
        try:
            restored_tasks, restored_settings = self.storage.load_file(path)
        except TaskStorageError as error:
            QMessageBox.warning(
                self,
                tr("Не удалось восстановить копию", self.language),
                str(error),
            )
            return

        answer = QMessageBox.question(
            self,
            tr("Восстановить резервную копию?", self.language),
            tr("Текущие задачи и настройки будут заменены выбранной копией.", self.language),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.storage.save_file(
                self.storage.path.with_name("tasks.before_restore.json"),
                self.tasks,
                self._settings_snapshot(),
            )
            self.storage.save(restored_tasks, restored_settings)
        except OSError as error:
            QMessageBox.warning(
                self,
                tr("Не удалось восстановить копию", self.language),
                str(error),
            )
            return

        self._apply_restored_data(restored_tasks, restored_settings)
        QMessageBox.information(
            self,
            tr("Данные восстановлены", self.language),
            tr("Задачи и настройки восстановлены из резервной копии.", self.language),
        )

    def _apply_restored_data(
        self, tasks: list[Task], settings: dict[str, object]
    ) -> None:
        if self.focus_timer_panel.isVisible():
            self._close_focus_mode()
        if self.selection_mode:
            self.set_selection_mode(False)
        self.search_query = ""
        self.current_filter = "all"
        self.search_input.clear()
        self.filter_buttons["all"].setChecked(True)
        self._undo_deleted_tasks.clear()
        self.undo_delete_button.hide()

        for row in self.task_rows.values():
            self.rows_layout.removeWidget(row)
            row.hide()
            row.deleteLater()
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                if widget is not self.empty_state:
                    widget.deleteLater()
        self.tasks = tasks
        self.task_rows.clear()
        self._apply_setting_values(settings)
        self.storage_ready = True
        for task in self.tasks:
            self._create_task_row(task)
        self._sort_rows()

        self.pet_name_edit.setText(self.pet_name.upper())
        background_index = self.pet_background_combo.findData(self.pet_background)
        self.pet_background_combo.setCurrentIndex(background_index)
        self.focus_timer_panel.focus_spin.setValue(self.focus_minutes)
        self.focus_timer_panel.break_spin.setValue(self.break_minutes)
        self.pet_scene.set_background(self.pet_background)
        self._apply_language()
        self._apply_saved_visibility()
        if self.show_pet_panel:
            self.splitter.setChildrenCollapsible(False)
            self.splitter.setSizes(self._saved_splitter_sizes)
        else:
            self.splitter.setChildrenCollapsible(True)
            self.splitter.setSizes([sum(self.splitter.sizes()), 0])
        self._refresh_task_list_state()
        self._update_mood()
        self._save_tasks()

    def _setup_reminders(self) -> None:
        self.tray_icon = QSystemTrayIcon(QIcon(str(ASSETS / "app_icon.png")), self)
        self.tray_icon.setToolTip("TamagoToDo — напоминания о задачах")
        tray_menu = QMenu(self)
        self.tray_open_action = QAction("Открыть TamagoToDo", tray_menu)
        self.tray_quit_action = QAction("Выход", tray_menu)
        self.tray_open_action.triggered.connect(self._restore_from_tray)
        self.tray_quit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(self.tray_open_action)
        tray_menu.addSeparator()
        tray_menu.addAction(self.tray_quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_icon_activated)
        self.tray_available = QSystemTrayIcon.isSystemTrayAvailable()
        if self.tray_available:
            self.tray_icon.show()

        self.reminder_timer = QTimer(self)
        self.reminder_timer.setInterval(30_000)
        self.reminder_timer.timeout.connect(self._check_reminders)
        self.reminder_timer.start()
        QTimer.singleShot(1200, self._check_reminders)

    def _restore_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._restore_from_tray()

    def _check_reminders(self) -> None:
        now = datetime.now()
        due: list[Task] = []
        for task in self.tasks:
            if task.completed or task.reminder_minutes is None:
                continue
            deadline_key = task.deadline.isoformat()
            if task.reminded_deadline == deadline_key:
                continue
            reminder_time = task.deadline - timedelta(minutes=task.reminder_minutes)
            if reminder_time <= now <= task.deadline + timedelta(minutes=5):
                task.reminded_deadline = deadline_key
                due.append(task)
        if not due:
            return

        self._save_tasks()
        titles = [task.title for task in due[:4]]
        message = "\n".join(titles)
        if len(due) > 4:
            message += "\n" + tr("И ещё задач: {count}", self.language).format(count=len(due) - 4)
        if self.tray_available:
            self.tray_icon.showMessage(
                tr("Напоминание о задачах", self.language),
                message,
                QSystemTrayIcon.MessageIcon.Information,
                10_000,
            )
        else:
            self._show_status_message(
                tr("Напоминание: {titles}", self.language).format(titles=', '.join(titles))
            )
            QApplication.alert(self)

    def delete_task(self, task_id: str) -> None:
        if task_id == self._focus_task_id:
            self._close_focus_mode()
        self.tasks = [task for task in self.tasks if task.task_id != task_id]
        row = self.task_rows.pop(task_id, None)
        if row is not None:
            self.rows_layout.removeWidget(row)
            row.deleteLater()
        self._on_tasks_changed()

    def _on_tasks_changed(self) -> None:
        self._sort_rows()
        self._refresh_task_list_state()
        self._update_mood(update_deadlines=False)
        self._schedule_save()

    def _start_focus_for_task(self, task_id: str) -> None:
        if self._focus_task_id is not None:
            self._show_status_message(tr("Сначала заверши текущую фокус-сессию.", self.language))
            return
        task = next((item for item in self.tasks if item.task_id == task_id), None)
        if task is None or task.completed:
            return
        self._focus_task_id = task_id
        self.focus_timer_panel.prepare_session(task.title, self.focus_minutes, self.break_minutes)
        self.pet_scene.hide()
        self.focus_timer_panel.show()

    def _begin_focus_session(self, focus_minutes: int, break_minutes: int) -> None:
        task = next((item for item in self.tasks if item.task_id == self._focus_task_id), None)
        if task is None or task.completed:
            self._close_focus_mode()
            return
        self.focus_minutes = min(180, max(1, focus_minutes))
        self.break_minutes = min(60, max(1, break_minutes))
        title = self.focus_timer_panel.current_task_title() or task.title
        self.focus_timer_panel.start_session(title, self.focus_minutes, self.break_minutes)
        self._save_tasks()

    def _update_focus_task_title(self, task_id: str, title: str) -> None:
        if task_id == self._focus_task_id:
            self.focus_timer_panel.set_task_title(title)

    def _on_focus_phase_finished(self, phase: str) -> None:
        message = (
            "Фокус-сессия завершена — можно отдохнуть."
            if phase == "focus" else "Перерыв завершён."
        )
        self._show_status_message(tr(message, self.language))

    def _close_focus_mode(self) -> None:
        if hasattr(self, "focus_timer_panel"):
            self.focus_timer_panel.stop()
            self.focus_timer_panel.hide()
        if hasattr(self, "pet_scene"):
            self.pet_scene.show()
        self._focus_task_id = None

    def _sort_rows(self) -> None:
        self.tasks.sort(
            key=lambda task: (
                1 if task.completed else 0,
                (task.completed_at or datetime.max) if task.completed else task.deadline,
            )
        )

    def _refresh_task_list_state(self) -> None:
        while self.rows_layout.count():
            self.rows_layout.takeAt(0)
        self.empty_state.hide()
        for row in self.task_rows.values():
            row.hide()

        visible_tasks = self._visible_tasks()

        if not visible_tasks:
            messages = {
                "all": tr("Здесь пока тихо.\nДобавь первую задачу — питомец будет рядом!", self.language),
                "active": tr("Активных задач нет — можно выдохнуть :)", self.language),
                "completed": tr("Выполненные задачи появятся здесь.", self.language),
            }
            empty_text = (
                tr("Ничего не найдено.\nПопробуй изменить поисковый запрос.", self.language)
                if self.search_query
                else messages[self.current_filter]
            )
            self.empty_state.setText(empty_text)
            self.empty_state.show()
            self.rows_layout.addWidget(self.empty_state)
        else:
            for task in visible_tasks:
                self._add_visible_row(task)
        self.rows_layout.addStretch(1)
        self._update_bulk_controls()

    def _add_visible_row(self, task: Task) -> None:
        row = self.task_rows[task.task_id]
        row.show()
        self.rows_layout.addWidget(row)

    def _update_mood(self, update_deadlines: bool = True) -> None:
        mood = evaluate_mood(self.tasks)
        self.pet_scene.set_mood(mood, THEMES[self.theme])
        if self.pet_overlay is not None:
            self.pet_overlay.pet_scene.set_mood(mood, THEMES[self.theme])
        if update_deadlines:
            for row in self.task_rows.values():
                row._update_deadline_pill()

    def _set_pet_name(self, name: str) -> None:
        self.pet_name = name.strip()[:9]
        self._schedule_save()

    def _commit_pet_name(self) -> None:
        self.pet_name = self.pet_name_edit.text().strip() or tr("Тамагочи", self.language)
        self.pet_name = self.pet_name[:9]
        self.pet_name_edit.setText(self.pet_name.upper())
        self.pet_name_label.setText(self.pet_name.upper())
        self.pet_name_stack.setCurrentWidget(self.pet_name_label)
        self._save_tasks()

    def toggle_theme(self) -> None:
        self.theme = "dark" if self.theme == "light" else "light"
        self._apply_theme()
        self._save_tasks()

    def toggle_language(self) -> None:
        self.language = "en" if self.language == "ru" else "ru"
        self._apply_language()
        self._save_tasks()

    def toggle_mood_status(self) -> None:
        self.set_mood_status_visible(not self.show_mood_status)

    def hide_pet_panel(self) -> None:
        if not self.show_pet_panel:
            return
        self.show_pet_panel = False
        self.pet_setting_button.setChecked(False)
        sizes = self.splitter.sizes()
        if len(sizes) == 2 and sizes[1] > 0:
            self._saved_splitter_sizes = sizes
        self.restore_pet_button.show()
        self._animate_pet_panel_width(0)
        self._save_tasks()
        self._sync_pet_overlay_visibility()

    def show_pet_panel_again(self) -> None:
        if self.show_pet_panel and self.pet_panel.isVisible():
            return
        self.show_pet_panel = True
        self.pet_setting_button.setChecked(True)
        self.pet_panel.show()
        self.restore_pet_button.hide()
        target = self._saved_splitter_sizes[1] if len(self._saved_splitter_sizes) == 2 else 600
        total = max(1, sum(self.splitter.sizes()))
        self.splitter.setChildrenCollapsible(True)
        self.splitter.setSizes([total, 0])
        self._animate_pet_panel_width(target)
        self._save_tasks()
        self._sync_pet_overlay_visibility()

    def _animate_pet_panel_width(self, target_width: int) -> None:
        if self._pet_panel_animation is not None:
            self._pet_panel_animation.stop()
        sizes = self.splitter.sizes()
        current_width = sizes[1] if len(sizes) == 2 else 0
        total_width = max(1, sum(sizes))
        self.splitter.setChildrenCollapsible(True)
        animation = QVariantAnimation(self)
        distance = abs(target_width - current_width)
        animation.setDuration(max(190, min(340, int(190 + distance * 0.22))))
        animation.setStartValue(current_width)
        animation.setEndValue(max(0, target_width))
        animation.setEasingCurve(
            QEasingCurve.Type.OutCubic if target_width > current_width
            else QEasingCurve.Type.InOutSine
        )

        def apply_width(value) -> None:
            right_width = max(0, int(value))
            self.splitter.setSizes([max(0, total_width - right_width), right_width])

        def finish() -> None:
            if self.show_pet_panel:
                self.splitter.setChildrenCollapsible(False)
                if len(self._saved_splitter_sizes) == 2:
                    self.splitter.setSizes(self._saved_splitter_sizes)
            else:
                self.pet_panel.hide()
                self.splitter.setChildrenCollapsible(False)

        animation.valueChanged.connect(apply_width)
        animation.finished.connect(finish)
        self._pet_panel_animation = animation
        animation.start()

    def _apply_saved_visibility(self) -> None:
        self.mood_card.setVisible(self.show_mood_status)
        self.mood_card.setMaximumHeight(16_777_215)
        self.status_button.setChecked(self.show_mood_status)
        self.pet_setting_button.setChecked(self.show_pet_panel)
        if self.show_pet_panel:
            self.pet_panel.show()
            self.restore_pet_button.hide()
        else:
            self.pet_panel.hide()
            self.restore_pet_button.show()

    def show_settings_menu(self) -> None:
        self.settings_panel.setVisible(not self.settings_panel.isVisible())
        self.settings_button.setChecked(self.settings_panel.isVisible())
        if self.settings_panel.isVisible():
            self._position_settings_panel()
            self.settings_panel.raise_()

    def _set_pet_background(self, _index: int) -> None:
        background = self.pet_background_combo.currentData()
        if background not in {"room", "solid"}:
            return
        self.pet_background = background
        self.pet_scene.set_background(background)
        self._save_tasks()

    def _focus_pet_name(self) -> None:
        self.pet_name_edit.setText(self.pet_name.upper())
        self.pet_name_stack.setCurrentWidget(self.pet_name_edit)
        self.pet_name_edit.setFocus()
        self.pet_name_edit.selectAll()

    def set_mood_status_visible(self, visible: bool) -> None:
        if visible == self.show_mood_status:
            return
        self.show_mood_status = visible
        self.mood_setting_button.setChecked(visible)
        self.pet_scene.set_mood_card_visible(visible)
        self.status_button.setChecked(visible)
        self._save_tasks()

    def set_pet_panel_visible(self, visible: bool) -> None:
        if hasattr(self, "pet_setting_button"):
            self.pet_setting_button.setChecked(visible)
        if not visible and hasattr(self, "settings_panel"):
            self.settings_panel.hide()
            self.settings_button.setChecked(False)
        if visible:
            self.show_pet_panel_again()
        else:
            self.hide_pet_panel()

    def _apply_theme(self) -> None:
        self.setStyleSheet(build_stylesheet(self.theme))
        self.pet_scene.set_dark(self.theme == "dark")
        if self.pet_overlay is not None:
            self.pet_overlay.pet_scene.set_dark(self.theme == "dark")
        dark = self.theme == "dark"
        self.theme_button.setIcon(
            QIcon(str(ASSETS / "icons" / ("moon_slate.svg" if dark else "sun.svg")))
        )
        self.status_button.setIcon(QIcon(str(ASSETS / "icons" / ("chart_slate.svg" if dark else "chart.svg"))))
        self.settings_button.setIcon(QIcon(str(ASSETS / "icons" / ("gear_slate.svg" if dark else "gear.svg"))))
        self.add_button.setIcon(QIcon(str(ASSETS / "icons" / ("add_circle_slate.svg" if dark else "add_circle.svg"))))
        for button in self.findChildren(AnimatedButton):
            button.set_dark_theme(dark)
        self.title_bar.set_dark(dark)
        for row in self.task_rows.values():
            row.set_dark_theme(dark)
        self.theme_button.setToolTip(
            tr(
                "Переключить на тёмную тему" if self.theme == "light" else "Переключить на светлую тему",
                self.language,
            )
        )
        self._update_mood(update_deadlines=False)

    def _apply_language(self) -> None:
        """Update visible controls in place, preserving the current app state."""
        language = self.language
        text = lambda value: tr(value, language)
        self.title_bar.set_language(language)
        if self.pet_overlay is not None:
            self.pet_overlay.pet_scene.set_language(language)
        self.undo_delete_button.setText(text("Отменить"))
        self.task_heading.setText(text("МОИ ЗАДАЧИ"))
        self.restore_pet_button.setText(text("Показать питомца"))
        self.restore_pet_button.setToolTip(text("Вернуть правую панель"))
        for key, source in (("all", "Все"), ("active", "Активные"), ("completed", "Выполненные")):
            self.filter_buttons[key].setText(text(source))
        self.search_input.setPlaceholderText(text("Поиск по задачам…"))
        self.selection_mode_button.setText(
            text("Выбор включён" if self.selection_mode else "Выбрать")
        )
        self.quick_add_input.setPlaceholderText(text("Быстро добавить задачу…"))
        self.quick_add_button.setText(text("Добавить"))
        self.select_all_button.setText(
            text("Снять выбор" if self._all_visible_tasks_selected() else "Выбрать все")
        )
        self.bulk_delete_button.setText(text("Удалить выбранные"))
        self.cancel_selection_button.setText(text("Готово"))
        self.add_button.setText("\u2002" + text("Добавить задачу"))
        self.add_button.setAccessibleName(text("Добавить задачу"))

        default_pet_names = {tr("Тамагочи", "ru"), tr("Тамагочи", "en")}
        display_name = text("Тамагочи") if self.pet_name in default_pet_names else self.pet_name
        self.pet_name_label.setText(display_name.upper())
        if not self.pet_name_edit.hasFocus() or self.pet_name_edit.text() in default_pet_names:
            self.pet_name_edit.setText(display_name.upper())
        self.pet_name_edit.setPlaceholderText(text("Имя питомца"))
        self.pet_name_label.setToolTip(text("Нажми, чтобы изменить имя"))
        self.pet_name_edit.setToolTip(text("Нажми, чтобы изменить имя"))
        self.theme_button.setToolTip(text("Переключить тему"))
        self.status_button.setToolTip(text("Показать или скрыть состояние"))
        self.settings_button.setToolTip(text("Настройки"))
        self.mood_setting_button.setText(text("Статус"))
        self.mood_setting_button.setToolTip(text("Показывать состояние питомца"))
        self.pet_setting_button.setText(text("Питомец"))
        self.pet_setting_button.setToolTip(text("Показывать панель питомца"))
        self.rename_pet_button.setText(text("Имя"))
        self.rename_pet_button.setToolTip(text("Изменить имя питомца"))
        self.pet_background_label.setText(text("Фон питомца"))
        self.pet_background_combo.setItemText(0, text("Комната"))
        self.pet_background_combo.setItemText(1, text("Цвет приложения"))
        self.create_backup_button.setText(text("Создать копию"))
        self.restore_backup_button.setText(text("Восстановить"))

        for row in self.task_rows.values():
            row.set_language(language)
        self.focus_timer_panel.set_language(language)
        self.pet_scene.set_language(language)
        if hasattr(self, "tray_open_action"):
            self.tray_open_action.setText(text("Открыть TamagoToDo"))
            self.tray_quit_action.setText(text("Выход"))
            self.tray_icon.setToolTip(text("TamagoToDo — напоминания о задачах"))
        self._apply_theme()
        self._refresh_task_list_state()

    def _all_visible_tasks_selected(self) -> bool:
        visible_ids = {task.task_id for task in self._visible_tasks()}
        return bool(visible_ids) and visible_ids.issubset(self.selected_task_ids)

    def closeEvent(self, event) -> None:
        self.save_timer.stop()
        self.status_timer.stop()
        if hasattr(self, "focus_timer_panel"):
            self.focus_timer_panel.stop()
        if hasattr(self, "reminder_timer"):
            self.reminder_timer.stop()
        if hasattr(self, "tray_icon"):
            self.tray_icon.hide()
        if self.pet_overlay is not None:
            self.pet_overlay.hide()
        self._save_tasks()
        super().closeEvent(event)


