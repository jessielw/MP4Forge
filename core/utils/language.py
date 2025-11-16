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
