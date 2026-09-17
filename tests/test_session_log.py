import csv
import re

from valise_diag import session_log


class _FakeObd2:
    def __init__(self):
        self._compteur = 0

    def live_value(self, command_name: str):
        self._compteur += 1
        return float(self._compteur)


def test_enregistrer_ecrit_entetes_et_lignes(tmp_path):
    chemin = tmp_path / "session.csv"
    commandes = [("RPM", "Régime moteur"), ("SPEED", "Vitesse")]

    def arreter_apres_3_tours(tick: int) -> None:
        if tick >= 3:
            raise KeyboardInterrupt

    resultat = session_log.enregistrer(
        _FakeObd2(), commandes, duree_s=0, chemin=chemin, periode_s=0, sur_tick=arreter_apres_3_tours
    )

    assert resultat == chemin
    with open(chemin, newline="", encoding="utf-8") as f:
        lignes = list(csv.reader(f))

    assert lignes[0] == ["horodatage", "Régime moteur", "Vitesse"]
    assert len(lignes) == 4  # entête + 3 mesures
    assert lignes[1][1:] == ["1.0", "2.0"]


def test_enregistrer_respecte_la_duree(tmp_path):
    chemin = tmp_path / "session.csv"
    commandes = [("RPM", "Régime moteur")]

    session_log.enregistrer(_FakeObd2(), commandes, duree_s=0.05, chemin=chemin, periode_s=0.02)

    with open(chemin, newline="", encoding="utf-8") as f:
        lignes = list(csv.reader(f))
    assert len(lignes) >= 2  # au moins l'entête + une mesure


def test_chemin_session_inclut_le_nom_du_vehicule(tmp_path):
    chemin = session_log.chemin_session(dossier=tmp_path, vehicule="Renault Clio_4 (X98)")
    assert chemin.name.startswith("session_Renault_Clio_4_X98_")
    assert chemin.suffix == ".csv"


def test_chemin_session_sans_vehicule_reste_generique(tmp_path):
    chemin = session_log.chemin_session(dossier=tmp_path)
    assert re.fullmatch(r"session_\d{8}_\d{6}\.csv", chemin.name)
