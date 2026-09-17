"""Sauvegarde/restauration de la configuration (app.yaml, profil véhicule,
profils enregistrés, historique) dans une archive horodatée — utile avant
une réinstallation ou un reclonage du dépôt, pour ne pas repartir de zéro
sur les réglages (rien de tout ceci n'est suivi par Git, voir .gitignore).
"""
from __future__ import annotations

import tarfile
from datetime import datetime
from pathlib import Path
from typing import List

DOSSIER_SAUVEGARDES = Path("config/sauvegardes")

FICHIERS_A_SAUVEGARDER = [
    Path("config/app.yaml"),
    Path("config/vehicle_profile.yaml"),
    Path("config/historique.log"),
]
DOSSIERS_A_SAUVEGARDER = [
    Path("config/vehicles"),
]


def creer_sauvegarde(dossier: Path = DOSSIER_SAUVEGARDES) -> Path:
    """Archive tar.gz horodatée. Les chemins internes reproduisent
    l'arborescence (config/app.yaml, config/vehicles/...) : restaurer revient
    juste à extraire l'archive à la racine du projet."""
    dossier.mkdir(parents=True, exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    chemin = dossier / f"sauvegarde_{horodatage}.tar.gz"
    with tarfile.open(chemin, "w:gz") as archive:
        for fichier in FICHIERS_A_SAUVEGARDER:
            if fichier.exists():
                archive.add(fichier, arcname=str(fichier))
        for sous_dossier in DOSSIERS_A_SAUVEGARDER:
            if sous_dossier.exists():
                archive.add(sous_dossier, arcname=str(sous_dossier))
    return chemin


def lister_sauvegardes(dossier: Path = DOSSIER_SAUVEGARDES) -> List[Path]:
    if not dossier.exists():
        return []
    return sorted(dossier.glob("sauvegarde_*.tar.gz"), reverse=True)


def restaurer_sauvegarde(chemin: Path, destination: Path = Path(".")) -> None:
    """Écrase les fichiers de config actuels avec ceux de l'archive —
    l'appelant est responsable de confirmer avant d'appeler ceci."""
    with tarfile.open(chemin, "r:gz") as archive:
        archive.extractall(destination, filter="data")
