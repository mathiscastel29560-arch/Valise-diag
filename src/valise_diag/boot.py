"""Écran de démarrage : logo en reveal, scroll de logs, barre de progression."""
from __future__ import annotations

import time

from . import effects
from .theme import CYAN, GREEN, MAGENTA, YELLOW, clear_screen, print_centre

LOGO = r"""
   _____ _    _____ _____ ___ _
  / ____/ \  / ____|_   _/ __| |
 | |    /   \\___ \ | || |__| |
 | |___/ /_\ \___) || ||  __| |___
  \_____\_/ \_\____/ |_||_|  |____|
        V A L I S E   D I A G
"""

_LOGS = [
    "kernel: initialisation des sous-systèmes",
    "usb: détection des adaptateurs série (ELM327 / KKL)",
    "diag: pilote UDS (ISO 14229) chargé",
    "diag: pilote KWP2000 (ISO 14230) chargé",
    "diag: pilote KW1281 chargé",
    "fs: profil véhicule chargé",
    "sys: garde-fous de sécurité activés",
    "net: interface réseau prête",
    "sec: verrouillage console vérifié",
    "core: menu principal prêt",
]


def show_boot_screen(rapide: bool = False) -> None:
    duree_logs = 0.4 if rapide else 1.6
    iterations_logo = 3 if rapide else 10
    duree_barre = 0.4 if rapide else 1.5

    clear_screen()
    print_centre("CHARGEMENT DES MODULES", YELLOW)
    print()
    effects.defilement_logs(_LOGS, duree=duree_logs)
    effects.decrypt_reveal_centre(LOGO, MAGENTA, iterations=iterations_logo, delai=0.03)
    print()
    effects.barre_progression(duree_barre, 36, CYAN)
    print_centre("STATUS: SYSTÈME OPÉRATIONNEL", GREEN)
    time.sleep(0.2 if rapide else 0.8)
