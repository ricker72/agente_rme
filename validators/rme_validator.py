import re

FORBIDDEN_PATTERNS = [
    r"Map\.addItem",
    r"Map\.addCreature",
    r"Map\.addNpc",
    r"Map\.setTile",
    r"(?<!setCamera)Position\s*\(",
    r"Game\.createTile",
]


class RMEValidationError(Exception):
    pass


def validate(lua_text: str) -> bool:
    errors = []

    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, lua_text):
            errors.append(pattern)

    if errors:
        raise RMEValidationError("Forbidden APIs detected:\n" + "\n".join(errors))

    return True
