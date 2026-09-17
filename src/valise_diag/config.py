"""Loads the app config and the per-vehicle profile (CAN headers, actuators, parameters)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

import yaml

# Two physical adapters are supported. "obd2" is a generic ELM327/CAN dongle
# (standard OBD-II PIDs + UDS-on-CAN for newer vehicles). "kkl" is a classic
# K-line cable (e.g. a "VAG-COM 409.1"-style KKL cable): no CAN, 5-baud init
# only, talking either KWP2000 (ISO 14230) or the older VAG-proprietary
# KW1281 block protocol depending on the ECU.
INTERFACES = ("obd2", "kkl")

# Per-ECU protocol: which of the three diagnostic "languages" above to speak.
# uds_can needs interface "obd2"; the other two need interface "kkl".
PROTOCOLS = ("uds_can", "kwp2000_kline", "kw1281")

VEILLE_TYPES = ("matrix", "citations", "glitch", "voiture", "aleatoire")

# Console font sizes applied via `setfont` (Linux console, e.g. on the Pi's
# own HDMI/composite output — irrelevant over SSH). None means "leave as is".
POLICES = {
    "defaut": None,
    "petit": "Lat15-Terminus16",
    "moyen": "Lat15-TerminusBold20x10",
    "grand": "Lat15-TerminusBold32x16",
}


@dataclass
class ActuatorDef:
    name: str
    description: str
    did: int  # UDS Data Identifier (hex) — must come from documentation you legitimately hold
    control_parameter: int = 0x03  # UDS IOControlByIdentifier: 0x03 = shortTermAdjustment
    on_state: bytes = b"\x01"
    off_state: bytes = b"\x00"
    max_duration_s: float = 3.0
    requires_engine_off: bool = True
    requires_stationary: bool = True


@dataclass
class ParameterDef:
    name: str
    description: str
    did: int
    writable: bool = False
    data_format: str = "uint8"  # uint8 | int8 | uint16 | int16
    scale: float = 1.0
    offset: float = 0.0
    unit: str = ""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    requires_engine_off: bool = True
    requires_stationary: bool = True


@dataclass
class EcuProfile:
    name: str
    tx_header: str  # CAN header (uds_can) or 5-baud init ECU address (kwp2000_kline / kw1281), e.g. "01"
    rx_header: Optional[str] = None  # uds_can only; kwp2000_kline/kw1281 don't use a separate rx address
    protocol: str = "uds_can"
    actuators: List[ActuatorDef] = field(default_factory=list)
    parameters: List[ParameterDef] = field(default_factory=list)
    # kw1281 only: maps a function name to the KW1281 block title byte to use for it
    # (e.g. {"read_fault_codes": 0x07, "clear_fault_codes": 0x05}). Block titles are
    # ECU/model-year specific — confirm them against documentation you legitimately
    # hold before filling this in; nothing here is guessed or assumed correct.
    kw1281_blocks: Dict[str, int] = field(default_factory=dict)


@dataclass
class VehicleProfile:
    make: str
    model: str
    year: int
    ecus: List[EcuProfile] = field(default_factory=list)

    def find_ecu(self, name: str) -> EcuProfile:
        for ecu in self.ecus:
            if ecu.name == name:
                return ecu
        raise KeyError(f"Unknown ECU '{name}' in vehicle profile")


@dataclass
class AppConfig:
    interface: str = "obd2"  # "obd2" (ELM327/CAN) or "kkl" (K-line VAG cable)
    port: str = "/dev/ttyUSB0"
    baudrate: int = 38400
    # Code ATSP ELM327 ("6" = CAN 11 bits/500k, etc., voir elm327.PROTOCOLES_TESTABLES)
    # à forcer au lieu de laisser l'adaptateur négocier lui-même ("AUTO").
    # Utile avec certains clones dont l'auto-négociation est buguée : voir
    # Diagnostic > Diagnostic bas niveau adaptateur, qui peut renseigner ce
    # champ automatiquement une fois un protocole qui fonctionne trouvé.
    protocole_obd2: str = "AUTO"
    max_speed_kmh: float = 0.0
    require_confirmation: bool = True
    simulate: bool = False
    vehicle_profile_path: str = "config/vehicle_profile.yaml"

    # Cosmetics / appliance behaviour (dashboard, screensaver, console lock).
    titre_menu: str = "VALISE DIAG"
    boot_rapide: bool = False  # passe l'écran de démarrage en version courte
    veille_active: bool = True
    veille_delai: int = 60  # seconds of inactivity before the screensaver kicks in
    veille_type: str = "aleatoire"  # one of VEILLE_TYPES
    police: str = "defaut"  # one of POLICES
    autostart: bool = True
    pin_active: bool = False
    pin_hash: str = ""
    pin_salt: str = ""


def _parse_int(value) -> int:
    return int(value, 16) if isinstance(value, str) else int(value)


def load_vehicle_profile(path: Union[str, Path]) -> VehicleProfile:
    data = yaml.safe_load(Path(path).read_text())
    ecus = []
    for ecu_data in data.get("ecus", []):
        actuators = [
            ActuatorDef(
                name=a["name"],
                description=a.get("description", ""),
                did=_parse_int(a["did"]),
                control_parameter=_parse_int(a.get("control_parameter", 0x03)),
                on_state=bytes.fromhex(a.get("on_state", "01")),
                off_state=bytes.fromhex(a.get("off_state", "00")),
                max_duration_s=float(a.get("max_duration_s", 3.0)),
                requires_engine_off=bool(a.get("requires_engine_off", True)),
                requires_stationary=bool(a.get("requires_stationary", True)),
            )
            for a in ecu_data.get("actuators", [])
        ]
        parameters = [
            ParameterDef(
                name=p["name"],
                description=p.get("description", ""),
                did=_parse_int(p["did"]),
                writable=bool(p.get("writable", False)),
                data_format=p.get("data_format", "uint8"),
                scale=float(p.get("scale", 1.0)),
                offset=float(p.get("offset", 0.0)),
                unit=p.get("unit", ""),
                min_value=p.get("min_value"),
                max_value=p.get("max_value"),
                requires_engine_off=bool(p.get("requires_engine_off", True)),
                requires_stationary=bool(p.get("requires_stationary", True)),
            )
            for p in ecu_data.get("parameters", [])
        ]
        protocol = ecu_data.get("protocol", "uds_can")
        if protocol not in PROTOCOLS:
            raise ValueError(f"Unknown protocol '{protocol}' for ECU '{ecu_data['name']}' (expected one of {PROTOCOLS})")
        kw1281_blocks = {k: _parse_int(v) for k, v in ecu_data.get("blocks", {}).items()}
        ecus.append(
            EcuProfile(
                name=ecu_data["name"],
                tx_header=str(ecu_data["tx_header"]),
                rx_header=ecu_data.get("rx_header"),
                protocol=protocol,
                actuators=actuators,
                parameters=parameters,
                kw1281_blocks=kw1281_blocks,
            )
        )
    return VehicleProfile(make=data["make"], model=data["model"], year=int(data["year"]), ecus=ecus)


def load_app_config(path: Union[str, Path]) -> AppConfig:
    if not Path(path).exists():
        return AppConfig()
    data = yaml.safe_load(Path(path).read_text()) or {}
    config = AppConfig(**{**AppConfig().__dict__, **data})
    if config.interface not in INTERFACES:
        raise ValueError(f"Unknown interface '{config.interface}' (expected one of {INTERFACES})")
    return config


def save_app_config(config: AppConfig, path: Union[str, Path]) -> None:
    Path(path).write_text(yaml.safe_dump(config.__dict__, sort_keys=False, allow_unicode=True))
