from __future__ import annotations

"""Frame construction and parsing helpers."""


PREAMBLE_BITS: list[int] = ([0, 0, 0, 1, 1, 1, 1, 0] * 8)
LENGTH_BITS = 32
CHECKSUM_BITS = 32


def _bit_list(bits) -> list[int]:
    return [int(bit) for bit in list(bits)]


def _int_to_bits(value: int, width: int) -> list[int]:
    if value < 0:
        raise ValueError("Frame integer fields must be non-negative")
    return [(value >> shift) & 1 for shift in range(width - 1, -1, -1)]


def _bits_to_int(bits) -> int:
    value = 0
    for bit in _bit_list(bits):
        value = (value << 1) | bit
    return value


def _checksum_bits(bits) -> int:
    checksum = 0
    for index, bit in enumerate(_bit_list(bits)):
        checksum = (checksum + ((index + 1) * int(bit))) & 0xFFFFFFFF
    return checksum


def build_frame(payload_bits, raw_payload_length=None, checksum=None, **kwargs):
    """Build a frame with preamble, lengths, checksum, and coded payload."""
    payload = _bit_list(payload_bits)
    if any(bit not in (0, 1) for bit in payload):
        raise ValueError("Frame payload bits must contain only 0 and 1")

    if raw_payload_length is None:
        raw_payload_length = kwargs.get("payload_length", len(payload))
    raw_payload_length = int(raw_payload_length)

    if checksum is None:
        checksum_bits = kwargs.get("checksum_bits")
        checksum = _bits_to_int(checksum_bits) if checksum_bits is not None else _checksum_bits(payload)
    checksum = int(checksum) & 0xFFFFFFFF

    coded_payload_length = int(kwargs.get("coded_payload_length", len(payload)))
    header = (
        PREAMBLE_BITS
        + _int_to_bits(raw_payload_length, LENGTH_BITS)
        + _int_to_bits(coded_payload_length, LENGTH_BITS)
        + _int_to_bits(checksum, CHECKSUM_BITS)
    )
    bits = header + payload

    return {
        "preamble": PREAMBLE_BITS.copy(),
        "raw_payload_length": raw_payload_length,
        "length": raw_payload_length,
        "coded_payload_length": coded_payload_length,
        "payload_length": coded_payload_length,
        "checksum": checksum,
        "crc": checksum,
        "payload": payload.copy(),
        "coded_payload": payload.copy(),
        "bits": bits,
        "frame": bits,
    }


def parse_frame(frame_bits):
    """Parse a frame dict or serialized frame bits into dict-like metadata."""
    if isinstance(frame_bits, dict):
        payload = _bit_list(frame_bits.get("payload") or frame_bits.get("coded_payload") or [])
        bits = _bit_list(frame_bits.get("bits") or frame_bits.get("frame") or [])
        raw_length = int(frame_bits.get("raw_payload_length", frame_bits.get("length", len(payload))))
        coded_length = int(frame_bits.get("coded_payload_length", frame_bits.get("payload_length", len(payload))))
        checksum = int(frame_bits.get("checksum", frame_bits.get("crc", _checksum_bits(payload))))
        return {
            "preamble": _bit_list(frame_bits.get("preamble", PREAMBLE_BITS)),
            "raw_payload_length": raw_length,
            "length": raw_length,
            "coded_payload_length": coded_length,
            "payload_length": coded_length,
            "checksum": checksum,
            "crc": checksum,
            "payload": payload,
            "coded_payload": payload,
            "bits": bits,
            "frame": bits,
        }

    bits = _bit_list(frame_bits)
    min_len = len(PREAMBLE_BITS) + (2 * LENGTH_BITS) + CHECKSUM_BITS
    if len(bits) < min_len:
        raise ValueError("Frame is too short to contain required metadata")

    cursor = 0
    preamble = bits[cursor : cursor + len(PREAMBLE_BITS)]
    cursor += len(PREAMBLE_BITS)
    raw_length = _bits_to_int(bits[cursor : cursor + LENGTH_BITS])
    cursor += LENGTH_BITS
    coded_length = _bits_to_int(bits[cursor : cursor + LENGTH_BITS])
    cursor += LENGTH_BITS
    checksum = _bits_to_int(bits[cursor : cursor + CHECKSUM_BITS])
    cursor += CHECKSUM_BITS
    payload = bits[cursor : cursor + coded_length]

    return {
        "preamble": preamble,
        "raw_payload_length": raw_length,
        "length": raw_length,
        "coded_payload_length": coded_length,
        "payload_length": coded_length,
        "checksum": checksum,
        "crc": checksum,
        "payload": payload,
        "coded_payload": payload,
        "bits": bits,
        "frame": bits,
    }


frame_build = build_frame
create_frame = build_frame
make_frame = build_frame
frame_parse = parse_frame
extract_frame = parse_frame
decode_frame = parse_frame
