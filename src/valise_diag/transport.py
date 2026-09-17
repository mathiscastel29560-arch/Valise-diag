"""Builds the right diagnostic client for each ECU, based on the selected
physical interface (config.AppConfig.interface) and each ECU's declared
protocol in the vehicle profile. An ECU whose protocol needs the adapter
that isn't currently selected is simply skipped (it isn't reachable right
now — plug in the other cable and switch interface in the Paramètres tab).

A physical connection failure (no adapter plugged in, wrong port, adapter
not responding) is just as expected as "not selected": it must never take
the whole menu down, only that one ECU. Every connect() call below is
wrapped and turned into a warning string instead of a crash.
"""
from __future__ import annotations

from typing import Dict, List, Tuple, Union

import serial

from .config import AppConfig, EcuProfile, VehicleProfile
from .elm327 import ELM327Config, ELM327Error, ELM327Serial
from .kkl import KKLConfig, KKLError, KKLSerial
from .kwp1281 import KWP1281Client
from .kwp2000 import KWP2000Client
from .simulator import SimulatedELM327
from .uds import UDSClient

DiagnosticClient = Union[UDSClient, KWP2000Client]

# Tout ce qui peut raisonnablement sortir d'une tentative de connexion à du
# matériel série réel : port absent/mauvais nom (SerialException), adaptateur
# qui ne répond pas dans les temps ou renvoie n'importe quoi (nos propres
# ELM327Error/KKLError), permissions insuffisantes (OSError).
_ERREURS_CONNEXION = (serial.SerialException, ELM327Error, KKLError, OSError)

_PROTOCOL_INTERFACE = {
    "uds_can": "obd2",
    "kwp2000_kline": "kkl",
    "kw1281": "kkl",
}


def build_diagnostic_clients(
    app_config: AppConfig, profile: VehicleProfile
) -> Tuple[Dict[str, DiagnosticClient], List[str]]:
    """UDS/KWP2000 clients only (used by actuators.py/parameters.py).

    ECUs on protocol "kw1281" are not returned here: that protocol has a
    different, non-DID-based API. Use build_kw1281_clients() for those.

    Renvoie (clients, avertissements) : un ECU dont la connexion échoue est
    absent de `clients` et explique pourquoi dans `avertissements`, plutôt
    que de faire planter tout le programme.
    """
    clients: Dict[str, DiagnosticClient] = {}
    avertissements: List[str] = []
    for ecu in profile.ecus:
        required_interface = _PROTOCOL_INTERFACE.get(ecu.protocol)
        if required_interface is None:
            raise ValueError(f"Unknown ECU protocol '{ecu.protocol}' for ECU '{ecu.name}'")
        if required_interface != app_config.interface:
            continue
        try:
            if ecu.protocol == "uds_can":
                clients[ecu.name] = _build_uds_client(app_config, ecu)
            elif ecu.protocol == "kwp2000_kline" and not app_config.simulate:
                clients[ecu.name] = _build_kwp2000_client(app_config, ecu)
        except _ERREURS_CONNEXION as exc:
            avertissements.append(f"ECU '{ecu.name}' injoignable ({app_config.port}) : {exc}")
    return clients, avertissements


def build_kw1281_clients(app_config: AppConfig, profile: VehicleProfile) -> Tuple[Dict[str, KWP1281Client], List[str]]:
    clients: Dict[str, KWP1281Client] = {}
    avertissements: List[str] = []
    if app_config.simulate:
        return clients, avertissements  # no K-line simulator yet: keep --simulate honest rather than faking the handshake
    for ecu in profile.ecus:
        if ecu.protocol != "kw1281" or app_config.interface != "kkl":
            continue
        try:
            transport = KKLSerial(KKLConfig(port=app_config.port, comms_baudrate=app_config.baudrate))
            client = KWP1281Client(transport, int(ecu.tx_header, 16))
            client.connect()
            clients[ecu.name] = client
        except _ERREURS_CONNEXION as exc:
            avertissements.append(f"ECU '{ecu.name}' injoignable ({app_config.port}) : {exc}")
    return clients, avertissements


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
