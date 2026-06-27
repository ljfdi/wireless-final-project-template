from __future__ import annotations

import importlib
import inspect
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture()
def find_function():
    def _find(module_names: list[str], function_names: list[str], missing_message: str):
        import_errors: list[str] = []
        for module_name in module_names:
            try:
                module = importlib.import_module(module_name)
            except Exception as exc:
                import_errors.append(f"{module_name}: {type(exc).__name__}: {exc}")
                continue

            for function_name in function_names:
                candidate = getattr(module, function_name, None)
                if callable(candidate):
                    return candidate

        details = (
            f"{missing_message}\n"
            f"Tried modules: {module_names}\n"
            f"Tried functions: {function_names}\n"
            f"Import errors: {import_errors}"
        )
        pytest.fail(details)

    return _find


def to_bit_list(value) -> list[int]:
    if isinstance(value, str):
        assert set(value) <= {"0", "1"}, "Bit string must contain only 0 and 1"
        return [int(ch) for ch in value]
    if hasattr(value, "tolist"):
        value = value.tolist()
    return [int(x) for x in list(value)]


def to_complex_array(value) -> np.ndarray:
    if hasattr(value, "tolist"):
        value = value.tolist()
    return np.asarray([complex(x) for x in list(value)], dtype=complex)


def call_with_compatible_kwargs(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except TypeError as original_error:
        try:
            signature = inspect.signature(func)
        except (TypeError, ValueError):
            raise original_error

        filtered = {
            name: value
            for name, value in kwargs.items()
            if name in signature.parameters
        }
        try:
            return func(*args, **filtered)
        except TypeError:
            return func(*args)


def expected_qpsk_symbols() -> np.ndarray:
    return np.asarray(
        [
            (1 + 1j) / math.sqrt(2),
            (-1 + 1j) / math.sqrt(2),
            (-1 - 1j) / math.sqrt(2),
            (1 - 1j) / math.sqrt(2),
        ],
        dtype=complex,
    )


def run_required_cli(project_root: Path, timeout: int = 20) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        "main.py",
        "--input",
        "Test.txt",
        "--output",
        "results/received.txt",
        "--snr",
        "12",
        "--seed",
        "2026",
        "--mod",
        "qpsk",
        "--channel",
        "awgn",
    ]
    return subprocess.run(
        cmd,
        cwd=project_root,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
