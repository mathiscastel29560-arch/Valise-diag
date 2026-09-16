"""Builds the right diagnostic client for each ECU, based on the selected
physical interface (config.AppConfig.interface) and each ECU's declared
protocol in the vehicle profile. An ECU whose protocol needs the adapter
that isn't currently selected is simply skipped (it isn't reachable right
now — plug in the other cable and switch interface in the Paramètres tab).
"""
from __future__ import annotations

from typing import Dict, Union

from .config import AppConfig, EcuProfile, VehicleProfile
from .elm327 import ELM327Config, ELM327Serial
from .kkl import KKLConfig, KKLSerial
from .kwp1281 import KWP1281Client
from .kwp2000 import KWP2000Client
from .simulator import SimulatedELM327
from .uds import UDSClient

DiagnosticClient = Union[UDSClient, KWP2000Client]

_PROTOCOL_INTERFACE = {
    "uds_can": "obd2",
    "kwp2000_kline": "kkl",
    "kw1281": "kkl",
}


def build_diagnostic_clients(app_config: AppConfig, profile: VehicleProfile) -> Dict[str, DiagnosticClient]:
    """UDS/KWP2000 clients only (used by actuators.py/parameters.py).

    ECUs on protocol "kw1281" are not returned here: that protocol has a
    different, non-DID-based API. Use build_kw1281_clients() for those.
    """
    clients: Dict[str, DiagnosticClient] = {}
    for ecu in profile.ecus:
        required_interface = _PROTOCOL_INTERFACE.get(ecu.protocol)
        if required_interface is None:
            raise ValueError(f"Unknown ECU protocol '{ecu.protocol}' for ECU '{ecu.name}'")
        if required_interface != app_config.interface:
            continue
        if ecu.protocol == "uds_can":
            clients[ecu.name] = _build_uds_client(app_config, ecu)
        elif ecu.protocol == "kwp2000_kline" and not app_config.simulate:
            clients[ecu.name] = _build_kwp2000_client(app_config, ecu)
    return clients


def build_kw1281_clients(app_config: AppConfig, profile: VehicleProfile) -> Dict[str, KWP1281Client]:
    clients: Dict[str, KWP1281Client] = {}
    if app_config.simulate:
        return clients  # no K-line simulator yet: keep --simulate honest rather than faking the handshake
    for ecu in profile.ecus:
        if ecu.protocol != "kw1281" or app_config.interface != "kkl":
            continue
        transport = KKLSerial(KKLConfig(port=app_config.port, comms_baudrate=app_config.baudrate))
        client = KWP1281Client(transport, int(ecu.tx_header, 16))
        client.connect()
        clients[ecu.name] = client
    return clients


def _build_uds_client(app_config: AppConfig, ecu: EcuProfile) -> UDSClient:
    if app_config.simulate:
        adapter = SimulatedELM327()
    else:
        adapter = ELM327Serial(ELM327Config(port=app_config.port, baudrate=app_config.baudrate))
        adapter.connect()
    return UDSClient(adapter, ecu.tx_header, ecu.rx_header)


def _build_kwp2000_client(app_config: AppConfig, ecu: EcuProfile) -> KWP2000Client:
    transport = KKLSerial(KKLConfig(port=app_config.port, comms_baudrate=app_config.baudrate))
    client = KWP2000Client(transport, int(ecu.tx_header, 16))
    client.connect()
    return client
