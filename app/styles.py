"""Цветовые палитры и общие стили TamagoToDo."""

THEMES = {
    "light": {
        "window": "#e7dfe8",
        "panel": "#fffaf4",
        "card": "#fffdf9",
        "card_hover": "#fffefa",
        "border": "#e9ded7",
        "text": "#252442",
        "heading": "#5c5277",
        "muted": "#77748c",
        "input": "#fffdf9",
        "input_border": "#e3d9e5",
        "accent": "#a58dd2",
        "accent_hover": "#947bc6",
        "accent_text": "#ffffff",
        "accent_start": "#ad96d7",
        "accent_end": "#9077c6",
        "subtle": "#f5f0f3",
        "selected_bg": "#f5effa",
        "task_tools_bg": "#f2edf7",
        "task_tools_button": "#fffdf9",
        "task_tools_border": "#e1d7ea",
        "task_edit_bg": "#ece3f8",
        "task_edit_fg": "#584773",
        "task_edit_border": "#d6c7ec",
        "task_done_bg": "#d9f0df",
        "task_done_fg": "#2d704b",
        "task_done_border": "#b4dfc0",
        "task_focus_bg": "#e1ebfc",
        "task_focus_fg": "#405f91",
        "task_focus_border": "#bfd1ef",
        "task_delete_hover": "#f5cbc7",
        "filter_active": "#eee4f1",
        "delete": "#f7dedb",
        "delete_text": "#a6434b",
        "meter_empty": "#e8e6e1",
        "positive_bg": "#f3fff5",
        "positive_fg": "#3f825a",
        "positive_fill": "#70cc8c",
        "positive_border": "#b7ddb9",
        "tense_bg": "#fff4df",
        "tense_fg": "#a26520",
        "tense_fill": "#edbd62",
        "tense_border": "#f0d49f",
        "angry_bg": "#fff0ed",
        "angry_fg": "#b85858",
        "angry_fill": "#ed9184",
        "angry_border": "#efb8b0",
        "deadline_normal_bg": "#d9f0e0",
        "deadline_normal_fg": "#31805a",
        "deadline_soon_bg": "#ffedc5",
        "deadline_soon_fg": "#a76719",
        "deadline_urgent_bg": "#ffded8",
        "deadline_urgent_fg": "#b54f51",
        "deadline_overdue_bg": "#ffded8",
        "deadline_overdue_fg": "#b54f51",
    },
    "dark": {
        "window": "#151b35",
        "panel": "#1b2342",
        "card": "#202a49",
        "card_hover": "#253150",
        "border": "#3b496e",
        "text": "#e3e4fb",
        "heading": "#e8e6ff",
        "muted": "#bbc4e2",
        "input": "#202a49",
        "input_border": "#46577e",
        "accent": "#aaa0ed",
        "accent_hover": "#bbb2f4",
        "accent_text": "#1d2141",
        "accent_start": "#a79ce9",
        "accent_end": "#857bd0",
        "subtle": "#293452",
        "selected_bg": "#2d3355",
        "task_tools_bg": "#2d3754",
        "task_tools_button": "#222c49",
        "task_tools_border": "#485678",
        "task_edit_bg": "#3a3456",
        "task_edit_fg": "#e7ddff",
        "task_edit_border": "#595078",
        "task_done_bg": "#284a42",
        "task_done_fg": "#bcebd1",
        "task_done_border": "#3d7562",
        "task_focus_bg": "#2c4262",
        "task_focus_fg": "#c8dcff",
        "task_focus_border": "#466991",
        "task_delete_hover": "#613d52",
        "filter_active": "#796db2",
        "delete": "#553647",
        "delete_text": "#ffc4c3",
        "meter_empty": "#46506c",
        "positive_bg": "#263a59",
        "positive_fg": "#d8e9ff",
        "positive_fill": "#a7d4f1",
        "positive_border": "#7896b8",
        "tense_bg": "#2d385b",
        "tense_fg": "#d9dcff",
        "tense_fill": "#a6b5f2",
        "tense_border": "#7e8fc7",
        "angry_bg": "#3c3156",
        "angry_fg": "#eadbff",
        "angry_fill": "#c0a5ed",
        "angry_border": "#9d83cc",
        "deadline_normal_bg": "#2d4563",
        "deadline_normal_fg": "#c5e2ff",
        "deadline_soon_bg": "#373d68",
        "deadline_soon_fg": "#d8dcff",
        "deadline_urgent_bg": "#49365e",
        "deadline_urgent_fg": "#f0d7ff",
        "deadline_overdue_bg": "#4c3038",
        "deadline_overdue_fg": "#ffb2a7",
    },
}


def build_stylesheet(theme: str) -> str:
    """Собрать таблицу стилей выбранной темы."""
    colors = THEMES[theme]
    return f"""
        * {{ font-family: "Comfortaa"; color: {colors['text']}; }}
        QMainWindow#appWindow {{ background: {colors['window']}; }}
        QFrame#appFrame {{ background: {colors['panel']}; border: 2px solid {colors['border']};
            border-radius: 20px; }}
        QWidget#titleBar {{ background: {colors['panel']}; border: none;
            border-bottom: 2px solid {colors['border']}; }}
        QLabel#appTitle {{ color: {colors['heading']}; font-size: 31px; font-weight: 700; }}
        QPushButton#windowButton, QPushButton#closeWindowButton, QPushButton#languageButton {{
            color: {colors['heading']}; background: transparent;
            border: 0; border-radius: 10px; outline: 0; padding: 0; }}
        QPushButton#windowButton:hover, QPushButton#languageButton:hover {{ background: {colors['subtle']}; border: 0; }}
        QPushButton#closeWindowButton:hover {{ background: {colors['angry_bg']}; border: 0; }}
        QWidget#taskPanel, QWidget#petPanel {{ background: {colors['panel']};
            border: 1px solid {colors['border']}; border-radius: 21px; }}
        QLabel#sectionHeading, QLabel#petNameDisplay, QLineEdit#petNameEdit {{ color: {colors['heading']};
            font-size: 32px; font-weight: 900; }}
        QStackedWidget#petNameStack {{ background: transparent; border: none; }}
        QLineEdit#petNameEdit {{ min-height: 50px; padding: 0; border: none;
            background: transparent; selection-background-color: {colors['accent']}; }}
        QLineEdit#petNameEdit:focus {{ border-bottom: 2px solid {colors['accent']}; }}
        QPushButton#restorePetButton {{ color: {colors['heading']}; background: {colors['subtle']};
            border: 1px solid {colors['border']}; border-radius: 16px; font-size: 14px;
            padding: 0 16px; }}
        QPushButton#restorePetButton:hover {{ background: {colors['card']};
            border-color: {colors['accent']}; }}
        QPushButton#filterButton {{ min-height: 44px; padding: 0 15px; color: {colors['muted']};
            background: {colors['subtle']}; border: 1px solid transparent; border-radius: 18px;
            font-size: 16px; font-weight: 400; }}
        QPushButton#filterButton:checked {{ color: {colors['accent_text']}; background: {colors['accent']};
            border-color: transparent; }}
        QPushButton#filterButton:hover {{ border-color: {colors['filter_active']}; }}
        QPushButton#filterButton:checked:hover {{ background: {colors['accent_hover']}; }}
        QPushButton#filterButton:pressed {{ background: {colors['accent_end']}; }}
        QLineEdit#searchTasksInput, QLineEdit#quickAddInput {{ min-height: 44px;
            padding: 0 15px; color: {colors['text']}; background: {colors['input']};
            border: 1px solid {colors['input_border']}; border-radius: 15px; font-size: 16px; }}
        QLineEdit#searchTasksInput:focus, QLineEdit#quickAddInput:focus {{
            border: 2px solid {colors['accent']}; }}
        QFrame#taskRow QLineEdit#taskTitleEdit:focus,
        QFrame#taskRow QPlainTextEdit#taskDescriptionEdit:focus,
        QFrame#taskRow QDateTimeEdit:focus, QComboBox#reminderCombo:focus,
        QComboBox#petBackgroundCombo:focus,
        QSpinBox#focusDurationSpin:focus, QSpinBox#breakDurationSpin:focus {{
            border-color: {colors['accent']}; }}
        QPushButton#selectionModeButton, QPushButton#bulkActionButton,
        QPushButton#undoDeleteButton {{ min-height: 42px; padding: 0 15px;
            color: {colors['heading']}; background: {colors['subtle']};
            border: 1px solid {colors['border']}; border-radius: 15px;
            font-size: 16px; font-weight: 400; }}
        QPushButton#selectionModeButton:hover, QPushButton#bulkActionButton:hover,
        QPushButton#undoDeleteButton:hover {{ border-color: {colors['accent']}; }}
        QPushButton#selectionModeButton:pressed, QPushButton#bulkActionButton:pressed,
        QPushButton#undoDeleteButton:pressed {{ background: {colors['border']}; }}
        QPushButton#selectionModeButton:checked {{ color: {colors['accent_text']};
            background: {colors['accent']}; border-color: transparent; }}
        QPushButton#selectionModeButton:checked:hover {{ background: {colors['accent_hover']}; }}
        QPushButton#finishSelectionButton {{ min-height: 44px; padding: 0 15px;
            color: {colors['accent_text']}; background: {colors['accent']}; border: none;
            border-radius: 15px; font-size: 16px; font-weight: 400; }}
        QPushButton#finishSelectionButton:hover {{ background: {colors['accent_hover']}; }}
        QPushButton#finishSelectionButton:pressed {{ background: {colors['accent_end']}; }}
        QPushButton#quickAddButton {{ min-height: 44px; padding: 0 20px;
            color: {colors['accent_text']}; background: {colors['accent']};
            border: none; border-radius: 17px; font-size: 17px; font-weight: 400; }}
        QPushButton#quickAddButton:hover {{ background: {colors['accent_hover']}; }}
        QPushButton#bulkDeleteButton {{ min-height: 42px; padding: 0 15px;
            color: {colors['delete_text']}; background: {colors['delete']};
            border: 1px solid {colors['border']}; border-radius: 15px;
            font-size: 16px; font-weight: 400; }}
        QPushButton#bulkDeleteButton:disabled {{ color: {colors['muted']}; }}
        QLabel#bulkCountLabel {{ color: {colors['heading']}; font-size: 17px; font-weight: 400; }}
        QFrame#taskRow {{ background: {colors['card']}; border: 1px solid {colors['border']};
            border-radius: 22px; }}
        QFrame#taskRow:hover {{ background: {colors['card_hover']};
            border: 1px solid {colors['accent']}; }}
        QFrame#taskRow[completed="true"] {{ background: {colors['subtle']}; }}
        QFrame#taskRow[selected="true"] {{ background: {colors['selected_bg']};
            border: 2px solid {colors['accent']}; }}
        QLabel#taskTitle {{ color: {colors['text']}; font-size: 24px; font-weight: 700; }}
        QLabel#taskTitle[completed="true"] {{ color: {colors['muted']}; text-decoration: line-through; }}
        QLabel#taskDescription {{ color: {colors['muted']}; font-size: 18px; font-weight: 400; }}
        QFrame#deadlinePill {{ border: none; border-radius: 18px; }}
        QFrame#deadlinePill[tone="normal"] {{ background: {colors['deadline_normal_bg']}; }}
        QFrame#deadlinePill[tone="soon"] {{ background: {colors['deadline_soon_bg']}; }}
        QFrame#deadlinePill[tone="urgent"] {{ background: {colors['deadline_urgent_bg']}; }}
        QFrame#deadlinePill[tone="overdue"] {{ background: {colors['deadline_overdue_bg']}; }}
        QFrame#deadlinePill[tone="completed"] {{ background: {colors['subtle']}; }}
        QLabel#deadlineText {{ font-size: 16px; font-weight: 400; }}
        QLabel#deadlineText[tone="normal"] {{ color: {colors['deadline_normal_fg']}; }}
        QLabel#deadlineText[tone="soon"] {{ color: {colors['deadline_soon_fg']}; }}
        QLabel#deadlineText[tone="urgent"] {{ color: {colors['deadline_urgent_fg']}; }}
        QLabel#deadlineText[tone="overdue"] {{ color: {colors['deadline_overdue_fg']}; }}
        QLabel#deadlineText[tone="completed"] {{ color: {colors['muted']}; }}
        QPushButton#moreButton {{ color: {colors['heading']}; background: transparent;
            border: none; border-radius: 18px; font-size: 30px; font-weight: 400; }}
        QPushButton#moreButton:hover {{ background: {colors['subtle']}; border: none;
            color: {colors['heading']}; }}
        QPushButton#moreButton:pressed {{ background: {colors['border']}; }}
        QPushButton#taskIconButton {{ color: {colors['heading']}; background: {colors['subtle']};
            border: 1px solid {colors['border']}; border-radius: 14px; }}
        QPushButton#taskIconButton:hover {{ background: {colors['card']}; border-color: {colors['accent']}; }}
        QPushButton#addTaskButton {{ min-height: 78px; padding: 0 40px 0 0; color: {colors['accent_text']};
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {colors['accent_start']}, stop:1 {colors['accent_end']});
            border: none; border-radius: 23px; font-size: 21px; font-weight: 400; }}
        QPushButton#addTaskButton:hover {{ background: {colors['accent_hover']}; }}
        QPushButton#addTaskButton:pressed {{ background: {colors['accent_end']}; }}
        QLabel#emptyState {{ color: {colors['muted']}; background: {colors['subtle']};
            border: 1px dashed {colors['border']}; border-radius: 24px;
            padding: 32px; font-size: 21px; }}
        QFrame#moodCard {{ background: {colors['positive_bg']}; border: 3px solid {colors['positive_border']};
            border-radius: 26px; }}
        QLabel#moodTitle {{ font-size: 21px; font-weight: 400; }}
        QLabel#moodHeart {{ background: transparent; }}
        QFrame#moodSegment {{ border-radius: 7px; }}
        QPushButton#toolbarButton {{ color: {colors['heading']}; background: {colors['panel']};
            border: 2px solid {colors['border']}; border-radius: 19px; padding: 0; }}
        QPushButton#toolbarButton:hover {{
            background: {colors['subtle']}; border-color: {colors['accent']}; }}
        QPushButton#toolbarButton:checked {{ background: {colors['subtle']}; border-color: {colors['accent']}; }}
        QPushButton#toolbarButton:pressed {{ background: {colors['border']}; }}
        QFrame#inlineSettingsPanel, QFrame#taskIconChooser {{
            background: {colors['subtle']}; border: 1px solid {colors['border']}; border-radius: 14px; }}
        QLabel#petBackgroundLabel {{ color: {colors['muted']}; font-size: 13px; }}
        QComboBox#petBackgroundCombo {{ min-height: 32px; padding: 0 9px; color: {colors['text']};
            background: {colors['card']}; border: 1px solid {colors['border']}; border-radius: 10px; }}
        QComboBox#petBackgroundCombo::drop-down {{ width: 24px; border: none; }}
        QFrame#inlineTaskTools {{ background: transparent; border: none; }}
        QPushButton#inlineSettingButton, QPushButton#taskActionButton,
        QPushButton#taskEditActionButton, QPushButton#taskDoneActionButton,
        QPushButton#taskFocusActionButton, QPushButton#taskDeleteButton {{ min-height: 34px;
            min-width: 0; padding: 0 8px;
            color: {colors['text']}; background: {colors['task_tools_button']};
            border: 1px solid {colors['task_tools_border']}; border-radius: 11px; font-size: 13px; }}
        QPushButton#inlineSettingButton:hover, QPushButton#taskActionButton:hover,
        QPushButton#taskEditActionButton:hover, QPushButton#taskDoneActionButton:hover,
        QPushButton#taskFocusActionButton:hover, QPushButton#taskDeleteButton:hover {{
            background: {colors['card']}; border-color: {colors['accent']}; }}
        QPushButton#inlineSettingButton:focus, QPushButton#taskActionButton:focus,
        QPushButton#taskEditActionButton:focus, QPushButton#taskDoneActionButton:focus,
        QPushButton#taskFocusActionButton:focus, QPushButton#taskDeleteButton:focus,
        QPushButton#focusPrimaryButton:focus, QPushButton#focusSecondaryButton:focus,
        QPushButton#secondaryButton:focus {{ border-color: {colors['accent']}; }}
        QPushButton#taskDeleteButton {{ color: {colors['delete_text']};
            background: {colors['delete']}; border-color: {colors['delete']}; }}
        QPushButton#taskDeleteButton:hover {{ background: {colors['task_delete_hover']};
            border-color: {colors['delete_text']}; }}
        QPushButton#taskEditActionButton {{ color: {colors['task_edit_fg']};
            background: {colors['task_edit_bg']}; border-color: {colors['task_edit_border']}; }}
        QPushButton#taskEditActionButton:hover {{ background: {colors['task_edit_border']};
            border-color: {colors['task_edit_fg']}; }}
        QPushButton#taskDoneActionButton {{ color: {colors['task_done_fg']};
            background: {colors['task_done_bg']}; border-color: {colors['task_done_border']}; }}
        QPushButton#taskDoneActionButton:hover {{ background: {colors['task_done_border']};
            border-color: {colors['task_done_fg']}; }}
        QPushButton#taskFocusActionButton {{ color: {colors['task_focus_fg']};
            background: {colors['task_focus_bg']}; border-color: {colors['task_focus_border']}; }}
        QPushButton#taskFocusActionButton:hover {{ background: {colors['task_focus_border']};
            border-color: {colors['task_focus_fg']}; }}
        QPushButton#taskEditActionButton:pressed, QPushButton#taskDoneActionButton:pressed,
        QPushButton#taskFocusActionButton:pressed {{ background: {colors['task_tools_border']}; }}
        QPushButton#taskDeleteButton:pressed {{ background: {colors['task_delete_hover']}; }}
        QPushButton#inlineSettingButton:checked {{ color: {colors['accent_text']};
            background: {colors['accent']}; border-color: {colors['accent']}; }}
        QPushButton#taskIconChoiceButton {{ padding: 4px; background: {colors['panel']};
            border: 1px solid {colors['border']}; border-radius: 10px; }}
        QPushButton#taskIconChoiceButton[selected="true"] {{
            background: {colors['accent']}; border-color: {colors['accent']}; }}
        QPushButton#taskIconChoiceButton:hover {{ border-color: {colors['accent']}; }}
        QFrame#focusTimerPanel {{ background: {colors['subtle']}; border: 1px solid {colors['border']};
            border-radius: 24px; }}
        QLabel#focusEyebrow {{ color: {colors['accent']}; font-size: 15px; font-weight: 700; }}
        QLabel#focusTaskTitle {{ color: {colors['heading']}; font-size: 24px; font-weight: 700; }}
        QLabel#focusTime {{ color: {colors['heading']}; font-size: 60px; font-weight: 700; }}
        QLabel#focusHint {{ color: {colors['muted']}; font-size: 15px; }}
        QFrame#focusProgressTrack {{ background: {colors['border']}; border: none; border-radius: 5px; }}
        QFrame#focusProgressFill {{ background: {colors['accent']}; border: none; border-radius: 5px; }}
        QPushButton#focusPrimaryButton {{ min-height: 42px; padding: 0 16px; color: {colors['accent_text']};
            background: {colors['accent']}; border: none; border-radius: 14px; font-size: 15px; }}
        QPushButton#focusPrimaryButton:hover {{ background: {colors['accent_hover']}; }}
        QPushButton#focusSecondaryButton {{ min-height: 42px; padding: 0 14px; color: {colors['text']};
            background: {colors['panel']}; border: 1px solid {colors['border']};
            border-radius: 14px; font-size: 15px; }}
        QPushButton#focusSecondaryButton:hover {{ border-color: {colors['accent']}; }}
        QSpinBox#focusDurationSpin, QSpinBox#breakDurationSpin {{ min-height: 38px; padding: 0 10px;
            color: {colors['text']}; background: {colors['input']};
            border: 1px solid {colors['input_border']}; border-radius: 12px; font-size: 15px; }}
        QFrame#taskRow QLineEdit#taskTitleEdit, QFrame#taskRow QPlainTextEdit#taskDescriptionEdit,
        QFrame#taskRow QDateTimeEdit {{ color: {colors['text']}; background: {colors['input']};
            border: 1px solid {colors['input_border']}; border-radius: 15px; padding: 11px 14px;
            font-size: 18px; }}
        QPlainTextEdit#taskDescriptionEdit {{ min-height: 54px; }}
        QDateTimeEdit#deadlineEdit {{ min-height: 42px; }}
        QComboBox#reminderCombo {{ min-height: 40px; padding: 0 12px; color: {colors['text']};
            background: {colors['input']}; border: 1px solid {colors['input_border']};
            border-radius: 14px; font-size: 16px; }}
        QComboBox#reminderCombo::drop-down {{ width: 28px; border: none; }}
        QLabel#reminderLabel {{ color: {colors['muted']}; font-size: 16px; font-weight: 400; }}
        QDateTimeEdit::drop-down {{ width: 30px; border: none; }}
        QPushButton#saveEditButton {{ min-height: 46px; padding: 0 20px; color: {colors['accent_text']};
            background: {colors['accent']}; border: none; border-radius: 14px; font-size: 17px; font-weight: 400; }}
        QPushButton#saveEditButton:hover {{ background: {colors['accent_hover']}; }}
        QPushButton#saveEditButton:pressed {{ background: {colors['accent_end']}; }}
        QPushButton#secondaryButton {{ min-height: 46px; padding: 0 20px; color: {colors['text']};
            background: {colors['subtle']}; border: 1px solid {colors['border']}; border-radius: 14px;
            font-size: 16px; font-weight: 400; }}
        QPushButton#secondaryButton:hover {{ background: {colors['card']}; border-color: {colors['accent']}; }}
        QPushButton#secondaryButton:pressed {{ background: {colors['border']}; }}
        /* Keep the deadline and all editor actions readable in one row. */
        QFrame#taskRow QPushButton#saveEditButton,
        QFrame#taskRow QPushButton#secondaryButton {{ padding-left: 9px; padding-right: 9px; }}
        QCheckBox {{ padding: 0; margin: 0; spacing: 0; }}
        QCheckBox::indicator {{ width: 30px; height: 30px; border: 3px solid {colors['muted']};
            border-radius: 12px; background: {colors['card']}; }}
        QCheckBox::indicator:checked {{ background: {colors['accent']}; border-color: {colors['accent']};
            image: url("{(__import__('pathlib').Path(__file__).resolve().parent.parent / 'assets' / 'icons' / 'check.svg').as_posix()}"); }}
        /* Breakpoints are driven by the available main-window width. */
        QMainWindow#appWindow[compact="true"] QLabel#appTitle {{ font-size: 25px; }}
        QMainWindow#appWindow[compact="true"] QLabel#sectionHeading,
        QMainWindow#appWindow[compact="true"] QLabel#petNameDisplay,
        QMainWindow#appWindow[compact="true"] QLineEdit#petNameEdit {{ font-size: 24px; min-height: 38px; }}
        QMainWindow#appWindow[compact="true"] QLabel#focusTime {{ font-size: 48px; }}
        QMainWindow#appWindow[compact="true"] QLabel#focusTaskTitle {{ font-size: 20px; }}
        QMainWindow#appWindow[compact="true"] QPushButton#filterButton {{
            min-height: 36px; padding: 0 10px; border-radius: 13px; font-size: 13px; }}
        QMainWindow#appWindow[compact="true"] QPushButton#restorePetButton {{ font-size: 13px; padding: 0 12px; }}
        QMainWindow#appWindow[compact="true"] QLineEdit#searchTasksInput,
        QMainWindow#appWindow[compact="true"] QLineEdit#quickAddInput {{ min-height: 38px; font-size: 14px; }}
        QMainWindow#appWindow[compact="true"] QPushButton#selectionModeButton,
        QMainWindow#appWindow[compact="true"] QPushButton#quickAddButton,
        QMainWindow#appWindow[compact="true"] QPushButton#bulkActionButton,
        QMainWindow#appWindow[compact="true"] QPushButton#finishSelectionButton,
        QMainWindow#appWindow[compact="true"] QPushButton#bulkDeleteButton {{ font-size: 13px; padding: 0 10px; }}
        QMainWindow#appWindow[compact="true"] QLabel#taskTitle {{ font-size: 20px; font-weight: 700; }}
        QMainWindow#appWindow[compact="true"] QLabel#taskDescription {{ font-size: 15px; }}
        QMainWindow#appWindow[compact="true"] QLabel#deadlineText {{ font-size: 13px; }}
        QMainWindow#appWindow[compact="true"] QPushButton#addTaskButton {{
            min-height: 64px; font-size: 18px; border-radius: 19px; }}
        QMainWindow#appWindow[compact="true"] QLabel#moodTitle {{ font-size: 17px; }}
        QMainWindow#appWindow[compact="true"] QFrame#moodCard {{ border-radius: 21px; }}
        QMainWindow#appWindow[compact="true"] QCheckBox::indicator {{ width: 22px; height: 22px;
            border-width: 2px; border-radius: 8px; }}
        QMainWindow#appWindow[compact="true"] QFrame#taskRow QLineEdit#taskTitleEdit,
        QMainWindow#appWindow[compact="true"] QFrame#taskRow QPlainTextEdit#taskDescriptionEdit,
        QMainWindow#appWindow[compact="true"] QFrame#taskRow QDateTimeEdit {{ font-size: 14px; padding: 7px 9px; }}
        QMainWindow#appWindow[compact="true"] QComboBox#reminderCombo {{ font-size: 13px; }}
        QMainWindow#appWindow[compact="true"] QLabel#reminderLabel {{ font-size: 13px; }}
        QMainWindow#appWindow[compact="true"] QLabel#emptyState {{ padding: 16px; font-size: 15px; }}
        QMainWindow#appWindow[compact="true"] QPushButton#saveEditButton,
        QMainWindow#appWindow[compact="true"] QPushButton#secondaryButton {{ min-height: 36px;
            font-size: 12px; padding: 0 8px; }}
        QMainWindow#appWindow[tiny="true"] QLabel#appTitle {{ font-size: 19px; }}
        QMainWindow#appWindow[tiny="true"] QLabel#sectionHeading,
        QMainWindow#appWindow[tiny="true"] QLabel#petNameDisplay,
        QMainWindow#appWindow[tiny="true"] QLineEdit#petNameEdit {{ font-size: 18px; min-height: 30px; }}
        QMainWindow#appWindow[tiny="true"] QLabel#focusTime {{ font-size: 38px; }}
        QMainWindow#appWindow[tiny="true"] QLabel#focusTaskTitle {{ font-size: 17px; }}
        QMainWindow#appWindow[tiny="true"] QPushButton#filterButton {{
            min-height: 30px; padding: 0 7px; border-radius: 11px; font-size: 11px; }}
        QMainWindow#appWindow[tiny="true"] QPushButton#restorePetButton {{ font-size: 12px; padding: 0 9px; }}
        QMainWindow#appWindow[tiny="true"] QLineEdit#searchTasksInput,
        QMainWindow#appWindow[tiny="true"] QLineEdit#quickAddInput {{ min-height: 32px;
            padding: 0 9px; font-size: 12px; }}
        QMainWindow#appWindow[tiny="true"] QPushButton#selectionModeButton,
        QMainWindow#appWindow[tiny="true"] QPushButton#quickAddButton,
        QMainWindow#appWindow[tiny="true"] QPushButton#bulkActionButton,
        QMainWindow#appWindow[tiny="true"] QPushButton#finishSelectionButton,
        QMainWindow#appWindow[tiny="true"] QPushButton#bulkDeleteButton {{ min-height: 30px;
            font-size: 11px; padding: 0 7px; }}
        QMainWindow#appWindow[tiny="true"] QLabel#taskTitle {{ font-size: 16px; font-weight: 700; }}
        QMainWindow#appWindow[tiny="true"] QLabel#taskDescription {{ font-size: 12px; }}
        QMainWindow#appWindow[tiny="true"] QLabel#deadlineText {{ font-size: 11px; }}
        QMainWindow#appWindow[tiny="true"] QPushButton#addTaskButton {{
            min-height: 54px; font-size: 15px; border-radius: 16px; }}
        QMainWindow#appWindow[tiny="true"] QLabel#moodTitle {{ font-size: 14px; }}
        QMainWindow#appWindow[tiny="true"] QFrame#moodCard {{ border-radius: 16px; border-width: 2px; }}
        QMainWindow#appWindow[tiny="true"] QCheckBox::indicator {{ width: 18px; height: 18px;
            border-width: 2px; border-radius: 7px; }}
        QMainWindow#appWindow[tiny="true"] QFrame#taskRow QLineEdit#taskTitleEdit,
        QMainWindow#appWindow[tiny="true"] QFrame#taskRow QPlainTextEdit#taskDescriptionEdit,
        QMainWindow#appWindow[tiny="true"] QFrame#taskRow QDateTimeEdit {{ font-size: 12px; padding: 5px 6px; }}
        QMainWindow#appWindow[tiny="true"] QComboBox#reminderCombo {{ min-height: 32px; font-size: 11px; }}
        QMainWindow#appWindow[tiny="true"] QLabel#reminderLabel {{ font-size: 11px; }}
        QMainWindow#appWindow[tiny="true"] QLabel#emptyState {{ padding: 9px; font-size: 12px; }}
        QMainWindow#appWindow[tiny="true"] QPushButton#saveEditButton,
        QMainWindow#appWindow[tiny="true"] QPushButton#secondaryButton {{ min-height: 30px;
            font-size: 10px; padding: 0 5px; }}
        QScrollArea, QWidget#taskListContent {{ border: none; background: transparent; }}
        QScrollBar:vertical {{ width: 10px; background: transparent; margin: 3px; }}
        QScrollBar::handle:vertical {{ background: {colors['border']}; border-radius: 5px; min-height: 38px; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QMenu {{ color: {colors['text']}; background: {colors['panel']}; border: 1px solid {colors['border']};
            border-radius: 15px; padding: 8px; font-size: 16px; }}
        QMenu::item {{ padding: 10px 24px 10px 14px; border-radius: 9px; }}
        QMenu::item:selected {{ background: {colors['subtle']}; }}
        QMenu::separator {{ height: 1px; background: {colors['border']}; margin: 5px 8px; }}
        QStatusBar {{ background: {colors['panel']}; color: {colors['muted']}; }}
        QToolTip {{ color: {colors['text']}; background: {colors['panel']};
            border: 1px solid {colors['border']}; padding: 7px 10px; border-radius: 7px; }}
        QSplitter::handle {{ background: transparent; width: 10px; }}
    """
