# Mock Test Report

## 1. Phase 2 Scope

This report records the Phase 2 mock/unit test RED stage. The goal was to create tests first, run them, and confirm that they fail because production implementation does not exist yet.

This phase intentionally did not create or modify:

- `main.py`
- `src/`
- `results/`
- `public_tests/`
- `Test.txt`
- `requirements.txt`

## 2. Test Command and Overall Result

Command run:

```bash
python -m pytest tests -q
```

Observed result:

```text
17 failed in 0.28s
```

Pytest collection succeeded after one test-annotation compatibility fix. The final failures are valid TDD RED evidence. They are caused by missing implementation modules such as `src/` and missing CLI entry point `main.py`.

Representative failure messages:

```text
src.source.source_encode not implemented yet
src.scramble.scramble not implemented yet
src.channel_coding.channel_encode not implemented yet
src.framing.build_frame not implemented yet
src.modulation.qpsk_modulate not implemented yet
src.channel.awgn not implemented yet
src.synchronization.synchronize not implemented yet
main.py not implemented yet
```

No production code was written to fix these failures.

## 3. Mock Scenario Records

### 3.1 UTF-8 / Bitstream Reversibility Mock

- Test target: `tests/test_source.py`
- Expected interface: `source_encode(text)` / `source_decode(bits)`, compatible aliases `text_to_bits(text)` / `bits_to_text(bits)`.
- Expected result after implementation: Chinese UTF-8 text encodes to byte-aligned bits and decodes back to the exact original string.
- Current actual result: RED failure.
- Failure reason: `src.source.source_encode not implemented yet`; `src/` does not exist.
- DESIGN.md revision needed: No. The current design already states UTF-8 bytes and bitstream round-trip.
- Next implementation suggestion: Create `src/source.py` only in a later implementation phase and make the bit order deterministic and byte aligned.

### 3.2 PN Scramble / Descramble Round-Trip Mock

- Test target: `tests/test_scramble.py`
- Expected interface: `scramble(bits, seed)` / `descramble(bits, seed)`.
- Expected result after implementation: fixed seed produces reproducible scrambling, and descrambling recovers the original bit list.
- Current actual result: RED failure.
- Failure reason: `src.scramble.scramble not implemented yet`; `src/` does not exist.
- DESIGN.md revision needed: No. The design already chooses seed-controlled PN XOR.
- Next implementation suggestion: Use the same seeded PN generator for scramble and descramble so XOR reversibility is obvious and explainable.

### 3.3 Channel Coding Round-Trip Mock

- Test target: `tests/test_channel_coding.py`
- Expected interface: `channel_encode(bits)` / `channel_decode(encoded_bits)`.
- Expected result after implementation: noiseless channel encode/decode recovers original bits.
- Current actual result: RED failure.
- Failure reason: `src.channel_coding.channel_encode not implemented yet`; `src/` does not exist.
- DESIGN.md revision needed: No. The current repetition-code design is sufficient for this test.
- Next implementation suggestion: Start with the documented repetition code and make decode trim or preserve payload length using frame metadata in later pipeline code.

### 3.4 Frame Structure and QPSK Padding Mock

- Test target: `tests/test_framing.py` and `tests/test_pipeline.py`
- Expected interface: `build_frame(...)`, `parse_frame(frame_bits)`, `qpsk_modulate(bits)`, `qpsk_demodulate(symbols)`.
- Expected result after implementation: frame exposes preamble, raw payload length, coded payload length, checksum/CRC, and payload; odd bit payloads survive QPSK padding and are trimmed by `raw_payload_length`.
- Current actual result: RED failure.
- Failure reason: `src.framing.build_frame not implemented yet`; `src.modulation.qpsk_modulate not implemented yet`; `src/` does not exist.
- DESIGN.md revision needed: No. The design already defines `preamble + raw_payload_length + coded_payload_length + checksum/CRC + coded_payload`.
- Next implementation suggestion: Make `build_frame` accept compatible keyword names where practical: `raw_payload_length`, `payload_length`, `checksum`, and `checksum_bits`.

### 3.5 QPSK Gray Mapping Mock

- Test target: `tests/test_modulation.py`
- Expected interface: `qpsk_modulate(bits)` / `qpsk_demodulate(symbols)`.
- Expected result after implementation:
  - `00 -> (1+j)/sqrt(2)`
  - `01 -> (-1+j)/sqrt(2)`
  - `11 -> (-1-j)/sqrt(2)`
  - `10 -> (1-j)/sqrt(2)`
  - average ideal symbol power is approximately 1
  - noiseless demodulation restores the original bits
- Current actual result: RED failure.
- Failure reason: `src.modulation.qpsk_modulate not implemented yet`; `src/` does not exist.
- DESIGN.md revision needed: No. Mapping and normalization are already explicit.
- Next implementation suggestion: Implement the mapping table directly and keep padding behavior documented through length fields.

### 3.6 AWGN Seed Reproducibility Mock

- Test target: `tests/test_channel.py`
- Expected interface: `awgn(symbols, snr_db, seed)`.
- Expected result after implementation: same symbols, SNR, and seed produce identical noisy outputs within floating-point tolerance.
- Current actual result: RED failure.
- Failure reason: `src.channel.awgn not implemented yet`; `src/` does not exist.
- DESIGN.md revision needed: No. The design already defines SNR as average symbol power over average complex Gaussian noise power.
- Next implementation suggestion: Use a local RNG seeded by the function argument and avoid global random state.

### 3.7 Synchronization Offset Mock

- Test target: `tests/test_synchronization.py`
- Expected interface: `synchronize(received_symbols, preamble=None)`.
- Expected result after implementation: for offsets 0, 1, 25, 64, and 128, default return value is `int start_index` within one QPSK symbol of the true offset.
- Current actual result: RED failures for all five offsets.
- Failure reason: `src.synchronization.synchronize not implemented yet`; `src/` does not exist.
- DESIGN.md revision needed: No. The design already corrected the default API to return an integer and reserves detailed correlation output for `correlate_preamble(...)` or optional detailed mode.
- Next implementation suggestion: Implement preamble correlation and return only the integer index by default.

### 3.8 CLI, Metrics, Plots, and Anti-Copy Mock

- Test target: `tests/test_cli.py`
- Expected interface: `main.py` supporting:

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

- Expected result after implementation:
  - CLI exits with code 0.
  - `results/metrics.json` includes `snr_db`, `seed`, `modulation`, `channel`, `payload_bits`, `ber`, `fer`, `text_match_rate`, `checksum_pass`, `sync_start_index`.
  - At least two of `constellation.png`, `ber_curve.png`, and `sync_peak.png` are generated.
  - Source scan does not find direct-copy or hardcoding shortcuts.
- Current actual result: RED failures.
- Failure reason: `main.py not implemented yet`; `src/` also does not exist for anti-copy scan.
- DESIGN.md revision needed: No.
- Next implementation suggestion: Implement CLI only after Phase 3 approval, and ensure `received.txt` is produced by receiver decoding rather than file copying.

## 4. Anti-Hardcoding and Hidden-Test Notes

Future validation must include:

- Different Chinese UTF-8 texts.
- Different seeds.
- Different SNR values.
- Random synchronization offsets.
- Static scan for direct copy patterns such as `shutil.copy`, `copyfile`, or direct `Test.txt` to `received.txt` writes.
- Behavioral check that modifying input text changes the decoded output through the communication chain.

The current RED tests intentionally do not hardcode a public expected output. They define interface and behavior contracts for later implementation.

## 5. Design Revision Decision

No Phase 2 design revision is required at this point. The RED failures confirm that implementation is missing, not that the Phase 1 design is inconsistent.

The only adjustment made during this phase was in the test code itself: a Python type-annotation compatibility issue in `tests/test_framing.py` was fixed so pytest collection could proceed. This did not alter the communication design.

## 6. Next Step Recommendation

Phase 3 should review this RED evidence and confirm whether to revise `DESIGN.md` or `TEST_PLAN.md`. If no revisions are needed, the next implementation phase should begin with the same tests and follow TDD GREEN one module at a time.

## 7. Phase 3 Review Conclusion

Phase 3 reviewed:

- `DESIGN.md`
- `TEST_PLAN.md`
- `MOCK_TEST_REPORT.md`
- `AI_LOG.md`
- all files under `tests/`

Conclusion:

- The 17 RED failures are expected and valid TDD evidence.
- The root cause is missing implementation: `src/` and `main.py` have not been created yet.
- No business logic failure was observed because no business implementation exists.
- No core interface conflict was found between the Phase 2 tests and the design.
- `synchronize(...)` is consistent across design and tests: it must return `int start_index` by default.
- QPSK Gray mapping, AWGN SNR definition, `raw_payload_length` meaning, and required `metrics.json` fields remain unchanged.

Design revision decision:

- `DESIGN.md`: only a small clarification is needed for `build_frame` compatibility aliases and dict-like `parse_frame` metadata.
- `TEST_PLAN.md`: only a matching clarification is needed for frame tests.
- Test files: no revision needed.

Compatibility clarification: build_frame may accept compatibility aliases, but `raw_payload_length` remains the authoritative length field for source-encoded payload bits before scrambling.

Phase 4 recommendation:

- The project can enter Phase 4 only after explicit user confirmation.
- Phase 4 should implement modules one at a time using TDD GREEN, starting from the existing RED tests.
- Phase 4 must not bypass the communication chain or directly copy `Test.txt` to `results/received.txt`.

## 8. Phase 4B GREEN Verification Addendum

Phase 4B reviewed the remaining RED failures after Phase 4A:

- `main.py not implemented yet`
- `results/metrics.json` not generated because CLI was missing
- required plot files not generated because CLI/pipeline was missing

Implementation conclusion:

- The RED failures were resolved by adding the CLI, pipeline orchestration, metrics, and plotting modules.
- No mock tests were weakened, skipped, or rewritten.
- No `public_tests/`, `Test.txt`, or `requirements.txt` files were modified.
- The pipeline still follows the designed communication chain rather than directly copying the input text.

Verification commands:

```bash
python -m pytest tests/test_cli.py -q
```

Result:

```text
4 passed
```

```bash
python -m pytest tests -q
```

Result:

```text
17 passed
```

Fixed CLI command:

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

Result:

```text
Wireless pipeline complete: text_match_rate=1.000, checksum_pass=True
```

Output checks:

- `results/received.txt` matched `Test.txt` exactly for the fixed CLI run.
- `results/metrics.json` contained all required fields.
- `results/constellation.png`, `results/ber_curve.png`, and `results/sync_peak.png` were generated and non-empty.

Public tests:

- `python -m pytest public_tests -q` was run in a temporary sandbox copy to avoid the public-test fixture leaving a modification in repository `Test.txt`.
- Result: `22 passed`.

Design revision decision:

- No `DESIGN.md` or `TEST_PLAN.md` revision was needed in Phase 4B.
- The implemented `synchronize(...)` default return type, `raw_payload_length` semantics, QPSK Gray mapping, AWGN SNR definition, and metrics fields remain aligned with the Phase 1/3 design.

Next recommendation:

- Phase 5 can focus on final result solidification, report completion, and any remaining packaging or commit/push steps after user confirmation.
