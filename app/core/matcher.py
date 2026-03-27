from rapidfuzz import fuzz

from app.core.normalizer import normalize_name



def name_similarity(name_a: str, name_b: str) -> float:
    normalized_a = normalize_name(name_a)
    normalized_b = normalize_name(name_b)

    if not normalized_a or not normalized_b:
        return 0.0

    return float(fuzz.token_sort_ratio(normalized_a, normalized_b))
