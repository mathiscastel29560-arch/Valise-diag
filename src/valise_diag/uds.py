"""Minimal ISO 14229 (UDS) client built on top of an ELM327-style raw CAN transport.

This module only implements the generic protocol mechanics (framing requests,
parsing responses, raising on negative responses). It deliberately ships no
manufacturer-specific data: no catalogue of Data Identifiers, no SecurityAccess
seed->key algorithm. Those must come from documentation you legitimately hold
for the vehicle/ECU you are working on, and belong in your vehicle_profile.yaml
(DIDs) or in a `compute_key` function you supply yourself (SecurityAccess).
"""
from __future__ import annotations

from typing import Callable, Optional

NEGATIVE_RESPONSE = 0x7F

NRC_NAMES = {
    0x10: "generalReject",
    0x11: "serviceNotSupported",
    0x12: "subFunctionNotSupported",
    0x13: "incorrectMessageLengthOrInvalidFormat",
    0x22: "conditionsNotCorrect",
    0x24: "requestSequenceError",
    0x31: "requestOutOfRange",
    0x33: "securityAccessDenied",
    0x35: "invalidKey",
    0x36: "exceedNumberOfAttempts",
    0x37: "requiredTimeDelayNotExpired",
    0x78: "requestCorrectlyReceived-ResponsePending",
}

SID_DIAGNOSTIC_SESSION_CONTROL = 0x10
SID_ECU_RESET = 0x11
SID_READ_DATA_BY_IDENTIFIER = 0x22
SID_SECURITY_ACCESS = 0x27
SID_WRITE_DATA_BY_IDENTIFIER = 0x2E
SID_IO_CONTROL_BY_IDENTIFIER = 0x2F
SID_ROUTINE_CONTROL = 0x31
SID_TESTER_PRESENT = 0x3E

IO_RETURN_CONTROL_TO_ECU = 0x00
IO_RESET_TO_DEFAULT = 0x01
IO_FREEZE_CURRENT_STATE = 0x02
IO_SHORT_TERM_ADJUSTMENT = 0x03

ROUTINE_START = 0x01
ROUTINE_STOP = 0x02
ROUTINE_REQUEST_RESULTS = 0x03


class UDSError(RuntimeError):
    pass


class UDSNegativeResponse(UDSError):
    def __init__(self, service_id: int, nrc: int):
        name = NRC_NAMES.get(nrc, f"NRC 0x{nrc:02X}")
        super().__init__(f"Negative response to service 0x{service_id:02X}: {name}")
        self.service_id = service_id
        self.nrc = nrc


class UDSClient:
    """Speaks UDS request/response over an ELM327 in CAN-auto-formatting mode.

    The transport (`adapter`) only needs set_header / set_receive_filter /
    send_raw, so a real ELM327Serial and the SimulatedELM327 are interchangeable.
    """

    def __init__(self, adapter, tx_header: str, rx_header: Optional[str] = None):
        self._adapter = adapter
        self._tx_header = tx_header
        self._rx_header = rx_header or self._default_rx_header(tx_header)
        self._adapter.set_header(self._tx_header)
        self._adapter.set_receive_filter(self._rx_header)

    @staticmethod
    def _default_rx_header(tx_header: str) -> str:
        # Common ISO 15765-4 (11-bit) convention: the ECU replies on request+8
        # (e.g. 7E0 -> 7E8). Not universal — pass rx_header explicitly whenever
        # the vehicle profile documents a different pair.
        try:
            return f"{int(tx_header, 16) + 8:03X}"
        except ValueError:
            return tx_header

    def request(self, service_id: int, data: bytes = b"") -> bytes:
        payload = bytes([service_id]) + data
        lines = self._adapter.send_raw(payload.hex())
        response = self._parse_response(lines)
        if response and response[0] == NEGATIVE_RESPONSE:
            requested_sid = response[1] if len(response) > 1 else service_id
            nrc = response[2] if len(response) > 2 else 0x10
            raise UDSNegativeResponse(requested_sid, nrc)
        expected_sid = service_id + 0x40
        if not response or response[0] != expected_sid:
            got = response.hex() if response else "(empty)"
            raise UDSError(f"Unexpected response to service 0x{service_id:02X}: {got}")
        return response[1:]

    @staticmethod
    def _parse_response(lines) -> bytes:
        # With AT H1 (headers on) + AT CAF1 (CAN auto formatting), each line
        # looks like "<header> <byte-count> <data...>", e.g. "7E8 06 62 F1 90 01".
        # CAF1 also means the adapter has already reassembled any multi-frame
        # ISO-TP reply for us before printing this line.
        for line in lines:
            tokens = line.split()
            if len(tokens) < 2:
                continue
            try:
                int(tokens[0], 16)
            except ValueError:
                continue
            data_tokens = tokens[2:]
            try:
                return bytes(int(t, 16) for t in data_tokens)
            except ValueError:
                continue
        return b""

    def diagnostic_session_control(self, session_type: int) -> bytes:
        return self.request(SID_DIAGNOSTIC_SESSION_CONTROL, bytes([session_type]))

    def tester_present(self) -> None:
        self.request(SID_TESTER_PRESENT, bytes([0x00]))

    def security_access(self, level: int, compute_key: Callable[[bytes], bytes]) -> None:
        """Perform a UDS SecurityAccess seed/key exchange.

        `compute_key` must be supplied by the caller and must implement the key
        algorithm for the target ECU. This client ships no seed->key algorithm
        of its own: only pass one you are legitimately entitled to use (from the
        vehicle/ECU manufacturer's own documentation or tooling), for a vehicle
        you own or are authorized to service.
        """
        seed_response = self.request(SID_SECURITY_ACCESS, bytes([level]))
        seed = seed_response[1:]
        if all(b == 0 for b in seed):
            return  # ECU reports an all-zero seed: security is already unlocked
        key = compute_key(seed)
        self.request(SID_SECURITY_ACCESS, bytes([level + 1]) + key)

    def read_data_by_identifier(self, did: int) -> bytes:
        response = self.request(SID_READ_DATA_BY_IDENTIFIER, did.to_bytes(2, "big"))
        return response[2:]  # skip the echoed DID

    def write_data_by_identifier(self, did: int, value: bytes) -> None:
        self.request(SID_WRITE_DATA_BY_IDENTIFIER, did.to_bytes(2, "big") + value)

    def io_control_by_identifier(self, did: int, control_parameter: int, control_state: bytes = b"") -> bytes:
        response = self.request(
            SID_IO_CONTROL_BY_IDENTIFIER,
            did.to_bytes(2, "big") + bytes([control_parameter]) + control_state,
        )
        return response[2:]

    def routine_control(self, routine_id: int, sub_function: int, data: bytes = b"") -> bytes:
        response = self.request(
            SID_ROUTINE_CONTROL,
            bytes([sub_function]) + routine_id.to_bytes(2, "big") + data,
        )
        return response[3:]
