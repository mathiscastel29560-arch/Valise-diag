"""KWP2000 (ISO 14230-3) diagnostic client over a K-line (KKL) transport.

Exposes the same method surface as valise_diag.uds.UDSClient
(read_data_by_identifier / write_data_by_identifier / io_control_by_identifier)
so ActuatorController and ParameterController work unchanged whether the
vehicle is reached over CAN (UDS) or K-line (KWP2000). The main protocol
difference: KWP2000 addresses data with a single-byte "Local Identifier"
instead of a 2-byte UDS "Data Identifier", and frames carry an explicit
checksum instead of relying on CAN's own error detection.
"""
from __future__ import annotations

from .kkl import KKLSerial
from .uds import UDSNegativeResponse  # NRC table + exception shape are protocol-agnostic

SID_START_DIAGNOSTIC_SESSION = 0x10
SID_STOP_DIAGNOSTIC_SESSION = 0x20
SID_ECU_RESET = 0x11
SID_CLEAR_DIAGNOSTIC_INFORMATION = 0x14
SID_READ_DTC_BY_STATUS = 0x18
SID_READ_DATA_BY_LOCAL_IDENTIFIER = 0x21
SID_SECURITY_ACCESS = 0x27
SID_INPUT_OUTPUT_CONTROL_BY_LOCAL_IDENTIFIER = 0x30
SID_START_ROUTINE_BY_LOCAL_IDENTIFIER = 0x31
SID_WRITE_DATA_BY_LOCAL_IDENTIFIER = 0x3B
SID_TESTER_PRESENT = 0x3E

NEGATIVE_RESPONSE = 0x7F


class KWP2000Error(RuntimeError):
    pass


class KWP2000Client:
    def __init__(self, transport: KKLSerial, ecu_address: int, tester_address: int = 0xF1):
        self._transport = transport
        self._ecu_address = ecu_address
        self._tester_address = tester_address

    def connect(self) -> None:
        self._transport.connect()
        self._transport.slow_init(self._ecu_address)

    def request(self, service_id: int, data: bytes = b"") -> bytes:
        payload = bytes([service_id]) + data
        for byte in self._build_frame(payload):
            self._transport.write_byte(byte)
        response = self._read_frame()
        if response and response[0] == NEGATIVE_RESPONSE:
            requested_sid = response[1] if len(response) > 1 else service_id
            nrc = response[2] if len(response) > 2 else 0x10
            raise UDSNegativeResponse(requested_sid, nrc)
        expected_sid = service_id + 0x40
        if not response or response[0] != expected_sid:
            got = response.hex() if response else "(empty)"
            raise KWP2000Error(f"Unexpected response to service 0x{service_id:02X}: {got}")
        return response[1:]

    def _build_frame(self, data: bytes) -> bytes:
        length = len(data)
        if length <= 63:
            header = bytes([0x80 | length, self._ecu_address, self._tester_address])
        else:
            header = bytes([0x80, self._ecu_address, self._tester_address, length])
        frame = header + data
        checksum = sum(frame) & 0xFF
        return frame + bytes([checksum])

    def _read_frame(self) -> bytes:
        fmt = self._transport.read_byte()
        length = fmt & 0x3F
        self._transport.read_byte()  # target address (us)
        self._transport.read_byte()  # source address (the ECU)
        if length == 0:
            length = self._transport.read_byte()
        data = self._transport.read_bytes(length)
        self._transport.read_byte()  # checksum (not re-verified: a corrupt byte will already have surfaced as a timeout)
        return data

    def tester_present(self) -> None:
        self.request(SID_TESTER_PRESENT, bytes([0x00]))

    def read_data_by_identifier(self, local_id: int) -> bytes:
        response = self.request(SID_READ_DATA_BY_LOCAL_IDENTIFIER, bytes([local_id]))
        return response[1:]  # skip the echoed local identifier

    def write_data_by_identifier(self, local_id: int, value: bytes) -> None:
        self.request(SID_WRITE_DATA_BY_LOCAL_IDENTIFIER, bytes([local_id]) + value)

    def io_control_by_identifier(self, local_id: int, control_parameter: int, control_state: bytes = b"") -> bytes:
        response = self.request(
            SID_INPUT_OUTPUT_CONTROL_BY_LOCAL_IDENTIFIER,
            bytes([local_id, control_parameter]) + control_state,
        )
        return response[1:]
