"""Détection du constructeur à partir du VIN (World Manufacturer Identifier,
les 3 premiers caractères du VIN) + petit logo ASCII décoratif associé.

Le WMI est un standard public (ISO 3780) : ce module se limite à un
sous-ensemble courant de constructeurs, pas une base complète — un WMI
absent de la table renvoie simplement "constructeur inconnu", jamais une
supposition. Ça ne remplace pas un décodage VIN complet (modèle, usine,
année) : ces informations-là restent propriétaires au constructeur et ne
sont pas fiables à déduire génériquement, contrairement au WMI.
"""
from __future__ import annotations

from typing import Optional

# Sous-ensemble courant du registre public WMI (ISO 3780). Certains WMI sont
# partagés entre marques d'un même groupe ou selon l'usine d'assemblage :
# c'est une meilleure estimation, pas une garantie absolue.
WMI_MARQUES = {
    "VF1": "Renault",
    "VF2": "Renault",
    "VF6": "Renault (utilitaires)",
    "VF3": "Peugeot",
    "VF7": "Citroën",
    "VF8": "Peugeot/Citroën (DS)",
    "VF9": "Bugatti / Alpine",
    "UU1": "Dacia",
    "WVW": "Volkswagen",
    "WV1": "Volkswagen (utilitaires)",
    "WV2": "Volkswagen (utilitaires)",
    "WAU": "Audi",
    "WBA": "BMW",
    "WBS": "BMW M",
    "WBY": "BMW (électrique)",
    "WDB": "Mercedes-Benz",
    "WDD": "Mercedes-Benz",
    "WP0": "Porsche",
    "VSS": "SEAT",
    "TMB": "Škoda",
    "ZFA": "Fiat",
    "ZAR": "Alfa Romeo",
    "ZLA": "Lancia",
    "SAJ": "Jaguar",
    "SAL": "Land Rover",
    "JHM": "Honda",
    "JH4": "Honda",
    "JN1": "Nissan",
    "JT2": "Toyota",
    "JTD": "Toyota",
    "JTE": "Toyota",
    "KMH": "Hyundai",
    "KNA": "Kia",
    "KNM": "Kia",
    "YV1": "Volvo",
    "YS3": "Saab",
}

_LOGO_DEFAUT = r"""
   .-------.
  /  ?    \
 |  MARQUE  |
  \  ??    /
   '-------'
"""

LOGOS_ASCII = {
    "Renault": r"""
      /\
     /  \
    / /\ \
   / /  \ \
  /_/    \_\
""",
    "Peugeot": r"""
     _
   .' '.
  /  .  \
 |  / \  |
  \  '  /
   '._.'
""",
    "Citroën": r"""
   /\      /\
  /  \    /  \
 /    \  /    \
/      \/      \
""",
    "Volkswagen": r"""
     ______
   .'  VW  '.
  /  ______  \
 |  |      |  |
  \  '.__.'  /
   '.______.'
""",
    "Audi": r"""
   __ __ __ __
  (__)(__)(__)(__)
""",
    "BMW": r"""
    .------.
   / .----. \
  | | \  / | |
  | |  \/  | |
   \ '----' /
    '------'
""",
    "Mercedes-Benz": r"""
       ___
      /   \
   __| * * |__
  |__ *   * __|
      \___/
""",
    "Dacia": r"""
   ______
  / DACIA \
  \________/
""",
    "Škoda": r"""
     __
    /--\
   /    \
   \_/\_/
""",
}


def marque_depuis_vin(vin: Optional[str]) -> Optional[str]:
    """Renvoie le nom du constructeur d'après le WMI (3 premiers caractères du
    VIN), ou None si le VIN est absent/trop court ou le WMI inconnu de cette
    table — jamais une supposition."""
    if not vin or len(vin) < 3:
        return None
    return WMI_MARQUES.get(vin[:3].upper())


def logo_ascii(marque: Optional[str]) -> str:
    """Logo ASCII décoratif pour la marque, ou un placeholder générique si la
    marque est inconnue/absente — purement cosmétique, ne prétend pas
    reproduire fidèlement un logo officiel."""
    if marque:
        for nom, art in LOGOS_ASCII.items():
            if nom.lower() in marque.lower():
                return art
    return _LOGO_DEFAUT
