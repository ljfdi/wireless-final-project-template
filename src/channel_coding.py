from __future__ import annotations

"""Simple repetition channel coding."""


REPETITION = 3


def _bit_list(bits) -> list[int]:
    return [int(bit) for bit in list(bits)]


def channel_encode(bits) -> list[int]:
    """Encode bits using a 3-times repetition code."""
    encoded: list[int] = []
    for bit in _bit_list(bits):
        if bit not in (0, 1):
            raise ValueError("Channel coding input bits must contain only 0 and 1")
        encoded.extend([bit] * REPETITION)
    return encoded


def channel_decode(encoded_bits) -> list[int]:
    """Decode a repetition-coded bitstream by majority vote."""
    bits = _bit_list(encoded_bits)
    decoded: list[int] = []
    for offset in range(0, len(bits), REPETITION):
        group = bits[offset : offset + REPETITION]
        if not group:
            continue
        ones = sum(1 for bit in group if bit == 1)
        decoded.append(1 if ones >= (len(group) / 2) else 0)
    return decoded


encode = channel_encode
decode = channel_decode
encode_bits = channel_encode
decode_bits = channel_decode
fec_encode = channel_encode
fec_decode = channel_decode
