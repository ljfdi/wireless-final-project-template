# Wireless Final Project Design

## 1. Project Goal

This project implements a wireless communication baseband simulation system for the course final project. The system reads the UTF-8 text file `Test.txt`, converts it into a bitstream, transmits it through a modular transmitter, AWGN channel, and receiver chain, then writes the recovered text to `results/received.txt`.

The required command-line entry point is:

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

Required outputs after the final implementation phase:

- `results/received.txt`
- `results/metrics.json`
- At least two of `results/constellation.png`, `results/ber_curve.png`, and `results/sync_peak.png`; the intended implementation will generate all three.

This document is the Phase 1 design artifact. It does not claim the system has been implemented.

## 2. Fixed System Chain

The implementation must follow the PRD fixed system chain:

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

The selected basic system uses Scramble rather than a separate Encrypt algorithm. Documentation and code may mention `Encrypt/Scramble` for PRD compatibility, but the implemented reversible transform will be PN XOR scrambling.

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

The final implementation should expose module-level functions with names compatible with the public tests.

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

The reversible Scramble/Encrypt stage will use PN XOR scrambling:

```text
scrambled_bit[i] = raw_payload_bit[i] XOR pn_bit[i]
```

The PN sequence is generated from the CLI `--seed`, so the same seed reproduces the same scrambling sequence. Descrambling uses the same PN sequence and the same XOR operation.

Reasons for this choice:

- It satisfies the PRD requirement for reversible scrambling or encryption.
- It is easy to explain in the report and defense.
- It avoids hidden-test brittleness because it does not depend on the public input text.

## 7. Channel Coding

The default channel code will be a simple, stable, and explainable repetition code, such as rate 1/3 repetition with majority-vote decoding.

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

This code is not spectrally efficient, but it is appropriate for the base project because it demonstrates redundancy, coding rate, and noise tolerance while remaining easy to test and explain. If later mock tests show this is insufficient for hidden low-SNR cases, the design may be revised to an equivalent simple course-related code such as Hamming code, but Phase 1 defaults to repetition code.

## 8. Frame Structure

The serialized frame must include:

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

At SNR >= 12 dB in AWGN, the frame-start detection error should be no more than one QPSK symbol. For plotting, `correlate_preamble(...)` will expose the correlation curve used to create `sync_peak.png`.

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

Planned plots:

- `constellation.png`: noisy received QPSK symbols, ideally clustered around four Gray-coded constellation points.
- `ber_curve.png`: BER versus SNR, using deterministic seeds for reproducible simulation points.
- `sync_peak.png`: preamble correlation score versus candidate start index.

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
