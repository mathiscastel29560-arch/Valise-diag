"""Standard OBD-II diagnostics (DTC read/clear, live PIDs) via the python-obd library.

`obd` (and its dependency `pint`) is imported lazily, inside the functions
that actually need it, rather than at module import time. Importing it eagerly
would cost every startup — even on the KKL interface, which never touches
python-obd — and that import is measurably slow (pint builds a whole unit
registry), which matters on a Raspberry Pi Zero's single slow core. Repeating
`import obd` in each method is cheap after the first real import: Python
caches it in sys.modules.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .safety import VehicleState


@dataclass
class DtcEntry:
    code: str
    description: str


class Obd2Client:
    def __init__(self, port: str, baudrate: int = 38400):
        import logging

        import obd

        # python-obd (et pint, qu'il charge) écrivent leurs propres messages
        # directement sur la console — bruyant et redondant avec nos propres
        # messages d'erreur affichés dans le menu (voir transport.py/cli.py).
        logging.getLogger("obd").setLevel(logging.CRITICAL)
        logging.getLogger("pint").setLevel(logging.CRITICAL)

        self._connection = obd.OBD(portstr=port, baudrate=baudrate)

    def is_connected(self) -> bool:
        return self._connection.is_connected()

    def read_dtcs(self) -> List[DtcEntry]:
        import obd

        response = self._connection.query(obd.commands.GET_DTC)
        if response.is_null():
            return []
        return [DtcEntry(code=code, description=desc or "") for code, desc in response.value]

    def clear_dtcs(self) -> None:
        import obd

        self._connection.query(obd.commands.CLEAR_DTC)

    def live_value(self, command_name: str):
        import obd

        command = getattr(obd.commands, command_name, None)
        if command is None:
            return None  # unknown in this version of python-obd — treated like "unsupported"
        response = self._connection.query(command)
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


_UNITES_COURTES = {
    "revolutions_per_minute": "tr/min",
    "kilometer_per_hour": "km/h",
    "kilopascal": "kPa",
    "pascal": "Pa",
    "percent": "%",
    "degree_Celsius": "°C",
    "volt": "V",
    "milliampere": "mA",
    "degree": "°",
    "gps": "g/s",
    "liters_per_hour": "L/h",
    "count": "",
}


def format_live_value(value) -> str:
    if value is None:
        return "non disponible"
    magnitude = getattr(value, "magnitude", None)
    if magnitude is None:
        return str(value)
    unite = _UNITES_COURTES.get(str(value.units), str(value.units))
    return f"{magnitude:g} {unite}".rstrip()


def valeur_numerique(value):
    """Magnitude numérique d'une grandeur Pint renvoyée par python-obd (ou la
    valeur telle quelle si ce n'en est pas une), pour l'export CSV — voir
    session_log.py."""
    if value is None:
        return None
    magnitude = getattr(value, "magnitude", None)
    return magnitude if magnitude is not None else value
