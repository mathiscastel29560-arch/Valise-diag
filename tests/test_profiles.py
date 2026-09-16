import pytest

from valise_diag import profiles


def test_nom_valide_accepts_letters_numbers_space_dash_underscore():
    assert profiles.nom_valide("Golf de Mathis-2015_v2")


@pytest.mark.parametrize("nom", ["", "  ", "../../etc/passwd", "a/b", "a;rm -rf", ".."])
def test_nom_valide_rejects_dangerous_or_empty_names(nom):
    assert not profiles.nom_valide(nom)


def test_chemin_profil_rejects_invalid_name(tmp_path):
    with pytest.raises(profiles.NomProfilInvalide):
        profiles.chemin_profil("../escape", dossier=tmp_path)


def test_enregistrer_puis_lister_profil(tmp_path):
    source = tmp_path / "vehicle_profile.yaml"
    source.write_text("make: Test\nmodel: Test\nyear: 2020\necus: []\n")
    dossier = tmp_path / "vehicles"

    destination = profiles.enregistrer_profil_actuel(str(source), "Ma Voiture", dossier=dossier)

    assert destination.exists()
    assert destination.read_text() == source.read_text()
    assert profiles.lister_profils(dossier) == ["Ma Voiture"]
