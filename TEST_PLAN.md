# Wireless Final Project Test Plan

## 1. Scope and Phase Boundary

This document defines the testing strategy for the wireless communication final project. It is created during Phase 1, the design-document stage.

Phase 1 only creates or updates planning documents. It does not create `main.py`, `src/`, `tests/`, or `results/`, and it does not implement Python business code.

Phase 2 will create mock tests and begin the TDD RED stage. Production implementation should start only after the relevant failing tests have been written and observed to fail for the expected reason.

## 2. Test Environment and Commands

Expected local setup:

```bash
pip install -r requirements.txt
```

Public test command:

```bash
pytest public_tests -q
```

Required end-to-end command:

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

GitHub Actions will run public tests in Python 3.11 and install dependencies from `requirements.txt`, with optional `student_requirements.txt` if later added. The design should avoid undeclared dependencies and interactive input.

## 3. Mock Test Plan

Mock tests will be written in Phase 2 before production code. Their purpose is to validate the design assumptions before full implementation.

Planned mock tests:

| Mock test | Purpose | Expected result |
|---|---|---|
| Source and scrambling mock | Verify UTF-8 text becomes bits, PN XOR scrambling changes bits, and descrambling recovers exact bits | Raw payload bits match after descramble |
| Frame and QPSK padding mock | Verify odd-length payload can be framed, modulated, demodulated, parsed, and trimmed using `raw_payload_length` | Recovered payload length and bits match input |
| AWGN and synchronization mock | Verify a known QPSK preamble can be detected after offsets 0, 1, 25, 64, and 128 at SNR 12 dB | `synchronize(...)` returns an integer start index within tolerance |
| Low-SNR failure mock | Verify low SNR produces metrics and does not crash even if checksum fails | Program records failure indicators |

Mock results will later be summarized in `MOCK_TEST_REPORT.md`, including at least one design risk or defect and any DESIGN.md revisions.

## 4. Unit Test Plan

Unit tests should target stable module-level APIs compatible with public test discovery.

### 4.1 Source Coding

Test: UTF-8 text and bitstream round-trip.

- Input: Chinese UTF-8 sample text, including punctuation.
- Action: `source_encode(text)` then `source_decode(bits)`.
- Expected:
  - `bits` is non-empty.
  - `len(bits) % 8 == 0`.
  - Recovered text equals input text.

### 4.2 PN XOR Scrambling

Test: scramble/descramble round-trip.

- Input: random bit list and fixed seed 2026.
- Action: `scramble(bits, seed)` then `descramble(scrambled, seed)`.
- Expected:
  - Scrambled bits are reproducible for the same seed.
  - Descrambled bits equal original bits.
  - Different seeds produce different PN sequences for non-trivial inputs.

### 4.3 Channel Coding

Test: channel encode/decode round-trip.

- Input: random bit list with lengths divisible and not divisible by repetition block size.
- Action: `channel_encode(bits)` then `channel_decode(coded_bits)`.
- Expected:
  - Decoded bits match original bits after any internal padding is trimmed according to metadata or known length.
  - Noiseless channel decode has zero errors.

### 4.4 Framing

Test: frame build and parse.

- Input: coded payload, raw payload length, coded payload length, checksum/CRC.
- Action: `build_frame(...)` then `parse_frame(frame_bits)`.
- Expected:
  - Frame contains preamble, `raw_payload_length`, `coded_payload_length`, checksum/CRC, and `coded_payload`.
  - Parsed payload and metadata match the build inputs.
  - Checksum/CRC covers original payload bytes or original payload bitstream.
  - `build_frame` should primarily accept `raw_payload_length` and `checksum`, and may also accept compatibility aliases `payload_length` and `checksum_bits`.
  - `parse_frame` should preferably return dict-like metadata with inspectable preamble, length, checksum/CRC, and payload fields.

### 4.5 QPSK Modulation

Test: fixed Gray mapping.

- Input bits: `00 01 11 10`.
- Expected mapping:
  - `00 -> (1+j)/sqrt(2)`
  - `01 -> (-1+j)/sqrt(2)`
  - `11 -> (-1-j)/sqrt(2)`
  - `10 -> (1-j)/sqrt(2)`
- Expected average symbol power: approximately 1.

Test: noiseless QPSK demodulation.

- Input: random even-length bitstream.
- Action: `qpsk_modulate(bits)` then `qpsk_demodulate(symbols)`.
- Expected: recovered bits match input bits.

Test: odd bit payload and QPSK padding.

- Input: odd-length payload bits.
- Action: frame, modulate, demodulate, parse, decode, descramble, trim by `raw_payload_length`.
- Expected: recovered source payload has the original odd length and exact bits.

### 4.6 AWGN Channel

Test: AWGN seed reproducibility.

- Input: fixed QPSK symbols, SNR 12 dB, seed 2026.
- Action: run `awgn(symbols, snr_db=12, seed=2026)` twice.
- Expected: outputs are equal within floating-point tolerance.

Test: SNR definition.

- Input: normalized QPSK symbols and target SNR.
- Expected: measured average noise power is consistent with `signal_power / snr_linear` within statistical tolerance for a large symbol set.

### 4.7 Synchronization

Test: synchronization offsets 0, 1, 25, 64, and 128.

- Input: random prefix symbols, known QPSK preamble, payload symbols.
- Action: `synchronize(received_symbols, preamble=preamble)`.
- Expected:
  - Default return value is an `int`.
  - Detected start is within 1 QPSK symbol at SNR 12 dB.

Test: correlation details.

- Action: `correlate_preamble(received_symbols, preamble)` or optional `synchronize(..., return_details=True)`.
- Expected: returns data suitable for `sync_peak.png` without changing the default `synchronize` API.

## 5. End-to-End Test Plan

### 5.1 Public Required Scenario

Run:

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

Expected:

- Process exits with code 0.
- No interactive prompt.
- `results/received.txt` exists.
- `results/metrics.json` exists.
- `received.txt` exactly matches `Test.txt`.
- `metrics.json` has:
  - `snr_db`
  - `seed`
  - `modulation`
  - `channel`
  - `payload_bits`
  - `ber`
  - `fer`
  - `text_match_rate`
  - `checksum_pass`
  - `sync_start_index`
- At least two required plots exist and are non-empty.

### 5.2 Low SNR Scenario

Run with a lower SNR, such as 0 dB or 3 dB.

Expected:

- Process exits cleanly.
- `metrics.json` is generated.
- `checksum_pass` may be false.
- `ber`, `fer`, and `text_match_rate` are present.
- Any UTF-8 decode issue is handled without an unhandled exception.

### 5.3 Different Input Texts

Use temporary UTF-8 test files with:

- Short Chinese text.
- Longer Chinese text.
- Mixed Chinese, English, digits, and punctuation.
- Empty or very small text, if the PRD validation permits.

Expected:

- For SNR >= 12 dB, normal non-empty texts recover exactly.
- Metrics reflect actual payload bit length.
- No output is hardcoded to the public `Test.txt`.

## 6. Public Tests Alignment

The public tests check the following areas, so implementation and documentation must align with them:

| Public area | Planned coverage |
|---|---|
| Required files | Phase 1 creates docs; later phases create `main.py`, `src/`, `tests/`, `results/` |
| DESIGN.md fixed chain | This document explicitly names Source Encode, Encrypt/Scramble, Channel Encode, Frame Build, QPSK Modulate/Demodulate, Channel, Synchronization, Channel Decode, Source Decode, Metrics |
| MOCK_TEST_REPORT.md | Phase 3 will summarize mock tests, risks, and design revisions |
| UTF-8 codec | Unit tests for source round-trip |
| Frame fields | Unit tests for preamble, length, payload, checksum/CRC |
| Scramble/encrypt | Unit tests for PN XOR reversibility |
| Channel coding | Unit tests for noiseless encode/decode |
| QPSK mapping | Unit tests for PRD Gray-coded quadrants and unit power |
| QPSK padding | Unit and end-to-end tests using odd bit lengths |
| AWGN | Seed reproducibility and SNR behavior tests |
| Synchronization | Offset tests at 0, 1, 25, 64, and 128 |
| CLI and outputs | End-to-end command test |
| metrics.json | Schema and value tests |
| Plots | Existence and non-empty file tests |
| Anti-shortcut | Static and behavioral checks against direct copy and hardcoding |

## 7. Hidden Tests Risk Plan

Hidden tests may use broader cases than public tests. Planned risk tests:

- Different Chinese UTF-8 texts and lengths.
- Different seeds, verifying reproducible AWGN and PN scrambling per seed.
- Different SNR values, including low SNR.
- Random synchronization offsets from 0 to 128 symbols.
- Invalid modulation or channel arguments.
- Missing input file.
- Output directory creation behavior.
- Static scan for suspicious direct-copy patterns.
- Re-running with modified `Test.txt` to ensure the output follows decoded receiver data, not hardcoded public text.
- Documentation consistency scan: algorithm names, metrics fields, and frame field meanings match `DESIGN.md`.

## 8. Anti-Copy and Anti-Hardcoding Checks

Manual and automated checks should verify:

- No `shutil.copy`, `copyfile`, or equivalent direct copy from `Test.txt` to `received.txt` in the main data path.
- No hardcoded public sample text.
- No hardcoded received output.
- No bypass that writes decoded text before the receive chain completes.
- Metrics are computed from actual run data.

## 9. Phase 2 Entry Criteria

Before Phase 2 starts:

- `DESIGN.md`, `TEST_PLAN.md`, and `AI_LOG.md` have been created or updated.
- The user confirms Phase 2.
- Mock tests are written first.
- TDD RED is observed before production implementation.

Phase 2 should stop after mock/TDD RED tasks unless the user explicitly approves moving into implementation.

## 10. Phase 3 Review Notes

Phase 3 reviewed the RED mock results against `DESIGN.md`, `TEST_PLAN.md`, and the created tests. The failures were caused by missing `src/` modules and missing `main.py`, not by a design contradiction.

No test changes are required. The only design clarification is that `build_frame` may accept compatibility aliases (`payload_length`, `checksum_bits`) while preserving the primary `raw_payload_length` and `checksum` semantics, and `parse_frame` should return dict-like metadata to make frame fields easy to inspect.

## 11. Phase 5 Final Verification Summary

Phase 5 regenerated the final required outputs with the fixed command:

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

Final output checks:

- `results/received.txt` exists and matches `Test.txt` exactly.
- `results/metrics.json` exists and includes the required fields:
  `snr_db`, `seed`, `modulation`, `channel`, `payload_bits`, `ber`, `fer`,
  `text_match_rate`, `checksum_pass`, and `sync_start_index`.
- `text_match_rate` is `1.0`.
- `checksum_pass` is `true`.
- `ber` is `0.0`.
- `results/constellation.png`, `results/ber_curve.png`, and `results/sync_peak.png`
  all exist and are non-empty.

Final test commands:

```bash
python -m pytest tests -q
```

Result:

```text
17 passed
```

Public tests were run in a temporary sandbox copy because the public-test fixture writes
`Test.txt`; this preserves the repository's checked input file while still validating the
same code and documents.

```bash
python -m pytest public_tests -q
```

Result:

```text
22 passed
```

Final anti-copy and anti-hardcoding checks:

- Static scan of `main.py` and `src/` found no `shutil.copy` or `copyfile`.
- Static scan found no embedded chunk of the current `Test.txt` content.
- Metrics and plots are generated from the actual pipeline run rather than hardcoded fixed outputs.
- `results/received.txt` is written after receiver decoding, not by direct file copy.
