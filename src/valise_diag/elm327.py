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


@dataclass
class DiagnosticAdaptateur:
    """Résultat d'un sondage AT brut du port série (voir diagnostiquer_port) —
    volontairement séparé de ELM327Serial, qui lève une exception si le
    prompt ">" n'arrive jamais : ici on veut justement pouvoir observer une
    absence de réponse plutôt que la transformer en erreur."""

    port: str
    baudrate: int
    reponse_atz: str = ""
    reponse_atsp0: str = ""
    reponse_0100: str = ""
    erreur_ouverture: Optional[str] = None

    @property
    def adaptateur_repond(self) -> bool:
        return bool(self.reponse_atz.strip())

    @property
    def vehicule_repond(self) -> bool:
        reponse = self.reponse_0100.upper()
        if not reponse.strip():
            return False
        return not any(mot in reponse for mot in ("NO DATA", "UNABLE TO CONNECT", "ERROR", "?"))


def diagnostiquer_port(port: str, baudrate: int = 38400, timeout_s: float = 2.0) -> DiagnosticAdaptateur:
    """Envoie ATZ / ATSP0 / 0100 directement sur le port, sans négociation de
    protocole ni interprétation — pour distinguer un adaptateur qui ne
    répond pas du tout (port/débit/câble) d'un véhicule qui ne répond pas
    malgré un adaptateur fonctionnel."""
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout_s)
    except Exception as exc:  # noqa: BLE001 - matériel externe, on veut le message tel quel
        return DiagnosticAdaptateur(port=port, baudrate=baudrate, erreur_ouverture=str(exc))

    def envoyer(commande: str, attente_s: float) -> str:
        ser.write((commande + "\r").encode("ascii"))
        time.sleep(attente_s)
        return ser.read(500).decode(errors="replace")

    try:
        atz = envoyer("ATZ", 1.0)
        atsp0 = envoyer("ATSP0", 0.5)
        pid0100 = envoyer("0100", 2.0)
    finally:
        ser.close()

    return DiagnosticAdaptateur(port=port, baudrate=baudrate, reponse_atz=atz, reponse_atsp0=atsp0, reponse_0100=pid0100)


# Codes ATSP (protocole ELM327) couverts par diagnostiquer_protocoles, du plus
# probable (CAN, véhicules 2008+) au moins probable (protocoles pré-CAN) —
# certains clones bon marché ont une auto-négociation (ATSP0) buguée qui
# échoue alors qu'un protocole précis, une fois forcé, fonctionne très bien.
PROTOCOLES_TESTABLES = [
    ("6", "CAN 11 bits, 500 kbit/s"),
    ("7", "CAN 29 bits, 500 kbit/s"),
    ("8", "CAN 11 bits, 250 kbit/s"),
    ("9", "CAN 29 bits, 250 kbit/s"),
    ("3", "ISO 9141-2"),
    ("4", "ISO 14230-4 KWP2000 (init lent)"),
    ("5", "ISO 14230-4 KWP2000 (init rapide)"),
]


@dataclass
class ResultatProtocole:
    code: str
    libelle: str
    reponse_0100: str = ""

    @property
    def fonctionne(self) -> bool:
        reponse = self.reponse_0100.upper()
        if not reponse.strip():
            return False
        return not any(mot in reponse for mot in ("NO DATA", "UNABLE TO CONNECT", "ERROR", "?"))


def diagnostiquer_protocoles(
    port: str, baudrate: int = 38400, timeout_s: float = 2.0
) -> List[ResultatProtocole]:
    """Force chaque protocole ELM327 un par un (au lieu de laisser
    l'adaptateur négocier via ATSP0/AUTO) et note lesquels obtiennent une
    vraie réponse à 0100. Renvoie une liste vide si le port ne s'ouvre pas."""
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout_s)
    except Exception:  # noqa: BLE001 - matériel externe, déjà signalé par diagnostiquer_port
        return []

    def envoyer(commande: str, attente_s: float) -> str:
        ser.write((commande + "\r").encode("ascii"))
        time.sleep(attente_s)
        return ser.read(500).decode(errors="replace")

    resultats: List[ResultatProtocole] = []
    try:
        for code, libelle in PROTOCOLES_TESTABLES:
            # ATZ (reset complet) avant chaque essai plutôt qu'un simple ATPC
            # ("protocol close") entre deux tentatives : certains clones bon
            # marché implémentent mal ATPC et restent bloqués dans l'état du
            # protocole précédent, faussant l'essai suivant. ATZ est la
            # commande la plus basique et la plus universellement supportée.
            envoyer("ATZ", 1.0)
            envoyer(f"ATSP{code}", 0.3)
            reponse = envoyer("0100", 1.5)
            resultats.append(ResultatProtocole(code=code, libelle=libelle, reponse_0100=reponse))
    finally:
        ser.close()

    return resultats
