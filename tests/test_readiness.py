from types import SimpleNamespace

from valise_diag.readiness import EtatMonitorings, lire_etat, pret_pour_controle


class _FauxTest:
    def __init__(self, name, available, complete):
        self.name = name
        self.available = available
        self.complete = complete


def _faux_status(mil, dtc_count, ignition_type, tests):
    status = SimpleNamespace(MIL=mil, DTC_count=dtc_count, ignition_type=ignition_type)
    for t in tests:
        setattr(status, t.name, t)
    return status


class _FakeObd2:
    def __init__(self, status):
        self._status = status

    def live_value(self, name):
        assert name == "STATUS"
        return self._status


def test_lire_etat_absent_renvoie_none():
    assert lire_etat(_FakeObd2(None)) is None


def test_lire_etat_extrait_mil_dtc_et_monitorings():
    tests = [_FauxTest("PM_FILTER_MONITORING", True, True), _FauxTest("EGR_VVT_SYSTEM_MONITORING", True, False)]
    status = _faux_status(False, 0, "compression", tests)

    etat = lire_etat(_FakeObd2(status))

    assert etat.voyant_moteur_allume is False
    assert etat.nombre_codes_actifs == 0
    assert etat.type_allumage == "compression"
    assert ("PM_FILTER_MONITORING", True, True) in etat.monitorings
    assert ("EGR_VVT_SYSTEM_MONITORING", True, False) in etat.monitorings


def test_pret_pour_controle_faux_si_voyant_allume():
    etat = EtatMonitorings(True, 0, "compression", [("X", True, True)])
    assert pret_pour_controle(etat) is False


def test_pret_pour_controle_faux_si_monitoring_incomplet():
    etat = EtatMonitorings(False, 0, "compression", [("PM_FILTER_MONITORING", True, False)])
    assert pret_pour_controle(etat) is False


def test_pret_pour_controle_ignore_les_monitorings_non_disponibles():
    etat = EtatMonitorings(False, 0, "spark", [("EVAP", False, False), ("CATALYST", True, True)])
    assert pret_pour_controle(etat) is True


def test_pret_pour_controle_vrai_si_tout_complet():
    etat = EtatMonitorings(False, 0, "compression", [("PM_FILTER_MONITORING", True, True)])
    assert pret_pour_controle(etat) is True
