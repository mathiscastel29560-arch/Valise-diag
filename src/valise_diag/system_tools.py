"""Outils système/développeur (onglet Système) : accès shell, éditeur, mise à
jour du système, police console, démarrage automatique.

Distinct de l'onglet Programmation : ici on touche au Raspberry Pi lui-même,
jamais au véhicule."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .config import POLICES
from .theme import GREEN, RESET

AUTOSTART_DISABLE_FILE = Path.home() / ".autostart_disabled"


def ouvrir_shell() -> None:
    subprocess.run(["bash"])


def ouvrir_python_repl() -> None:
    subprocess.run(["python3"])


def editer_fichier(nom: str) -> None:
    subprocess.run(["nano", nom])


def appliquer_police(nom: str) -> bool:
    fichier = POLICES.get(nom)
    if fichier is None:
        return True
    try:
        subprocess.run(["sudo", "setfont", fichier], timeout=10, check=True)
        return True
    except Exception:
        return False


def appliquer_autostart(actif: bool) -> bool:
    try:
        if actif:
            AUTOSTART_DISABLE_FILE.unlink(missing_ok=True)
        else:
            AUTOSTART_DISABLE_FILE.touch()
        return True
    except OSError:
        return False


def infos_systeme() -> str:
    lignes = []
    try:
        out = subprocess.check_output(["vcgencmd", "measure_temp"], timeout=2).decode().strip()
        lignes.append(f"Température CPU : {out.split('=')[1]}")
    except Exception:
        lignes.append("Température CPU : non disponible")

    try:
        total, utilise, _ = shutil.disk_usage("/")
        lignes.append(f"Disque : {utilise / (1024**3):.1f} / {total / (1024**3):.1f} Go utilisés")
    except Exception:
        lignes.append("Disque : non disponible")

    try:
        uptime = subprocess.check_output(["uptime", "-p"], timeout=2).decode().strip()
        lignes.append(f"Uptime : {uptime}")
    except Exception:
        lignes.append("Uptime : non disponible")

    return "\n".join(lignes)


def mettre_a_jour_systeme(confirmer: bool) -> None:
    if not confirmer:
        print("Annulé.")
        return
    subprocess.run(["sudo", "apt-get", "update"])
    subprocess.run(["sudo", "apt-get", "upgrade", "-y"])
    print(GREEN + "Mise à jour terminée." + RESET)


def eteindre_pi() -> None:
    subprocess.run(["sudo", "shutdown", "-h", "now"])
