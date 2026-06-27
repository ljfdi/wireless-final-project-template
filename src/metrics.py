from __future__ import annotations

"""Metrics and checksum helpers for the end-to-end simulation."""

import json
import zlib
from pathlib import Path


def _bit_list(bits) -> list[int]:
    return [int(bit) for bit in list(bits)]


def bits_to_bytes(bits) -> bytes:
    """Pack MSB-first bits into bytes, padding the final byte with zeros if needed."""
    bit_list = _bit_list(bits)
    data = bytearray()
    for offset in range(0, len(bit_list), 8):
        chunk = bit_list[offset : offset + 8]
        if len(chunk) < 8:
            chunk = chunk + [0] * (8 - len(chunk))
        value = 0
        for bit in chunk:
            if bit not in (0, 1):
                raise ValueError("Metric bitstreams must contain only 0 and 1")
            value = (value << 1) | bit
        data.append(value)
    return bytes(data)


def crc32_bits(bits) -> int:
    """Return a reproducible CRC32 checksum over the original payload bitstream."""
    return zlib.crc32(bits_to_bytes(bits)) & 0xFFFFFFFF


def bit_error_rate(reference_bits, recovered_bits) -> float:
    """Compute BER, treating missing or extra bits as errors."""
    reference = _bit_list(reference_bits)
    recovered = _bit_list(recovered_bits)
    total = max(len(reference), len(recovered))
    if total == 0:
        return 0.0

    errors = abs(len(reference) - len(recovered))
    for ref_bit, got_bit in zip(reference, recovered):
        errors += int(ref_bit != got_bit)
    return errors / total


def text_match_rate(reference_text: str, recovered_text: str) -> float:
    """Return exact-match 1.0, otherwise a simple character match ratio."""
    if reference_text == recovered_text:
        return 1.0
    total = max(len(reference_text), len(recovered_text))
    if total == 0:
        return 1.0
    matches = sum(1 for expected, actual in zip(reference_text, recovered_text) if expected == actual)
    return matches / total


def build_metrics(
    *,
    snr_db: float,
    seed: int,
    modulation: str,
    channel: str,
    payload_bits: int,
    ber: float,
    text_rate: float,
    checksum_pass: bool,
    sync_start_index: int,
    sync_true_offset: int | None = None,
    frame_bits: int | None = None,
    coded_payload_bits: int | None = None,
    failure_reason: str = "",
) -> dict[str, object]:
    """Build the required metrics.json payload plus useful diagnostic fields."""
    fer = 0.0 if checksum_pass and text_rate == 1.0 and ber == 0.0 else 1.0
    metrics: dict[str, object] = {
        "snr_db": float(snr_db),
        "seed": int(seed),
        "modulation": str(modulation),
        "channel": str(channel),
        "payload_bits": int(payload_bits),
        "ber": float(ber),
        "fer": float(fer),
        "text_match_rate": float(text_rate),
        "checksum_pass": bool(checksum_pass),
        "sync_start_index": int(sync_start_index),
        "sync_true_offset": None if sync_true_offset is None else int(sync_true_offset),
        "sync_error_symbols": None
        if sync_true_offset is None
        else int(sync_start_index) - int(sync_true_offset),
        "failure_reason": str(failure_reason),
        "frame_bits": None if frame_bits is None else int(frame_bits),
        "coded_payload_bits": None if coded_payload_bits is None else int(coded_payload_bits),
    }
    return metrics


def write_metrics(metrics: dict[str, object], path) -> Path:
    """Write metrics as UTF-8 JSON and return the output path."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return output_path
