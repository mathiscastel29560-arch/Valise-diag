import shutil

from valise_diag import theme


def test_definir_decalage_vertical_deplace_le_bloc_vers_le_haut(monkeypatch, capsys):
    monkeypatch.setattr(shutil, "get_terminal_size", lambda *_a, **_k: shutil.os.terminal_size((80, 24)))

    theme.definir_decalage_vertical(0)
    theme.afficher_bloc_centre(["une ligne"], effacer=False)
    sortie_neutre = capsys.readouterr().out

    theme.definir_decalage_vertical(-5)
    theme.afficher_bloc_centre(["une ligne"], effacer=False)
    sortie_decalee = capsys.readouterr().out

    theme.definir_decalage_vertical(0)  # ne pas polluer les autres tests

    assert sortie_decalee.count("\n") < sortie_neutre.count("\n")


def test_definir_decalage_vertical_ne_produit_jamais_une_marge_negative(monkeypatch, capsys):
    monkeypatch.setattr(shutil, "get_terminal_size", lambda *_a, **_k: shutil.os.terminal_size((80, 24)))

    theme.definir_decalage_vertical(-1000)
    # Ne doit pas lever, et la marge doit être coupée à 0 plutôt que négative.
    theme.afficher_bloc_centre(["une ligne"], effacer=False)

    theme.definir_decalage_vertical(0)
