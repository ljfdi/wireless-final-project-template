from __future__ import annotations

import json


def test_compute_system_ber_curve_uses_full_pipeline_and_preserves_outputs(tmp_path):
    from src.pipeline import compute_system_ber_curve
    from src.plotting import plot_system_ber_curve

    input_path = tmp_path / "input.txt"
    input_path.write_text("完整重复码系统 BER 曲线测试。", encoding="utf-8")
    formal_received = tmp_path / "received.txt"
    formal_metrics = tmp_path / "metrics.json"
    formal_received.write_text("formal output sentinel", encoding="utf-8")
    formal_metrics.write_text('{"formal": true}', encoding="utf-8")

    curve = compute_system_ber_curve(
        input_path=input_path,
        snr_values=[8, 12],
        seeds=[2026, 2027],
        channel="awgn",
        mod="qpsk",
        temp_root=tmp_path,
    )
    plot_path = plot_system_ber_curve(curve, tmp_path / "system_ber_curve.png")

    assert plot_path.exists() and plot_path.stat().st_size > 0
    assert formal_received.read_text(encoding="utf-8") == "formal output sentinel"
    assert json.loads(formal_metrics.read_text(encoding="utf-8")) == {"formal": True}
    assert len(curve["ber_values"]) == len(curve["snr_values"]) == 2
    assert curve["seeds"] == [2026, 2027]
    assert all(0.0 <= float(value) <= 1.0 for value in curve["ber_values"])
    assert len(curve["checksum_pass_rates"]) == 2
    assert len(curve["text_match_rates"]) == 2


def test_system_ber_plot_handles_zero_ber(tmp_path):
    from src.plotting import plot_system_ber_curve

    curve = {
        "snr_values": [10.0, 12.0, 14.0],
        "ber_values": [0.0, 0.0, 0.0],
        "seeds": [2026],
        "frame_success_rates": [1.0, 1.0, 1.0],
        "checksum_pass_rates": [1.0, 1.0, 1.0],
        "text_match_rates": [1.0, 1.0, 1.0],
    }
    path = plot_system_ber_curve(curve, tmp_path / "zero_system_ber_curve.png")

    assert path.exists()
    assert path.stat().st_size > 0
