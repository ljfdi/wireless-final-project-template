import json
from pathlib import Path

import pytest

from conftest import run_required_cli


REQUIRED_METRIC_FIELDS = {
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
}

REQUIRED_PLOTS = ["constellation.png", "ber_curve.png", "system_ber_curve.png", "sync_peak.png"]


def test_required_cli_contract_exists_and_runs(project_root):
    main_path = project_root / "main.py"
    if not main_path.exists():
        pytest.fail(
            "main.py not implemented yet; expected command: "
            "python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn"
        )

    result = run_required_cli(project_root)
    assert result.returncode == 0, result.stderr


def test_metrics_json_contains_required_fields_after_cli(project_root):
    main_path = project_root / "main.py"
    if not main_path.exists():
        pytest.fail("main.py not implemented yet; cannot generate results/metrics.json")

    result = run_required_cli(project_root)
    assert result.returncode == 0, result.stderr

    metrics_path = project_root / "results" / "metrics.json"
    assert metrics_path.exists(), "results/metrics.json should be generated"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert REQUIRED_METRIC_FIELDS <= set(metrics)
    assert metrics["system_ber_curve_path"].endswith("results/system_ber_curve.png")
    assert len(metrics["system_ber_values"]) == len(metrics["system_ber_snr_values"])
    assert all(0.0 <= float(value) <= 1.0 for value in metrics["system_ber_values"])


def test_required_plots_generate_after_cli(project_root):
    main_path = project_root / "main.py"
    if not main_path.exists():
        pytest.fail("main.py not implemented yet; cannot generate required plots")

    result = run_required_cli(project_root)
    assert result.returncode == 0, result.stderr

    existing = [
        path
        for name in REQUIRED_PLOTS
        if (path := project_root / "results" / name).exists() and path.stat().st_size > 0
    ]
    assert len(existing) >= 3


def test_future_anti_copy_and_anti_hardcoding_check(project_root):
    src_path = project_root / "src"
    main_path = project_root / "main.py"
    if not src_path.exists() and not main_path.exists():
        pytest.fail("src/ and main.py not implemented yet; anti-copy scan will run after implementation exists")

    source_files = list(src_path.rglob("*.py")) if src_path.exists() else []
    if main_path.exists():
        source_files.append(main_path)
    combined = "\n".join(Path(path).read_text(encoding="utf-8", errors="ignore") for path in source_files)

    suspicious_patterns = ["shutil.copy", "copyfile", "received.txt').write_text(Path('Test.txt')"]
    assert not any(pattern in combined for pattern in suspicious_patterns)
