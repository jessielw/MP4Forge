import iso639
from PySide6.QtWidgets import QWidget

from frontend_desktop.widgets.combo_box import CustomComboBox

# cache to ensure we only build the language list once
_languages_cache = []


def get_language_combo_box(parent: QWidget | None = None) -> CustomComboBox:
    """Creates and returns a language selection combo box."""
    lang_combo = CustomComboBox(
        completer=True, completer_strict=True, max_items=15, parent=parent
    )

    if not _languages_cache:
        for lang in iso639.ALL_LANGUAGES:
            lang_code = (lang.part3 or lang.part2t or lang.part2b or lang.part1) or None
            name = lang.name
            if name and lang_code:
                _languages_cache.append((lang_code, name))

        # sort by language name
        _languages_cache.sort(key=lambda x: x[1])

    # update combo box
    lang_combo.addItem("", None)
    for lang in _languages_cache:
        lang_combo.addItem(lang[1], lang[0])

    return lang_combo
