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
        # Chaque effet lit lui-même le clavier pour s'interrompre plus tôt et
        # renvoie True s'il a consommé une touche : on se fie à cette valeur
        # plutôt que de revérifier le clavier ici, qui ne trouverait plus rien
        # (déjà lu) et laisserait repartir un cycle entier pour rien.
        if choix == "matrix":
            interrompu = effects.effet_matrix(duree=5.0)
        elif choix == "citations":
            interrompu = effects.galerie_citations(CITATIONS, CYAN)
        elif choix == "voiture":
            interrompu = effects.voiture_ascii(duree=6.0)
        else:
            interrompu = effects.glitch_flash()
        if interrompu:
            break
    clear_screen()


def _choisir_effet(veille_type: str) -> str:
    if veille_type in ("matrix", "citations", "glitch", "voiture"):
        return veille_type
    return random.choices(["matrix", "citations", "glitch", "voiture"], weights=[3, 3, 1, 3])[0]
