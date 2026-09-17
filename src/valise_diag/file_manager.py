"""Petit gestionnaire de fichiers (Système > Gestionnaire de fichiers) pour
parcourir/consulter/supprimer les fichiers que la valise génère elle-même
(sessions CSV, rapports de scan réseau, profils véhicule), sans avoir à
connaître les commandes shell — le terminal libre reste disponible pour
tout le reste.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from . import netscan, profiles, session_log

DOSSIERS_SURVEILLES: Dict[str, Path] = {
    "Sessions CSV": session_log.DOSSIER_LOGS,
    "Rapports de scan réseau": netscan.DOSSIER_RAPPORTS,
    "Profils véhicule": profiles.DOSSIER_PROFILS,
}


def formater_taille(octets: int) -> str:
    if octets < 1024:
        return f"{octets} o"
    if octets < 1024 * 1024:
        return f"{octets / 1024:.1f} Ko"
    return f"{octets / (1024 * 1024):.1f} Mo"


def lister(dossier: Path) -> List[Tuple[Path, int, float]]:
    """Fichiers du dossier (chemin, taille en octets, date de modification en
    timestamp Unix), les plus récents d'abord. Dossier absent -> liste vide,
    pas une erreur (rien n'a encore été généré)."""
    if not dossier.exists():
        return []
    fichiers = [(p, p.stat().st_size, p.stat().st_mtime) for p in dossier.iterdir() if p.is_file()]
    return sorted(fichiers, key=lambda t: t[2], reverse=True)


def supprimer(chemin: Path) -> None:
    """Supprime un fichier — uniquement s'il est dans un des dossiers
    surveillés, pour ne jamais effacer autre chose par erreur de saisie."""
    dossiers_autorises = {d.resolve() for d in DOSSIERS_SURVEILLES.values() if d.exists()}
    if chemin.resolve().parent not in dossiers_autorises:
        raise ValueError(f"Suppression refusée : '{chemin}' n'est pas dans un dossier surveillé.")
    chemin.unlink()
