from valise_diag.kwp1281 import BLOCK_END, KWP1281Client


class _FakeTransportRx:
    """Feeds a pre-built block to receive_block(); records the ack bytes sent back."""

    def __init__(self, block_bytes: bytes):
        self._queue = list(block_bytes)
        self.acks_sent = []

    def read_byte(self) -> int:
        return self._queue.pop(0)

    def write_byte(self, value: int) -> None:
        self.acks_sent.append(value)


class _FakeTransportAutoAck:
    """Auto-acknowledges every byte the client sends, to exercise send_block()."""

    def __init__(self):
        self.sent_bytes = []
        self._last = None

    def write_byte(self, value: int) -> None:
        self.sent_bytes.append(value)
        self._last = value

    def read_byte(self) -> int:
        return 0xFF - self._last


def _build_block(counter: int, title: int, data: bytes) -> bytes:
    length = 3 + len(data)
    return bytes([length, counter, title]) + data + bytes([BLOCK_END])


def test_receive_block_parses_length_counter_title_data():
    ident_block = _build_block(counter=1, title=0xF6, data=b"ECU-IDENT")
    transport = _FakeTransportRx(ident_block)
    client = KWP1281Client(transport, ecu_address=0x01)

    block = client.receive_block()

    assert block.title == 0xF6
    assert block.data == b"ECU-IDENT"
    # one ack byte (complement) is sent per received byte except the final 0x03
    assert len(transport.acks_sent) == len(ident_block) - 1
    assert all(ack == 0xFF - byte for ack, byte in zip(transport.acks_sent, ident_block))


def test_send_block_waits_for_complement_ack_on_every_byte():
    transport = _FakeTransportAutoAck()
    client = KWP1281Client(transport, ecu_address=0x01)
    client._block_counter = 5

    client.send_block(title=0x07, data=b"\x01\x02")

    # length(5) counter(6) title(0x07) data(2 bytes) acked one by one, then a raw 0x03 (not acked)
    assert transport.sent_bytes == [5, 6, 0x07, 0x01, 0x02, BLOCK_END]
