from __future__ import annotations

"""Wireless channel models."""

import numpy as np


def awgn(symbols, snr_db: float = 12.0, seed: int | None = None):
    """Add complex AWGN using symbol-power / complex-noise-power SNR."""
    signal = np.asarray(symbols, dtype=complex)
    if signal.size == 0:
        return signal.copy()

    signal_power = float(np.mean(np.abs(signal) ** 2))
    snr_linear = 10.0 ** (float(snr_db) / 10.0)
    noise_power = signal_power / snr_linear if snr_linear > 0 else signal_power
    sigma = np.sqrt(noise_power / 2.0)

    rng = np.random.default_rng(seed)
    noise = sigma * (rng.normal(size=signal.shape) + 1j * rng.normal(size=signal.shape))
    return signal + noise


awgn_channel = awgn
add_awgn = awgn
add_noise = awgn
