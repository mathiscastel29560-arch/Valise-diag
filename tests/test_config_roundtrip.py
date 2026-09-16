from valise_diag.config import AppConfig, load_app_config, save_app_config


def test_save_then_load_preserves_cosmetic_fields(tmp_path):
    path = tmp_path / "app.yaml"
    original = AppConfig(
        interface="kkl",
        titre_menu="MA VALISE",
        veille_active=False,
        veille_delai=45,
        veille_type="matrix",
        police="grand",
        autostart=False,
        boot_rapide=True,
        pin_active=True,
        pin_hash="deadbeef",
        pin_salt="cafef00d",
    )

    save_app_config(original, path)
    loaded = load_app_config(path)

    assert loaded == original


def test_missing_config_file_returns_defaults(tmp_path):
    assert load_app_config(tmp_path / "does-not-exist.yaml") == AppConfig()
