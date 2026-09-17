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

from typing import Dict, List, Tuple

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
