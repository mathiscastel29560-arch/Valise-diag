"""In-memory ELM327 stand-in used by --simulate mode and by the unit tests.

Implements the same duck-typed interface as ELM327Serial (connect/close/reset/
set_header/set_receive_filter/send_raw) so UDSClient and the CLI can use either
one interchangeably, without any hardware attached.
"""
from __future__ import annotations

from typing import Dict, List, Optional


class SimulatedELM327:
    def __init__(self, canned_responses: Optional[Dict[str, List[str]]] = None):
        self._responses = canned_responses or {}
        self._header = "7E0"

    def connect(self) -> None:
        pass

    def close(self) -> None:
        pass

    def reset(self) -> None:
        pass

    def set_header(self, header_hex: str) -> None:
        self._header = header_hex.upper()

    def set_receive_filter(self, header_hex: str) -> None:
        pass

    def send_raw(self, payload_hex: str) -> List[str]:
        key = f"{self._header}:{payload_hex.upper().replace(' ', '')}"
        if key in self._responses:
            return self._responses[key]
        # No canned response registered: fabricate a generic positive response
        # (service_id + 0x40, no data) so simple flows can run without hardware.
        service_id = int(payload_hex.strip()[:2], 16)
        data = bytes([service_id + 0x40])
        rx_header = f"{(int(self._header, 16) + 8):03X}"
        data_str = " ".join(f"{b:02X}" for b in data)
        return [f"{rx_header} {len(data):02X} {data_str}"]
