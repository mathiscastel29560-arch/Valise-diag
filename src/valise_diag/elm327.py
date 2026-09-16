"""Low-level serial interface to a real ELM327-compatible OBD adapter."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Optional

import serial


class ELM327Error(RuntimeError):
    pass


class ELM327Timeout(ELM327Error):
    pass


@dataclass
class ELM327Config:
    port: str
    baudrate: int = 38400
    timeout_s: float = 2.0
    protocol: str = "AUTO"  # "AUTO" -> ATSP0 (adapter auto-detects the vehicle's OBD protocol)


class ELM327Serial:
    """Sends AT commands and raw OBD/UDS requests to a physical ELM327 adapter."""

    def __init__(self, config: ELM327Config):
        self._config = config
        self._ser: Optional[serial.Serial] = None

    def connect(self) -> None:
        self._ser = serial.Serial(
            self._config.port,
            self._config.baudrate,
            timeout=self._config.timeout_s,
        )
        self.reset()
        self._at("E0")  # echo off
        self._at("L0")  # linefeeds off
        self._at("S0")  # spaces off in the OBD (non-AT) parsing path
        self._at("H1")  # headers on: we need to see which ECU answered
        self._at("CAF1")  # CAN auto formatting: adapter reassembles multi-frame ISO-TP for us
        protocol_cmd = "SP0" if self._config.protocol == "AUTO" else f"SP{self._config.protocol}"
        self._at(protocol_cmd)

    def close(self) -> None:
        if self._ser and self._ser.is_open:
            self._ser.close()

    def reset(self) -> None:
        self._at("Z")
        time.sleep(1.0)

    def set_header(self, header_hex: str) -> None:
        self._at(f"SH {header_hex}")

    def set_receive_filter(self, header_hex: str) -> None:
        self._at(f"CRA {header_hex}")

    def send_raw(self, payload_hex: str) -> List[str]:
        """Send a raw hex payload (spaces optional) and return the raw reply lines."""
        return self._write(payload_hex.replace(" ", ""))

    def _at(self, cmd: str) -> List[str]:
        return self._write(f"AT{cmd}")

    def _write(self, line: str) -> List[str]:
        if not self._ser:
            raise ELM327Error("Adapter not connected: call connect() first")
        self._ser.reset_input_buffer()
        self._ser.write((line + "\r").encode("ascii"))
        self._ser.flush()
        return self._read_until_prompt()

    def _read_until_prompt(self) -> List[str]:
        buf = ""
        deadline = time.time() + self._config.timeout_s
        while time.time() < deadline:
            chunk = self._ser.read(self._ser.in_waiting or 1)
            if chunk:
                buf += chunk.decode("ascii", errors="ignore")
                if ">" in buf:
                    break
        else:
            raise ELM327Timeout("No prompt ('>') received from adapter before timeout")
        lines = [line.strip() for line in buf.replace(">", "").splitlines() if line.strip()]
        if lines and lines[0].upper().replace(" ", "") == "?":
            raise ELM327Error("Adapter did not understand the command")
        return lines
