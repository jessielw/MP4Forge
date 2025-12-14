from PySide6.QtCore import QObject, Signal


class GlobalSignals(QObject):
    """Singleton used to keep up with global signals"""

    _instance = None

    ########### SIGNALS ###########
    # main window
    main_window_set_disabled = Signal(bool)
    main_window_update_status_tip = Signal(str, int)  # message, timeout[milliseconds]
    main_window_clear_status_tip = Signal()
    # main_window_hide = Signal(bool)
    main_window_progress_bar_busy = Signal(bool)

    # chapters
    chapters_updated = Signal(str)

    # video audio tracks
    video_audio_tracks_detected = Signal(
        object, object, list
    )  # MediaInfo, Path, selected_track_ids

    # video subtitle tracks
    video_subtitle_tracks_detected = Signal(
        object, object, list
    )  # MediaInfo, Path, selected_track_ids

    # video generate output filepath
    video_generate_output_filepath = Signal(object)  # suggested Path

    # tab loaded
    tab_loaded = Signal()

    # scaling # TODO: add this feature in
    # scale_factor_changed_by_user = Signal(float)  # user hotkey changes (auto-save)
    # scale_factor_changed = Signal(float)  # all changes (UI sync)
    # scale_factor_set_from_settings = Signal(float)  # settings UI changes (no auto-save)

    # settings
    ########### SIGNALS ###########

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, parent=None) -> None:
        # ensure we've only initialized once
        if not hasattr(self, "_initialized"):
            super().__init__(parent)
            self._initialized = True


# alias to shorted class name
GSigs = GlobalSignals
