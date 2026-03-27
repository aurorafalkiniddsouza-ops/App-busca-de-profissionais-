from app.core.normalizer import normalize_name



def test_normalize_name_removes_accents_and_extra_spaces():
    assert normalize_name("  José   da   Silva ") == "JOSE DA SILVA"
