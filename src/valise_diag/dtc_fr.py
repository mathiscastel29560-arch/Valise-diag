"""Traduction française des codes défauts OBD-II génériques les plus courants.

`python-obd` fournit déjà une description (en anglais) pour ~2000 codes,
tirée de sa propre table (voir `obd.codes.DTC`) — `Obd2Client.read_dtcs()`
la renvoie telle quelle. Cette table ne couvre qu'un sous-ensemble des codes
génériques SAE J2012 les plus fréquents (ratés d'allumage, richesse du
mélange, sondes O2, EGR/EVAP, catalyseur, capteurs d'admission...) : pour un
code absent d'ici, `decrire()` retombe sur la description anglaise de
python-obd, puis sur un message générique si elle aussi est vide.

Seuls les codes P0xxx/P2xxx génériques sont couverts : les codes P1xxx/P3xxx
et les codes réseau/carrosserie (B/C/U) sont en grande partie spécifiques au
constructeur, donc hors de portée d'une table générique.
"""
from __future__ import annotations

TRADUCTIONS_FR = {
    # Ratés d'allumage
    "P0300": "Ratés d'allumage détectés, cylindres multiples ou aléatoires",
    "P0301": "Raté d'allumage détecté, cylindre 1",
    "P0302": "Raté d'allumage détecté, cylindre 2",
    "P0303": "Raté d'allumage détecté, cylindre 3",
    "P0304": "Raté d'allumage détecté, cylindre 4",
    "P0305": "Raté d'allumage détecté, cylindre 5",
    "P0306": "Raté d'allumage détecté, cylindre 6",
    "P0307": "Raté d'allumage détecté, cylindre 7",
    "P0308": "Raté d'allumage détecté, cylindre 8",
    "P0351": "Circuit primaire/secondaire bobine d'allumage A",
    "P0352": "Circuit primaire/secondaire bobine d'allumage B",
    "P0353": "Circuit primaire/secondaire bobine d'allumage C",
    "P0354": "Circuit primaire/secondaire bobine d'allumage D",
    "P0325": "Circuit capteur de cliquetis — banc 1",
    "P0330": "Circuit capteur de cliquetis — banc 2",
    # Richesse du mélange / trims
    "P0171": "Mélange trop pauvre — banc 1",
    "P0172": "Mélange trop riche — banc 1",
    "P0174": "Mélange trop pauvre — banc 2",
    "P0175": "Mélange trop riche — banc 2",
    "P0128": "Thermostat — température de liquide de refroidissement trop basse",
    # Sondes O2
    "P0130": "Circuit sonde O2 — banc 1 capteur 1",
    "P0131": "Sonde O2 tension basse — banc 1 capteur 1",
    "P0132": "Sonde O2 tension haute — banc 1 capteur 1",
    "P0133": "Sonde O2 réponse lente — banc 1 capteur 1",
    "P0134": "Sonde O2 pas d'activité détectée — banc 1 capteur 1",
    "P0135": "Circuit chauffage sonde O2 — banc 1 capteur 1",
    "P0136": "Circuit sonde O2 — banc 1 capteur 2",
    "P0141": "Circuit chauffage sonde O2 — banc 1 capteur 2",
    "P0150": "Circuit sonde O2 — banc 2 capteur 1",
    "P0155": "Circuit chauffage sonde O2 — banc 2 capteur 1",
    # Capteurs d'admission
    "P0100": "Circuit débitmètre d'air (MAF) — défaut",
    "P0101": "Débitmètre d'air (MAF) — plage/performance",
    "P0102": "Débitmètre d'air (MAF) — signal faible",
    "P0103": "Débitmètre d'air (MAF) — signal fort",
    "P0105": "Circuit pression collecteur d'admission (MAP) — défaut",
    "P0106": "Capteur MAP — plage/performance",
    "P0107": "Capteur MAP — signal faible",
    "P0108": "Capteur MAP — signal fort",
    "P0110": "Circuit capteur température d'air admission — défaut",
    "P0113": "Capteur température d'air admission — signal fort",
    "P0115": "Circuit capteur température liquide de refroidissement — défaut",
    "P0117": "Capteur température liquide de refroidissement — signal faible",
    "P0118": "Capteur température liquide de refroidissement — signal fort",
    "P0120": "Circuit capteur position papillon/pédale A — défaut",
    "P0121": "Capteur position papillon A — plage/performance",
    "P0122": "Capteur position papillon A — signal faible",
    "P0123": "Capteur position papillon A — signal fort",
    # Suralimentation / turbo
    "P0234": "Suralimentation excessive (surpression turbo/compresseur)",
    "P0299": "Sous-suralimentation (dépression turbo/compresseur)",
    "P0243": "Électrovanne de régulation turbo A — défaut électrique",
    "P0245": "Électrovanne de régulation turbo A — signal faible",
    "P0246": "Électrovanne de régulation turbo A — signal fort",
    # Injection / rampe carburant
    "P0087": "Pression rampe carburant trop basse",
    "P0088": "Pression rampe carburant trop haute",
    "P0089": "Régulateur de pression carburant — performance",
    "P0191": "Capteur pression rampe carburant — plage/performance",
    "P0192": "Capteur pression rampe carburant — signal faible",
    "P0193": "Capteur pression rampe carburant — signal fort",
    "P0201": "Circuit injecteur cylindre 1 — défaut",
    "P0202": "Circuit injecteur cylindre 2 — défaut",
    "P0203": "Circuit injecteur cylindre 3 — défaut",
    "P0204": "Circuit injecteur cylindre 4 — défaut",
    # EGR
    "P0400": "Débit EGR — défaut",
    "P0401": "Débit EGR insuffisant",
    "P0402": "Débit EGR excessif",
    "P0403": "Circuit électrovanne EGR — défaut",
    "P0404": "Électrovanne EGR — plage/performance",
    "P0405": "Capteur position EGR A — signal faible",
    "P0406": "Capteur position EGR A — signal fort",
    # EVAP
    "P0440": "Circuit EVAP — défaut général",
    "P0441": "Circuit EVAP — débit de purge incorrect",
    "P0442": "Circuit EVAP — fuite détectée (petite fuite)",
    "P0443": "Circuit électrovanne de purge EVAP — défaut",
    "P0446": "Circuit de mise à l'air libre EVAP — défaut",
    "P0455": "Circuit EVAP — fuite détectée (grosse fuite)",
    "P0456": "Circuit EVAP — fuite détectée (très petite fuite)",
    "P0457": "Circuit EVAP — fuite détectée (bouchon mal remis)",
    # Catalyseur
    "P0420": "Rendement catalyseur insuffisant — banc 1",
    "P0421": "Catalyseur de préchauffage — rendement insuffisant, banc 1",
    "P0430": "Rendement catalyseur insuffisant — banc 2",
    # Filtre à particules
    "P2002": "Rendement filtre à particules insuffisant — banc 1",
    "P2003": "Rendement filtre à particules insuffisant — banc 2",
    "P2463": "Filtre à particules — accumulation de suie excessive",
    "P244A": "Différentiel de pression filtre à particules trop bas — banc 1",
    "P244B": "Différentiel de pression filtre à particules trop haut — banc 1",
    # Régime / vitesse / ralenti
    "P0500": "Capteur de vitesse véhicule — défaut",
    "P0501": "Capteur de vitesse véhicule — plage/performance",
    "P0505": "Circuit de régulation de ralenti — défaut",
    "P0506": "Régime de ralenti trop bas",
    "P0507": "Régime de ralenti trop haut",
    "P0562": "Tension système trop basse",
    "P0563": "Tension système trop haute",
    # Transmission
    "P0700": "Défaut détecté par le calculateur de boîte de vitesses",
    "P0715": "Capteur régime d'entrée de boîte — circuit défectueux",
    "P0720": "Capteur régime de sortie de boîte — circuit défectueux",
    "P0730": "Rapport de boîte incorrect",
    "P0740": "Circuit d'embrayage de convertisseur de couple — défaut",
    # Réseau / calculateur
    "U0100": "Perte de communication avec le calculateur moteur/module de commande",
    "U0101": "Perte de communication avec le calculateur de boîte de vitesses",
    "P0600": "Circuit de communication série — défaut",
    "P0601": "Mémoire calculateur — erreur de somme de contrôle",
    "P0603": "Calculateur — erreur mémoire vive (KAM)",
    "P0606": "Calculateur — performance du processeur interne",
}


def decrire(code: str, description_originale: str = "") -> str:
    """Description en français si le code est répertorié ici, sinon la
    description de python-obd (généralement en anglais) si elle existe,
    sinon un message générique."""
    if code in TRADUCTIONS_FR:
        return TRADUCTIONS_FR[code]
    if description_originale:
        return description_originale
    return "code non répertorié — consultez une base de codes OBD2 pour plus de détails"
