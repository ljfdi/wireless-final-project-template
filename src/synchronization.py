from __future__ import annotations

"""Preamble correlation synchronization."""

import numpy as np


def default_preamble_symbols():
    """Return the default 32-symbol QPSK preamble used by tests and framing."""
    return np.asarray([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j] * 8, dtype=complex) / np.sqrt(2)


def correlate_preamble(received_symbols, preamble=None) -> dict[str, object]:
    """Compute sliding preamble correlation and return details."""
    received = np.asarray(received_symbols, dtype=complex).ravel()
    known = default_preamble_symbols() if preamble is None else np.asarray(preamble, dtype=complex).ravel()
    if known.size == 0:
        raise ValueError("Preamble must not be empty")
    if received.size < known.size:
        return {"correlation": np.asarray([], dtype=float), "peak_index": 0, "peak_value": 0.0}

    scores = np.empty(received.size - known.size + 1, dtype=float)
    norm = float(np.linalg.norm(known)) or 1.0
    for start in range(scores.size):
        window = received[start : start + known.size]
        denom = norm * (float(np.linalg.norm(window)) or 1.0)
        scores[start] = abs(np.vdot(known, window)) / denom

    peak_index = int(np.argmax(scores))
    return {
        "correlation": scores,
        "peak_index": peak_index,
        "peak_value": float(scores[peak_index]),
    }


def synchronize(received_symbols, preamble=None, return_details: bool = False):
    """Detect frame start. By default return only int start_index."""
    details = correlate_preamble(received_symbols, preamble=preamble)
    if return_details:
        return details
    return int(details["peak_index"])


detect_frame_start = synchronize
find_preamble = synchronize
sync = synchronize
