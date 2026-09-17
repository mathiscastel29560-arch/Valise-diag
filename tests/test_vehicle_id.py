from valise_diag.vehicle_id import LOGOS_ASCII, logo_ascii, marque_depuis_vin


def test_marque_depuis_vin_reconnait_renault():
    assert marque_depuis_vin("VF15RFN0H12345678") == "Renault"


def test_marque_depuis_vin_reconnait_dacia():
    assert marque_depuis_vin("UU1DBAAA51A123456") == "Dacia"


def test_marque_depuis_vin_wmi_inconnu_renvoie_none():
    assert marque_depuis_vin("ZZZ00000000000000") is None


def test_marque_depuis_vin_absent_renvoie_none():
    assert marque_depuis_vin(None) is None
    assert marque_depuis_vin("") is None
    assert marque_depuis_vin("VF") is None


def test_logo_ascii_connu_renvoie_le_bon_logo():
    assert logo_ascii("Renault") == LOGOS_ASCII["Renault"]


def test_logo_ascii_inconnu_renvoie_un_placeholder_non_vide():
    logo = logo_ascii("Marque totalement inventée")
    assert logo.strip() != ""
    assert logo not in LOGOS_ASCII.values()


def test_logo_ascii_absent_renvoie_un_placeholder():
    logo = logo_ascii(None)
    assert logo.strip() != ""
