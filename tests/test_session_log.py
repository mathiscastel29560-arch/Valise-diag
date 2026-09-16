import csv

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
