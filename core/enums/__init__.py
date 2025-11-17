from enum import Enum, StrEnum


def _missing_func(cls, value):
    """Helper function to check member/value for a match."""
    if value is None:
        return

    value_str = str(value).lower() if isinstance(value, str) else value

    for member in cls:
        member_name = member.name.lower()
        member_value = member.value

        # compare member name (case-insensitive)
        if isinstance(value, str):
            if member_name == value_str or member_name.replace("_", " ") == value_str:
                return member

        # compare member value
        if isinstance(member_value, str) and isinstance(value, str):
            member_value_lower = member_value.lower()
            if (
                member_value_lower == value_str
                or member_value_lower.replace("_", " ") == value_str
            ):
                return member
        elif member_value == value:
            return member


class CaseInsensitiveEnum(Enum):
    """Case insensitive Enum that will attempt to match on both the value and member."""

    @classmethod
    def _missing_(cls, value):
        """Override this method to ignore case sensitivity"""
        missing = _missing_func(cls, value)
        if missing:
            return missing
        raise ValueError(f"No {cls.__name__} member with value '{value}'")


class CaseInsensitiveStrEnum(StrEnum):
    """Case insensitive StrEnum that will attempt to match on both the value and member."""

    @classmethod
    def _missing_(cls, value):
        """Override this method to ignore case sensitivity"""
        missing = _missing_func(cls, value)
        if missing:
            return missing
        raise ValueError(f"No {cls.__name__} member with value '{value}'")
