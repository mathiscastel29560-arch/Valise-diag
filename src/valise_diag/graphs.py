"""Graphiques temps réel ASCII pour suivre le comportement moteur en direct —
pratique pour comparer un "avant/après" une intervention (reprogrammation
pro, boîtier additionnel) sans quitter la valise.

Deux vues : une vue d'ensemble compacte (sparklines sur une ligne, comme un
tableau de bord) et une vue "zoom" sur une seule courbe, en plusieurs lignes
avec des points reliés par des traits — bien plus lisible comme une vraie
courbe qu'une sparkline d'un seul caractère de haut.

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

_BLOCS = " ▁▂▃▄▅▆▇█"  # index 0 = pas de donnée, 1-8 = intensité croissante (vue d'ensemble)
_POINT = "●"
_TRAIT = "│"

LARGEUR_GRAPHE = 28
LARGEUR_LIBELLE = 32
HAUTEUR_COURBE = 9  # vue zoom : plus de lignes = courbe plus lisible

# Sélection pensée pour surveiller turbo/injection/richesse plutôt qu'une
# liste exhaustive (voir live_data.py pour le catalogue complet). L'avance à
# l'allumage ne concerne que les moteurs essence : sur un diesel, elle
# s'affichera normalement en "N/D", ce qui est le comportement attendu, pas
# un bug.
PARAMETRES_PAR_DEFAUT: List[Tuple[str, str]] = [
    ("RPM", "Régime moteur (proxy puiss.)"),
    ("ENGINE_LOAD", "Charge moteur (proxy puiss.)"),
    ("INTAKE_PRESSURE", "Pression admission (turbo)"),
    ("FUEL_RAIL_PRESSURE_DIRECT", "Pression rail injection"),
    ("FUEL_RATE", "Débit carburant (proxy puiss.)"),
    ("TIMING_ADVANCE", "Avance allumage (essence)"),
    ("COMMANDED_EGR", "EGR commandée (diesel)"),
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


def dessiner_courbe(valeurs: List[Optional[float]], hauteur: int = HAUTEUR_COURBE) -> List[str]:
    """Trace une courbe ASCII sur plusieurs lignes : un point par valeur
    connue, relié au point précédent par un trait vertical quand le niveau
    change — se lit comme une vraie courbe, pas comme une simple sparkline."""
    connues = [v for v in valeurs if v is not None]
    if not connues:
        return [" " * len(valeurs) for _ in range(hauteur)]
    vmin, vmax = min(connues), max(connues)
    etendue = vmax - vmin

    def rangee_pour(v: float) -> int:
        if etendue == 0:
            return hauteur // 2
        return round((v - vmin) / etendue * (hauteur - 1))

    grille = [[" "] * len(valeurs) for _ in range(hauteur)]
    precedente: Optional[int] = None
    for x, v in enumerate(valeurs):
        if v is None:
            precedente = None
            continue
        rangee = hauteur - 1 - rangee_pour(v)  # rangée 0 = haut d'écran = valeur max
        grille[rangee][x] = _POINT
        if precedente is not None and precedente != rangee:
            debut, fin = sorted((precedente, rangee))
            for y in range(debut + 1, fin):
                if grille[y][x] == " ":
                    grille[y][x] = _TRAIT
        precedente = rangee
    return ["".join(rangee) for rangee in grille]


def _lire_valeur(obd2: Obd2Client, commande: str) -> Optional[float]:
    try:
        valeur = valeur_numerique(obd2.live_value(commande))
    except Exception:  # noqa: BLE001 - matériel externe, une lecture ratée ne doit pas interrompre le graphe
        return None
    return valeur if isinstance(valeur, (int, float)) else None


def _rendu_vue_ensemble(parametres: List[Tuple[str, str]], tampons: Dict[str, Deque[Optional[float]]]) -> List[str]:
    lignes = boite_titre("GRAPHIQUES TEMPS REEL", MAGENTA, CYAN) + [""]
    for i, (nom, libelle) in enumerate(parametres, start=1):
        valeurs = list(tampons[nom])
        spark = rendu_sparkline(valeurs)
        dernier = next((v for v in reversed(valeurs) if v is not None), None)
        texte_valeur = f"{dernier:.3g}" if dernier is not None else "N/D"
        libelle_fixe = f"[{i}] {libelle}"[:LARGEUR_LIBELLE].ljust(LARGEUR_LIBELLE)
        lignes.append(f"{libelle_fixe}{GREEN}{spark}{RESET} {texte_valeur}")
    lignes.append("")
    lignes.append(YELLOW + f"1-{len(parametres)} : zoomer sur une courbe   |   q : retour au menu" + RESET)
    return lignes


def _rendu_zoom(libelle: str, valeurs: List[Optional[float]]) -> List[str]:
    connues = [v for v in valeurs if v is not None]
    dernier = next((v for v in reversed(valeurs) if v is not None), None)
    lignes = boite_titre(libelle.upper()[:38], MAGENTA, CYAN) + [""]
    if not connues:
        lignes.append("Aucune donnée pour l'instant (N/D).")
    else:
        vmax, vmin = max(connues), min(connues)
        courbe = dessiner_courbe(valeurs)
        texte_max = f"{vmax:.3g}".ljust(8)
        texte_min = f"{vmin:.3g}".ljust(8)
        for i, rangee in enumerate(courbe):
            etiquette = texte_max if i == 0 else (texte_min if i == len(courbe) - 1 else " " * 8)
            lignes.append(f"{etiquette}{GREEN}{rangee}{RESET}")
        texte_valeur = f"{dernier:.3g}" if dernier is not None else "N/D"
        lignes.append("")
        lignes.append(f"Valeur actuelle : {texte_valeur}")
    lignes.append("")
    lignes.append(YELLOW + "q : retour au menu   |   autre touche : vue d'ensemble" + RESET)
    return lignes


def boucle_graphiques(obd2: Obd2Client, parametres: Optional[List[Tuple[str, str]]] = None, intervalle_s: float = 0.8) -> None:
    parametres = parametres or PARAMETRES_PAR_DEFAUT
    largeur = max(LARGEUR_GRAPHE, 40)
    tampons: Dict[str, Deque[Optional[float]]] = {
        nom: deque([None] * largeur, maxlen=largeur) for nom, _ in parametres
    }
    zoom: Optional[int] = None  # index dans `parametres`, None = vue d'ensemble

    fd = sys.stdin.fileno()
    reglages = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    try:
        while True:
            touche = effects.touche_en_attente()
            if touche is not None:
                if touche.lower() == "q":
                    return
                if zoom is None and touche.isdigit() and 1 <= int(touche) <= len(parametres):
                    zoom = int(touche) - 1
                elif zoom is not None:
                    zoom = None

            for nom, _ in parametres:
                tampons[nom].append(_lire_valeur(obd2, nom))

            if zoom is None:
                lignes = _rendu_vue_ensemble(parametres, tampons)
            else:
                nom, libelle = parametres[zoom]
                lignes = _rendu_zoom(libelle, list(tampons[nom]))
            afficher_bloc_centre(lignes)
            time.sleep(intervalle_s)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, reglages)
