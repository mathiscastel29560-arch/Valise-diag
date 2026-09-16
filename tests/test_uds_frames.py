import pytest

from valise_diag.simulator import SimulatedELM327
from valise_diag.uds import IO_RETURN_CONTROL_TO_ECU, UDSClient, UDSNegativeResponse


def test_read_data_by_identifier_positive_response():
    adapter = SimulatedELM327({"7E0:22F190": ["7E8 06 62 F1 90 01 02 03"]})
    client = UDSClient(adapter, tx_header="7E0", rx_header="7E8")
    assert client.read_data_by_identifier(0xF190) == bytes([0x01, 0x02, 0x03])


def test_negative_response_raises_with_correct_nrc():
    adapter = SimulatedELM327({"7E0:22F190": ["7E8 03 7F 22 31"]})
    client = UDSClient(adapter, tx_header="7E0", rx_header="7E8")
    with pytest.raises(UDSNegativeResponse) as excinfo:
        client.read_data_by_identifier(0xF190)
    assert excinfo.value.nrc == 0x31
    assert excinfo.value.service_id == 0x22


def test_io_control_return_to_ecu_does_not_raise():
    adapter = SimulatedELM327()
    client = UDSClient(adapter, tx_header="7E0")
    client.io_control_by_identifier(0xF1A0, IO_RETURN_CONTROL_TO_ECU)


def test_write_data_by_identifier_builds_expected_payload():
    adapter = SimulatedELM327({"7E0:2EF1A001": ["7E8 01 6E"]})
    client = UDSClient(adapter, tx_header="7E0", rx_header="7E8")
    client.write_data_by_identifier(0xF1A0, b"\x01")
