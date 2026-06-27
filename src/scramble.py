from __future__ import annotations

"""Seed-controlled PN XOR scrambling."""

import numpy as np


def _bit_list(bits) -> list[int]:
    return [int(bit) for bit in list(bits)]


def scramble(bits, seed: int = 2026) -> list[int]:
    """Apply reproducible PN XOR scrambling without mutating input bits."""
    input_bits = _bit_list(bits)
    rng = np.random.default_rng(seed)
    pn = rng.integers(0, 2, size=len(input_bits), dtype=np.int8).tolist()
    return [bit ^ int(mask) for bit, mask in zip(input_bits, pn)]


def descramble(bits, seed: int = 2026) -> list[int]:
    """Reverse PN XOR scrambling with the same seed."""
    return scramble(bits, seed=seed)


scramble_bits = scramble
descramble_bits = descramble
encrypt = scramble
decrypt = descramble
encrypt_bits = scramble
decrypt_bits = descramble
