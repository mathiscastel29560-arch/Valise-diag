from valise_diag.graphs import PARAMETRES_PAR_DEFAUT, dessiner_courbe, rendu_sparkline


def test_rendu_sparkline_toutes_valeurs_inconnues():
    assert rendu_sparkline([None, None, None]) == "   "


def test_rendu_sparkline_valeurs_constantes_donne_niveau_median():
    resultat = rendu_sparkline([5, 5, 5])
    assert resultat == "▄▄▄"


def test_rendu_sparkline_croissante_va_du_plus_bas_au_plus_haut():
    resultat = rendu_sparkline([0, 1, 2, 3, 4, 5, 6, 7])
    assert resultat[0] == "▁"
    assert resultat[-1] == "█"


def test_rendu_sparkline_conserve_les_trous():
    resultat = rendu_sparkline([1, None, 3])
    assert resultat[1] == " "


def test_parametres_par_defaut_couvre_puissance_pression_injection_avance():
    noms = [nom for nom, _ in PARAMETRES_PAR_DEFAUT]
    assert "RPM" in noms  # proxy puissance
    assert "INTAKE_PRESSURE" in noms  # pression
    assert "FUEL_RAIL_PRESSURE_DIRECT" in noms  # injection
    assert "TIMING_ADVANCE" in noms  # avance


def test_dessiner_courbe_toutes_valeurs_inconnues():
    courbe = dessiner_courbe([None, None, None], hauteur=4)
    assert courbe == ["   ", "   ", "   ", "   "]


def test_dessiner_courbe_place_le_max_en_haut_et_le_min_en_bas():
    courbe = dessiner_courbe([0, 10], hauteur=5)
    assert courbe[0][1] == "●"  # valeur max (10) en haut
    assert courbe[-1][0] == "●"  # valeur min (0) en bas


def test_dessiner_courbe_relie_les_points_par_un_trait():
    courbe = dessiner_courbe([0, 10], hauteur=5)
    colonne_intermediaire = "".join(rangee[1] for rangee in courbe[1:-1])
    assert "│" in colonne_intermediaire


def test_dessiner_courbe_hauteur_respectee():
    courbe = dessiner_courbe([1, 2, 3], hauteur=6)
    assert len(courbe) == 6
    assert all(len(rangee) == 3 for rangee in courbe)
