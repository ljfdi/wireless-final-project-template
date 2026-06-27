import numpy as np

from conftest import expected_qpsk_symbols, to_bit_list, to_complex_array


def test_qpsk_gray_mapping_matches_prd(find_function):
    modulate = find_function(
        ["src.modulation", "src.modem", "src.qpsk"],
        ["qpsk_modulate", "modulate_qpsk", "qpsk_mapper", "modulate"],
        "src.modulation.qpsk_modulate not implemented yet",
    )

    symbols = to_complex_array(modulate([0, 0, 0, 1, 1, 1, 1, 0]))
    expected = expected_qpsk_symbols()

    assert len(symbols) >= 4
    assert np.allclose(symbols[:4], expected, atol=1e-12)
    assert np.isclose(np.mean(np.abs(symbols[:4]) ** 2), 1.0, atol=1e-12)


def test_qpsk_noiseless_demodulation_restores_bits_with_padding_rule(find_function):
    modulate = find_function(
        ["src.modulation", "src.modem", "src.qpsk"],
        ["qpsk_modulate", "modulate_qpsk", "qpsk_mapper", "modulate"],
        "src.modulation.qpsk_modulate not implemented yet",
    )
    demodulate = find_function(
        ["src.modulation", "src.modem", "src.qpsk"],
        ["qpsk_demodulate", "demodulate_qpsk", "qpsk_demapper", "demodulate"],
        "src.modulation.qpsk_demodulate not implemented yet",
    )

    bits = [1, 0, 1, 1, 0, 0, 1]
    symbols = modulate(bits)
    recovered = to_bit_list(demodulate(symbols))

    assert recovered[: len(bits)] == bits
