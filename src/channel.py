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


def rayleigh(
    symbols,
    snr_db: float = 12.0,
    seed: int | None = None,
    return_channel: bool = False,
):
    """Apply flat Rayleigh fading plus AWGN.

    The Level 3 extension uses one complex fading coefficient per frame. The
    true coefficient may be returned for simulation diagnostics, but the
    receiver estimates the channel from the known preamble before equalization.
    """
    signal = np.asarray(symbols, dtype=complex)
    if signal.size == 0:
        empty = signal.copy()
        return (empty, 1.0 + 0.0j) if return_channel else empty

    rng = np.random.default_rng(seed)
    h = complex(rng.normal(), rng.normal()) / np.sqrt(2.0)
    if abs(h) < 1e-12:
        h = 1.0 + 0.0j

    faded = h * signal
    noise_seed = None if seed is None else int(seed) + 100003
    noisy = awgn(faded, snr_db=snr_db, seed=noise_seed)
    return (noisy, h) if return_channel else noisy


awgn_channel = awgn
add_awgn = awgn
add_noise = awgn
rayleigh_channel = rayleigh
add_rayleigh = rayleigh
