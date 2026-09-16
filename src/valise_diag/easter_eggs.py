"""Easter egg purement cosmétique déclenché en tapant "hack" sur le tableau de
bord (voir cli.py) : une mise en scène, aucune action réelle."""
from __future__ import annotations

import time

from . import effects
from .theme import GREEN, RED, YELLOW, print_centre

FAUX_LIGNES = [
    "Connexion au serveur distant...",
    "Analyse du pare-feu...",
    "Recherche de vulnérabilités...",
    "Tentative de contournement...",
    "Déchiffrement en cours...",
]


def sequence_piratage() -> None:
    print_centre("=== ACCÈS NON AUTORISÉ DÉTECTÉ ===", RED)
    time.sleep(0.5)
    for ligne in FAUX_LIGNES:
        effects.effet_frappe("> " + ligne, GREEN, 0.008)
        time.sleep(0.2)
    print()
    effects.decrypt_reveal_centre("ACCES REFUSE", RED, iterations=8, delai=0.04)
    time.sleep(0.3)
    print()
    print_centre("(simulation — aucune donnée n'a été touchée)", YELLOW)
    time.sleep(2)
