from valise_diag.consommation import calculer_l_100km


def test_calculer_l_100km_cas_normal():
    # 6 L/h à 60 km/h -> 10 L/100km
    assert calculer_l_100km(6.0, 60.0) == 10.0


def test_calculer_l_100km_vitesse_nulle_renvoie_none():
    assert calculer_l_100km(1.5, 0) is None


def test_calculer_l_100km_vitesse_negative_renvoie_none():
    assert calculer_l_100km(1.5, -5) is None


def test_calculer_l_100km_valeur_manquante_renvoie_none():
    assert calculer_l_100km(None, 60) is None
    assert calculer_l_100km(6.0, None) is None
