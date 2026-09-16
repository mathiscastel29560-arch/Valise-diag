"""Standard OBD-II diagnostics (DTC read/clear, live PIDs) via the python-obd library."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import obd

from .safety import VehicleState


@dataclass
class DtcEntry:
    code: str
    description: str


class Obd2Client:
    def __init__(self, port: str, baudrate: int = 38400):
        self._connection = obd.OBD(portstr=port, baudrate=baudrate)

    def is_connected(self) -> bool:
        return self._connection.is_connected()

    def read_dtcs(self) -> List[DtcEntry]:
        response = self._connection.query(obd.commands.GET_DTC)
        if response.is_null():
            return []
        return [DtcEntry(code=code, description=desc or "") for code, desc in response.value]

    def clear_dtcs(self) -> None:
        self._connection.query(obd.commands.CLEAR_DTC)

    def live_value(self, command_name: str):
        response = self._connection.query(getattr(obd.commands, command_name))
        return None if response.is_null() else response.value

    def vehicle_state(self) -> VehicleState:
        speed = self.live_value("SPEED")
        rpm = self.live_value("RPM")
        return VehicleState(
            speed_kmh=speed.to("kph").magnitude if speed is not None else None,
            rpm=rpm.magnitude if rpm is not None else None,
            engine_running=(rpm.magnitude > 0) if rpm is not None else None,
        )

    def close(self) -> None:
        self._connection.close()
