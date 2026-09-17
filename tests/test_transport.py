from valise_diag.config import AppConfig, EcuProfile, VehicleProfile
from valise_diag.transport import build_diagnostic_clients, build_kw1281_clients
from valise_diag.uds import UDSClient


def _profile(*ecus) -> VehicleProfile:
    return VehicleProfile(make="Test", model="Test", year=2020, ecus=list(ecus))


def test_only_matching_interface_ecus_are_built():
    profile = _profile(
        EcuProfile(name="moteur_can", tx_header="7E0", rx_header="7E8", protocol="uds_can"),
        EcuProfile(name="moteur_kline", tx_header="01", protocol="kwp2000_kline"),
    )
    app_config = AppConfig(interface="obd2", simulate=True)

    clients, avertissements = build_diagnostic_clients(app_config, profile)

    assert set(clients) == {"moteur_can"}
    assert isinstance(clients["moteur_can"], UDSClient)
    assert avertissements == []


def test_kw1281_ecus_are_empty_in_simulate_mode():
    profile = _profile(EcuProfile(name="ecu_legacy", tx_header="01", protocol="kw1281"))
    app_config = AppConfig(interface="kkl", simulate=True)

    assert build_kw1281_clients(app_config, profile) == ({}, [])


def test_unreachable_adapter_is_a_warning_not_a_crash():
    # Port réel mais forcément absent sur la machine de test : simule
    # l'adaptateur débranché/mal identifié qu'on voit en usage réel.
    profile = _profile(EcuProfile(name="moteur_can", tx_header="7E0", rx_header="7E8", protocol="uds_can"))
    app_config = AppConfig(interface="obd2", simulate=False, port="/dev/ttyUSB-inexistant-999")

    clients, avertissements = build_diagnostic_clients(app_config, profile)

    assert clients == {}
    assert len(avertissements) == 1
    assert "moteur_can" in avertissements[0]
