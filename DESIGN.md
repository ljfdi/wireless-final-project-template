# Wireless Final Project Design

## 1. Project Goal

This project implements a wireless communication baseband simulation system for the course final project. The system reads the UTF-8 text file `Test.txt`, converts it into a bitstream, transmits it through a modular transmitter, AWGN channel, and receiver chain, then writes the recovered text to `results/received.txt`.

The required command-line entry point is:

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

Generated outputs after the final implementation phase:

- `results/received.txt`
- `results/metrics.json`
- `results/constellation.png`
- `results/ber_curve.png`
- `results/system_ber_curve.png`
- `results/sync_peak.png`

This document describes the final implemented architecture of the wireless baseband simulation system, including the required AWGN/QPSK baseline, the Level 3 Rayleigh and GUI extensions, and both reference and end-to-end BER-SNR visualizations where available.

## 2. Fixed System Chain

The implementation follows the PRD fixed system chain:

```text
Test.txt
-> Source Encode
-> Scramble/Encrypt
-> Channel Encode
-> Frame Build
-> QPSK Modulate
-> Channel
-> Synchronization
-> QPSK Demodulate
-> Channel Decode
-> Descramble/Decrypt
-> Source Decode
-> results/received.txt
-> Metrics/Plots
```

The selected basic system uses Scramble rather than a separate Encrypt algorithm. Documentation and code may mention `Encrypt/Scramble` for PRD compatibility, but the implemented reversible transform is PN XOR scrambling.

## 3. Transmit and Receive Ordering

The transmit-side data flow is:

1. `source_encode(text)` converts UTF-8 text into raw payload bits.
2. `scramble(raw_payload_bits, seed)` applies PN XOR scrambling.
3. `channel_encode(scrambled_payload_bits)` applies a simple channel code and returns `coded_payload`.
4. `build_frame(...)` creates:

```text
preamble + raw_payload_length + coded_payload_length + checksum/CRC + coded_payload
```

The receive-side data flow is:

1. `synchronize(received_symbols, preamble=None)` detects the QPSK frame start.
2. `qpsk_demodulate(frame_symbols)` recovers frame bits.
3. `parse_frame(frame_bits)` extracts `raw_payload_length`, `coded_payload_length`, checksum/CRC, and `coded_payload`.
4. `channel_decode(coded_payload)` recovers scrambled payload bits.
5. `descramble(scrambled_payload_bits, seed)` recovers raw payload bits.
6. The receiver uses `raw_payload_length` to remove padding and restore the exact source bit count.
7. `source_decode(raw_payload_bits)` converts UTF-8 bits back to text.

The `raw_payload_length` field must mean the original source-encoded payload bit count before scrambling and before channel coding. The checksum/CRC covers the original payload bytes or original payload bitstream, not the coded payload.

## 4. Module Interfaces and Data Types

The final implementation exposes module-level functions with names compatible with the public tests.

| Module | Function | Input | Output |
|---|---|---|---|
| `src/source.py` | `source_encode(text)` / `text_to_bits(text)` | `str` | `list[int]` of 0/1 bits |
| `src/source.py` | `source_decode(bits)` / `bits_to_text(bits)` | `list[int]` | `str` |
| `src/scramble.py` | `scramble(bits, seed)` | `list[int]`, `int` | scrambled `list[int]` |
| `src/scramble.py` | `descramble(bits, seed)` | `list[int]`, `int` | recovered `list[int]` |
| `src/channel_coding.py` | `channel_encode(bits)` | `list[int]` | coded `list[int]` |
| `src/channel_coding.py` | `channel_decode(bits)` | coded `list[int]` | decoded `list[int]` |
| `src/framing.py` | `build_frame(payload_bits, raw_payload_length=None, checksum=None)` | coded payload bits plus metadata | serialized frame bits or dict-like frame |
| `src/framing.py` | `parse_frame(frame_bits)` | demodulated frame bits | dict-like parsed payload and metadata |
| `src/modulation.py` | `qpsk_modulate(bits)` | `list[int]` | complex QPSK symbols |
| `src/modulation.py` | `qpsk_demodulate(symbols)` | complex symbols | demodulated bits |
| `src/channel.py` | `awgn(symbols, snr_db, seed)` | complex symbols | noisy complex symbols |
| `src/synchronization.py` | `synchronize(received_symbols, preamble=None)` | complex symbols | `int start_index` |
| `src/synchronization.py` | `correlate_preamble(received_symbols, preamble)` | complex symbols | correlation values and peak details |

Important synchronization API rule: `synchronize(received_symbols, preamble=None)` should return an integer start index by default. If detailed correlation data is needed for `sync_peak.png`, use `correlate_preamble(...)` or an optional `synchronize(..., return_details=True)` mode. The default return value should not be a dict or tuple.

Frame API compatibility note: the primary frame interface uses `raw_payload_length` and `checksum`. For compatibility with tests and public-test-style callers, implementation may also accept `payload_length` as an alias for `raw_payload_length`, and `checksum_bits` as an alias or bit-level representation of `checksum`. `parse_frame(...)` should preferably return a dict-like object containing preamble/length/checksum/payload metadata so tests and reports can inspect the frame structure directly.

## 5. Source Coding

Source coding converts text to UTF-8 bytes and then to bits in a deterministic order. Source decoding groups recovered bits into bytes and decodes them as UTF-8 after the receiver trims to `raw_payload_length`.

Design constraints:

- The bitstream length after source encoding must be divisible by 8.
- The codec must work for different Chinese UTF-8 texts, not only the public `Test.txt`.
- UTF-8 decode errors in low SNR cases should be handled without crashing; the receiver should still write metrics explaining failure.

## 6. Scramble/Encrypt

The reversible Scramble/Encrypt stage uses PN XOR scrambling:

```text
scrambled_bit[i] = raw_payload_bit[i] XOR pn_bit[i]
```

The PN sequence is generated from the CLI `--seed`, so the same seed reproduces the same scrambling sequence. Descrambling uses the same PN sequence and the same XOR operation.

Reasons for this choice:

- It satisfies the PRD requirement for reversible scrambling or encryption.
- It is easy to explain in the report and defense.
- It avoids hidden-test brittleness because it does not depend on the public input text.

## 7. Channel Coding

The default channel code is a simple, stable, and explainable rate 1/3 repetition code with majority-vote decoding.

Transmit:

```text
0 -> 000
1 -> 111
```

Receive:

```text
000, 001, 010, 100 -> 0
111, 110, 101, 011 -> 1
```

This code is not spectrally efficient, but it is appropriate for the base project because it demonstrates redundancy, coding rate, and noise tolerance while remaining easy to test and explain.

## 8. Frame Structure

The serialized frame includes:

```text
preamble
raw_payload_length
coded_payload_length
checksum/CRC
coded_payload
```

Field meanings:

- `preamble`: known bit pattern that maps to known QPSK symbols for synchronization.
- `raw_payload_length`: number of bits after source encoding and before scrambling. This is the authoritative length for padding removal and UTF-8 recovery.
- `coded_payload_length`: number of bits after channel encoding. This helps `parse_frame` extract the exact coded payload from the demodulated bitstream.
- `checksum/CRC`: error-detection field covering original payload bytes or original payload bits.
- `coded_payload`: channel-coded version of the scrambled payload.

The frame parser should validate length fields and checksum/CRC. In SNR >= 12 dB AWGN public conditions, `checksum_pass` is expected to be true. In low SNR conditions, checksum failure should be recorded rather than causing an unhandled crash.

Recommended `parse_frame(...)` metadata keys include `preamble`, `raw_payload_length` or compatible `length`, `coded_payload_length` or compatible payload length metadata, `checksum` or `crc`, and `payload` or `coded_payload`. This recommendation does not change the meaning of `raw_payload_length`: it remains the source-encoded payload bit count before scrambling.

## 9. QPSK Modulation

The required QPSK mapping is PRD Gray coding:

```text
00 -> ( 1 + 1j) / sqrt(2)
01 -> (-1 + 1j) / sqrt(2)
11 -> (-1 - 1j) / sqrt(2)
10 -> ( 1 - 1j) / sqrt(2)
```

The `1/sqrt(2)` normalization makes each ideal symbol have unit power:

```text
abs((+/-1 +/- 1j) / sqrt(2))^2 = 1
```

If the bit count entering QPSK modulation is odd, the modulator pads one `0` bit at the frame tail. The receiver must remove padding by using the length fields, especially `raw_payload_length`, after frame parsing, channel decoding, and descrambling.

## 10. AWGN Channel and SNR

The base channel is AWGN. The SNR definition follows the PRD:

```text
SNR = average modulated-symbol power / average complex Gaussian noise power
```

For QPSK symbols normalized to average power near 1:

```text
snr_linear = 10 ** (snr_db / 10)
noise_power = signal_power / snr_linear
noise = sqrt(noise_power / 2) * (N(0,1) + j*N(0,1))
```

The AWGN function must accept a fixed `seed` so repeated runs with the same input, SNR, and seed are reproducible.

## 11. Synchronization

The system must not assume the receiver naturally knows the frame start. The transmitter or channel wrapper will support a random prefix offset of 0 to 128 QPSK symbols before the frame.

The synchronization method is preamble correlation:

1. Convert the known preamble bits into known QPSK preamble symbols.
2. Slide the preamble over received symbols.
3. Compute a correlation score at each candidate start.
4. Return the index with the strongest peak as `sync_start_index`.

The preamble correlation peak is treated as coarse synchronization, not as an unquestioned final decision. The receiver performs a checksum-assisted local candidate search around the detected peak:

- Search radius: `detected_start +/- 32` QPSK symbols.
- For each candidate start, cut the frame, demodulate, parse the frame, channel-decode, descramble, trim by `raw_payload_length`, UTF-8 decode, and verify CRC/checksum.
- Prefer candidates with `checksum_pass=true`.
- When multiple candidates pass checksum, prefer stronger preamble correlation, then smaller distance from the coarse peak, then valid payload length and valid UTF-8 decode.
- If no candidate passes checksum, write the best failure result and a `failure_reason` in `metrics.json` instead of crashing.

This protects hidden-test cases where the preamble-correlation peak is several symbols away from the true frame start. For plotting, `correlate_preamble(...)` exposes the correlation curve used to create `sync_peak.png`.

## 12. Metrics and Plots

The final implementation must write `results/metrics.json` with at least:

```json
{
  "snr_db": 12,
  "seed": 2026,
  "modulation": "qpsk",
  "channel": "awgn",
  "payload_bits": 2400,
  "ber": 0.0,
  "fer": 0.0,
  "text_match_rate": 1.0,
  "checksum_pass": true,
  "sync_start_index": 25
}
```

Field definitions:

- `snr_db`: CLI SNR value.
- `seed`: CLI random seed.
- `modulation`: expected to be `qpsk`.
- `channel`: expected to be `awgn`.
- `payload_bits`: `raw_payload_length`.
- `ber`: bit error rate measured against the source payload bits when reference text is available.
- `fer`: frame error indicator or frame error rate for this run.
- `text_match_rate`: 1.0 for exact text recovery; otherwise a similarity or exact-match score documented in code.
- `checksum_pass`: CRC/checksum validation result.
- `sync_start_index`: detected QPSK symbol start index.

Additional diagnostic fields may include:

- `sync_true_offset`: simulated random prefix length when known.
- `sync_error_symbols`: `sync_start_index - sync_true_offset` when known.
- `sync_coarse_start_index`: raw preamble-correlation peak before CRC refinement.
- `sync_search_radius`: candidate-search radius around the coarse peak.
- `sync_candidates_tried`: number of start positions considered.
- `failure_reason`: receiver or checksum failure explanation for low SNR cases.

Generated plots:

- `constellation.png`: noisy received QPSK symbols, ideally clustered around four Gray-coded constellation points.
- `ber_curve.png`: uncoded QPSK reference BER-SNR curve, also used as the combined BER plot when the end-to-end system curve is available.
- `system_ber_curve.png`: complete system BER-SNR plot only, computed from full pipeline runs.
- `sync_peak.png`: preamble correlation score versus candidate start index.

The project generates two BER-related visualizations when the system BER sweep is enabled. `ber_curve.png` is used as the QPSK reference BER-SNR curve, showing the modulation-layer trend under AWGN. `system_ber_curve.png` records the end-to-end repetition-coded system BER-SNR curve by running the complete pipeline across multiple SNR values and seeds. The end-to-end curve includes source coding, scrambling, repetition coding, framing, QPSK modulation, AWGN channel, synchronization, demodulation, channel decoding, descrambling, checksum validation, and text recovery.

The project keeps both BER views because they explain different layers:

- The uncoded QPSK reference curve shows modulation-layer AWGN behavior.
- The end-to-end system curve shows the actual file-transfer chain after scrambling, repetition coding, frame synchronization, QPSK demodulation, repetition decoding, descrambling, UTF-8 recovery, and checksum validation.
- Repetition coding reduces end-to-end BER at medium/high SNR by adding redundancy, but the tradeoff is lower coding rate.

The system BER sweep uses default SNR values `[0, 2, 4, 6, 8, 10, 12, 14]` and seeds `[2026, 2027, 2028]`. It runs into temporary output directories with plot generation disabled, so it does not overwrite the formal `results/received.txt` or final `results/metrics.json`.

Additional system BER metrics may include:

- `ber_curve_type`
- `system_ber_curve_path`
- `system_ber_snr_values`
- `system_ber_values`
- `system_ber_seeds`
- `system_ber_frame_success_rates`
- `system_ber_checksum_pass_rates`
- `system_ber_text_match_rates`

## 13. Low SNR Behavior

At low SNR, exact text recovery is not guaranteed. The system must still:

- Exit cleanly.
- Write `results/metrics.json`.
- Mark `checksum_pass` false or report an error reason in metrics/log output.
- Write a safe `results/received.txt` representation if UTF-8 decoding fails.
- Avoid interactive prompts or crashes.

## 14. Hidden Tests and Anti-Hardcoding Constraints

Hidden validation may use:

- Different Chinese UTF-8 texts.
- Different text lengths.
- Different SNR values.
- Different random seeds.
- Random synchronization offsets from 0 to 128 QPSK symbols.
- Missing files or invalid CLI parameters.
- Anti-hardcoding checks.
- Documentation and implementation consistency checks.

The implementation must not:

- Copy `Test.txt` directly to `results/received.txt`.
- Hardcode public test input, output, or intermediate values.
- Bypass the wireless communication chain.
- Break communication principles only to satisfy public tests.
- Generate complex code that cannot be explained in the report or defense.

## 15. OpenSpec and Superpowers Process

Superpowers skills are available and guide the workflow. OpenSpec skills are present, but the `openspec` CLI is not available in this environment and will not be installed or repaired during this project.

Therefore, the project follows an OpenSpec-equivalent process:

- Proposal intent maps to the project goal and scope in this `DESIGN.md`.
- Design maps to this document's architecture and module decisions.
- Specs map to the required interfaces, data flow, and behavioral constraints.
- Tasks map to `TEST_PLAN.md`, later `MOCK_TEST_REPORT.md`, and Phase 2 TDD steps.

The final submission remains the teacher-required files rather than an `openspec/` directory.

## 16. Level 3 Optional Rayleigh Extension

The Level 3 copy adds one optional advanced channel mode while preserving the default AWGN validation path.

- Default required command remains unchanged:
  `python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn`.
- Optional command uses `--channel rayleigh`.
- The Rayleigh model is block-flat fading:
  `y = h * x + n`, where `h` is a seed-controlled complex Gaussian fading coefficient and `n` is complex AWGN.
- The receiver does not use the true simulation `h` for decisions. It estimates the flat channel from the known preamble:
  `h_hat = vdot(preamble_symbols, rx_preamble) / vdot(preamble_symbols, preamble_symbols)`.
- The receiver applies one-tap equalization with `received / h_hat`.
- The true `h` may still be recorded for diagnostic `channel_estimation_error`, but it is not the equalizer input.
- The AWGN branch is kept separate and remains the main public-test and grading path.
- Rayleigh mode may use CRC-aided synchronization refinement around the preamble-correlation peak to avoid a one-symbol ambiguity under fading. The default `synchronize(...)` API still returns an integer start index.
- Rayleigh metrics include `equalization=preamble_one_tap`, `estimated_channel_abs`, and, when simulation truth is available, `fading_abs` and `channel_estimation_error`.
- Rayleigh demonstration artifacts are saved separately as `results/rayleigh_received.txt` and `results/rayleigh_metrics.json`; final `results/metrics.json` is restored to the AWGN result for default grading.

## 17. Level 3 Optional GUI Extension

The project also provides an optional Tkinter desktop GUI for demonstration:

- Launch command: `python gui.py`.
- The GUI is a thin wrapper around `src.pipeline.run_pipeline(...)`.
- Default GUI parameters match the required AWGN command: `Test.txt`, `results/received.txt`, SNR `12`, seed `2026`, modulation `qpsk`, and channel `awgn`.
- Users can select input and output files, change SNR and seed, and switch between `awgn` and `rayleigh`.
- After a run, the GUI displays core metrics, exact text-match status, and the generated constellation, BER, system BER, and synchronization-peak plots.
- The GUI does not replace `main.py`; the CLI remains the official grading entry point.
- The GUI does not change the base communication algorithms or public-test interfaces.
