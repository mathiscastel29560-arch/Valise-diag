"""Graphiques temps réel en ASCII (sparklines) pour suivre le comportement
moteur en direct — pratique pour comparer un "avant/après" une intervention
(reprogrammation pro, boîtier additionnel) sans quitter la valise.

Il n'existe pas de PID OBD-II standard pour la puissance moteur (ça se
mesure sur un banc, pas par l'ECU) : régime et charge moteur servent ici de
proxys de tendance, explicitement étiquetés comme tels — jamais un chiffre
de puissance inventé.
"""
from __future__ import annotations

import sys
import termios
import time
import tty
from collections import deque
from typing import Deque, Dict, List, Optional, Tuple

from . import effects
from .dtc import Obd2Client, valeur_numerique
from .theme import CYAN, GREEN, MAGENTA, RESET, YELLOW, afficher_bloc_centre, boite_titre

_BLOCS = " ▁▂▃▄▅▆▇█"  # index 0 = pas de donnée, 1-8 = intensité croissante
LARGEUR_GRAPHE = 28

# Sélection pensée pour surveiller turbo/injection/richesse plutôt qu'une
# liste exhaustive (voir live_data.py pour le catalogue complet). L'avance à
# l'allumage ne concerne que les moteurs essence : sur un diesel, elle
# s'affichera normalement en "N/D", ce qui est le comportement attendu, pas
# un bug.
LARGEUR_LIBELLE = 32

PARAMETRES_PAR_DEFAUT: List[Tuple[str, str]] = [
    ("RPM", "Régime moteur (proxy puiss.)"),
    ("ENGINE_LOAD", "Charge moteur (proxy puiss.)"),
    ("INTAKE_PRESSURE", "Pression admission (turbo)"),
    ("FUEL_RAIL_PRESSURE_DIRECT", "Pression rail injection"),
    ("FUEL_RATE", "Débit carburant (proxy puiss.)"),
    ("TIMING_ADVANCE", "Avance allumage (essence)"),
]


def rendu_sparkline(valeurs: List[Optional[float]]) -> str:
    """Convertit une série de valeurs (None = pas de donnée à cet instant) en
    une ligne de blocs Unicode, mise à l'échelle sur le min/max de la fenêtre
    affichée — pas d'échelle fixe par paramètre, qui serait fausse pour
    certains moteurs (ex : la pression rail varie énormément entre modèles)."""
    connues = [v for v in valeurs if v is not None]
    if not connues:
        return " " * len(valeurs)
    vmin, vmax = min(connues), max(connues)
    etendue = vmax - vmin
    caracteres = []
    for v in valeurs:
        if v is None:
            caracteres.append(" ")
        elif etendue == 0:
            caracteres.append(_BLOCS[4])
        else:
            niveau = 1 + int((v - vmin) / etendue * 7)
            caracteres.append(_BLOCS[niveau])
    return "".join(caracteres)


def _lire_valeur(obd2: Obd2Client, commande: str) -> Optional[float]:
    try:
        valeur = valeur_numerique(obd2.live_value(commande))
    except Exception:  # noqa: BLE001 - matériel externe, une lecture ratée ne doit pas interrompre le graphe
        return None
    return valeur if isinstance(valeur, (int, float)) else None


def boucle_graphiques(obd2: Obd2Client, parametres: Optional[List[Tuple[str, str]]] = None, intervalle_s: float = 0.8) -> None:
    parametres = parametres or PARAMETRES_PAR_DEFAUT
    tampons: Dict[str, Deque[Optional[float]]] = {
        nom: deque([None] * LARGEUR_GRAPHE, maxlen=LARGEUR_GRAPHE) for nom, _ in parametres
    }

    fd = sys.stdin.fileno()
    reglages = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    try:
        while True:
            if effects.touche_en_attente():
                return

            for nom, _ in parametres:
                tampons[nom].append(_lire_valeur(obd2, nom))

            lignes = boite_titre("GRAPHIQUES TEMPS REEL", MAGENTA, CYAN) + [""]
            for nom, libelle in parametres:
                valeurs = list(tampons[nom])
                spark = rendu_sparkline(valeurs)
                dernier = next((v for v in reversed(valeurs) if v is not None), None)
                texte_valeur = f"{dernier:.3g}" if dernier is not None else "N/D"
                libelle_fixe = libelle[:LARGEUR_LIBELLE].ljust(LARGEUR_LIBELLE)
                lignes.append(f"{libelle_fixe}{GREEN}{spark}{RESET} {texte_valeur}")
            lignes.append("")
            lignes.append(YELLOW + "Appuyez sur une touche pour revenir au menu." + RESET)
            afficher_bloc_centre(lignes)
            time.sleep(intervalle_s)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, reglages)
