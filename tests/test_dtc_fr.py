from valise_diag import dtc_fr


def test_known_code_returns_french_translation():
    assert dtc_fr.decrire("P0301") == "Raté d'allumage détecté, cylindre 1"


def test_unknown_code_falls_back_to_original_description():
    assert dtc_fr.decrire("P9999", "Some English description") == "Some English description"


def test_unknown_code_without_description_gives_generic_message():
    assert "non répertorié" in dtc_fr.decrire("P9999", "")
