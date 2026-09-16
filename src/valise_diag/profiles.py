"""Plusieurs profils véhicule enregistrés (Paramètres > Profil véhicule).

Chaque profil est un simple fichier YAML dans config/vehicles/, copié depuis
le profil actuellement actif (config.AppConfig.vehicle_profile_path). Changer
de véhicule revient à pointer vehicle_profile_path vers l'un de ces fichiers.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import List

DOSSIER_PROFILS = Path("config/vehicles")

_NOM_INVALIDE = re.compile(r"[^A-Za-z0-9 _-]")


class NomProfilInvalide(ValueError):
    pass


def nom_valide(nom: str) -> bool:
    nom = nom.strip()
    return bool(nom) and ".." not in nom and not _NOM_INVALIDE.search(nom)


def lister_profils(dossier: Path = DOSSIER_PROFILS) -> List[str]:
    if not dossier.exists():
        return []
    return sorted(p.stem for p in dossier.glob("*.yaml"))


def chemin_profil(nom: str, dossier: Path = DOSSIER_PROFILS) -> Path:
    if not nom_valide(nom):
        raise NomProfilInvalide(f"Nom de profil invalide : '{nom}' (lettres, chiffres, espace, - et _ uniquement)")
    return dossier / f"{nom.strip()}.yaml"


def enregistrer_profil_actuel(chemin_actuel: str, nom: str, dossier: Path = DOSSIER_PROFILS) -> Path:
    destination = chemin_profil(nom, dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    shutil.copy(chemin_actuel, destination)
    return destination
