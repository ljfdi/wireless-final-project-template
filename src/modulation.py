from __future__ import annotations

"""QPSK modulation and demodulation."""

import math

import numpy as np


_SCALE = 1.0 / math.sqrt(2.0)
_MAPPING = {
    (0, 0): (1 + 1j) * _SCALE,
    (0, 1): (-1 + 1j) * _SCALE,
    (1, 1): (-1 - 1j) * _SCALE,
    (1, 0): (1 - 1j) * _SCALE,
}


def _bit_list(bits) -> list[int]:
    return [int(bit) for bit in list(bits)]


def qpsk_modulate(bits):
    """Map bits to unit-power Gray-coded QPSK symbols."""
    bit_list = _bit_list(bits)
    if any(bit not in (0, 1) for bit in bit_list):
        raise ValueError("QPSK input bits must contain only 0 and 1")
    if len(bit_list) % 2 == 1:
        bit_list = bit_list + [0]

    symbols = [_MAPPING[(bit_list[i], bit_list[i + 1])] for i in range(0, len(bit_list), 2)]
    return np.asarray(symbols, dtype=complex)


def qpsk_demodulate(symbols) -> list[int]:
    """Hard-decision demodulation using nearest QPSK quadrant."""
    recovered: list[int] = []
    for symbol in np.asarray(symbols, dtype=complex).ravel():
        if symbol.real >= 0 and symbol.imag >= 0:
            recovered.extend([0, 0])
        elif symbol.real < 0 and symbol.imag >= 0:
            recovered.extend([0, 1])
        elif symbol.real < 0 and symbol.imag < 0:
            recovered.extend([1, 1])
        else:
            recovered.extend([1, 0])
    return recovered


modulate_qpsk = qpsk_modulate
qpsk_mapper = qpsk_modulate
modulate = qpsk_modulate
demodulate_qpsk = qpsk_demodulate
qpsk_demapper = qpsk_demodulate
demodulate = qpsk_demodulate
