"""Enregistrement d'une session de lecture temps réel en CSV (Diagnostic >
Enregistrer une session), pour rouvrir un trajet dans un tableur.

Interface OBD2 uniquement : les valeurs viennent de Obd2Client.live_value(),
qui n'existe que pour cette interface (voir dtc.py). L'enregistrement
KKL/paramètres ECU n'est pas couvert ici.
"""
from __future__ import annotations

import csv
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from .dtc import valeur_numerique

DOSSIER_LOGS = Path("config/logs")

_CARACTERE_INVALIDE = re.compile(r"[^A-Za-z0-9_-]+")


def _nom_fichier_vehicule(vehicule: str) -> str:
    """Convertit un nom de véhicule libre (ex: "Renault Clio 4 (X98)") en un
    nom de fichier sûr : espaces -> underscore, tout le reste retiré."""
    slug = _CARACTERE_INVALIDE.sub("", vehicule.strip().replace(" ", "_"))
    return slug or "vehicule"


def chemin_session(dossier: Path = DOSSIER_LOGS, vehicule: Optional[str] = None) -> Path:
    dossier.mkdir(parents=True, exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefixe = f"session_{_nom_fichier_vehicule(vehicule)}" if vehicule else "session"
    return dossier / f"{prefixe}_{horodatage}.csv"


def enregistrer(
    obd2,
    commandes: List[Tuple[str, str]],
    duree_s: float,
    chemin: Optional[Path] = None,
    periode_s: float = 1.0,
    sur_tick: Optional[Callable[[int], None]] = None,
) -> Path:
    """Interroge `commandes` (nom python-obd, libellé) toutes les `periode_s`
    secondes et ajoute une ligne par cycle dans un CSV, pendant `duree_s`
    secondes (0 ou négatif = jusqu'à Ctrl+C). Renvoie le chemin du fichier
    écrit, y compris en cas d'arrêt anticipé par Ctrl+C.
    """
    chemin = chemin or chemin_session()
    entetes = ["horodatage"] + [label for _, label in commandes]

    fin = time.time() + duree_s if duree_s > 0 else None
    tick = 0
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        ecrivain = csv.writer(f)
        ecrivain.writerow(entetes)
        try:
            while fin is None or time.time() < fin:
                ligne = [datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]]
                for command_name, _ in commandes:
                    valeur = valeur_numerique(obd2.live_value(command_name))
                    ligne.append("" if valeur is None else valeur)
                ecrivain.writerow(ligne)
                f.flush()
                tick += 1
                if sur_tick:
                    sur_tick(tick)
                time.sleep(periode_s)
        except KeyboardInterrupt:
            pass
    return chemin
