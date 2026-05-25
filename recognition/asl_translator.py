ASL_MAP = {
    "FIST": "A",
    "A (FIST)": "A",
    "OPEN HAND": "B",
    "B": "B",
    "L": "L",
    "Y": "Y",
    "THUMB": "Y",
    "PINKY": "I",
    "I": "I",
    "PEACE": "V",
}


def translate_gesture(gesture: str) -> str:
    """Translate a gesture label into an ASL letter.

    Returns empty string when no mapping is available.
    """
    if not gesture:
        return ""

    # Direct lookup first
    letter = ASL_MAP.get(gesture)
    if letter:
        return letter

    # Some gesture names include annotations, try substring matches
    g = gesture.upper()
    if "FIST" in g:
        return "A"
    if g == "OPEN HAND" or g == "B":
        return "B"
    if "PEACE" in g:
        return "V"

    return ""
