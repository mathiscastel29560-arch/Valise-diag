import obd

from valise_diag import live_data
from valise_diag.dtc import format_live_value, valeur_numerique


def test_all_catalogue_commands_exist_in_python_obd():
    unknown = [name for name, _ in live_data.all_commands() if getattr(obd.commands, name, None) is None]
    assert unknown == []


def test_all_pids_entretien_exist_in_python_obd():
    unknown = [name for name, _ in live_data.PIDS_ENTRETIEN if getattr(obd.commands, name, None) is None]
    assert unknown == []


def test_categories_are_not_empty():
    for categorie in live_data.categories():
        assert live_data.commands_for(categorie), categorie


def test_format_live_value_none_is_non_disponible():
    assert format_live_value(None) == "non disponible"


def test_format_live_value_formats_known_units_compactly():
    assert format_live_value(42 * obd.Unit.kPa) == "42 kPa"
    assert format_live_value(15.5 * obd.Unit.percent) == "15.5 %"
    assert format_live_value(900 * obd.Unit.rpm) == "900 tr/min"
    assert format_live_value(obd.Unit.Quantity(90, obd.Unit.celsius)) == "90 °C"
    assert format_live_value(1.02 * obd.Unit.ratio) == "1.02 λ"


def test_format_live_value_falls_back_to_str_for_plain_values():
    assert format_live_value("P0301") == "P0301"


def test_valeur_numerique_extracts_magnitude():
    assert valeur_numerique(42 * obd.Unit.kPa) == 42
    assert valeur_numerique(None) is None
    assert valeur_numerique("P0301") == "P0301"


def test_valeur_anormale_hors_bornes():
    assert live_data.valeur_anormale("COOLANT_TEMP", 115) is True
    assert live_data.valeur_anormale("COOLANT_TEMP", 90) is False
    assert live_data.valeur_anormale("CONTROL_MODULE_VOLTAGE", 9.5) is True
    assert live_data.valeur_anormale("CONTROL_MODULE_VOLTAGE", 12.5) is False


def test_valeur_anormale_parametre_sans_seuil_jamais_signale():
    assert live_data.valeur_anormale("RPM", 999999) is False


def test_valeur_anormale_valeur_manquante_jamais_signalee():
    assert live_data.valeur_anormale("COOLANT_TEMP", None) is False
