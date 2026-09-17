from valise_diag import file_manager


def test_lister_dossier_absent_renvoie_liste_vide(tmp_path):
    assert file_manager.lister(tmp_path / "nexiste_pas") == []


def test_lister_trie_du_plus_recent_au_plus_ancien(tmp_path):
    ancien = tmp_path / "ancien.csv"
    recent = tmp_path / "recent.csv"
    ancien.write_text("a")
    recent.write_text("b")
    import os
    import time

    os.utime(ancien, (time.time() - 100, time.time() - 100))

    resultat = file_manager.lister(tmp_path)
    noms = [chemin.name for chemin, _, _ in resultat]
    assert noms == ["recent.csv", "ancien.csv"]


def test_formater_taille():
    assert file_manager.formater_taille(500) == "500 o"
    assert file_manager.formater_taille(2048) == "2.0 Ko"
    assert file_manager.formater_taille(5 * 1024 * 1024) == "5.0 Mo"


def test_supprimer_refuse_hors_dossiers_surveilles(tmp_path):
    fichier = tmp_path / "hors_surveillance.txt"
    fichier.write_text("x")
    try:
        file_manager.supprimer(fichier)
        assert False, "aurait dû lever ValueError"
    except ValueError:
        pass
    assert fichier.exists()  # jamais supprimé


def test_supprimer_efface_dans_un_dossier_surveille(tmp_path, monkeypatch):
    monkeypatch.setitem(file_manager.DOSSIERS_SURVEILLES, "Test", tmp_path)
    fichier = tmp_path / "session_test.csv"
    fichier.write_text("x")

    file_manager.supprimer(fichier)

    assert not fichier.exists()
