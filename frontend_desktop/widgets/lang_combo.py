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
            name = lang.name
            if name:
                _languages_cache.append((lang, name))

        # sort by language name
        _languages_cache.sort(key=lambda x: x[1])

    # update combo box
    lang_combo.addItem("", None)
    for lang_obj, lang_name in _languages_cache:
        lang_combo.addItem(lang_name, lang_obj)

    return lang_combo
