from valise_diag import pin_lock


def test_correct_pin_validates():
    sel = pin_lock.generer_sel()
    hash_attendu = pin_lock.hash_pin("1234", sel)
    assert pin_lock.pin_valide("1234", sel, hash_attendu)


def test_wrong_pin_is_rejected():
    sel = pin_lock.generer_sel()
    hash_attendu = pin_lock.hash_pin("1234", sel)
    assert not pin_lock.pin_valide("0000", sel, hash_attendu)


def test_same_pin_different_salt_gives_different_hash():
    hash_a = pin_lock.hash_pin("1234", pin_lock.generer_sel())
    hash_b = pin_lock.hash_pin("1234", pin_lock.generer_sel())
    assert hash_a != hash_b
