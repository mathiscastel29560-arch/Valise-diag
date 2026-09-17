from valise_diag.config import VEILLE_TYPES
from valise_diag.screensaver import _choisir_effet


def test_voiture_fait_partie_des_types_de_veille():
    assert "voiture" in VEILLE_TYPES


def test_choisir_effet_respecte_un_type_explicite():
    for type_veille in ("matrix", "citations", "glitch", "voiture"):
        assert _choisir_effet(type_veille) == type_veille


def test_choisir_effet_aleatoire_renvoie_un_type_connu():
    for _ in range(20):
        assert _choisir_effet("aleatoire") in ("matrix", "citations", "glitch", "voiture")
