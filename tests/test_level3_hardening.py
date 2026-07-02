from __future__ import annotations

import json
import py_compile
import subprocess
import sys


REQUIRED_METRICS = {
    "snr_db",
    "seed",
    "modulation",
    "channel",
    "payload_bits",
    "ber",
    "fer",
    "text_match_rate",
    "checksum_pass",
    "sync_start_index",
    "sync_true_offset",
    "sync_error_symbols",
    "failure_reason",
}


def _write_input(path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def test_seed_126_awgn_recovers_after_wide_sync_candidate_search(tmp_path):
    from src.pipeline import run_pipeline

    input_path = tmp_path / "seed126_input.txt"
    output_path = tmp_path / "received.txt"
    text = "同步鲁棒性回归测试：seed=126 曾经出现相关峰偏移，必须依靠 CRC 候选搜索恢复。"
    _write_input(input_path, text)

    metrics = run_pipeline(
        input_path=input_path,
        output_path=output_path,
        snr_db=12,
        seed=126,
        modulation="qpsk",
        channel="awgn",
        generate_plot_files=False,
    )

    assert output_path.read_text(encoding="utf-8") == text
    assert metrics["checksum_pass"] is True
    assert metrics["text_match_rate"] == 1.0
    assert metrics["ber"] == 0.0
    assert metrics["sync_true_offset"] == 39
    assert metrics["sync_start_index"] == metrics["sync_true_offset"]
    assert metrics["sync_search_radius"] >= 16


def test_awgn_multiple_seeds_and_chinese_lengths_round_trip(tmp_path):
    from src.pipeline import run_pipeline

    cases = [
        (1, "短文本"),
        (7, "中等长度中文文本，用来验证 UTF-8 编码、扰码、编码、同步和恢复。" * 2),
        (126, "较长中文文本：" + "无线通信基带仿真链路必须保持端到端稳定。" * 5),
        (2026, "默认种子回归：AWGN 主链路仍然是自动评分入口。"),
    ]
    for seed, text in cases:
        input_path = tmp_path / f"input_{seed}.txt"
        output_path = tmp_path / f"received_{seed}.txt"
        _write_input(input_path, text)

        metrics = run_pipeline(
            input_path=input_path,
            output_path=output_path,
            snr_db=12,
            seed=seed,
            modulation="qpsk",
            channel="awgn",
            generate_plot_files=False,
        )

        assert output_path.read_text(encoding="utf-8") == text
        assert metrics["checksum_pass"] is True
        assert metrics["text_match_rate"] == 1.0
        assert metrics["ber"] == 0.0


def test_low_snr_does_not_crash_and_writes_metrics(tmp_path):
    from src.pipeline import run_pipeline

    input_path = tmp_path / "low_snr_input.txt"
    output_path = tmp_path / "received.txt"
    _write_input(input_path, "低 SNR 场景允许恢复失败，但程序必须输出 metrics.json 并给出失败指标。")

    metrics = run_pipeline(
        input_path=input_path,
        output_path=output_path,
        snr_db=-2,
        seed=2026,
        modulation="qpsk",
        channel="awgn",
        generate_plot_files=False,
    )

    metrics_path = output_path.parent / "metrics.json"
    assert output_path.exists()
    assert metrics_path.exists()
    saved = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert REQUIRED_METRICS <= set(saved)
    assert REQUIRED_METRICS <= set(metrics)
    assert isinstance(saved["failure_reason"], str)


def test_rayleigh_cli_uses_preamble_one_tap_equalization(project_root, tmp_path):
    input_path = tmp_path / "rayleigh_input.txt"
    output_path = tmp_path / "rayleigh_received.txt"
    text = "Rayleigh 平坦衰落通过前导估计单个复信道系数，并用一抽头均衡补偿。"
    _write_input(input_path, text)

    result = subprocess.run(
        [
            sys.executable,
            str(project_root / "main.py"),
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--snr",
            "18",
            "--seed",
            "2026",
            "--mod",
            "qpsk",
            "--channel",
            "rayleigh",
        ],
        cwd=project_root,
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert output_path.read_text(encoding="utf-8") == text
    metrics = json.loads((output_path.parent / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["channel"] == "rayleigh"
    assert metrics["equalization"] == "preamble_one_tap"
    assert metrics["checksum_pass"] is True
    assert metrics["text_match_rate"] == 1.0
    assert metrics["ber"] == 0.0
    assert metrics["estimated_channel_abs"] is not None


def test_gui_py_compiles_and_import_has_no_tk_side_effect(project_root):
    gui_path = project_root / "gui.py"
    py_compile.compile(str(gui_path), doraise=True)

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import tkinter as tk; import gui; print(tk._default_root is None)",
        ],
        cwd=project_root,
        text=True,
        capture_output=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "True"
