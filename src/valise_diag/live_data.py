"""Catalogue des paramètres OBD-II temps réel (Mode 01), organisés par
catégorie pour l'onglet Diagnostic > Lecture temps réel.

Ne couvre que des identifiants standard SAE J1979 (aucune donnée
constructeur) : un véhicule donné peut ne pas tous les exposer, auquel cas la
lecture renvoie simplement "non disponible". Il n'existe pas de PID standard
appelé "pression turbo" : sur un moteur suralimenté, l'indicateur universel
est la pression d'admission (INTAKE_PRESSURE / capteur MAP), qui monte
au-dessus de la pression atmosphérique quand le turbo souffle.
"""
from __future__ import annotations

import sys
import termios
import time
import tty
from typing import Dict, List, Optional, Tuple

from . import effects
from .dtc import format_live_value, valeur_numerique
from .theme import CYAN, GREEN, MAGENTA, RED, RESET, YELLOW, afficher_bloc_centre, boite_titre

CATEGORIE_MOTEUR = "Moteur"
CATEGORIE_ADMISSION = "Admission / suralimentation"
CATEGORIE_CARBURANT = "Carburant"
CATEGORIE_ECHAPPEMENT = "Échappement / dépollution"
CATEGORIE_ELECTRIQUE = "Électrique / divers"

CATALOGUE: Dict[str, List[Tuple[str, str]]] = {
    CATEGORIE_MOTEUR: [
        ("RPM", "Régime moteur"),
        ("SPEED", "Vitesse véhicule"),
        ("ENGINE_LOAD", "Charge moteur calculée"),
        ("COOLANT_TEMP", "Température liquide de refroidissement"),
        ("OIL_TEMP", "Température huile moteur"),
        ("TIMING_ADVANCE", "Avance à l'allumage"),
        ("RUN_TIME", "Temps moteur tournant"),
    ],
    CATEGORIE_ADMISSION: [
        ("INTAKE_PRESSURE", "Pression admission (MAP — indicateur de suralimentation turbo)"),
        ("MAF", "Débit d'air admis (MAF)"),
        ("THROTTLE_POS", "Position papillon des gaz"),
        ("INTAKE_TEMP", "Température air admission"),
        ("BAROMETRIC_PRESSURE", "Pression atmosphérique"),
        ("AMBIANT_AIR_TEMP", "Température air ambiant"),
    ],
    CATEGORIE_CARBURANT: [
        ("FUEL_PRESSURE", "Pression carburant (injection indirecte)"),
        ("FUEL_RAIL_PRESSURE_DIRECT", "Pression rampe d'injection directe"),
        ("FUEL_RAIL_PRESSURE_VAC", "Pression rampe (relative au vide)"),
        ("FUEL_RAIL_PRESSURE_ABS", "Pression rampe (absolue)"),
        ("FUEL_LEVEL", "Niveau de carburant"),
        ("FUEL_RATE", "Débit de carburant"),
        ("SHORT_FUEL_TRIM_1", "Correction carburant court terme — banc 1"),
        ("LONG_FUEL_TRIM_1", "Correction carburant long terme — banc 1"),
        ("SHORT_FUEL_TRIM_2", "Correction carburant court terme — banc 2"),
        ("LONG_FUEL_TRIM_2", "Correction carburant long terme — banc 2"),
        ("ETHANOL_PERCENT", "Taux d'éthanol"),
        ("COMMANDED_EQUIV_RATIO", "Richesse du mélange commandée (λ — 1.0 = stœchiométrique)"),
    ],
    CATEGORIE_ECHAPPEMENT: [
        ("O2_B1S1", "Sonde O2 — banc 1 capteur 1"),
        ("O2_B1S2", "Sonde O2 — banc 1 capteur 2"),
        ("O2_B2S1", "Sonde O2 — banc 2 capteur 1"),
        ("CATALYST_TEMP_B1S1", "Température catalyseur — banc 1"),
        ("COMMANDED_EGR", "EGR commandée"),
        ("EGR_ERROR", "Erreur EGR"),
        ("EVAP_VAPOR_PRESSURE", "Pression vapeur circuit EVAP"),
    ],
    CATEGORIE_ELECTRIQUE: [
        ("CONTROL_MODULE_VOLTAGE", "Tension calculateur"),
        ("HYBRID_BATTERY_REMAINING", "Charge batterie hybride restante"),
    ],
}


def categories() -> List[str]:
    return list(CATALOGUE.keys())


def commands_for(categorie: str) -> List[Tuple[str, str]]:
    return CATALOGUE[categorie]


def all_commands() -> List[Tuple[str, str]]:
    result: List[Tuple[str, str]] = []
    for commandes in CATALOGUE.values():
        result.extend(commandes)
    return result


# Seuils indicatifs génériques (bas, haut) — pas des limites constructeur ni
# un régime moteur "rouge" (ça dépend du moteur) : juste des bornes de bon
# sens, dans l'esprit de ce qu'affichent en rouge les applis OBD généralistes
# (ex: tension batterie/alternateur, corrections carburant anormalement
# grandes, surchauffe). None = pas de borne de ce côté. Un paramètre absent
# de cette table n'est jamais coloré, plutôt que d'inventer un seuil.
SEUILS_ALERTE: Dict[str, Tuple[Optional[float], Optional[float]]] = {
    "COOLANT_TEMP": (None, 110.0),
    "OIL_TEMP": (None, 130.0),
    "CONTROL_MODULE_VOLTAGE": (11.0, 15.5),
    "SHORT_FUEL_TRIM_1": (-25.0, 25.0),
    "LONG_FUEL_TRIM_1": (-25.0, 25.0),
    "SHORT_FUEL_TRIM_2": (-25.0, 25.0),
    "LONG_FUEL_TRIM_2": (-25.0, 25.0),
    "EGR_ERROR": (-25.0, 25.0),
}


def valeur_anormale(nom_commande: str, valeur: Optional[float]) -> bool:
    bornes = SEUILS_ALERTE.get(nom_commande)
    if bornes is None or valeur is None or not isinstance(valeur, (int, float)):
        return False
    bas, haut = bornes
    if bas is not None and valeur < bas:
        return True
    if haut is not None and valeur > haut:
        return True
    return False


# PID standard SAE J1979 liés à l'entretien — pas un intervalle de révision
# (vidange, etc.), qui n'est jamais exposé génériquement en OBD-II standard
# (propriétaire au constructeur, affiché seulement sur le combiné
# d'instruments) : ceci indique depuis quand/combien les codes défaut ont
# été effacés pour la dernière fois, ce qui est standardisé.
PIDS_ENTRETIEN: List[Tuple[str, str]] = [
    ("DISTANCE_SINCE_DTC_CLEAR", "Distance depuis effacement des codes"),
    ("TIME_SINCE_DTC_CLEARED", "Temps depuis effacement des codes"),
    ("WARMUPS_SINCE_DTC_CLEAR", "Cycles moteur depuis effacement des codes"),
    ("DISTANCE_W_MIL", "Distance parcourue avec voyant moteur allumé"),
    ("RUN_TIME_MIL", "Temps moteur avec voyant allumé"),
]

INTERVALLE_RAFRAICHISSEMENT_S = 1.0


def _lire_valeur_securisee(obd2, commande: str):
    try:
        return obd2.live_value(commande)
    except Exception:  # noqa: BLE001 - matériel externe, une lecture ratée ne doit pas interrompre l'affichage
        return None


def boucle_lecture_temps_reel(obd2, commandes: List[Tuple[str, str]], intervalle_s: float = INTERVALLE_RAFRAICHISSEMENT_S) -> None:
    """Affichage continu (rafraîchi toutes les `intervalle_s` secondes) des
    valeurs demandées, en rouge quand elles sortent des seuils indicatifs de
    SEUILS_ALERTE. Une touche quelconque revient au menu."""
    fd = sys.stdin.fileno()
    reglages = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    try:
        while True:
            if effects.touche_en_attente():
                return

            lignes = boite_titre("LECTURE TEMPS REEL", MAGENTA, CYAN) + [""]
            for nom, label in commandes:
                brute = _lire_valeur_securisee(obd2, nom)
                texte = format_live_value(brute)
                nombre = valeur_numerique(brute)
                couleur = RED if valeur_anormale(nom, nombre) else GREEN
                lignes.append(f"{label[:44]:<44}{couleur}{texte}{RESET}")
            lignes.append("")
            lignes.append(
                YELLOW
                + f"Rafraîchi toutes les {intervalle_s:g}s — appuyez sur une touche pour revenir au menu."
                + RESET
            )
            afficher_bloc_centre(lignes)
            time.sleep(intervalle_s)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, reglages)
