"""Relit une session CSV déjà enregistrée (voir session_log.py) : soit pour
la rejouer en courbe (graphs.dessiner_courbe), soit pour comparer deux
sessions entre elles (ex: avant/après un boîtier additionnel ou une
reprogrammation faite par un professionnel).
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def lire_csv(chemin: Path) -> Tuple[List[str], Dict[str, List[Optional[float]]]]:
    """Renvoie (colonnes de données dans l'ordre du fichier, valeurs par
    colonne). La colonne "horodatage" est ignorée : ces courbes se rejouent
    par index, pas par heure réelle."""
    with open(chemin, newline="", encoding="utf-8") as f:
        lecteur = csv.reader(f)
        entetes = next(lecteur)[1:]  # ignore "horodatage"
        colonnes: Dict[str, List[Optional[float]]] = {nom: [] for nom in entetes}
        for ligne in lecteur:
            for nom, brut in zip(entetes, ligne[1:]):
                try:
                    colonnes[nom].append(float(brut) if brut != "" else None)
                except ValueError:
                    colonnes[nom].append(None)
    return entetes, colonnes


def statistiques(valeurs: List[Optional[float]]) -> Optional[Tuple[float, float, float]]:
    """(min, max, moyenne) des valeurs connues, ou None si aucune valeur
    exploitable (colonne entièrement vide)."""
    connues = [v for v in valeurs if v is not None]
    if not connues:
        return None
    return min(connues), max(connues), sum(connues) / len(connues)


def echantillonner(valeurs: List[Optional[float]], largeur: int) -> List[Optional[float]]:
    """Réduit une série à `largeur` points en la découpant en tranches
    régulières (moyenne des valeurs connues de chaque tranche) — pour
    afficher une session entière dans la largeur du terminal sans la
    tronquer aux derniers points comme le ferait une simple troncature."""
    if not valeurs or largeur <= 0:
        return []
    if len(valeurs) <= largeur:
        return list(valeurs)
    resultat: List[Optional[float]] = []
    taille_tranche = len(valeurs) / largeur
    for i in range(largeur):
        debut = int(i * taille_tranche)
        fin = max(int((i + 1) * taille_tranche), debut + 1)
        tranche = [v for v in valeurs[debut:fin] if v is not None]
        resultat.append(sum(tranche) / len(tranche) if tranche else None)
    return resultat


def colonnes_communes(entetes_a: List[str], entetes_b: List[str]) -> List[str]:
    """Colonnes présentes dans les deux sessions, dans l'ordre de la première
    — seules celles-là peuvent être comparées de façon sensée."""
    ensemble_b = set(entetes_b)
    return [nom for nom in entetes_a if nom in ensemble_b]
