from app.core.normalizer import normalize_name


NEGATIVE_TERMS = [
    "INATIV",
    "CANCEL",
    "BAIXAD",
    "SUSPENS",
    "VENCID",
    "IRREGULAR",
]



def classify_status(status_text: str | None) -> str:
    if not status_text:
        return "REVISAR"

    normalized = normalize_name(status_text)

    if "ATIV" in normalized:
        return "ATIVO"

    if any(term in normalized for term in NEGATIVE_TERMS):
        return "INATIVO"

    return "REVISAR"
