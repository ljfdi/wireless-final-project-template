from __future__ import annotations

"""UTF-8 source coding helpers."""


def source_encode(text: str) -> list[int]:
    """Convert a UTF-8 string to MSB-first bits."""
    data = text.encode("utf-8")
    bits: list[int] = []
    for byte in data:
        bits.extend((byte >> shift) & 1 for shift in range(7, -1, -1))
    return bits


def source_decode(bits) -> str:
    """Convert MSB-first UTF-8 bits back to text."""
    bit_list = [int(bit) for bit in bits]
    if len(bit_list) % 8 != 0:
        raise ValueError("UTF-8 source bitstream length must be divisible by 8")

    data = bytearray()
    for offset in range(0, len(bit_list), 8):
        value = 0
        for bit in bit_list[offset : offset + 8]:
            if bit not in (0, 1):
                raise ValueError("Source bits must contain only 0 and 1")
            value = (value << 1) | bit
        data.append(value)
    return bytes(data).decode("utf-8")


text_to_bits = source_encode
bits_to_text = source_decode
