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
        # so simple flows (read/write/io-control on any DID) can run without
        # hardware. Echo back whatever the request carried after the service ID
        # (e.g. the DID) plus two zero padding bytes, so a parameter read has
        # enough bytes to decode instead of crashing on an empty payload.
        request = bytes.fromhex(payload_hex)
        service_id = request[0]
        echoed = request[1:]
        data = bytes([service_id + 0x40]) + echoed + b"\x00\x00"
        rx_header = f"{(int(self._header, 16) + 8):03X}"
        data_str = " ".join(f"{b:02X}" for b in data)
        return [f"{rx_header} {len(data):02X} {data_str}"]
