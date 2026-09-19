import subprocess
from pathlib import Path

from valise_diag import system_tools


def _init_repo(tmp_path: Path) -> Path:
    depot = tmp_path / "depot"
    depot.mkdir()
    subprocess.run(["git", "init"], cwd=depot, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=depot, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=depot, check=True, capture_output=True)
    (depot / "fichier.txt").write_text("contenu")
    subprocess.run(["git", "add", "."], cwd=depot, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=depot, check=True, capture_output=True)
    return depot


def test_mettre_a_jour_valise_echoue_proprement_sans_remote(tmp_path, monkeypatch):
    depot = _init_repo(tmp_path)
    # `Path(__file__).resolve().parent` doit se retrouver dans le dépôt de
    # test : on simule ça en pointant le __file__ du module dans ce dépôt.
    monkeypatch.setattr(system_tools, "__file__", str(depot / "system_tools.py"))

    succes, sortie = system_tools.mettre_a_jour_valise()

    assert succes is False
    assert sortie != ""


def test_mettre_a_jour_valise_hors_depot_git_echoue_proprement(tmp_path, monkeypatch):
    monkeypatch.setattr(system_tools, "__file__", str(tmp_path / "system_tools.py"))

    succes, sortie = system_tools.mettre_a_jour_valise()

    assert succes is False
    assert sortie != ""


def test_est_raspberry_pi_detecte_le_modele(tmp_path, monkeypatch):
    system_tools.est_raspberry_pi.cache_clear()
    fichier = tmp_path / "model"
    fichier.write_text("Raspberry Pi Zero W Rev 1.1\x00")
    monkeypatch.setattr(system_tools, "Path", lambda _chemin: fichier)

    assert system_tools.est_raspberry_pi() is True
    system_tools.est_raspberry_pi.cache_clear()


def test_est_raspberry_pi_faux_sur_pc_classique(tmp_path, monkeypatch):
    system_tools.est_raspberry_pi.cache_clear()
    monkeypatch.setattr(system_tools, "Path", lambda _chemin: tmp_path / "absent")

    assert system_tools.est_raspberry_pi() is False
    system_tools.est_raspberry_pi.cache_clear()
