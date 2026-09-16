"""Utilitaires réseau pour l'onglet Internet (statut, test de connectivité, Wi-Fi)."""
from __future__ import annotations

import socket
import subprocess
from dataclasses import dataclass
from typing import List


@dataclass
class NetworkStatus:
    hostname: str
    ip_addresses: List[str]
    internet_reachable: bool


def get_status(probe_host: str = "1.1.1.1", probe_port: int = 53, timeout_s: float = 2.0) -> NetworkStatus:
    return NetworkStatus(
        hostname=socket.gethostname(),
        ip_addresses=_local_ip_addresses(),
        internet_reachable=_can_reach(probe_host, probe_port, timeout_s),
    )


def _local_ip_addresses() -> List[str]:
    addresses = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            addr = info[4][0]
            if not addr.startswith("127."):
                addresses.add(addr)
    except socket.gaierror:
        pass
    return sorted(addresses)


def _can_reach(host: str, port: int, timeout_s: float) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return True
    except OSError:
        return False


def list_wifi_networks() -> List[str]:
    try:
        output = subprocess.run(
            ["nmcli", "-t", "-f", "SSID", "device", "wifi", "list"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        ).stdout
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return []
    return sorted({line.strip() for line in output.splitlines() if line.strip()})


def connect_wifi(ssid: str, password: str) -> str:
    """Connects via NetworkManager's nmcli. Returns a human-readable status line."""
    try:
        result = subprocess.run(
            ["nmcli", "device", "wifi", "connect", ssid, "password", password],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        return "nmcli introuvable : gestion Wi-Fi non disponible sur ce système."
    except subprocess.TimeoutExpired:
        return "Délai dépassé lors de la connexion Wi-Fi."
    return result.stdout.strip() or result.stderr.strip() or "Commande exécutée."
