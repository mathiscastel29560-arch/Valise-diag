import pytest

from valise_diag.kwp2000 import KWP2000Client
from valise_diag.uds import UDSNegativeResponse


class _FakeTransport:
    def __init__(self, response_bytes: bytes = b""):
        self._rx = list(response_bytes)
        self.tx = []

    def write_byte(self, value: int) -> None:
        self.tx.append(value)

    def read_byte(self) -> int:
        return self._rx.pop(0)

    def read_bytes(self, count: int) -> bytes:
        return bytes(self.read_byte() for _ in range(count))


def _frame(payload: bytes, ecu_address: int = 0x01, tester_address: int = 0xF1) -> bytes:
    header = bytes([0x80 | len(payload), ecu_address, tester_address])
    body = header + payload
    return body + bytes([sum(body) & 0xFF])


def test_build_frame_header_and_checksum():
    client = KWP2000Client(_FakeTransport(), ecu_address=0x01, tester_address=0xF1)
    frame = client._build_frame(bytes([0x21, 0x10]))
    assert frame[:3] == bytes([0x82, 0x01, 0xF1])  # 0x80 | length(2)
    assert frame[3:5] == bytes([0x21, 0x10])
    assert frame[-1] == sum(frame[:-1]) & 0xFF


def test_read_data_by_identifier_positive_response():
    response = _frame(bytes([0x61, 0x10, 0xAB]))  # SID 0x21 + 0x40, echoed LID, one data byte
    client = KWP2000Client(_FakeTransport(response), ecu_address=0x01, tester_address=0xF1)
    assert client.read_data_by_identifier(0x10) == bytes([0xAB])


def test_negative_response_raises_with_correct_nrc():
    response = _frame(bytes([0x7F, 0x21, 0x31]))  # NRC 0x31 = requestOutOfRange
    client = KWP2000Client(_FakeTransport(response), ecu_address=0x01, tester_address=0xF1)
    with pytest.raises(UDSNegativeResponse) as excinfo:
        client.read_data_by_identifier(0x10)
    assert excinfo.value.nrc == 0x31
