"""Statistiques système pour le tableau de bord (CPU, RAM, disque, wifi...).

Toutes les fonctions renvoient None (ou un tuple de None) plutôt que de lever
une exception quand l'information n'est pas disponible (ex : hors d'un
Raspberry Pi, ou en conteneur) — le tableau de bord affiche alors "N/A"."""
from __future__ import annotations

import shutil
import socket
import subprocess
from typing import Optional, Tuple


def get_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "hors ligne"


def lire_temp_cpu() -> Optional[float]:
    try:
        out = subprocess.check_output(["vcgencmd", "measure_temp"], timeout=2).decode()
        return float(out.split("=")[1].split("'")[0])
    except Exception:
        return None


class LecteurCpu:
    """Le pourcentage CPU se calcule sur un delta entre deux lectures de
    /proc/stat : on garde donc un peu d'état entre deux appels."""

    def __init__(self) -> None:
        self._precedent: Optional[Tuple[int, int]] = None

    def lire_pct(self) -> Optional[float]:
        try:
            with open("/proc/stat") as f:
                ligne = f.readline()
            valeurs = [int(x) for x in ligne.split()[1:]]
            idle = valeurs[3] + valeurs[4]
            total = sum(valeurs)
        except Exception:
            return None
        if self._precedent is None:
            self._precedent = (idle, total)
            return 0.0
        idle_prev, total_prev = self._precedent
        delta_idle = idle - idle_prev
        delta_total = total - total_prev
        self._precedent = (idle, total)
        if delta_total <= 0:
            return 0.0
        return (1 - delta_idle / delta_total) * 100


def lire_ram() -> Tuple[Optional[float], Optional[float], Optional[float]]:
    try:
        with open("/proc/meminfo") as f:
            lignes = f.readlines()
        infos = {}
        for ligne in lignes:
            parts = ligne.split(":")
            if len(parts) == 2:
                infos[parts[0].strip()] = int(parts[1].strip().split()[0])
        total = infos.get("MemTotal", 0)
        dispo = infos.get("MemAvailable", 0)
        if not total:
            return None, None, None
        utilise = total - dispo
        return utilise / 1024, total / 1024, utilise / total * 100
    except Exception:
        return None, None, None


def lire_disque() -> Tuple[Optional[float], Optional[float], Optional[float]]:
    try:
        total, utilise, _ = shutil.disk_usage("/")
        return utilise / (1024**3), total / (1024**3), utilise / total * 100
    except Exception:
        return None, None, None


def lire_uptime() -> Tuple[Optional[int], Optional[int]]:
    try:
        with open("/proc/uptime") as f:
            secondes = float(f.readline().split()[0])
        return int(secondes // 3600), int((secondes % 3600) // 60)
    except Exception:
        return None, None


def lire_wifi_signal() -> Optional[int]:
    try:
        with open("/proc/net/wireless") as f:
            lignes = f.readlines()
        for ligne in lignes[2:]:
            if "wlan0" in ligne:
                return int(float(ligne.split(":")[1].split()[1]))
        return None
    except Exception:
        return None
