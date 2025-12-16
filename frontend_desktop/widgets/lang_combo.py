import iso639
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QWidget

from frontend_desktop.widgets.combo_box import CustomComboBox

COMMON_LANGUAGES = [
    "eng",  # English
    "jpn",  # Japanese
    "spa",  # Spanish
    "fra",  # French
    "deu",  # German
    "ita",  # Italian
    "por",  # Portuguese
    "rus",  # Russian
    "chi",  # Chinese
    "kor",  # Korean
    "ara",  # Arabic
    "hin",  # Hindi
]

# cache to ensure we only build the language list once
_languages_cache: list[list[tuple[iso639.Language | None, str]]] = [[]]


def get_language_combo_box(parent: QWidget | None = None) -> CustomComboBox:
    """Creates and returns a language selection combo box."""
    lang_combo = CustomComboBox(
        completer=True,
        completer_strict=True,
        max_items=15,
        disable_mouse_wheel=True,
        parent=parent,
    )

    if not _languages_cache[0]:
        # build common languages first
        common_langs = []
        common_codes_set = set(COMMON_LANGUAGES)

        for lang in iso639.ALL_LANGUAGES:
            name = lang.name
            if name and lang.part3 and lang.part3 in common_codes_set:
                common_langs.append((lang, name))

        # sort common languages by the order defined in COMMON_LANGUAGES
        def get_common_index(lang_tuple) -> int:
            lang_obj = lang_tuple[0]
            if lang_obj.part3 and lang_obj.part3 in COMMON_LANGUAGES:
                return COMMON_LANGUAGES.index(lang_obj.part3)
            return 999

        common_langs.sort(key=get_common_index)

        # build remaining languages (alphabetically)
        other_langs = []
        for lang in iso639.ALL_LANGUAGES:
            name = lang.name
            if name:
                is_common = lang.part3 and lang.part3 in common_codes_set
                if not is_common:
                    other_langs.append((lang, name))

        # sort other languages alphabetically
        other_langs.sort(key=lambda x: x[1])

        # combine: common languages + separator + other languages
        _languages_cache[0] = common_langs + [(None, "─────────")] + other_langs

    # update combo box
    lang_combo.addItem("", None)
    for lang_obj, lang_name in _languages_cache[0]:
        if lang_obj is None:
            # add separator as disabled item
            lang_combo.addItem(lang_name, None)
            # make separator non-selectable
            model = lang_combo.model()
            if isinstance(model, QStandardItemModel):
                item = model.item(lang_combo.count() - 1)
                if item:
                    # clear the enabled and selectable flags
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
        else:
            lang_combo.addItem(lang_name, lang_obj)

    return lang_combo
