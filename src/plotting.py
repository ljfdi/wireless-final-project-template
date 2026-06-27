from __future__ import annotations

"""Plot generation for constellation, BER curve, and synchronization peak."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from .channel import awgn
from .metrics import bit_error_rate
from .modulation import qpsk_demodulate, qpsk_modulate


def plot_constellation(symbols, output_path) -> Path:
    """Save a received QPSK constellation scatter plot."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.asarray(symbols, dtype=complex).ravel()
    if data.size > 2000:
        data = data[:2000]

    fig, ax = plt.subplots(figsize=(5, 5), dpi=120)
    if data.size:
        ax.scatter(data.real, data.imag, s=8, alpha=0.55, linewidths=0)
    ax.axhline(0, color="0.55", linewidth=0.8)
    ax.axvline(0, color="0.55", linewidth=0.8)
    ax.set_title("QPSK Constellation")
    ax.set_xlabel("In-phase")
    ax.set_ylabel("Quadrature")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def plot_sync_peak(correlation, peak_index: int, output_path) -> Path:
    """Save the preamble correlation curve and detected peak."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    corr = np.asarray(correlation, dtype=float).ravel()

    fig, ax = plt.subplots(figsize=(7, 4), dpi=120)
    if corr.size:
        ax.plot(np.arange(corr.size), corr, color="#1f77b4", linewidth=1.4)
        safe_peak = max(0, min(int(peak_index), corr.size - 1))
        ax.scatter([safe_peak], [corr[safe_peak]], color="#d62728", zorder=3)
    ax.set_title("Preamble Correlation Peak")
    ax.set_xlabel("Candidate start index (symbols)")
    ax.set_ylabel("Normalized correlation")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def plot_ber_curve(output_path, seed: int = 2026, snr_values=None) -> Path:
    """Save a lightweight deterministic uncoded QPSK BER curve."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if snr_values is None:
        snr_values = [0, 3, 6, 9, 12, 15]

    rng = np.random.default_rng(seed + 1009)
    reference_bits = rng.integers(0, 2, size=2048, dtype=np.int8).tolist()
    symbols = qpsk_modulate(reference_bits)
    ber_values: list[float] = []
    for index, snr_db in enumerate(snr_values):
        noisy = awgn(symbols, snr_db=float(snr_db), seed=seed + 2000 + index)
        recovered = qpsk_demodulate(noisy)[: len(reference_bits)]
        ber_values.append(bit_error_rate(reference_bits, recovered))

    fig, ax = plt.subplots(figsize=(6, 4), dpi=120)
    ax.semilogy(snr_values, ber_values, marker="o", color="#2ca02c", linewidth=1.5)
    ax.set_title("QPSK BER vs SNR")
    ax.set_xlabel("SNR (dB)")
    ax.set_ylabel("Bit error rate")
    ax.grid(True, which="both", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def generate_plots(
    *,
    output_dir,
    constellation_symbols,
    sync_correlation,
    sync_peak_index: int,
    seed: int,
) -> dict[str, str]:
    """Generate all required plot files and return their paths."""
    directory = Path(output_dir)
    paths = {
        "constellation": plot_constellation(
            constellation_symbols, directory / "constellation.png"
        ),
        "sync_peak": plot_sync_peak(
            sync_correlation, sync_peak_index, directory / "sync_peak.png"
        ),
        "ber_curve": plot_ber_curve(directory / "ber_curve.png", seed=seed),
    }
    return {name: str(path) for name, path in paths.items()}
