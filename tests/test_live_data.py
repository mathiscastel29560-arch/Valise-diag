import obd

from valise_diag import live_data
from valise_diag.dtc import format_live_value


def test_all_catalogue_commands_exist_in_python_obd():
    unknown = [name for name, _ in live_data.all_commands() if getattr(obd.commands, name, None) is None]
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


def test_format_live_value_falls_back_to_str_for_plain_values():
    assert format_live_value("P0301") == "P0301"
