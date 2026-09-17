from valise_diag.elm327 import DiagnosticAdaptateur, ResultatProtocole, diagnostiquer_port, diagnostiquer_protocoles


def test_adaptateur_repond_faux_si_atz_vide():
    resultat = DiagnosticAdaptateur(port="/dev/ttyUSB0", baudrate=38400, reponse_atz="")
    assert resultat.adaptateur_repond is False


def test_adaptateur_repond_vrai_si_atz_non_vide():
    resultat = DiagnosticAdaptateur(port="/dev/ttyUSB0", baudrate=38400, reponse_atz="ELM327 v1.5\r\r>")
    assert resultat.adaptateur_repond is True


def test_vehicule_repond_faux_sur_no_data():
    resultat = DiagnosticAdaptateur(port="/dev/ttyUSB0", baudrate=38400, reponse_0100="NO DATA\r\r>")
    assert resultat.vehicule_repond is False


def test_vehicule_repond_faux_sur_unable_to_connect():
    resultat = DiagnosticAdaptateur(port="/dev/ttyUSB0", baudrate=38400, reponse_0100="UNABLE TO CONNECT\r\r>")
    assert resultat.vehicule_repond is False


def test_vehicule_repond_vrai_sur_reponse_hexa():
    resultat = DiagnosticAdaptateur(port="/dev/ttyUSB0", baudrate=38400, reponse_0100="41 00 BE 3F A8 13\r\r>")
    assert resultat.vehicule_repond is True


def test_diagnostiquer_port_gere_un_port_absent_sans_lever():
    resultat = diagnostiquer_port("/dev/ttyUSB-inexistant-999", 38400, timeout_s=0.5)
    assert resultat.erreur_ouverture is not None
    assert resultat.adaptateur_repond is False


def test_resultat_protocole_fonctionne_faux_sur_no_data():
    resultat = ResultatProtocole(code="6", libelle="CAN 11 bits, 500 kbit/s", reponse_0100="NO DATA\r\r>")
    assert resultat.fonctionne is False


def test_resultat_protocole_fonctionne_vrai_sur_reponse_hexa():
    resultat = ResultatProtocole(code="6", libelle="CAN 11 bits, 500 kbit/s", reponse_0100="41 00 BE 3F A8 13\r\r>")
    assert resultat.fonctionne is True


def test_diagnostiquer_protocoles_gere_un_port_absent_sans_lever():
    resultats = diagnostiquer_protocoles("/dev/ttyUSB-inexistant-999", 38400, timeout_s=0.5)
    assert resultats == []
