# Mock Test Report

## Final Status Summary

This report preserves the RED/GREEN TDD process required by the project workflow. The early RED failures were intentional because tests were written before implementation. The final implementation has resolved those failures: the AWGN/QPSK baseline passes the fixed CLI verification, public tests pass, Level 3 Rayleigh mode uses preamble-based channel estimation and one-tap equalization, the optional GUI compiles/imports without affecting CLI grading, and the end-to-end system BER curve is generated from full-pipeline runs.

Final verification:

- `python -m pytest public_tests -q`: `22 passed`.
- `python -m pytest tests -q`: `34 passed` after the classroom-review hardening regressions were added. Earlier `27 passed`, `25 passed`, and `17 passed` entries below are historical stage records.
- Fixed AWGN CLI run: `text_match_rate=1.0`, `checksum_pass=true`, `ber=0.0`.

## 1. Phase 2 Scope

This historical section records the Phase 2 mock/unit test RED stage. The goal was to create tests first, run them, and confirm that they failed because production implementation did not exist yet.

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

Historical RED result:

```text
17 failed in 0.28s
```

Pytest collection succeeded after one test-annotation compatibility fix. These failures were valid TDD RED evidence at that time. They were caused by missing implementation modules such as `src/` and missing CLI entry point `main.py`, and they are not the current final project status.

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

No production code was written in Phase 2 to fix these failures; implementation was completed in later GREEN phases.

## 3. Mock Scenario Records

### 3.1 UTF-8 / Bitstream Reversibility Mock

- Test target: `tests/test_source.py`
- Expected interface: `source_encode(text)` / `source_decode(bits)`, compatible aliases `text_to_bits(text)` / `bits_to_text(bits)`.
- Expected result after implementation: Chinese UTF-8 text encodes to byte-aligned bits and decodes back to the exact original string.
- Historical RED result: expected failure before implementation.
- Failure reason: `src.source.source_encode not implemented yet`; `src/` does not exist.
- DESIGN.md revision needed: No. The current design already states UTF-8 bytes and bitstream round-trip.
- Historical next implementation suggestion: Create `src/source.py` only in a later implementation phase and make the bit order deterministic and byte aligned.

### 3.2 PN Scramble / Descramble Round-Trip Mock

- Test target: `tests/test_scramble.py`
- Expected interface: `scramble(bits, seed)` / `descramble(bits, seed)`.
- Expected result after implementation: fixed seed produces reproducible scrambling, and descrambling recovers the original bit list.
- Historical RED result: expected failure before implementation.
- Failure reason: `src.scramble.scramble not implemented yet`; `src/` does not exist.
- DESIGN.md revision needed: No. The design already chooses seed-controlled PN XOR.
- Historical next implementation suggestion: Use the same seeded PN generator for scramble and descramble so XOR reversibility is obvious and explainable.

### 3.3 Channel Coding Round-Trip Mock

- Test target: `tests/test_channel_coding.py`
- Expected interface: `channel_encode(bits)` / `channel_decode(encoded_bits)`.
- Expected result after implementation: noiseless channel encode/decode recovers original bits.
- Historical RED result: expected failure before implementation.
- Failure reason: `src.channel_coding.channel_encode not implemented yet`; `src/` does not exist.
- DESIGN.md revision needed: No. The current repetition-code design is sufficient for this test.
- Historical next implementation suggestion: Start with the documented repetition code and make decode trim or preserve payload length using frame metadata in later pipeline code.

### 3.4 Frame Structure and QPSK Padding Mock

- Test target: `tests/test_framing.py` and `tests/test_pipeline.py`
- Expected interface: `build_frame(...)`, `parse_frame(frame_bits)`, `qpsk_modulate(bits)`, `qpsk_demodulate(symbols)`.
- Expected result after implementation: frame exposes preamble, raw payload length, coded payload length, checksum/CRC, and payload; odd bit payloads survive QPSK padding and are trimmed by `raw_payload_length`.
- Historical RED result: expected failure before implementation.
- Failure reason: `src.framing.build_frame not implemented yet`; `src.modulation.qpsk_modulate not implemented yet`; `src/` does not exist.
- DESIGN.md revision needed: No. The design already defines `preamble + raw_payload_length + coded_payload_length + checksum/CRC + coded_payload`.
- Historical next implementation suggestion: Make `build_frame` accept compatible keyword names where practical: `raw_payload_length`, `payload_length`, `checksum`, and `checksum_bits`.

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
- Historical RED result: expected failure before implementation.
- Failure reason: `src.modulation.qpsk_modulate not implemented yet`; `src/` does not exist.
- DESIGN.md revision needed: No. Mapping and normalization are already explicit.
- Historical next implementation suggestion: Implement the mapping table directly and keep padding behavior documented through length fields.

### 3.6 AWGN Seed Reproducibility Mock

- Test target: `tests/test_channel.py`
- Expected interface: `awgn(symbols, snr_db, seed)`.
- Expected result after implementation: same symbols, SNR, and seed produce identical noisy outputs within floating-point tolerance.
- Historical RED result: expected failure before implementation.
- Failure reason: `src.channel.awgn not implemented yet`; `src/` does not exist.
- DESIGN.md revision needed: No. The design already defines SNR as average symbol power over average complex Gaussian noise power.
- Historical next implementation suggestion: Use a local RNG seeded by the function argument and avoid global random state.

### 3.7 Synchronization Offset Mock

- Test target: `tests/test_synchronization.py`
- Expected interface: `synchronize(received_symbols, preamble=None)`.
- Expected result after implementation: for offsets 0, 1, 25, 64, and 128, default return value is `int start_index` within one QPSK symbol of the true offset.
- Historical RED result: expected failures for all five offsets before implementation.
- Failure reason: `src.synchronization.synchronize not implemented yet`; `src/` does not exist.
- DESIGN.md revision needed: No. The design already corrected the default API to return an integer and reserves detailed correlation output for `correlate_preamble(...)` or optional detailed mode.
- Historical next implementation suggestion: Implement preamble correlation and return only the integer index by default.

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
- Historical RED result: expected failures before implementation.
- Failure reason: `main.py not implemented yet`; `src/` also does not exist for anti-copy scan.
- DESIGN.md revision needed: No.
- Historical next implementation suggestion: Implement CLI only after Phase 3 approval, and ensure `received.txt` is produced by receiver decoding rather than file copying.

## 4. Anti-Hardcoding and Hidden-Test Notes

Hidden-test risk validation considers:

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

## 6. Historical Next Step Recommendation

At that historical stage, Phase 3 was expected to review this RED evidence and confirm whether to revise `DESIGN.md` or `TEST_PLAN.md`. If no revisions were needed, the next implementation phase was expected to begin with the same tests and follow TDD GREEN one module at a time.

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

- At that historical stage, the project was allowed to enter Phase 4 only after explicit user confirmation. The final implementation has since been completed and verified.
- At that historical stage, Phase 4 was expected to implement modules one at a time using TDD GREEN, starting from the existing RED tests.
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

Historical next recommendation:

- Phase 5 can focus on final result solidification, report completion, and any remaining packaging or commit/push steps after user confirmation.

## 9. Level 3 Final Hardening Review

New issue found:

- Hidden-test style run with `seed=126`, `snr=12`, and AWGN exposed a synchronization ambiguity.
- Observed pattern: true offset was `39`, coarse correlation could select a nearby but wrong frame start, and the previous candidate range was too narrow.
- Impact: checksum failed and text recovery could become `text_match_rate=0.0`.

Root cause:

- Preamble correlation is a good coarse synchronizer, but the short repeated preamble can have nearby ambiguous peaks under noise.
- The receiver only checked candidates around `detected_start` with offsets `0, +/-1, +/-2, +/-3`, so a true frame start four or more symbols away was not examined.

Correction:

- The receiver now treats preamble correlation as coarse sync and searches `detected_start +/- 32` QPSK symbols.
- Each candidate is demodulated, parsed, channel-decoded, descrambled, UTF-8 decoded, and CRC/checksum checked.
- The selected frame start prioritizes `checksum_pass=true`, then stronger preamble score, smaller distance from the coarse peak, valid length, and valid UTF-8.
- If no candidate passes checksum, the receiver writes the best failure output and records `failure_reason` instead of crashing.

Before/after evidence:

- Before: `seed=126` could produce checksum failure and zero text match when the correct start was outside the candidate window.
- After: the regression test recovers exactly with `sync_start_index=39`, `sync_true_offset=39`, `checksum_pass=true`, and `ber=0.0`.

Rayleigh revision:

- Previous Level 3 Rayleigh equalization used the true simulated fading coefficient directly in the receiver path.
- The receiver now estimates the flat channel from the known preamble:
  `h_hat = vdot(preamble_symbols, rx_preamble) / vdot(preamble_symbols, preamble_symbols)`.
- Equalization uses `received / h_hat`; the true `h` is retained only for diagnostic `channel_estimation_error`.

GUI verification:

- `gui.py` remains optional and calls `src.pipeline.run_pipeline(...)`.
- `python -m py_compile gui.py` passes.
- Importing `gui.py` does not create a Tk root, so pytest and CLI grading do not depend on a graphical environment.

## 10. End-to-End System BER Curve Addendum

New requirement:

- Preserve or enhance the existing `results/ber_curve.png` reference curve.
- Add `results/system_ber_curve.png` for the complete repetition-coded system BER-SNR curve.

Design decision:

- `ber_curve.png` now overlays two curves: uncoded QPSK reference and end-to-end repetition-coded system BER.
- `system_ber_curve.png` shows only the end-to-end coded system curve.
- The system curve uses full pipeline runs over SNR values `[0, 2, 4, 6, 8, 10, 12, 14]` and seeds `[2026, 2027, 2028]`.
- Temporary sweep outputs are used so formal `results/received.txt` and final `results/metrics.json` are not overwritten.

Tests added:

- `system_ber_curve.png` generation with complete pipeline-derived BER values.
- System BER sweep preserves existing formal output and metrics files.
- `system_ber_values` length matches `system_ber_snr_values`.
- All system BER values are in `[0, 1]`.
- A zero-BER curve can be plotted on a log-scale axis without crashing.
- CLI metrics retain PRD-required fields and include system BER metadata.

Expected behavior:

- BER generally improves as SNR increases, though finite seeds and sync failures can create small non-monotonic points.
- At BER=0, plotting uses a display floor only; the raw metrics still keep true `0.0` values.

## 11. Classroom Review Hardening Addendum

The teacher's classroom review emphasized that hidden tests check whether the system remains reusable under changed text, SNR, seed, synchronization offset, file path, and invalid input conditions. The repository was therefore extended with a final hardening test group.

New or reinforced scenarios:

- Invalid SNR: `nan`, `inf`, and `-inf` must be rejected at the CLI instead of entering the channel model.
- Invalid modulation: unsupported modes such as `bpsk` must be rejected by the CLI with a clear `argparse` error instead of silently running an undefined modulation path.
- UTF-8 generality: mixed Chinese, English, punctuation, numbers, and emoji text must recover exactly.
- Empty and long text: source coding, length fields, padding removal, and UTF-8 decoding must still be consistent.
- Custom output path: metrics and generated plots must be written beside the requested output file.
- Evidence chain: `metrics.json` and plots must support the explanation of what was transmitted, how many errors occurred, and why errors may occur.
- HTML dashboard: optional browser GUI must show input/output text comparison, metric cards, and generated plots without affecting `main.py`.
- Local hidden-test simulation: a temporary non-submitted harness ran 77 cases over mixed text, empty text, long text, AWGN SNR `6/8/12/15`, Rayleigh SNR `18`, multiple seeds including `126` and `2026`, missing input, invalid SNR, invalid modulation, low-SNR non-crash behavior, and custom output directories. The simulation reported zero failures.

TDD result:

- RED: `test_cli_rejects_non_finite_snr_values` initially failed because `--snr nan` entered the full pipeline and returned a receiver failure instead of a clear CLI error.
- GREEN: CLI SNR parsing now rejects non-finite values with an explicit finite-number error, while finite low-SNR values remain valid stress tests.
- Regression coverage: `tests/test_teacher_review_hardening.py` and `tests/test_web_gui.py` cover the classroom-review risks and HTML dashboard behavior.
