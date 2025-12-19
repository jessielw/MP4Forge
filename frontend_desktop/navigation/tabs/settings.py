import platform

from PySide6.QtCore import QSize, Qt, Slot
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core.config import Conf
from core.logger import LOG, LogLevel
from frontend_desktop.global_signals import GSigs
from frontend_desktop.utils.file_utils import open_explorer
from frontend_desktop.widgets.combo_box import CustomComboBox
from frontend_desktop.widgets.preset_title_editor import PresetTitleEditor
from frontend_desktop.widgets.qtawesome_theme_swapper import QTAThemeSwap
from frontend_desktop.widgets.utils import build_h_line


class GeneralSettingsTab(QWidget):
    """General settings tab with scrollable content."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # create scroll area
        scroll_area = QScrollArea(self, widgetResizable=True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # create content widget
        content_widget = QWidget()

        # listen for preset title updates from other tabs
        GSigs().preset_titles_updated.connect(self._reload_preset_editors)

        ######### ui elements #########
        # theme selection
        theme_lbl = QLabel("Theme", content_widget)
        self.theme_combo = CustomComboBox(
            disable_mouse_wheel=True, parent=content_widget
        )
        self.theme_combo.addItems(("Auto", "Light", "Dark"))
        self.theme_combo.setCurrentText(Conf.theme)
        self.theme_combo.currentIndexChanged.connect(self._change_theme)

        # log level selection
        log_level_lbl = QLabel("Log Level", content_widget)
        self.log_level_combo = CustomComboBox(
            disable_mouse_wheel=True, parent=content_widget
        )
        for level in LogLevel:
            self.log_level_combo.addItem(str(level), level)
        self.log_level_combo.setCurrentText(str(Conf.log_level))

        # log level see directory button
        self.log_level_open_dir_btn = QToolButton(content_widget)
        self.log_level_open_dir_btn.setToolTip("Open Log Directory")
        QTAThemeSwap().register(self.log_level_open_dir_btn, "ph.eye", QSize(20, 20))
        self.log_level_open_dir_btn.clicked.connect(self._open_log_directory)

        # log level combo + open dir layout
        log_level_layout = QHBoxLayout()
        log_level_layout.addWidget(self.log_level_combo, stretch=1)
        log_level_layout.addWidget(self.log_level_open_dir_btn)

        # mp4box path
        mp4box_lbl = QLabel("Mp4Box Path", content_widget)
        self.mp4box_line_edit = QLineEdit(content_widget, readOnly=True)
        self.mp4box_line_edit.setText(Conf.mp4box_path)
        mp4box_btn = QToolButton(content_widget)
        QTAThemeSwap().register(mp4box_btn, "ph.file-arrow-up", QSize(20, 20))
        mp4box_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        mp4box_btn.clicked.connect(self._browse_mp4box)

        # mp4box path layout
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.mp4box_line_edit)
        path_layout.addWidget(mp4box_btn)

        # audio preset titles
        audio_titles_lbl = QLabel("Audio Preset Titles", content_widget)
        audio_titles_desc = QLabel(
            "<i>Quick-access titles for audio tracks (e.g., 'Commentary', 'Director's Commentary')</i>",
            content_widget,
            wordWrap=True,
        )
        audio_titles_desc.setDisabled(True)
        self.audio_titles_editor = PresetTitleEditor(content_widget)
        self.audio_titles_editor.set_titles(Conf.audio_preset_titles)
        self.audio_titles_editor.setMinimumHeight(200)

        # subtitle preset titles
        subtitle_titles_lbl = QLabel("Subtitle Preset Titles", content_widget)
        subtitle_titles_desc = QLabel(
            "<i>Quick-access titles for subtitle tracks (e.g., 'SDH', 'Forced', 'Signs & Songs')</i>",
            content_widget,
            wordWrap=True,
        )
        subtitle_titles_desc.setDisabled(True)
        self.subtitle_titles_editor = PresetTitleEditor(content_widget)
        self.subtitle_titles_editor.set_titles(Conf.subtitle_preset_titles)
        self.subtitle_titles_editor.setMinimumHeight(200)
        ######### ui elements #########

        # content layout
        content_layout = QVBoxLayout(content_widget)
        content_layout.addWidget(theme_lbl)
        content_layout.addWidget(self.theme_combo)
        content_layout.addWidget(log_level_lbl)
        content_layout.addLayout(log_level_layout)
        content_layout.addWidget(mp4box_lbl)
        content_layout.addLayout(path_layout)
        content_layout.addWidget(build_h_line((10, 10, 10, 10)))
        content_layout.addWidget(audio_titles_lbl)
        content_layout.addWidget(audio_titles_desc)
        content_layout.addWidget(self.audio_titles_editor)
        content_layout.addWidget(build_h_line((10, 10, 10, 10)))
        content_layout.addWidget(subtitle_titles_lbl)
        content_layout.addWidget(subtitle_titles_desc)
        content_layout.addWidget(self.subtitle_titles_editor)
        content_layout.addStretch()

        # set content widget in scroll area
        scroll_area.setWidget(content_widget)

        # save button (outside scroll area, bottom right)
        self.save_btn = QPushButton("Save Settings", self)
        self.save_btn.clicked.connect(self._save_settings)

        # main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(scroll_area)
        self.main_layout.addWidget(self.save_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self.main_layout.addSpacing(6)

    @Slot(int)
    def _change_theme(self, _: int | None = None) -> None:
        """
        For what ever reason ```QApplication.instance()``` doesn't type hint correctly so we
        can ignore these errors for now.
        """
        app = QApplication.instance()
        get_theme = self.theme_combo.currentText()
        if get_theme != "Auto":
            app.styleHints().setColorScheme(  # pyright: ignore [reportAttributeAccessIssue, reportOptionalMemberAccess]
                Qt.ColorScheme.Light if get_theme == "Light" else Qt.ColorScheme.Dark
            )
        else:
            app.styleHints().unsetColorScheme()  # pyright: ignore [reportAttributeAccessIssue, reportOptionalMemberAccess]

    @Slot()
    def _open_log_directory(self) -> None:
        """Open the log directory in the system file explorer"""
        log_dir = LOG.log_file.parent
        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)
        open_explorer(log_dir)

    @Slot()
    def _browse_mp4box(self) -> None:
        """Browse for MP4Box executable"""
        is_windows = platform.system() == "Windows"
        file_filter = "Mp4Box (mp4box.exe)" if is_windows else "Mp4Box (mp4box)"

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select MP4Box Executable",
            "",
            file_filter,
        )
        if file_path:
            self.mp4box_line_edit.setText(file_path)

    @Slot()
    def _save_settings(self) -> None:
        """Save all settings to config"""
        Conf.theme = self.theme_combo.currentText()
        Conf.log_level = self.log_level_combo.currentData()
        Conf.mp4box_path = self.mp4box_line_edit.text()
        Conf.audio_preset_titles = self.audio_titles_editor.get_titles()
        Conf.subtitle_preset_titles = self.subtitle_titles_editor.get_titles()
        Conf.save()

        # notify tabs to reload preset titles
        GSigs().preset_titles_updated.emit()

    @Slot()
    def _reload_preset_editors(self) -> None:
        """Reload preset title editors from config (when updated from other tabs)"""
        self.audio_titles_editor.set_titles(Conf.audio_preset_titles)
        self.subtitle_titles_editor.set_titles(Conf.subtitle_preset_titles)
        GSigs().main_window_update_status_tip.emit("Settings saved successfully", 2000)


class AboutTab(QWidget):
    """About tab with scrollable content."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # create scroll area
        scroll_area = QScrollArea(self, widgetResizable=True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # create content widget
        content_widget = QWidget()

        ####### UI elements #######
        app_info_lbl = QLabel(
            f"""<h2 style="text-align: center;">Mp4Forge</h2>
            <span style="font-weight: bold;">Version:</span> {Conf.version}<br>
            <span style="font-weight: bold;">Homepage:</span><a href="https://github.com/jessielw/MP4Forge">
                https://github.com/jessielw/MP4Forge</a><br>
            <span style="font-weight: bold;">Help:</span> <a href="https://github.com/jessielw/MP4Forge/issues">
                https://github.com/jessielw/MP4Forge/issues</a>""",
            content_widget,
            wordWrap=True,
            openExternalLinks=True,
        )
        ####### UI elements #######

        # content layout
        content_layout = QVBoxLayout(content_widget)
        content_layout.addWidget(app_info_lbl)
        content_layout.addStretch()

        # set content widget in scroll area
        scroll_area.setWidget(content_widget)

        # main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(scroll_area)


class SettingsTab(QWidget):
    """Main settings tab with notebook interface."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # create tab widget
        self.tab_widget = QTabWidget(self)

        # create tabs
        self.general_settings_tab = GeneralSettingsTab(self)
        self.about_tab = AboutTab(self)

        # add tabs to widget
        self.tab_widget.addTab(self.general_settings_tab, "General")
        self.tab_widget.addTab(self.about_tab, "About")

        # main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.tab_widget)
