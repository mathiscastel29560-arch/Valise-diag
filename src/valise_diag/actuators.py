"""Runs actuator tests (UDS InputOutputControlByIdentifier) with mandatory safety guards."""
from __future__ import annotations

import time
from typing import Dict, Optional

from .config import EcuProfile
from .safety import SafetyGuard, VehicleState
from .uds import IO_RETURN_CONTROL_TO_ECU, UDSClient


class ActuatorError(RuntimeError):
    pass


class ActuatorController:
    def __init__(self, uds_by_ecu: Dict[str, UDSClient], ecus: Dict[str, EcuProfile], guard: SafetyGuard):
        self._uds_by_ecu = uds_by_ecu
        self._ecus = ecus
        self._guard = guard

    def _find(self, name: str):
        for ecu_name, ecu in self._ecus.items():
            for actuator in ecu.actuators:
                if actuator.name == name:
                    return ecu_name, actuator
        raise ActuatorError(f"Unknown actuator '{name}'")

    def activate(self, name: str, state: VehicleState, duration_s: Optional[float] = None) -> None:
        ecu_name, actuator = self._find(name)
        duration = min(duration_s, actuator.max_duration_s) if duration_s else actuator.max_duration_s
        self._guard.check(
            f"Activer l'actionneur '{name}' pendant {duration}s",
            state,
            requires_stationary=actuator.requires_stationary,
            requires_engine_off=actuator.requires_engine_off,
        )
        uds = self._uds_by_ecu[ecu_name]
        uds.io_control_by_identifier(actuator.did, actuator.control_parameter, actuator.on_state)
        try:
            time.sleep(duration)
        finally:
            # Always hand control back to the ECU, even on Ctrl-C or an error.
            uds.io_control_by_identifier(actuator.did, IO_RETURN_CONTROL_TO_ECU)
