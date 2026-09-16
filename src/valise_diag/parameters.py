"""Read and write ECU parameters (UDS ReadDataByIdentifier / WriteDataByIdentifier)."""
from __future__ import annotations

import struct
from typing import Dict

from .config import EcuProfile, ParameterDef
from .safety import SafetyGuard, VehicleState

# uds_by_ecu holds either UDSClient (CAN) or KWP2000Client (K-line) instances:
# both expose the same read/write_data_by_identifier(did, ...) methods.

_STRUCT_FORMATS = {
    "uint8": ">B",
    "int8": ">b",
    "uint16": ">H",
    "int16": ">h",
}


def decode_value(param: ParameterDef, raw: bytes) -> float:
    fmt = _STRUCT_FORMATS[param.data_format]
    size = struct.calcsize(fmt)
    (raw_value,) = struct.unpack(fmt, raw[:size])
    return raw_value * param.scale + param.offset


def encode_value(param: ParameterDef, value: float) -> bytes:
    fmt = _STRUCT_FORMATS[param.data_format]
    raw_value = round((value - param.offset) / param.scale)
    return struct.pack(fmt, raw_value)


class ParameterError(RuntimeError):
    pass


class ParameterController:
    def __init__(self, uds_by_ecu: Dict[str, object], ecus: Dict[str, EcuProfile], guard: SafetyGuard):
        self._uds_by_ecu = uds_by_ecu
        self._ecus = ecus
        self._guard = guard

    def _find(self, name: str):
        for ecu_name, ecu in self._ecus.items():
            for param in ecu.parameters:
                if param.name == name:
                    return ecu_name, param
        raise ParameterError(f"Unknown parameter '{name}'")

    def read(self, name: str) -> float:
        ecu_name, param = self._find(name)
        raw = self._uds_by_ecu[ecu_name].read_data_by_identifier(param.did)
        return decode_value(param, raw)

    def write(self, name: str, value: float, state: VehicleState) -> None:
        ecu_name, param = self._find(name)
        if not param.writable:
            raise ParameterError(f"Parameter '{name}' is marked read-only in the vehicle profile")
        if param.min_value is not None and value < param.min_value:
            raise ParameterError(f"{value} is below the allowed minimum ({param.min_value}) for '{name}'")
        if param.max_value is not None and value > param.max_value:
            raise ParameterError(f"{value} is above the allowed maximum ({param.max_value}) for '{name}'")
        self._guard.check(
            f"Écrire {name} = {value}{param.unit}",
            state,
            requires_stationary=param.requires_stationary,
            requires_engine_off=param.requires_engine_off,
        )
        uds = self._uds_by_ecu[ecu_name]
        uds.write_data_by_identifier(param.did, encode_value(param, value))
        readback = self.read(name)
        if abs(readback - value) > max(abs(param.scale), 1e-6):
            raise ParameterError(f"Write verification failed for '{name}': wrote {value}, ECU reports {readback}")
