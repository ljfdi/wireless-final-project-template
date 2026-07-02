import numpy as np


def test_rayleigh_pipeline_recovers_text_with_preamble_based_equalization(tmp_path):
    from src.pipeline import run_pipeline

    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "rayleigh_received.txt"
    sample = (
        "无线通信技术期末项目使用 Rayleigh 信道扩展验证。"
        "该测试要求前导同步、均衡、QPSK 解调和译码后仍能恢复 UTF-8 文本。"
    )
    input_path.write_text(sample, encoding="utf-8")

    metrics = run_pipeline(
        input_path=input_path,
        output_path=output_path,
        snr_db=18,
        seed=2026,
        modulation="qpsk",
        channel="rayleigh",
        generate_plot_files=False,
    )

    assert output_path.read_text(encoding="utf-8") == sample
    assert metrics["channel"] == "rayleigh"
    assert metrics["equalization"] == "preamble_one_tap"
    assert metrics["text_match_rate"] == 1.0
    assert metrics["checksum_pass"] is True
    assert metrics["ber"] == 0.0
    assert metrics["estimated_channel_abs"] is not None
    assert metrics["channel_estimation_error"] is not None


def test_rayleigh_seed_is_reproducible_and_returns_flat_channel(find_function):
    rayleigh = find_function(
        ["src.channel", "src.channels", "src.rayleigh"],
        ["rayleigh", "rayleigh_channel", "add_rayleigh"],
        "src.channel.rayleigh not implemented yet",
    )

    symbols = np.asarray([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j], dtype=complex) / np.sqrt(2)
    out1, h1 = rayleigh(symbols, snr_db=18, seed=2026, return_channel=True)
    out2, h2 = rayleigh(symbols, snr_db=18, seed=2026, return_channel=True)

    out1 = np.asarray(out1, dtype=complex)
    out2 = np.asarray(out2, dtype=complex)
    assert out1.shape == symbols.shape
    assert np.allclose(out1, out2)
    assert np.allclose(np.asarray(h1, dtype=complex), np.asarray(h2, dtype=complex))
    assert np.asarray(h1).shape == (), "Level 3 uses one flat Rayleigh coefficient per frame"
    assert abs(complex(h1)) > 1e-9


def test_rayleigh_flat_fading_can_be_equalized_at_high_snr(find_function):
    rayleigh = find_function(
        ["src.channel", "src.channels", "src.rayleigh"],
        ["rayleigh", "rayleigh_channel", "add_rayleigh"],
        "src.channel.rayleigh not implemented yet",
    )

    symbols = np.asarray([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j] * 4, dtype=complex) / np.sqrt(2)
    faded, h = rayleigh(symbols, snr_db=120, seed=2026, return_channel=True)
    equalized = np.asarray(faded, dtype=complex) / complex(h)

    assert np.allclose(equalized, symbols, atol=1e-5)
