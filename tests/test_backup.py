import time

from valise_diag import backup


def _preparer_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "app.yaml").write_text("interface: obd2\n")
    (tmp_path / "config" / "vehicle_profile.yaml").write_text("make: Renault\n")
    (tmp_path / "config" / "vehicles").mkdir()
    (tmp_path / "config" / "vehicles" / "clio4.yaml").write_text("make: Renault\n")


def test_creer_sauvegarde_produit_une_archive(tmp_path, monkeypatch):
    _preparer_config(tmp_path, monkeypatch)

    chemin = backup.creer_sauvegarde(dossier=tmp_path / "config" / "sauvegardes")

    assert chemin.exists()
    assert chemin.suffix == ".gz"


def test_lister_sauvegardes_dossier_absent_renvoie_liste_vide(tmp_path):
    assert backup.lister_sauvegardes(tmp_path / "nexiste_pas") == []


def test_creer_puis_restaurer_reproduit_les_fichiers(tmp_path, monkeypatch):
    _preparer_config(tmp_path, monkeypatch)
    chemin = backup.creer_sauvegarde(dossier=tmp_path / "config" / "sauvegardes")

    # On efface la config actuelle pour vérifier que la restauration la recrée.
    (tmp_path / "config" / "app.yaml").unlink()
    (tmp_path / "config" / "vehicles" / "clio4.yaml").unlink()

    destination = tmp_path / "restauration"
    destination.mkdir()
    backup.restaurer_sauvegarde(chemin, destination=destination)

    assert (destination / "config" / "app.yaml").read_text() == "interface: obd2\n"
    assert (destination / "config" / "vehicles" / "clio4.yaml").read_text() == "make: Renault\n"


def test_lister_sauvegardes_trie_du_plus_recent(tmp_path, monkeypatch):
    _preparer_config(tmp_path, monkeypatch)
    dossier = tmp_path / "config" / "sauvegardes"
    backup.creer_sauvegarde(dossier=dossier)
    time.sleep(1.1)  # les noms de fichiers n'ont qu'une résolution à la seconde
    deuxieme = backup.creer_sauvegarde(dossier=dossier)

    resultat = backup.lister_sauvegardes(dossier)

    assert len(resultat) == 2
    assert resultat[0].name == deuxieme.name
