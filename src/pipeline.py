from __future__ import annotations

"""End-to-end wireless baseband simulation pipeline."""

from pathlib import Path

import numpy as np

from .channel import awgn
from .channel_coding import channel_decode, channel_encode
from .framing import PREAMBLE_BITS, build_frame, parse_frame
from .metrics import (
    bit_error_rate,
    build_metrics,
    crc32_bits,
    text_match_rate,
    write_metrics,
)
from .modulation import qpsk_demodulate, qpsk_modulate
from .plotting import generate_plots
from .scramble import descramble, scramble
from .source import source_decode, source_encode
from .synchronization import correlate_preamble, synchronize


def _bit_list(bits) -> list[int]:
    return [int(bit) for bit in list(bits)]


def _random_prefix_symbols(seed: int, prefix_symbols: int) -> np.ndarray:
    if prefix_symbols <= 0:
        return np.asarray([], dtype=complex)
    rng = np.random.default_rng(seed + 17)
    prefix_bits = rng.integers(0, 2, size=prefix_symbols * 2, dtype=np.int8).tolist()
    return qpsk_modulate(prefix_bits)


def _safe_text_decode(bits) -> tuple[str, str]:
    try:
        return source_decode(bits), ""
    except Exception as exc:
        return "", f"source_decode failed: {type(exc).__name__}: {exc}"


def _append_failure(existing: str, new: str) -> str:
    if not new:
        return existing
    if not existing:
        return new
    return f"{existing}; {new}"


def run_pipeline(
    input_path,
    output_path,
    snr_db: float = 12.0,
    seed: int = 2026,
    modulation: str = "qpsk",
    channel: str = "awgn",
) -> dict[str, object]:
    """Run the complete transmitter, channel, receiver, metrics, and plot flow."""
    modulation_name = str(modulation).lower()
    channel_name = str(channel).lower()
    if modulation_name != "qpsk":
        raise ValueError("Only qpsk modulation is supported")
    if channel_name != "awgn":
        raise ValueError("Only awgn channel is supported")

    input_file = Path(input_path)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    results_dir = output_file.parent

    input_text = input_file.read_text(encoding="utf-8")
    raw_payload_bits = source_encode(input_text)
    scrambled_bits = scramble(raw_payload_bits, seed=seed)
    coded_payload = channel_encode(scrambled_bits)
    checksum = crc32_bits(raw_payload_bits)

    frame = build_frame(
        coded_payload,
        raw_payload_length=len(raw_payload_bits),
        checksum=checksum,
    )
    frame_bits = _bit_list(frame["bits"])
    frame_symbols = qpsk_modulate(frame_bits)
    preamble_symbols = qpsk_modulate(PREAMBLE_BITS)

    rng = np.random.default_rng(seed)
    prefix_len = int(rng.integers(0, 129))
    prefix = _random_prefix_symbols(seed, prefix_len)
    transmitted_symbols = np.concatenate([prefix, frame_symbols])
    received_symbols = awgn(transmitted_symbols, snr_db=float(snr_db), seed=seed)

    sync_start_index = 0
    recovered_payload_bits: list[int] = []
    recovered_text = ""
    checksum_pass = False
    failure_reason = ""
    constellation_symbols = received_symbols
    sync_details = correlate_preamble(received_symbols, preamble=preamble_symbols)

    try:
        sync_start_index = int(synchronize(received_symbols, preamble=preamble_symbols))
        frame_end = sync_start_index + len(frame_symbols)
        aligned_frame_symbols = received_symbols[sync_start_index:frame_end]
        constellation_symbols = aligned_frame_symbols

        received_frame_bits = qpsk_demodulate(aligned_frame_symbols)
        parsed = parse_frame(received_frame_bits)
        coded_payload_rx = parsed.get("coded_payload") or parsed.get("payload") or []
        raw_payload_length = int(
            parsed.get("raw_payload_length", parsed.get("length", len(raw_payload_bits)))
        )

        decoded_scrambled = channel_decode(coded_payload_rx)
        recovered_payload_bits = descramble(decoded_scrambled, seed=seed)[:raw_payload_length]
        recovered_text, decode_error = _safe_text_decode(recovered_payload_bits)
        failure_reason = _append_failure(failure_reason, decode_error)

        checksum_pass = (
            len(recovered_payload_bits) == len(raw_payload_bits)
            and int(parsed.get("checksum", parsed.get("crc", -1))) == crc32_bits(recovered_payload_bits)
        )
        if not checksum_pass and not failure_reason:
            failure_reason = "checksum mismatch"
    except Exception as exc:
        failure_reason = _append_failure(
            failure_reason,
            f"receiver failed: {type(exc).__name__}: {exc}",
        )

    output_file.write_text(recovered_text, encoding="utf-8")

    ber = bit_error_rate(raw_payload_bits, recovered_payload_bits)
    text_rate = text_match_rate(input_text, recovered_text)
    if text_rate == 1.0 and ber == 0.0 and not checksum_pass:
        failure_reason = _append_failure(failure_reason, "checksum mismatch despite text recovery")

    plot_failure = ""
    try:
        generate_plots(
            output_dir=results_dir,
            constellation_symbols=constellation_symbols,
            sync_correlation=sync_details.get("correlation", []),
            sync_peak_index=int(sync_details.get("peak_index", sync_start_index)),
            seed=seed,
        )
    except Exception as exc:
        plot_failure = f"plot generation failed: {type(exc).__name__}: {exc}"
        failure_reason = _append_failure(failure_reason, plot_failure)

    metrics = build_metrics(
        snr_db=float(snr_db),
        seed=int(seed),
        modulation=modulation_name,
        channel=channel_name,
        payload_bits=len(raw_payload_bits),
        ber=ber,
        text_rate=text_rate,
        checksum_pass=checksum_pass,
        sync_start_index=sync_start_index,
        sync_true_offset=prefix_len,
        frame_bits=len(frame_bits),
        coded_payload_bits=len(coded_payload),
        failure_reason=failure_reason,
    )
    write_metrics(metrics, results_dir / "metrics.json")
    return metrics
