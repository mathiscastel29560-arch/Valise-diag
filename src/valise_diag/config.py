"""Loads the app config and the per-vehicle profile (CAN headers, actuators, parameters)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union

import yaml


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
    tx_header: str
    rx_header: Optional[str] = None
    actuators: List[ActuatorDef] = field(default_factory=list)
    parameters: List[ParameterDef] = field(default_factory=list)


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
    port: str = "/dev/ttyUSB0"
    baudrate: int = 38400
    max_speed_kmh: float = 0.0
    require_confirmation: bool = True
    simulate: bool = False
    vehicle_profile_path: str = "config/vehicle_profile.yaml"


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
        ecus.append(
            EcuProfile(
                name=ecu_data["name"],
                tx_header=str(ecu_data["tx_header"]),
                rx_header=ecu_data.get("rx_header"),
                actuators=actuators,
                parameters=parameters,
            )
        )
    return VehicleProfile(make=data["make"], model=data["model"], year=int(data["year"]), ecus=ecus)


def load_app_config(path: Union[str, Path]) -> AppConfig:
    if not Path(path).exists():
        return AppConfig()
    data = yaml.safe_load(Path(path).read_text()) or {}
    return AppConfig(**{**AppConfig().__dict__, **data})
