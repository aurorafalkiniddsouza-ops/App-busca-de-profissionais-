from app.core.matcher import name_similarity



def test_name_similarity_returns_high_score_for_equivalent_names():
    assert name_similarity("José da Silva", "Jose da Silva") >= 95
