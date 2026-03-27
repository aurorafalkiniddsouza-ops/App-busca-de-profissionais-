from app.core.classifier import classify_status



def test_classify_status_active():
    assert classify_status("Ativa") == "ATIVO"



def test_classify_status_inactive():
    assert classify_status("Cancelado") == "INATIVO"
