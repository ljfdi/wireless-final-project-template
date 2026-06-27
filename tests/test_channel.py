import numpy as np


def test_awgn_seed_is_reproducible(find_function):
    awgn = find_function(
        ["src.channel", "src.channels", "src.awgn"],
        ["awgn", "awgn_channel", "add_awgn", "add_noise"],
        "src.channel.awgn not implemented yet",
    )

    symbols = np.asarray([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j], dtype=complex) / np.sqrt(2)
    out1 = np.asarray(awgn(symbols, snr_db=12, seed=2026), dtype=complex)
    out2 = np.asarray(awgn(symbols, snr_db=12, seed=2026), dtype=complex)

    assert np.allclose(out1, out2), "AWGN output should be reproducible for a fixed seed"
