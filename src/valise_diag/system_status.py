"""Statistiques système pour le tableau de bord (CPU, RAM, disque, wifi...).

Toutes les fonctions renvoient None (ou un tuple de None) plutôt que de lever
une exception quand l'information n'est pas disponible (ex : hors d'un
Raspberry Pi, ou en conteneur) — le tableau de bord affiche alors "N/A"."""
from __future__ import annotations

import shutil
import socket
import subprocess
import time
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


class MoniteurSysteme:
    """État du tableau de bord entre deux rafraîchissements.

    Le pourcentage CPU se calcule sur un delta entre deux lectures de
    /proc/stat, donc a besoin d'état. La température (vcgencmd, un
    sous-processus) et l'adresse IP (un socket) sont mises en cache quelques
    secondes : elles ne changent presque jamais d'un rafraîchissement à
    l'autre (le tableau de bord se redessine ~1x/s), et relancer un
    sous-processus chaque seconde coûte cher sur un Pi Zero premier du nom
    (mono-cœur, ~1 GHz).
    """

    def __init__(self, ttl_temperature_s: float = 5.0, ttl_ip_s: float = 20.0) -> None:
        self._cpu_precedent: Optional[Tuple[int, int]] = None
        self._ttl_temperature_s = ttl_temperature_s
        self._ttl_ip_s = ttl_ip_s
        self._temperature_cache: Tuple[Optional[float], float] = (None, 0.0)
        self._ip_cache: Tuple[Optional[str], float] = (None, 0.0)

    def cpu_pct(self) -> Optional[float]:
        try:
            with open("/proc/stat") as f:
                ligne = f.readline()
            valeurs = [int(x) for x in ligne.split()[1:]]
            idle = valeurs[3] + valeurs[4]
            total = sum(valeurs)
        except Exception:
            return None
        if self._cpu_precedent is None:
            self._cpu_precedent = (idle, total)
            return 0.0
        idle_prev, total_prev = self._cpu_precedent
        delta_idle = idle - idle_prev
        delta_total = total - total_prev
        self._cpu_precedent = (idle, total)
        if delta_total <= 0:
            return 0.0
        return (1 - delta_idle / delta_total) * 100

    def temperature_cpu(self) -> Optional[float]:
        valeur, expire_a = self._temperature_cache
        maintenant = time.monotonic()
        if maintenant >= expire_a:
            valeur = lire_temp_cpu()
            self._temperature_cache = (valeur, maintenant + self._ttl_temperature_s)
        return valeur

    def adresse_ip(self) -> str:
        valeur, expire_a = self._ip_cache
        maintenant = time.monotonic()
        if maintenant >= expire_a or valeur is None:
            valeur = get_ip()
            self._ip_cache = (valeur, maintenant + self._ttl_ip_s)
        return valeur


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
