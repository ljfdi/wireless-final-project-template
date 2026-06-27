from __future__ import annotations

"""Unified CLI entry point for the wireless final project."""

import argparse
import sys

from src.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the QPSK/AWGN wireless communication simulation."
    )
    parser.add_argument("--input", dest="input_path", required=True, help="Input UTF-8 text file")
    parser.add_argument("--output", dest="output_path", required=True, help="Recovered text output file")
    parser.add_argument("--snr", dest="snr_db", type=float, default=12.0, help="SNR in dB")
    parser.add_argument("--seed", dest="seed", type=int, default=2026, help="Random seed")
    parser.add_argument("--mod", dest="modulation", choices=["qpsk"], default="qpsk")
    parser.add_argument("--channel", dest="channel", choices=["awgn"], default="awgn")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

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
