"""Low-level K-line (ISO 9141-2 / ISO 14230) serial interface for a KKL-style cable.

A "KKL 409.1"-type cable (the classic VAG-COM USB K-line adapter) only
supports the 5-baud slow initialization sequence — there is no CAN and
usually no fast-init. This module implements that handshake plus the raw
byte-level read/write primitives that kwp1281.py and kwp2000.py build on.

Exact timing (baud rates, inter-byte gaps) varies between ECUs and cable
clones; the defaults below follow the commonly documented ISO 14230-2
values but may need adjusting for a specific vehicle.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional, Tuple

import serial


class KKLError(RuntimeError):
    pass


class KKLTimeout(KKLError):
    pass


@dataclass
class KKLConfig:
    port: str
    init_baudrate: int = 5  # the address byte is clocked out at 5 bit/s
    comms_baudrate: int = 10400  # typical KWP2000/KW1281 post-init baud; some ECUs use 9600
    timeout_s: float = 2.0


class KKLSerial:
    def __init__(self, config: KKLConfig):
        self._config = config
        self._ser: Optional[serial.Serial] = None

    def connect(self) -> None:
        self._ser = serial.Serial(self._config.port, self._config.comms_baudrate, timeout=self._config.timeout_s)

    def close(self) -> None:
        if self._ser and self._ser.is_open:
            self._ser.close()

    def slow_init(self, address: int) -> Tuple[int, int]:
        """5-baud slow init. Returns the two key bytes (KW1, KW2) sent by the ECU."""
        if not self._ser:
            raise KKLError("Adapter not connected: call connect() first")
        self._ser.baudrate = self._config.init_baudrate
        self._ser.write(bytes([address]))
        self._ser.flush()
        # one start bit + 8 data bits + one stop bit, at init_baudrate bit/s
        time.sleep(10 / self._config.init_baudrate + 0.05)
        self._ser.baudrate = self._config.comms_baudrate
        self._ser.reset_input_buffer()

        sync = self._read_byte()
        if sync != 0x55:
            raise KKLError(f"Expected sync byte 0x55, got {sync:#04x}")
        kw1 = self._read_byte()
        kw2 = self._read_byte()
        time.sleep(0.025)
        self.write_byte(0xFF ^ kw2)  # complement of KW2, per ISO 14230-2 timing
        return kw1, kw2

    def write_byte(self, value: int) -> None:
        if not self._ser:
            raise KKLError("Adapter not connected: call connect() first")
        self._ser.write(bytes([value & 0xFF]))
        self._ser.flush()

    def read_byte(self) -> int:
        return self._read_byte()

    def read_bytes(self, count: int) -> bytes:
        return bytes(self._read_byte() for _ in range(count))

    def _read_byte(self) -> int:
        data = self._ser.read(1)
        if not data:
            raise KKLTimeout("No byte received from ECU before timeout")
        return data[0]
