import re
import unicodedata


def normalize_name(name: str) -> str:
    if not name:
        return ""

    text = unicodedata.normalize("NFKD", name)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.upper().strip()
    text = re.sub(r"\s+", " ", text)
    return text
