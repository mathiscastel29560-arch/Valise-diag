"""Utilitaires réseau pour l'onglet Internet (statut, ping, débit, Wi-Fi, navigation)."""
from __future__ import annotations

import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import List, Optional

from .theme import CYAN, GREEN, RED, RESET, largeur_terminal


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


def ouvrir_configuration_wifi() -> None:
    """Lance l'éditeur Wi-Fi plein écran de NetworkManager (nmtui)."""
    try:
        subprocess.run(["sudo", "nmtui"])
    except FileNotFoundError:
        print(RED + "nmtui introuvable sur ce système." + RESET)


def naviguer(url: str) -> None:
    """Ouvre une page dans le navigateur texte w3m (léger, adapté à un Pi Zero)."""
    try:
        subprocess.run(["w3m", url])
    except FileNotFoundError:
        print(RED + "w3m n'est pas installé (sudo apt install w3m)." + RESET)


def ping_anime(cible: str, nb: int = 4) -> None:
    largeur = min(largeur_terminal(), 50)
    for i in range(nb):
        for pos in range(0, largeur, 2):
            sys.stdout.write("\r" + CYAN + "[" + "-" * pos + ">" + " " * (largeur - pos) + "]" + RESET)
            sys.stdout.flush()
            time.sleep(0.01)
        try:
            resultat = subprocess.run(["ping", "-c", "1", "-W", "2", cible], capture_output=True, text=True)
        except FileNotFoundError:
            print(RED + "  ping n'est pas disponible sur ce système." + RESET)
            return
        sys.stdout.write("\r" + " " * (largeur + 2) + "\r")
        if resultat.returncode == 0:
            lignes_temps = [l for l in resultat.stdout.split("\n") if "time=" in l]
            temps = lignes_temps[0].split("time=")[1].split(" ")[0] if lignes_temps else "?"
            print(GREEN + f"  Paquet {i + 1} reçu - {temps} ms" + RESET)
        else:
            print(RED + f"  Paquet {i + 1} perdu" + RESET)


def mesurer_debit(taille_octets: int = 10_000_000, timeout_s: float = 20.0) -> Optional[float]:
    """Télécharge un fichier test et renvoie le débit mesuré en Mbps, ou None en cas d'échec."""
    try:
        resultat = subprocess.run(
            [
                "curl", "-o", "/dev/null", "-s", "-w", "%{time_total} %{size_download}",
                f"https://speed.cloudflare.com/__down?bytes={taille_octets}",
            ],
            capture_output=True, text=True, timeout=timeout_s,
        )
        temps_str, taille_str = resultat.stdout.strip().split()
        temps, taille = float(temps_str), float(taille_str)
        if temps <= 0 or taille <= 0:
            return None
        return (taille * 8) / (temps * 1_000_000)
    except Exception:
        return None


def commentaire_debit(mbps: float) -> str:
    if mbps < 1:
        return "Très lent — à peine mieux qu'un pigeon voyageur."
    if mbps < 5:
        return "Ça avance... doucement."
    if mbps < 20:
        return "Correct, sans plus."
    if mbps < 50:
        return "Ça envoie plutôt bien !"
    if mbps < 150:
        return "Débit solide."
    return "Très rapide."
