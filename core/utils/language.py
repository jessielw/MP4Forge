import re

from iso639 import Language, LanguageNotFoundError
from pymediainfo import Track


def get_language_mi(media_track: Track, char_code: int = 1) -> str | None:
    """Used to properly detect the input language from pymediainfo track

    Args:
        media_track (Track): pymediainfo track
        char_code (int, optional): 1 or 2, if set to 2 it returns 'en' else if 3 it returns 'eng'
    """
    if char_code not in {1, 2}:
        raise ValueError("Input must be (int) 1 or 2")

    if media_track.language:
        try:
            if char_code == 1:
                return str(Language.match(media_track.language).part1).upper()
            elif char_code == 2:
                return str(Language.match(media_track.language).part2b).upper()
        except LanguageNotFoundError:
            if media_track.other_language:
                for track in media_track.other_language:
                    try:
                        if char_code == 1:
                            return str(Language.match(track).part1).upper()
                        elif char_code == 2:
                            return str(Language.match(track).part2b).upper()
                    except LanguageNotFoundError:
                        try:
                            if char_code == 1:
                                return str(
                                    Language.match(track.split(" ")[0]).part1
                                ).upper()
                            elif char_code == 2:
                                return str(
                                    Language.match(track.split(" ")[0]).part2b
                                ).upper()
                        except LanguageNotFoundError:
                            continue
    return None


def get_language_str(language_str: str, char_code: int = 1) -> str | None:
    """Used to properly detect the input language from input string

    Args:
        language_str (str): Language input string
        char_code (int, optional): 1 or 2, if set to 2 it returns 'en' else if 3 it returns 'eng'
    """
    if char_code not in {1, 2}:
        raise ValueError("Input must be (int) 1 or 2")

    if language_str:
        try:
            if char_code == 1:
                return str(Language.match(language_str).part1).upper()
            elif char_code == 2:
                return str(Language.match(language_str).part2b).upper()
        except LanguageNotFoundError:
            return None
    return None


def get_full_language_str(language_str: str) -> str | None:
    """Used to properly detect the input language from input string

    Args:
        language_str (str): Language input string
    """
    if language_str:
        try:
            return str(Language.match(language_str.lower()).name)
        except LanguageNotFoundError:
            return None
    return None


def get_language_obj(language_str: str) -> Language | None:
    """Used to properly detect the input language from input string

    Args:
        language_str (str): Language input string
    """
    if language_str:
        try:
            return Language.match(language_str.lower())
        except LanguageNotFoundError:
            return None
    return None


def detect_language_from_filename(filename: str) -> Language | None:
    """Detect language code from filename by searching for common patterns.

    Looks for ISO 639-1 (2-letter), ISO 639-2 (3-letter), and common language names.
    Prioritizes: naturally lowercase > naturally UPPERCASE > mixed case words

    Args:
        filename (str): The filename to search for language codes

    Returns:
        Language | None: Matched Language object or None
    """
    # remove extension but keep original case
    name_no_ext = filename.rsplit(".", 1)[0]

    # common patterns: "movie.eng.srt", "movie_eng_sub.srt", "movie.en.srt", etc.
    # look for word boundaries or underscores/dots around language codes
    patterns = [
        r"[._-]([a-zA-Z]{2,3})[._-]",  # .eng. or _en_ or -jpn-
        r"[._-]([a-zA-Z]{2,3})$",  # .eng or _en at end
        r"^([a-zA-Z]{2,3})[._-]",  # eng. or en_ at start
    ]

    # collect all candidates with their case type
    candidates = []
    for pattern in patterns:
        matches = re.finditer(pattern, name_no_ext)
        for match in matches:
            lang_code = match.group(1)
            # determine case type for priority
            if lang_code.islower():
                priority = 0  # highest priority
            elif lang_code.isupper():
                priority = 1  # medium priority
            else:
                priority = 2  # lowest priority (mixed case)
            candidates.append((priority, lang_code))

    # sort by priority (lower number = higher priority)
    candidates.sort(key=lambda x: x[0])

    # try to match in priority order
    for _, lang_code in candidates:
        try:
            return Language.match(lang_code.lower())
        except LanguageNotFoundError:
            continue

    return None
