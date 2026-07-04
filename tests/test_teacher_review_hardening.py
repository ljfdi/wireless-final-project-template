from __future__ import annotations

import json
import subprocess
import sys


def _write_text(path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def test_cli_rejects_non_finite_snr_values(project_root, tmp_path):
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "received.txt"
    _write_text(input_path, "invalid SNR should be rejected before the channel model runs")

    for invalid_snr in ("nan", "inf", "-inf"):
        result = subprocess.run(
            [
                sys.executable,
                str(project_root / "main.py"),
                "--input",
                str(input_path),
                "--output",
                str(output_path),
                "--snr",
                invalid_snr,
                "--seed",
                "2026",
                "--mod",
                "qpsk",
                "--channel",
                "awgn",
            ],
            cwd=project_root,
            text=True,
            capture_output=True,
            timeout=20,
        )

        assert result.returncode != 0
        assert "finite" in result.stderr.lower() or "invalid snr" in result.stderr.lower()


def test_cli_rejects_unsupported_modulation_with_clear_error(project_root, tmp_path):
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "received.txt"
    _write_text(input_path, "invalid modulation should be rejected by the CLI")

    result = subprocess.run(
        [
            sys.executable,
            str(project_root / "main.py"),
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--snr",
            "12",
            "--seed",
            "2026",
            "--mod",
            "bpsk",
            "--channel",
            "awgn",
        ],
        cwd=project_root,
        text=True,
        capture_output=True,
        timeout=20,
    )

    assert result.returncode != 0
    assert "invalid choice" in result.stderr.lower()
    assert "bpsk" in result.stderr.lower()


def test_utf8_emoji_empty_and_long_texts_round_trip(project_root, tmp_path):
    from src.pipeline import run_pipeline

    cases = [
        ("empty.txt", ""),
        ("mixed_utf8.txt", "Wireless 通信 mix: QPSK/AWGN, emoji=📡🚀✅, punctuation!? seed=2026"),
        ("long_utf8.txt", "传了什么、错了多少、为什么会错。Wireless payload 📶 " * 40),
    ]

    for index, (filename, text) in enumerate(cases):
        input_path = tmp_path / filename
        output_path = tmp_path / f"received_{index}.txt"
        _write_text(input_path, text)

        metrics = run_pipeline(
            input_path=input_path,
            output_path=output_path,
            snr_db=12,
            seed=2026 + index,
            modulation="qpsk",
            channel="awgn",
            generate_plot_files=False,
        )

        assert output_path.read_text(encoding="utf-8") == text
        assert metrics["payload_bits"] == len(text.encode("utf-8")) * 8
        assert metrics["text_match_rate"] == 1.0
        assert metrics["checksum_pass"] is True
        assert metrics["ber"] == 0.0


def test_custom_output_directory_generates_metrics_and_plots(project_root, tmp_path):
    from src.pipeline import run_pipeline

    input_path = tmp_path / "custom_input.txt"
    output_path = tmp_path / "nested" / "outputs" / "received.txt"
    _write_text(input_path, "custom output path should carry received text, metrics, and plots")

    metrics = run_pipeline(
        input_path=input_path,
        output_path=output_path,
        snr_db=12,
        seed=2026,
        modulation="qpsk",
        channel="awgn",
    )

    results_dir = output_path.parent
    saved = json.loads((results_dir / "metrics.json").read_text(encoding="utf-8"))
    assert output_path.read_text(encoding="utf-8") == input_path.read_text(encoding="utf-8")
    assert saved["text_match_rate"] == metrics["text_match_rate"] == 1.0
    assert saved["checksum_pass"] is True
    for name in ("constellation.png", "ber_curve.png", "system_ber_curve.png", "sync_peak.png"):
        plot_path = results_dir / name
        assert plot_path.exists()
        assert plot_path.stat().st_size > 0
