from __future__ import annotations

"""End-to-end wireless baseband simulation pipeline."""

import math
from pathlib import Path
import tempfile

import numpy as np

from .channel import awgn, rayleigh
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


SYNC_SEARCH_RADIUS = 32
SYSTEM_BER_SYNC_SEARCH_RADIUS = 12
SYSTEM_BER_SNR_VALUES = [0, 2, 4, 6, 8, 10, 12, 14]
SYSTEM_BER_SEEDS = [2026, 2027, 2028]


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


def _nearby_offsets(radius: int = SYNC_SEARCH_RADIUS) -> list[int]:
    offsets = list(range(-int(radius), int(radius) + 1))
    return sorted(offsets, key=lambda value: (abs(value), value))


def _estimate_flat_channel(received_preamble, known_preamble) -> complex:
    received = np.asarray(received_preamble, dtype=complex).ravel()
    known = np.asarray(known_preamble, dtype=complex).ravel()
    if received.size != known.size or known.size == 0:
        raise ValueError("invalid preamble window for channel estimation")

    denominator = np.vdot(known, known)
    if abs(denominator) < 1e-12:
        raise ValueError("known preamble has zero energy")
    estimate = complex(np.vdot(known, received) / denominator)
    if abs(estimate) < 1e-12:
        raise ValueError("estimated Rayleigh channel is too close to zero")
    return estimate


def run_pipeline(
    input_path,
    output_path,
    snr_db: float = 12.0,
    seed: int = 2026,
    modulation: str = "qpsk",
    channel: str = "awgn",
    generate_plot_files: bool = True,
    include_system_ber_curve: bool = True,
    sync_search_radius: int = SYNC_SEARCH_RADIUS,
) -> dict[str, object]:
    """Run the complete transmitter, channel, receiver, metrics, and plot flow."""
    modulation_name = str(modulation).lower()
    channel_name = str(channel).lower()
    if modulation_name != "qpsk":
        raise ValueError("Only qpsk modulation is supported")
    if channel_name not in {"awgn", "rayleigh"}:
        raise ValueError("Only awgn and rayleigh channels are supported")
    snr_value = float(snr_db)
    if not math.isfinite(snr_value):
        raise ValueError("invalid SNR: value must be finite")

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
    true_fading: complex | None = None
    if channel_name == "awgn":
        received_symbols = awgn(transmitted_symbols, snr_db=snr_value, seed=seed)
    else:
        received_symbols, true_fading = rayleigh(
            transmitted_symbols,
            snr_db=snr_value,
            seed=seed,
            return_channel=True,
        )

    sync_start_index = 0
    detected_start = 0
    sync_candidates_tried = 0
    sync_candidates_parseable = 0
    recovered_payload_bits: list[int] = []
    recovered_text = ""
    checksum_pass = False
    failure_reason = ""
    constellation_symbols = received_symbols
    selected_channel_estimate: complex | None = None
    equalization_mode = "none"
    sync_details = correlate_preamble(received_symbols, preamble=preamble_symbols)

    try:
        detected_start = int(synchronize(received_symbols, preamble=preamble_symbols))
        candidates = []
        search_radius = int(sync_search_radius)
        for offset in _nearby_offsets(search_radius):
            candidate = detected_start + offset
            if candidate >= 0 and candidate not in candidates:
                candidates.append(candidate)
        sync_candidates_tried = len(candidates)

        results = []
        last_error = ""
        for candidate_start in candidates:
            try:
                frame_end = candidate_start + len(frame_symbols)
                raw_frame_symbols = received_symbols[candidate_start:frame_end]
                if raw_frame_symbols.size < frame_symbols.size:
                    raise ValueError("candidate frame is shorter than expected")

                channel_estimate = None
                if channel_name == "rayleigh":
                    channel_estimate = _estimate_flat_channel(
                        received_symbols[candidate_start : candidate_start + len(preamble_symbols)],
                        preamble_symbols,
                    )
                    aligned_frame_symbols = raw_frame_symbols / channel_estimate
                else:
                    aligned_frame_symbols = raw_frame_symbols

                received_frame_bits = qpsk_demodulate(aligned_frame_symbols)
                parsed = parse_frame(received_frame_bits)
                coded_payload_rx = parsed.get("coded_payload") or parsed.get("payload") or []
                raw_payload_length = int(
                    parsed.get("raw_payload_length", parsed.get("length", len(raw_payload_bits)))
                )
                coded_payload_length = int(
                    parsed.get("coded_payload_length", parsed.get("payload_length", len(coded_payload_rx)))
                )

                decoded_scrambled = channel_decode(coded_payload_rx)
                candidate_payload_bits = descramble(decoded_scrambled, seed=seed)[:raw_payload_length]
                candidate_text, decode_error = _safe_text_decode(candidate_payload_bits)
                length_valid = (
                    raw_payload_length == len(raw_payload_bits)
                    and coded_payload_length == len(coded_payload)
                    and len(candidate_payload_bits) == len(raw_payload_bits)
                )
                candidate_checksum = (
                    length_valid
                    and int(parsed.get("checksum", parsed.get("crc", -1)))
                    == crc32_bits(candidate_payload_bits)
                )
                correlation = np.asarray(sync_details.get("correlation", []), dtype=float)
                preamble_score = (
                    float(correlation[candidate_start])
                    if 0 <= candidate_start < correlation.size
                    else 0.0
                )
                result = {
                    "start": candidate_start,
                    "symbols": aligned_frame_symbols,
                    "payload_bits": candidate_payload_bits,
                    "text": candidate_text,
                    "decode_error": decode_error,
                    "checksum": candidate_checksum,
                    "length_valid": length_valid,
                    "preamble_score": preamble_score,
                    "distance": abs(candidate_start - detected_start),
                    "channel_estimate": channel_estimate,
                }
                results.append(result)
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"

        sync_candidates_parseable = len(results)
        best_result = None
        if results:
            def _candidate_rank(result):
                return (
                    int(bool(result["checksum"])),
                    float(result["preamble_score"]),
                    -int(result["distance"]),
                    int(bool(result["length_valid"])),
                    int(not result["decode_error"]),
                )

            best_result = max(results, key=_candidate_rank)

        if best_result is None:
            raise ValueError(f"no valid frame candidate near synchronization peak; {last_error}")

        sync_start_index = int(best_result["start"])
        constellation_symbols = best_result["symbols"]
        recovered_payload_bits = best_result["payload_bits"]
        recovered_text = best_result["text"]
        selected_channel_estimate = best_result["channel_estimate"]
        equalization_mode = "preamble_one_tap" if channel_name == "rayleigh" else "none"
        failure_reason = _append_failure(failure_reason, best_result["decode_error"])
        checksum_pass = bool(best_result["checksum"])
        if not checksum_pass and not failure_reason:
            failure_reason = (
                "checksum mismatch after synchronization candidate search "
                f"(coarse_start={detected_start}, radius={search_radius}, "
                f"candidates={sync_candidates_tried})"
            )
    except Exception as exc:
        sync_start_index = int(detected_start)
        failure_reason = _append_failure(
            failure_reason,
            f"receiver failed: {type(exc).__name__}: {exc}",
        )

    output_file.write_text(recovered_text, encoding="utf-8")

    ber = bit_error_rate(raw_payload_bits, recovered_payload_bits)
    text_rate = text_match_rate(input_text, recovered_text)
    if text_rate == 1.0 and ber == 0.0 and not checksum_pass:
        failure_reason = _append_failure(failure_reason, "checksum mismatch despite text recovery")

    system_curve = None
    if generate_plot_files and include_system_ber_curve and channel_name == "awgn":
        try:
            system_curve = compute_system_ber_curve(
                input_path=input_file,
                snr_values=SYSTEM_BER_SNR_VALUES,
                seeds=SYSTEM_BER_SEEDS,
                channel=channel_name,
                mod=modulation_name,
                temp_root=results_dir,
            )
        except Exception as exc:
            failure_reason = _append_failure(
                failure_reason,
                f"system BER sweep failed: {type(exc).__name__}: {exc}",
            )

    plot_failure = ""
    try:
        if generate_plot_files:
            generate_plots(
                output_dir=results_dir,
                constellation_symbols=constellation_symbols,
                sync_correlation=sync_details.get("correlation", []),
                sync_peak_index=int(sync_details.get("peak_index", sync_start_index)),
                seed=seed,
                system_curve=system_curve,
            )
    except Exception as exc:
        plot_failure = f"plot generation failed: {type(exc).__name__}: {exc}"
        failure_reason = _append_failure(failure_reason, plot_failure)

    metrics = build_metrics(
        snr_db=snr_value,
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
    metrics["sync_coarse_start_index"] = int(detected_start)
    metrics["sync_search_radius"] = int(sync_search_radius)
    metrics["sync_candidates_tried"] = int(sync_candidates_tried)
    metrics["sync_candidates_parseable"] = int(sync_candidates_parseable)
    metrics["equalization"] = equalization_mode
    if system_curve is not None:
        metrics["ber_curve_type"] = "uncoded_reference_and_end_to_end_system"
        metrics["system_ber_curve_path"] = str(results_dir / "system_ber_curve.png").replace("\\", "/")
        metrics["system_ber_snr_values"] = system_curve["snr_values"]
        metrics["system_ber_values"] = system_curve["ber_values"]
        metrics["system_ber_seeds"] = system_curve["seeds"]
        metrics["system_ber_frame_success_rates"] = system_curve["frame_success_rates"]
        metrics["system_ber_checksum_pass_rates"] = system_curve["checksum_pass_rates"]
        metrics["system_ber_text_match_rates"] = system_curve["text_match_rates"]
    if channel_name == "rayleigh":
        metrics["fading_abs"] = None if true_fading is None else float(abs(true_fading))
        metrics["estimated_channel_abs"] = (
            None if selected_channel_estimate is None else float(abs(selected_channel_estimate))
        )
        metrics["channel_estimation_error"] = (
            None
            if true_fading is None or selected_channel_estimate is None
            else float(abs(selected_channel_estimate - true_fading))
        )
    write_metrics(metrics, results_dir / "metrics.json")
    return metrics


def compute_system_ber_curve(
    input_path,
    snr_values=None,
    seeds=None,
    channel: str = "awgn",
    mod: str = "qpsk",
    temp_root=None,
) -> dict[str, object]:
    """Compute end-to-end coded-system BER by running the full pipeline.

    The sweep writes only into a temporary output directory and disables plot
    generation, so it does not overwrite the caller's formal received text or
    metrics.json files.
    """
    snr_list = [float(value) for value in (snr_values or SYSTEM_BER_SNR_VALUES)]
    if any(not math.isfinite(value) for value in snr_list):
        raise ValueError("invalid SNR sweep value: all SNR values must be finite")
    seed_list = [int(value) for value in (seeds or SYSTEM_BER_SEEDS)]
    temp_parent = Path(temp_root) if temp_root is not None else Path(input_path).resolve().parent
    temp_parent.mkdir(parents=True, exist_ok=True)

    average_ber: list[float] = []
    frame_success_rates: list[float] = []
    checksum_pass_rates: list[float] = []
    text_match_rates: list[float] = []

    with tempfile.TemporaryDirectory(prefix="ber_sweep_tmp_", dir=str(temp_parent)) as tmp_dir:
        tmp_path = Path(tmp_dir)
        for snr_db in snr_list:
            ber_values: list[float] = []
            success_values: list[float] = []
            checksum_values: list[float] = []
            text_values: list[float] = []
            for seed in seed_list:
                output_path = tmp_path / f"snr_{snr_db:g}_seed_{seed}" / "received.txt"
                metrics = run_pipeline(
                    input_path=input_path,
                    output_path=output_path,
                    snr_db=float(snr_db),
                    seed=int(seed),
                    modulation=mod,
                    channel=channel,
                    generate_plot_files=False,
                    include_system_ber_curve=False,
                    sync_search_radius=SYSTEM_BER_SYNC_SEARCH_RADIUS,
                )
                ber_values.append(float(metrics.get("ber", 1.0)))
                text_rate = float(metrics.get("text_match_rate", 0.0))
                checksum_pass = bool(metrics.get("checksum_pass", False))
                fer = float(metrics.get("fer", 1.0))
                text_values.append(text_rate)
                checksum_values.append(1.0 if checksum_pass else 0.0)
                success_values.append(1.0 if fer == 0.0 else 0.0)

            average_ber.append(float(np.mean(ber_values)))
            frame_success_rates.append(float(np.mean(success_values)))
            checksum_pass_rates.append(float(np.mean(checksum_values)))
            text_match_rates.append(float(np.mean(text_values)))

    return {
        "snr_values": snr_list,
        "ber_values": average_ber,
        "seeds": seed_list,
        "frame_success_rates": frame_success_rates,
        "checksum_pass_rates": checksum_pass_rates,
        "text_match_rates": text_match_rates,
    }
