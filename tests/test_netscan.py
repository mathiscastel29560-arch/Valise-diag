from valise_diag import netscan

XML_EXEMPLE = """<?xml version="1.0"?>
<nmaprun>
  <host>
    <status state="up"/>
    <address addr="192.168.1.10" addrtype="ipv4"/>
    <hostnames><hostname name="routeur.lan" type="PTR"/></hostnames>
    <ports>
      <port protocol="tcp" portid="22">
        <state state="open"/>
        <service name="ssh" product="OpenSSH" version="9.2"/>
      </port>
      <port protocol="tcp" portid="80">
        <state state="closed"/>
        <service name="http"/>
      </port>
    </ports>
  </host>
  <host>
    <status state="down"/>
    <address addr="192.168.1.20" addrtype="ipv4"/>
  </host>
</nmaprun>
"""


def test_parser_xml_extrait_hotes_et_ports():
    resultat = netscan._parser_xml(XML_EXEMPLE, "192.168.1.0/24", "nmap -sV 192.168.1.0/24")

    assert resultat.cible == "192.168.1.0/24"
    assert len(resultat.hotes) == 2

    routeur = resultat.hotes[0]
    assert routeur.ip == "192.168.1.10"
    assert routeur.nom == "routeur.lan"
    assert routeur.etat == "up"
    assert len(routeur.ports) == 2
    assert routeur.ports[0].numero == 22
    assert routeur.ports[0].etat == "open"
    assert routeur.ports[0].service == "ssh"
    assert "OpenSSH" in routeur.ports[0].version

    hote_down = resultat.hotes[1]
    assert hote_down.etat == "down"
    assert hote_down.ports == []


def test_parser_xml_rejette_une_sortie_invalide():
    import pytest

    with pytest.raises(netscan.ErreurScan):
        netscan._parser_xml("<pas du xml valide", "cible", "commande")


def test_enregistrer_rapport_ecrit_un_fichier_lisible(tmp_path):
    resultat = netscan._parser_xml(XML_EXEMPLE, "192.168.1.0/24", "nmap -sV 192.168.1.0/24")

    chemin = netscan.enregistrer_rapport(resultat, dossier=tmp_path)

    assert chemin.exists()
    contenu = chemin.read_text(encoding="utf-8")
    assert "192.168.1.10" in contenu
    assert "22/tcp open ssh" in contenu
    assert netscan.lister_rapports(tmp_path) == [chemin]


def test_deviner_sous_reseau_ipv4(monkeypatch):
    monkeypatch.setattr(netscan.system_status, "get_ip", lambda: "192.168.1.42")
    assert netscan.deviner_sous_reseau() == "192.168.1.0/24"


def test_deviner_sous_reseau_hors_ligne(monkeypatch):
    monkeypatch.setattr(netscan.system_status, "get_ip", lambda: "hors ligne")
    assert netscan.deviner_sous_reseau() is None
