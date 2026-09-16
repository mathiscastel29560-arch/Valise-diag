"""KW1281 ("KWP1281") block-oriented protocol used by many pre-2004 VAG ECUs
over a classic K-line KKL cable.

The framing (length/counter/title/data/0x03 block structure) and the
byte-by-byte complement-echo handshake implemented here follow the widely
published KW1281 protocol description used by essentially every open-source
VAG-COM-compatible tool.

Block *titles* — what a given block number actually means for a given ECU
and model year (read fault codes, clear fault codes, read a measuring
group...) — are NOT hardcoded here: they vary between ECU generations and
must be supplied via your vehicle profile's `blocks:` map, from
documentation you legitimately hold. See docs/SECURITE.md.
"""
from __future__ import annotations

from dataclasses import dataclass

from .kkl import KKLSerial

BLOCK_END = 0x03
ACK_TITLE = 0x09  # commonly used as a bare acknowledgement block title in KW1281


class KWP1281Error(RuntimeError):
    pass


@dataclass
class Block:
    title: int
    data: bytes


class KWP1281Client:
    def __init__(self, transport: KKLSerial, ecu_address: int):
        self._transport = transport
        self._ecu_address = ecu_address
        self._block_counter = 0

    def connect(self) -> None:
        self._transport.connect()
        self._transport.slow_init(self._ecu_address)
        self.receive_block()  # the ECU's identification block; also syncs the block counter
        self.send_ack()

    def receive_block(self) -> Block:
        length = self._read_and_ack()
        counter = self._read_and_ack()
        title = self._read_and_ack()
        data = bytearray()
        for _ in range(max(length - 3, 0)):  # length counts counter + title + data, not itself
            data.append(self._read_and_ack())
        end = self._transport.read_byte()
        if end != BLOCK_END:
            raise KWP1281Error(f"Expected block end 0x03, got {end:#04x}")
        self._block_counter = counter
        return Block(title=title, data=bytes(data))

    def send_block(self, title: int, data: bytes = b"") -> None:
        self._block_counter = (self._block_counter + 1) & 0xFF
        length = 3 + len(data)
        payload = bytes([length, self._block_counter, title]) + data
        for byte in payload:
            self._write_and_wait_ack(byte)
        self._transport.write_byte(BLOCK_END)

    def send_ack(self) -> None:
        self.send_block(ACK_TITLE)

    def request(self, request_title: int, request_data: bytes = b"") -> Block:
        """Send a request block, ECU-ack the reply, and return it."""
        self.send_block(request_title, request_data)
        response = self.receive_block()
        self.send_ack()
        return response

    def _read_and_ack(self) -> int:
        value = self._transport.read_byte()
        self._transport.write_byte(0xFF - value)
        return value

    def _write_and_wait_ack(self, value: int) -> None:
        self._transport.write_byte(value)
        ack = self._transport.read_byte()
        expected = 0xFF - value
        if ack != expected:
            raise KWP1281Error(f"ECU did not acknowledge byte {value:#04x} (got {ack:#04x})")
