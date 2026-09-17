import csv

from valise_diag.session_replay import colonnes_communes, echantillonner, lire_csv, statistiques


def _ecrire_csv(chemin, entetes, lignes):
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        ecrivain = csv.writer(f)
        ecrivain.writerow(["horodatage"] + entetes)
        for i, ligne in enumerate(lignes):
            ecrivain.writerow([f"2026-01-01 00:00:{i:02d}"] + ligne)


def test_lire_csv_ignore_horodatage_et_convertit_en_float(tmp_path):
    chemin = tmp_path / "session.csv"
    _ecrire_csv(chemin, ["RPM", "Vitesse"], [["900", "0"], ["1500", "30"]])

    entetes, colonnes = lire_csv(chemin)

    assert entetes == ["RPM", "Vitesse"]
    assert colonnes["RPM"] == [900.0, 1500.0]
    assert colonnes["Vitesse"] == [0.0, 30.0]


def test_lire_csv_gere_les_cellules_vides(tmp_path):
    chemin = tmp_path / "session.csv"
    _ecrire_csv(chemin, ["RPM"], [["900"], [""]])

    _, colonnes = lire_csv(chemin)

    assert colonnes["RPM"] == [900.0, None]


def test_statistiques_min_max_moyenne():
    assert statistiques([1.0, 3.0, None, 5.0]) == (1.0, 5.0, 3.0)


def test_statistiques_toutes_valeurs_manquantes_renvoie_none():
    assert statistiques([None, None]) is None


def test_echantillonner_ne_change_rien_si_deja_plus_court():
    assert echantillonner([1.0, 2.0], 10) == [1.0, 2.0]


def test_echantillonner_reduit_a_la_largeur_demandee():
    valeurs = list(range(100))
    resultat = echantillonner([float(v) for v in valeurs], 10)
    assert len(resultat) == 10


def test_colonnes_communes_preserve_ordre_de_a():
    assert colonnes_communes(["RPM", "Vitesse", "Pression"], ["Pression", "RPM"]) == ["RPM", "Pression"]
