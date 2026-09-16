"""Scanner réseau (onglet Internet > Scanner réseau) — outil de travail
cybersécurité.

⚠️ N'utilisez ce scanner que sur des réseaux/hôtes que vous êtes autorisé à
tester : votre propre réseau, un engagement avec autorisation écrite, un
CTF... Scanner un réseau sans autorisation est un délit dans la plupart des
juridictions (en France : article 323-1 du code pénal — accès ou maintien
frauduleux dans un système de traitement automatisé de données).

S'appuie sur le binaire `nmap` (le standard du métier) plutôt que de
réimplémenter un scanner TCP en Python : nmap est très largement plus rapide
et plus fiable, ce qui compte d'autant plus sur un Pi Zero. Sortie récupérée
en XML (`-oX -`) et parsée avec la bibliothèque standard, plutôt que du texte
humain fragile à analyser.
"""
from __future__ import annotations

import shutil
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from . import system_status

DOSSIER_RAPPORTS = Path("config/scans")


class ErreurScan(RuntimeError):
    pass


@dataclass
class Port:
    numero: int
    protocole: str
    etat: str
    service: str
    version: str


@dataclass
class Hote:
    ip: str
    nom: str
    etat: str
    ports: List[Port] = field(default_factory=list)


@dataclass
class ResultatScan:
    cible: str
    commande: str
    hotes: List[Hote]
    horodatage: str


def nmap_disponible() -> bool:
    return shutil.which("nmap") is not None


def deviner_sous_reseau() -> Optional[str]:
    """Sous-réseau /24 probable à partir de l'IP locale (ex: 192.168.1.0/24).
    Une supposition raisonnable pour un réseau domestique, pas une garantie —
    l'utilisateur peut toujours saisir autre chose."""
    ip = system_status.get_ip()
    morceaux = ip.split(".")
    if len(morceaux) != 4:
        return None
    return ".".join(morceaux[:3]) + ".0/24"


def _executer_nmap(arguments: List[str], timeout_s: float) -> str:
    if not nmap_disponible():
        raise ErreurScan("nmap n'est pas installé (sudo apt install nmap).")
    try:
        resultat = subprocess.run(
            ["sudo", "nmap", *arguments, "-oX", "-"],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        raise ErreurScan(f"Scan interrompu après {int(timeout_s)}s (cible injoignable ou trop de ports).")
    if not resultat.stdout.strip():
        raise ErreurScan(resultat.stderr.strip() or "nmap n'a renvoyé aucun résultat.")
    return resultat.stdout


def _parser_xml(xml_text: str, cible: str, commande: str) -> ResultatScan:
    try:
        racine = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ErreurScan(f"Sortie nmap illisible : {exc}")

    hotes = []
    for host_el in racine.findall("host"):
        etat_el = host_el.find("status")
        etat = etat_el.get("state", "inconnu") if etat_el is not None else "inconnu"

        adresse_el = host_el.find("address")
        ip = adresse_el.get("addr", "?") if adresse_el is not None else "?"

        nom_el = host_el.find("hostnames/hostname")
        nom = nom_el.get("name", "") if nom_el is not None else ""

        ports = []
        for port_el in host_el.findall("ports/port"):
            etat_port_el = port_el.find("state")
            service_el = port_el.find("service")
            produit = service_el.get("product", "") if service_el is not None else ""
            version_num = service_el.get("version", "") if service_el is not None else ""
            ports.append(
                Port(
                    numero=int(port_el.get("portid", "0")),
                    protocole=port_el.get("protocol", "tcp"),
                    etat=etat_port_el.get("state", "?") if etat_port_el is not None else "?",
                    service=service_el.get("name", "") if service_el is not None else "",
                    version=" ".join(filter(None, [produit, version_num])),
                )
            )
        hotes.append(Hote(ip=ip, nom=nom, etat=etat, ports=ports))

    horodatage = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return ResultatScan(cible=cible, commande=commande, hotes=hotes, horodatage=horodatage)


def decouverte_hotes(sous_reseau: str) -> ResultatScan:
    """Ping sweep : quels hôtes répondent sur ce sous-réseau (ex: 192.168.1.0/24), sans scanner leurs ports."""
    arguments = ["-sn", sous_reseau]
    xml_text = _executer_nmap(arguments, timeout_s=120)
    return _parser_xml(xml_text, sous_reseau, "nmap -sn " + sous_reseau)


def scan_rapide(cible: str) -> ResultatScan:
    """Les 100 ports les plus courants, sans détection de version — quelques secondes à ~1 min."""
    arguments = ["-T3", "--top-ports", "100", cible]
    xml_text = _executer_nmap(arguments, timeout_s=180)
    return _parser_xml(xml_text, cible, "nmap --top-ports 100 " + cible)


def scan_standard(cible: str) -> ResultatScan:
    """~1000 ports les plus courants + détection de service/version — quelques minutes."""
    arguments = ["-T3", "-sV", cible]
    xml_text = _executer_nmap(arguments, timeout_s=600)
    return _parser_xml(xml_text, cible, "nmap -sV " + cible)


def scan_complet(cible: str) -> ResultatScan:
    """Les 65535 ports TCP + détection de service/version — peut prendre plusieurs dizaines de minutes."""
    arguments = ["-T3", "-p-", "-sV", cible]
    xml_text = _executer_nmap(arguments, timeout_s=3600)
    return _parser_xml(xml_text, cible, "nmap -p- -sV " + cible)


def scan_personnalise(cible: str, ports: str) -> ResultatScan:
    arguments = ["-T3", "-p", ports, "-sV", cible]
    xml_text = _executer_nmap(arguments, timeout_s=1800)
    return _parser_xml(xml_text, cible, f"nmap -p {ports} -sV " + cible)


def enregistrer_rapport(resultat: ResultatScan, dossier: Path = DOSSIER_RAPPORTS) -> Path:
    dossier.mkdir(parents=True, exist_ok=True)
    nom_fichier = "scan_" + resultat.horodatage.replace(" ", "_").replace(":", "-") + ".txt"
    chemin = dossier / nom_fichier
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(f"Cible : {resultat.cible}\n")
        f.write(f"Commande : {resultat.commande}\n")
        f.write(f"Date : {resultat.horodatage}\n\n")
        if not resultat.hotes:
            f.write("Aucun hôte trouvé.\n")
        for hote in resultat.hotes:
            f.write(f"Hôte {hote.ip} ({hote.nom or 'sans nom'}) — {hote.etat}\n")
            for port in hote.ports:
                ligne = f"  {port.numero}/{port.protocole} {port.etat} {port.service}"
                if port.version:
                    ligne += f" ({port.version})"
                f.write(ligne + "\n")
            f.write("\n")
    return chemin


def lister_rapports(dossier: Path = DOSSIER_RAPPORTS) -> List[Path]:
    if not dossier.exists():
        return []
    return sorted(dossier.glob("scan_*.txt"), reverse=True)
