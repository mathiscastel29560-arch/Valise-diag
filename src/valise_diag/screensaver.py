"""Écran de veille (onglet Paramètres > veille) : matrix / citations / glitch."""
from __future__ import annotations

import random

from . import effects
from .theme import CYAN, clear_screen

CITATIONS = [
    '"La route est longue, le protocole est court."',
    '"Chaque code défaut raconte une histoire."',
    '"Débranche, rebranche, espère."',
    '"VALISE DIAG — en veille, prête à repartir."',
    '"Un bon diagnostic commence par une bonne question."',
]


def ecran_veille(veille_type: str) -> None:
    clear_screen()
    while True:
        if effects.touche_en_attente():
            break
        choix = _choisir_effet(veille_type)
        if choix == "matrix":
            effects.effet_matrix(duree=5.0)
        elif choix == "citations":
            effects.galerie_citations(CITATIONS, CYAN)
        else:
            effects.glitch_flash()
        if effects.touche_en_attente():
            break
    clear_screen()


def _choisir_effet(veille_type: str) -> str:
    if veille_type in ("matrix", "citations", "glitch"):
        return veille_type
    return random.choices(["matrix", "citations", "glitch"], weights=[3, 3, 1])[0]
