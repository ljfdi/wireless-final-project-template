import numpy as np
import pytest


@pytest.mark.parametrize("offset", [0, 1, 25, 64, 128])
def test_synchronize_returns_integer_start_index_for_offsets(find_function, offset):
    synchronize = find_function(
        ["src.synchronization", "src.sync", "src.receiver"],
        ["synchronize", "detect_frame_start", "find_preamble", "sync"],
        "src.synchronization.synchronize not implemented yet",
    )

    rng = np.random.default_rng(2026 + offset)
    preamble = np.asarray([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j] * 8, dtype=complex) / np.sqrt(2)
    payload = np.asarray([1 - 1j, -1 - 1j, 1 + 1j, -1 + 1j] * 16, dtype=complex) / np.sqrt(2)
    prefix = (rng.normal(size=offset) + 1j * rng.normal(size=offset)) / np.sqrt(2)
    received = np.concatenate([prefix, preamble, payload])

    start_index = synchronize(received, preamble=preamble)

    assert isinstance(start_index, int), "synchronize should return int by default"
    assert abs(start_index - offset) <= 1
