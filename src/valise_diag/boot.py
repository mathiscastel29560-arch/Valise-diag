"""Écran de démarrage : œuvre ASCII + séquence de chargement avant le menu principal."""
from __future__ import annotations

import shutil
import sys
import time

ASCII_ART = r"""
        ______________________
       /|                    |\
      / |     VALISE DIAG    | \
     /__|____________________|__\
     |    ___    ___    ___    |
     |   | O |  | O |  | O |   |
     |   |___|  |___|  |___|   |
     |__________________________|
          ||              ||
         [==]            [==]
"""

_STEPS = [
    "Initialisation du matériel...",
    "Détection de l'interface (OBD2 / KKL)...",
    "Chargement du profil véhicule...",
    "Vérification des garde-fous de sécurité...",
    "Prêt.",
]


def show_boot_screen(duration_s: float = 1.5) -> None:
    width = shutil.get_terminal_size(fallback=(80, 24)).columns
    print("\n".join(line.center(width) for line in ASCII_ART.splitlines()))
    print("VALISE DE DIAGNOSTIC OBD2 / KKL".center(width))
    print()
    step_delay = max(duration_s / len(_STEPS), 0.05)
    for step in _STEPS:
        sys.stdout.write(f"  [..] {step}\r")
        sys.stdout.flush()
        time.sleep(step_delay)
        sys.stdout.write(f"  [OK] {step}\n")
    time.sleep(0.3)
