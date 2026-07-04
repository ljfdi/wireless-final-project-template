from __future__ import annotations

"""Unified CLI entry point for the wireless final project."""

import argparse
import math
import sys

from src.pipeline import run_pipeline


def finite_float(value: str) -> float:
    """Parse a finite floating-point value for CLI SNR arguments."""
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("invalid SNR: expected a finite number") from exc
    if not math.isfinite(parsed):
        raise argparse.ArgumentTypeError("invalid SNR: value must be finite")
    return parsed


def normalize_argv(argv: list[str] | None) -> list[str] | None:
    """Normalize edge-case SNR tokens so argparse can report clear errors."""
    if argv is None:
        return None
    normalized: list[str] = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--snr" and index + 1 < len(argv) and argv[index + 1].lower() == "-inf":
            normalized.append("--snr=-inf")
            index += 2
            continue
        normalized.append(token)
        index += 1
    return normalized


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the QPSK wireless communication simulation."
    )
    parser.add_argument("--input", dest="input_path", required=True, help="Input UTF-8 text file")
    parser.add_argument("--output", dest="output_path", required=True, help="Recovered text output file")
    parser.add_argument("--snr", dest="snr_db", type=finite_float, default=12.0, help="SNR in dB")
    parser.add_argument("--seed", dest="seed", type=int, default=2026, help="Random seed")
    parser.add_argument("--mod", dest="modulation", choices=["qpsk"], default="qpsk")
    parser.add_argument("--channel", dest="channel", choices=["awgn", "rayleigh"], default="awgn")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    effective_argv = sys.argv[1:] if argv is None else argv
    args = parser.parse_args(normalize_argv(effective_argv))

    try:
        metrics = run_pipeline(
            input_path=args.input_path,
            output_path=args.output_path,
            snr_db=args.snr_db,
            seed=args.seed,
            modulation=args.modulation,
            channel=args.channel,
        )
    except FileNotFoundError as exc:
        parser.error(f"input file not found: {exc.filename}")
    except ValueError as exc:
        parser.error(str(exc))
    except Exception as exc:
        print(f"pipeline failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(
        "Wireless pipeline complete: "
        f"text_match_rate={metrics['text_match_rate']:.3f}, "
        f"checksum_pass={metrics['checksum_pass']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
