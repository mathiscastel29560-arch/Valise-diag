"""État des monitorings antipollution avant un contrôle technique — PID
standard SAE J1979 (Mode 01 PID 01 "Status since DTCs cleared"), pas une
estimation ni une garantie de résultat au contrôle : ça reflète ce que
l'ECU elle-même considère prêt/pas prêt.
"""
from __future__ import annotations

from typing import List, NamedTuple, Optional, Tuple


class EtatMonitorings(NamedTuple):
    voyant_moteur_allume: bool
    nombre_codes_actifs: int
    type_allumage: str  # "spark" (essence) ou "compression" (diesel)
    monitorings: List[Tuple[str, bool, bool]]  # (nom, disponible, complet)


def lire_etat(obd2) -> Optional[EtatMonitorings]:
    """None si le véhicule ne répond pas à ce PID (adaptateur non connecté,
    ECU muette) — jamais une valeur inventée."""
    status = obd2.live_value("STATUS")
    if status is None:
        return None

    monitorings = []
    for nom, valeur in vars(status).items():
        if nom in ("MIL", "DTC_count", "ignition_type"):
            continue
        monitorings.append((valeur.name, valeur.available, valeur.complete))

    return EtatMonitorings(
        voyant_moteur_allume=status.MIL,
        nombre_codes_actifs=status.DTC_count,
        type_allumage=status.ignition_type,
        monitorings=monitorings,
    )


def pret_pour_controle(etat: EtatMonitorings) -> bool:
    """Prêt si le voyant moteur est éteint et que tous les monitorings
    disponibles sur ce véhicule sont marqués complets — les monitorings non
    disponibles (non applicables à ce moteur) ne comptent pas contre lui."""
    if etat.voyant_moteur_allume:
        return False
    return all(complet for _, disponible, complet in etat.monitorings if disponible)
