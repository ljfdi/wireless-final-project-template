# AI Assistance Log

## Current Stage

Final Level 3 submission hardening and verification completed.

The project now includes the implemented CLI pipeline, source modules, tests, results artifacts, Level 3 Rayleigh extension, preamble-based one-tap equalization, optional Tkinter GUI, and both QPSK reference and end-to-end system BER visualizations. Earlier Phase 1/2/3 entries are retained below as the chronological AI-assisted development record.

Current final verification:

- `python -m pytest public_tests -q`: `22 passed`.
- `python -m pytest tests -q`: `27 passed` after the system BER curve regression tests were added.
- Fixed AWGN CLI run: `text_match_rate=1.0`, `checksum_pass=true`, `ber=0.0`.

Historical initial stage record: Phase 1 design-document stage.

This stage creates or updates only:

- `DESIGN.md`
- `TEST_PLAN.md`
- `AI_LOG.md`
- `无线通信技术期末项目报告模板.docx`, copied into the repository root because the template existed outside the cloned repository

This stage does not create or modify `main.py`, `src/`, `tests/`, `results/`, `public_tests/`, `Test.txt`, or `requirements.txt`.

## Prompt and Interaction Record

### Prompt 1: repository setup and planning request

User prompt summary:

- Act as an AI programming assistant for the wireless communication final project.
- Use Superpowers and OpenSpec ideas.
- Clone the user's fork repository.
- Read `README.md`, `PRD.docx`, public tests, and the report template.
- Do not write final code.
- Produce a complete plan for the project.

AI actions:

- Cloned `https://github.com/ljfdi/wireless-final-project-template.git`.
- Checked repository structure.
- Confirmed repository contains `PRD.docx`, `README.md`, `Test.txt`, `requirements.txt`, `public_tests/`, `.github/`.
- Confirmed repository initially lacked `DESIGN.md`, `TEST_PLAN.md`, `MOCK_TEST_REPORT.md`, `AI_LOG.md`, `main.py`, `src/`, `tests/`, and `results/`.
- Read public tests and summarized their required behavior.
- Read `PRD.docx` and the report template outside the repository.
- Generated the initial full-project plan.

### Prompt 2: Phase 1 plan correction

User prompt summary:

- Correct the synchronization API so `synchronize(received_symbols, preamble=None)` returns an `int` by default.
- Move correlation details to `correlate_preamble(...)` or optional `return_details=True`.
- Clarify the exact frame and coding order.
- Use OpenSpec-equivalent workflow because OpenSpec skill exists but `openspec` CLI is unavailable.
- Start real-time `AI_LOG.md` recording.
- In Phase 1, only create or update `DESIGN.md`, `TEST_PLAN.md`, and `AI_LOG.md`.

AI actions:

- Accepted the corrected synchronization API rule.
- Updated the Phase 1 design plan to make `raw_payload_length` mean source-encoded bits before scrambling.
- Updated the frame design to:
  `preamble + raw_payload_length + coded_payload_length + checksum/CRC + coded_payload`.
- Clarified receiver order:
  synchronization -> demodulation -> parse frame -> channel decode -> descramble -> trim by `raw_payload_length` -> UTF-8 decode.
- Confirmed not to install or repair OpenSpec CLI.

### Prompt 3: implement Phase 1 design documents

User prompt summary:

- Implement the Phase 1 Design Documents Plan.
- Create or update only `DESIGN.md`, `TEST_PLAN.md`, `AI_LOG.md`.
- Copy the report template into the repository root if missing.
- Do not create or modify business code or test/result directories.

AI actions:

- Re-read the relevant Superpowers execution and verification instructions.
- Checked git status and confirmed the branch was clean before document edits.
- Confirmed the three Markdown documents and report template were missing from the repository root.
- Copied `无线通信技术期末项目报告模板.docx` from the parent workspace into the repository root.
- Created `DESIGN.md`.
- Created `TEST_PLAN.md`.
- Created this `AI_LOG.md`.

## Files Read or Checked

- `README.md`
- `PRD.docx`
- `Test.txt`
- `requirements.txt`
- `public_tests/README.md`
- `public_tests/conftest.py`
- `public_tests/test_01_structure_and_documents.py`
- `public_tests/test_02_core_modules.py`
- `public_tests/test_03_cli_end_to_end.py`
- `wireless_project_test_set_20.feature`
- `grading/summarize_public_tests.py`
- `.github/workflows/grading.yml`
- `.github/pull_request_template.md`
- Parent workspace report template: `无线通信技术期末项目报告模板.docx`
- Superpowers skill notes for planning, execution, TDD, debugging, and verification
- OpenSpec skill notes for explore/propose behavior

## Skill and Tool Status

- Superpowers skills are available and were used as workflow constraints.
- `superpowers:executing-plans` guided this Phase 1 plan execution.
- `superpowers:verification-before-completion` requires fresh verification before reporting completion.
- `superpowers:test-driven-development` will apply in Phase 2 and later: tests must be written and observed failing before production code is implemented.
- OpenSpec skills exist in the workspace.
- The `openspec` CLI is not available in PATH.
- Per user instruction, OpenSpec CLI was not installed, repaired, or worked around by adding new tooling.
- The project uses an OpenSpec-equivalent process:
  proposal/design/specs/tasks are mapped to teacher-required files, especially `DESIGN.md`, `TEST_PLAN.md`, later `MOCK_TEST_REPORT.md`, and this `AI_LOG.md`.

## Human Modifications and AI Changes

The user manually revised the initial plan before Phase 1 execution. Important user-provided changes adopted by the AI:

- Default `synchronize(...)` must return an `int`, not a dict or tuple.
- Detailed synchronization data must use `correlate_preamble(...)` or an optional detailed mode.
- Frame construction must happen after scrambling and channel encoding.
- `raw_payload_length` must represent source-encoded bits before scrambling.
- CRC/checksum must cover original payload bytes or original payload bits.
- Phase 1 must not write business code, mock tests, unit tests, or result artifacts.

These changes were adopted because they reduce public-test API risk, match the PRD length-field definition, and keep the project workflow explainable.

## Key Design Choices and Reasons

### Synchronization API

Choice:

- `synchronize(received_symbols, preamble=None)` returns `int start_index` by default.
- `correlate_preamble(...)` provides correlation data for `sync_peak.png`.

Reason:

- Public tests may call `synchronize(...)` and expect a simple numeric start index.
- Separating details avoids API ambiguity.

### Frame and Coding Order

Choice:

- Source encode -> PN XOR scramble -> channel encode -> frame build.
- Frame fields:
  `preamble + raw_payload_length + coded_payload_length + checksum/CRC + coded_payload`.

Reason:

- This preserves the PRD definition of `length` as the original payload bit count.
- It gives the receiver enough metadata to parse the coded payload and later remove QPSK/channel padding safely.

### PN XOR Scrambling

Choice:

- Use seed-controlled PN XOR scrambling.

Reason:

- It is reversible, deterministic, easy to test, and easy to explain in the report.

### Channel Coding

Choice:

- Default to a simple repetition code or equivalent course-related simple code.

Reason:

- It is stable, explainable, and appropriate for reliable SNR 12 dB recovery.

### QPSK

Choice:

- Use PRD Gray mapping:
  `00 -> (1+j)/sqrt(2)`,
  `01 -> (-1+j)/sqrt(2)`,
  `11 -> (-1-j)/sqrt(2)`,
  `10 -> (1-j)/sqrt(2)`.

Reason:

- This exactly matches PRD and public-test expectations.

### AWGN

Choice:

- Define SNR as average modulated-symbol power divided by average complex Gaussian noise power.

Reason:

- This exactly matches the PRD baseline definition and avoids Eb/N0 conversion ambiguity.

### Low SNR Behavior

Choice:

- Low SNR may fail text recovery but must not crash.
- Metrics must still be written.

Reason:

- Hidden tests may evaluate robustness, not only perfect recovery.

## Why No Code Was Written in Phase 1

No Python business code was written because:

- The user explicitly limited Phase 1 to design documents.
- The project PRD requires design and test planning before implementation.
- Superpowers TDD requires failing tests before production code.
- Phase 2 is responsible for mock tests and TDD RED.
- Creating `main.py`, `src/`, `tests/`, or `results/` in this stage would violate the user's boundary.

## Next Stage: Phase 2 Plan

Phase 2 should begin only after user confirmation.

Planned Phase 2 work:

- Create mock tests for source coding, scrambling, framing, QPSK padding, AWGN, synchronization, and end-to-end flow.
- Start TDD RED by writing tests that fail because implementation modules do not exist yet.
- Do not move into production implementation unless the user explicitly approves the next phase.
- Record all new prompts, test failures, root causes, and design revisions in this `AI_LOG.md`.

## Phase 2: Mock Tests and TDD RED

### Prompt 4: implement Phase 2 RED mock tests

User prompt summary:

- Enter Phase 2, but only execute mock/unit tests and TDD RED.
- Create tests under `tests/` using dynamic imports so pytest collection does not fail when `src/` is missing.
- Do not create or modify `main.py`, `src/`, `results/`, `public_tests/`, `Test.txt`, or `requirements.txt`.
- Run `python -m pytest tests -q`.
- Record the failing RED results in `MOCK_TEST_REPORT.md` and append this log.

AI actions:

- Created `tests/conftest.py` with dynamic function discovery and helper functions.
- Created tests:
  - `tests/test_source.py`
  - `tests/test_scramble.py`
  - `tests/test_channel_coding.py`
  - `tests/test_framing.py`
  - `tests/test_modulation.py`
  - `tests/test_channel.py`
  - `tests/test_synchronization.py`
  - `tests/test_pipeline.py`
  - `tests/test_cli.py`
- Ran `python -m pytest tests -q`.
- Initial run reported `ERROR: file or directory not found: tests` because the patch tool created `tests/` in the parent workspace. The tests were moved into the repository root.
- Second run had a collection error from `set[str]` in `tests/test_framing.py` on the local Python runtime. The annotation was removed. No production code was written.
- Final run collected tests successfully and produced expected RED failures.

### Phase 2 test command

```bash
python -m pytest tests -q
```

### Phase 2 RED result

```text
17 failed in 0.28s
```

Failed areas:

- `src.source.source_encode not implemented yet`
- `src.scramble.scramble not implemented yet`
- `src.channel_coding.channel_encode not implemented yet`
- `src.framing.build_frame not implemented yet`
- `src.modulation.qpsk_modulate not implemented yet`
- `src.channel.awgn not implemented yet`
- `src.synchronization.synchronize not implemented yet`
- `main.py not implemented yet`
- `src/ and main.py not implemented yet; anti-copy scan will run after implementation exists`

These failures match the TDD RED expectation: tests are now present, but production implementation has not been created yet.

### Phase 2 design revision decision

No `DESIGN.md` or `TEST_PLAN.md` revision was needed. The failures show missing implementation, not a design/interface contradiction.

### Phase 2 boundary confirmation

No business implementation code was written. The project still does not have `main.py`, `src/`, or `results/`.

### Next-stage recommendation

Phase 3 should review the mock results and decide whether the design needs revision. If no revision is needed, the later implementation phase should start TDD GREEN one module at a time.

## Phase 3: Mock Review and Design Revision Decision

### Prompt 5: implement Phase 3 review

User prompt summary:

- Enter Phase 3 only.
- Review `DESIGN.md`, `TEST_PLAN.md`, `MOCK_TEST_REPORT.md`, `AI_LOG.md`, and all tests under `tests/`.
- Decide whether Phase 2 RED failures reveal a design problem.
- Only revise `DESIGN.md` or `TEST_PLAN.md` if test interfaces conflict with the design.
- Do not create or modify `main.py`, `src/`, `results/`, `public_tests/`, `Test.txt`, or `requirements.txt`.
- Stop after Phase 3 and wait for confirmation before Phase 4.

Files reviewed:

- `DESIGN.md`
- `TEST_PLAN.md`
- `MOCK_TEST_REPORT.md`
- `AI_LOG.md`
- `tests/conftest.py`
- `tests/test_source.py`
- `tests/test_scramble.py`
- `tests/test_channel_coding.py`
- `tests/test_framing.py`
- `tests/test_modulation.py`
- `tests/test_channel.py`
- `tests/test_synchronization.py`
- `tests/test_pipeline.py`
- `tests/test_cli.py`

Review conclusion:

- The Phase 2 RED failures match TDD expectations.
- The failures are caused by missing `src/` and `main.py`.
- No production implementation exists yet, so no business logic defect was diagnosed.
- No core design conflict was found.
- `synchronize(...)` default return type, QPSK Gray mapping, AWGN SNR definition, `raw_payload_length`, and metrics fields remain unchanged.

Documentation changes made:

- `DESIGN.md` was clarified to state that `build_frame` may accept compatibility aliases `payload_length` and `checksum_bits`, while the primary semantics remain `raw_payload_length` and `checksum`.
- `DESIGN.md` was clarified to recommend dict-like `parse_frame` metadata.
- `TEST_PLAN.md` was clarified with the same frame compatibility expectations.
- `MOCK_TEST_REPORT.md` was updated with this Phase 3 review conclusion.

Boundary confirmation:

- No business implementation code was written.
- `main.py`, `src/`, and `results/` were not created.
- `public_tests/`, `Test.txt`, and `requirements.txt` were not modified.

Next-stage recommendation:

- Phase 4 is recommended only after explicit user confirmation.
- Phase 4 should use the existing RED tests and implement TDD GREEN one module at a time.

## Phase 4A: Base Module TDD GREEN

### Prompt 6: implement Phase 4A base modules only

User prompt summary:

- Enter Phase 4A.
- Implement only base communication modules under `src/`.
- Do not create `main.py`, `results/`, `src/pipeline.py`, `src/metrics.py`, or plotting modules.
- Do not modify `public_tests/`, `Test.txt`, or `requirements.txt`.
- Follow strict TDD GREEN order: source, scramble, channel coding, modulation, AWGN channel, synchronization, framing.
- Run each module's targeted test immediately after implementation.
- Run the basic module regression command.
- Optionally run all tests, but do not fix `main.py` / CLI failures in this phase.

Files created:

- `src/__init__.py`
- `src/source.py`
- `src/scramble.py`
- `src/channel_coding.py`
- `src/modulation.py`
- `src/channel.py`
- `src/synchronization.py`
- `src/framing.py`

Targeted test commands and results:

```bash
python -m pytest tests/test_source.py -q
```

- Initial result: failed because local Python evaluated `list[int]` annotations during module import.
- Fix: added `from __future__ import annotations` to `src/source.py`.
- Final result: `1 passed`.

```bash
python -m pytest tests/test_scramble.py -q
```

- Result: `1 passed`.

```bash
python -m pytest tests/test_channel_coding.py -q
```

- Result: `1 passed`.

```bash
python -m pytest tests/test_modulation.py -q
```

- Result: `2 passed`.

```bash
python -m pytest tests/test_channel.py -q
```

- Result: `1 passed`.

```bash
python -m pytest tests/test_synchronization.py -q
```

- Result: `5 passed`.

```bash
python -m pytest tests/test_framing.py -q
```

- Result: `1 passed`.

Required Phase 4A regression:

```bash
python -m pytest tests/test_source.py tests/test_scramble.py tests/test_channel_coding.py tests/test_modulation.py tests/test_channel.py tests/test_synchronization.py tests/test_framing.py -q
```

- Result: `12 passed`.

Optional full test check:

```bash
python -m pytest tests -q
```

- Result: `14 passed, 3 failed`.
- Remaining failures:
  - `test_required_cli_contract_exists_and_runs`: `main.py not implemented yet`.
  - `test_metrics_json_contains_required_fields_after_cli`: `main.py not implemented yet; cannot generate results/metrics.json`.
  - `test_required_plots_generate_after_cli`: `main.py not implemented yet; cannot generate required plots`.

These remaining failures are expected in Phase 4A because `main.py`, `results/`, metrics, plotting, and end-to-end CLI are explicitly out of scope.

Implementation notes:

- `source.py` implements UTF-8 MSB-first source encoding/decoding and aliases `text_to_bits` / `bits_to_text`.
- `scramble.py` implements seed-controlled PN XOR scrambling/descrambling without mutating input.
- `channel_coding.py` implements a 3-times repetition code with majority-vote decoding.
- `modulation.py` implements PRD Gray-coded QPSK and hard-decision demodulation.
- `channel.py` implements AWGN using local NumPy RNG and SNR as symbol power over complex noise power.
- `synchronization.py` implements preamble correlation; default `synchronize(...)` returns `int`.
- `framing.py` implements dict-like frame metadata with preamble, raw/coded lengths, checksum/CRC, payload, coded_payload, and serialized bits.

Boundary confirmation:

- `main.py` was not created.
- `results/` was not created.
- `public_tests/`, `Test.txt`, and `requirements.txt` were not modified.

Next-stage recommendation:

- Phase 4B should implement the CLI, pipeline orchestration, metrics, and plot generation after explicit user confirmation.

## Phase 4B: Pipeline, CLI, Metrics, and Plots

### Prompt 7: implement Phase 4B end-to-end flow

User prompt summary:

- Enter Phase 4B and implement the remaining pipeline, CLI, metrics, plots, and end-to-end behavior.
- Allowed files include `main.py`, `src/pipeline.py`, `src/metrics.py`, `src/plotting.py`, optional `src/plots.py`, `results/`, `AI_LOG.md`, and `MOCK_TEST_REPORT.md`.
- Do not modify `public_tests/`, `Test.txt`, `requirements.txt`, `PRD.docx`, or the report template.
- Do not directly copy `Test.txt` to `results/received.txt`.
- Run local tests, the fixed CLI, output checks, public tests, and `git status --short`.

Initial RED confirmation:

```bash
python -m pytest tests -q
```

Result before implementation:

```text
14 passed, 3 failed
```

Remaining failures:

- `test_required_cli_contract_exists_and_runs`: `main.py not implemented yet`.
- `test_metrics_json_contains_required_fields_after_cli`: `main.py not implemented yet; cannot generate results/metrics.json`.
- `test_required_plots_generate_after_cli`: `main.py not implemented yet; cannot generate required plots`.

Files created:

- `main.py`
- `src/pipeline.py`
- `src/metrics.py`
- `src/plotting.py`
- `src/plots.py`

Files modified:

- `AI_LOG.md`
- `MOCK_TEST_REPORT.md`

Pipeline design implemented:

- Read input text as UTF-8.
- Source encode to raw payload bits.
- PN XOR scramble using the CLI seed.
- Apply 3-times repetition channel coding.
- Build a frame with preamble, `raw_payload_length`, `coded_payload_length`, checksum/CRC, and coded payload.
- QPSK modulate using the PRD Gray mapping.
- Add a seed-controlled random QPSK prefix of 0 to 128 symbols.
- Pass through AWGN using the symbol-power / complex-noise-power SNR definition.
- Synchronize with preamble correlation.
- QPSK demodulate, parse frame, channel decode, descramble, trim by `raw_payload_length`, and source decode.
- Write recovered text to the requested output path.
- Generate metrics and plots.

`main.py` CLI design:

- Uses `argparse`.
- Supports the required command:

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

- Restricts current implementation to `qpsk` and `awgn`.
- Creates the output directory automatically.
- Runs non-interactively and does not call `input()`.
- Reports invalid arguments through argparse.

Metrics fields implemented:

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
- Extra diagnostics: `sync_true_offset`, `sync_error_symbols`, `failure_reason`, `frame_bits`, `coded_payload_bits`.

Plot generation:

- `src/plotting.py` uses matplotlib with the Agg backend.
- Generates:
  - `results/constellation.png`
  - `results/ber_curve.png`
  - `results/sync_peak.png`
- `src/plots.py` re-exports plotting helpers as a compatibility wrapper.

Verification commands and results:

```bash
python -m pytest tests/test_cli.py -q
```

- Result: `4 passed`.

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

- Result: exited with code 0.
- Output: `Wireless pipeline complete: text_match_rate=1.000, checksum_pass=True`.

```bash
python -m pytest tests -q
```

- Result: `17 passed`.

Fixed CLI output check:

- `results/received.txt` matched `Test.txt` exactly.
- `results/metrics.json` key values after the fixed run:
  - `snr_db`: `12.0`
  - `seed`: `2026`
  - `modulation`: `qpsk`
  - `channel`: `awgn`
  - `payload_bits`: `6128`
  - `ber`: `0.0`
  - `fer`: `0.0`
  - `text_match_rate`: `1.0`
  - `checksum_pass`: `true`
  - `sync_start_index`: `109`
  - `sync_true_offset`: `109`
  - `sync_error_symbols`: `0`

Public tests:

- The first sandbox public-test attempt failed to copy `public_tests/` into the temporary directory, so pytest could not find the directory. This was a sandbox setup mistake, not a project failure.
- The copy command was corrected and public tests were rerun in a temporary sandbox copy because the public-test fixture writes `Test.txt`, while this phase must not leave repository `Test.txt` modified.

```bash
python -m pytest public_tests -q
```

- Result in sandbox copy: `22 passed`.

Failures encountered and fixes:

- Initial Phase 4B RED failures were expected missing CLI/metrics/plots failures.
- The sandbox-copy command for public tests was corrected after it copied no `public_tests/` directory.
- No implementation test failures remained after the pipeline and CLI were added.

Boundary confirmation:

- `public_tests/` was not modified.
- `Test.txt` was not modified in the repository.
- `requirements.txt` was not modified.
- No tests were skipped, weakened, or changed.
- `results/received.txt` is written from decoded receiver output, not by direct file copy.

Unresolved issues:

- No known Phase 4B implementation issue remains after the verified test runs.
- Phase 5 should still perform final result solidification, report completion, and repository packaging after explicit user confirmation.

## Phase 5: Final Result Solidification and Commit Preparation

### Prompt 8: final verification and submission preparation

User prompt summary:

- Enter Phase 5.
- Do not perform large implementation refactors.
- Fix `.gitignore` so required `results/` artifacts can be tracked.
- Regenerate final CLI outputs.
- Run `tests/` and `public_tests/`.
- Check for direct-copy and hardcoding shortcuts.
- Append final verification records to project documents.
- Run `git status --short` and prepare commit guidance.

`.gitignore` change:

- Previous rule ignored the whole `results/` directory.
- Updated rules now ignore temporary result files while allowing the required final artifacts:

```text
results/*
!results/
!results/received.txt
!results/metrics.json
!results/constellation.png
!results/ber_curve.png
!results/sync_peak.png
```

Regenerated fixed CLI output:

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

Result:

```text
Wireless pipeline complete: text_match_rate=1.000, checksum_pass=True
```

Final results file status:

- `results/received.txt`: exists.
- `results/metrics.json`: exists.
- `results/constellation.png`: exists and non-empty.
- `results/ber_curve.png`: exists and non-empty.
- `results/sync_peak.png`: exists and non-empty.
- `results/received.txt` matches `Test.txt` exactly.

Final metrics check:

- Required fields present:
  `snr_db`, `seed`, `modulation`, `channel`, `payload_bits`, `ber`, `fer`,
  `text_match_rate`, `checksum_pass`, and `sync_start_index`.
- Key values from the final run:
  - `snr_db`: `12.0`
  - `seed`: `2026`
  - `modulation`: `qpsk`
  - `channel`: `awgn`
  - `payload_bits`: `6128`
  - `ber`: `0.0`
  - `fer`: `0.0`
  - `text_match_rate`: `1.0`
  - `checksum_pass`: `true`
  - `sync_start_index`: `109`
  - `sync_true_offset`: `109`
  - `sync_error_symbols`: `0`

Final test commands and results:

```bash
python -m pytest tests -q
```

- Result: `17 passed`.

`public_tests/` was run in a temporary sandbox copy because its fixture writes `Test.txt`.
This prevents the repository input file from being changed while still testing the same code.

```bash
python -m pytest public_tests -q
```

- Result in sandbox copy: `22 passed`.

Anti-copy and anti-hardcoding check:

- `rg` scan of `main.py` and `src/` found no `shutil.copy`, no `copyfile`, and no suspicious direct `Test.txt` to `received.txt` write.
- A PowerShell static scan checked for direct-copy patterns and embedded chunks of the current `Test.txt` content; result: `ANTI_HARDCODING_SCAN_OK`.
- The only benign `rg` hits were the CLI completion message and normal `metrics.json` output path.

Script issue encountered:

- The first anti-hardcoding script attempt failed because `src/__init__.py` is empty and PowerShell returned `$null` for `Get-Content -Raw`.
- Root cause was the scan script's handling of empty files, not project code.
- The scan script was rerun with explicit empty-string handling and passed.

Document updates:

- `AI_LOG.md` received this Phase 5 record.
- `TEST_PLAN.md` received the final verification summary.
- `MOCK_TEST_REPORT.md` already contains the Phase 4B GREEN verification addendum and did not require another Phase 5 change.

Git status expectation:

- Required final result files are now visible to Git because `.gitignore` was adjusted.
- `public_tests/`, `Test.txt`, `requirements.txt`, `PRD.docx`, and the report template were not modified in Phase 5.

Commit readiness:

- The repository is ready for user review and a commit after final confirmation.

## Level 3 Cleanup and Finalization

Current stage:

- Level 3 Rayleigh copy cleanup and finalization.
- Work was performed only in `wireless-final-project-template-level3`.
- The original Level 2 stable directory was not modified.

User prompt summary:

- Restore `Test.txt` after public-test side effects.
- Re-run the default AWGN validation command.
- Re-run the Rayleigh demonstration and save Rayleigh metrics separately.
- Restore final default AWGN `results/metrics.json` and `results/received.txt`.
- Run local tests and public tests without weakening or skipping tests.
- Confirm the Level 3 copy is ready as a final submission candidate, without pushing or merging.

Actions performed:

- Restored `Test.txt` with `git checkout -- Test.txt`.
- Re-ran the AWGN fixed command:
  `python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn`.
- Re-ran the Rayleigh demonstration:
  `python main.py --input Test.txt --output results/rayleigh_received.txt --snr 18 --seed 2026 --mod qpsk --channel rayleigh`.
- Saved Rayleigh metrics to `results/rayleigh_metrics.json`.
- Re-ran the AWGN fixed command again so final `results/metrics.json` and `results/received.txt` are AWGN outputs.
- Ran `python -m pytest tests -q`.
- Ran `python -m pytest public_tests -q` in a temporary sandbox copy to avoid modifying the working copy `Test.txt`.
- Updated `.gitignore` so `results/rayleigh_received.txt` and `results/rayleigh_metrics.json` are visible as candidate submission artifacts.
- Updated `DESIGN.md` and `TEST_PLAN.md` with the optional Level 3 Rayleigh extension and cleanup verification notes.

Verification results:

- Final AWGN command exited successfully.
- Final AWGN `results/received.txt` matches `Test.txt` exactly.
- Final `results/metrics.json` has `channel=awgn`, `text_match_rate=1.0`, `checksum_pass=true`, and `ber=0.0`.
- Rayleigh demonstration exited successfully.
- `results/rayleigh_received.txt` matches `Test.txt` exactly.
- `results/rayleigh_metrics.json` has `channel=rayleigh`, `text_match_rate=1.0`, `checksum_pass=true`, and `ber=0.0`.
- Local tests: `20 passed`.
- Public tests in sandbox: `22 passed`.

Final status summary:

- `Test.txt` is restored and not listed as modified.
- `public_tests/` is not listed as modified.
- `requirements.txt` is not listed as modified.
- Current candidate changes are `.gitignore`, `DESIGN.md`, `TEST_PLAN.md`, `main.py`, `src/channel.py`, `src/pipeline.py`, `tests/test_rayleigh.py`, `results/rayleigh_received.txt`, and `results/rayleigh_metrics.json`.
- Existing AWGN result files are present, with final `results/metrics.json` set to AWGN.

Recommendation:

- The Level 3 copy is a reasonable final submission candidate after user review.
- Do not push or merge automatically; wait for explicit confirmation.

## Level 3 GUI Extension

Current stage:

- Optional GUI add-on for the Level 3 copy.
- Work was performed only in `wireless-final-project-template-level3`.
- The original Level 2 stable directory was not modified.

User prompt summary:

- Add a Tkinter GUI that can run the existing simulation without changing the CLI or communication chain.
- Keep AWGN as the default grading path.
- Allow channel selection for AWGN and Rayleigh.
- Display metrics and generated plots for presentation.

Implementation notes:

- Added `gui.py`.
- The GUI calls `src.pipeline.run_pipeline(...)` directly.
- Default GUI values match the fixed AWGN grading command.
- The GUI displays `channel`, `snr_db`, `seed`, `ber`, `fer`, `text_match_rate`, `checksum_pass`, and `sync_start_index`.
- The GUI checks whether the recovered output text exactly matches the input text.
- The GUI loads `constellation.png`, `ber_curve.png`, and `sync_peak.png` from the selected output directory.
- `main.py`, public tests, and the base pipeline API were not changed for the GUI.
- No dependency was added to `requirements.txt`.

Verification:

- `python -m py_compile gui.py`: passed.
- Hidden Tkinter initialization check: passed with default `channel=awgn`, `snr=12`, and `seed=2026`.
- `python -m pytest tests -q`: `20 passed`.
- Fixed AWGN CLI command: exited successfully; `results/received.txt` matches `Test.txt`; final `results/metrics.json` has `channel=awgn`, `text_match_rate=1.0`, `checksum_pass=true`, and `ber=0.0`.
- `python -m pytest public_tests -q` in a temporary sandbox copy: `22 passed`.

Recommendation:

- Use the GUI for demonstration and screenshots.
- Keep CLI as the official grading entry point.

## Level 3 Final Submission Hardening

User prompt summary:

- Harden the Level 3 copy before final submission without breaking the official CLI.
- Fix a hidden-test style synchronization failure observed with `seed=126`, true offset `39`, and a coarse peak outside the old `+/-3` search range.
- Replace ideal Rayleigh CSI equalization with preamble-based flat-channel estimation and one-tap equalization.
- Keep `gui.py` optional and isolated from automated grading.
- Update README, DESIGN, MOCK test report, AI log, and tests.
- Remove cache files and keep public tests and `requirements.txt` unchanged.

Files changed by AI:

- `src/pipeline.py`: expanded checksum-assisted sync search to `+/-32`; added Rayleigh preamble channel estimation; added diagnostic metrics.
- `src/channel.py`: clarified Rayleigh docstring so true fading is diagnostic only.
- `tests/test_level3_hardening.py`: added regression tests for `seed=126`, multi-seed Chinese UTF-8, low SNR, Rayleigh CLI, GUI import safety, and metrics fields.
- `tests/test_rayleigh.py`: updated Rayleigh assertions to require `equalization=preamble_one_tap`.
- `DESIGN.md`, `TEST_PLAN.md`, `MOCK_TEST_REPORT.md`, `README.md`, and this `AI_LOG.md`: documented final Level 3 behavior.

Adoption rationale:

- The synchronization change preserves the public `synchronize(...)` API while making the receiver robust to nearby preamble-correlation ambiguity.
- CRC/checksum is the correct course-level discriminator because it validates the recovered original payload, not only the correlation peak.
- Rayleigh now uses a defensible receiver model: known preamble symbols estimate a single flat-fading coefficient, then one-tap equalization compensates it.
- The official `main.py` CLI remains unchanged because it is the grading contract.
- The GUI remains a Level 3 optional demo tool; it imports `run_pipeline(...)` and does not participate in automatic scoring.

Test failure and fix process:

- A direct regression probe confirmed the prior risk: the old narrow candidate window could miss the true frame start.
- After widening the candidate search and selecting by checksum, `seed=126` recovers with `sync_start_index=39`, `sync_true_offset=39`, `checksum_pass=true`, and `ber=0.0`.
- Rayleigh at `snr=18`, `seed=2026` recovers with `equalization=preamble_one_tap` and records channel-estimation diagnostics.
- Low SNR is handled as a metrics-producing receiver outcome rather than an unhandled crash.

Final verification:

- `python -m pytest tests -q`: `25 passed`.
- Fixed AWGN CLI command: exited successfully; `results/received.txt` matches `Test.txt`; final `results/metrics.json` has `channel=awgn`, `text_match_rate=1.0`, `checksum_pass=true`, `ber=0.0`, `sync_start_index=109`, `sync_true_offset=109`, and `sync_error_symbols=0`.
- Rayleigh demo command: exited successfully; `results/rayleigh_received.txt` matches `Test.txt`; saved `results/rayleigh_metrics.json` with `channel=rayleigh`, `equalization=preamble_one_tap`, `text_match_rate=1.0`, `checksum_pass=true`, and `ber=0.0`.
- `python -m pytest public_tests -q` in a temporary sandbox copy: `22 passed`.
- Cache cleanup removed `__pycache__/` and `.pytest_cache/`; `.gitignore` already excludes `__pycache__/`, `*.py[cod]`, and `.pytest_cache/`.

Final recommendation:

- Use this Level 3 copy as the final submission candidate after user review.
- Do not push or merge automatically.

## End-to-End System BER Curve Extension

User prompt summary:

- Add a complete repetition-coded end-to-end BER-SNR curve.
- Preserve the original CLI, public tests, GUI, and existing formal result outputs.
- Keep `results/ber_curve.png` as the reference curve or combined curve.
- Add `results/system_ber_curve.png` from full pipeline runs.
- Do not let the BER sweep overwrite formal `results/received.txt` or final `results/metrics.json`.

Implementation notes:

- Added `compute_system_ber_curve(...)` in `src.pipeline`.
- Added `generate_plot_files` and `include_system_ber_curve` optional flags to `run_pipeline(...)` so sweep runs do not recurse into plotting.
- The sweep uses SNR values `[0, 2, 4, 6, 8, 10, 12, 14]` and seeds `[2026, 2027, 2028]`.
- Sweep runs call the same full pipeline path with temporary outputs and plot generation disabled.
- `results/ber_curve.png` now overlays uncoded QPSK reference and end-to-end repetition-coded system BER.
- `results/system_ber_curve.png` is generated as the dedicated full-system BER plot.
- `metrics.json` now includes `ber_curve_type`, `system_ber_curve_path`, `system_ber_snr_values`, `system_ber_values`, `system_ber_seeds`, and aggregate pass-rate fields.
- GUI plot tabs now include `system_ber_curve.png`.

Performance note:

- The official run keeps robust `sync_search_radius=32`.
- Internal BER sweep uses a smaller temporary sync search radius to keep the public-test CLI runtime below the 20-second timeout while still exercising synchronization, demodulation, decoding, descrambling, and checksum/metrics calculation.

Final verification:

- `python -m pytest tests -q`: `27 passed`.
- `python -m pytest public_tests -q` in a temporary sandbox copy: `22 passed`.
- Fixed AWGN CLI command exited successfully.
- `results/received.txt` matches `Test.txt` exactly.
- `results/metrics.json` remains the formal AWGN result with `channel=awgn`, `text_match_rate=1.0`, `checksum_pass=true`, and `ber=0.0`.
- `results/metrics.json` includes `system_ber_curve_path=results/system_ber_curve.png`, 8 SNR points, and seeds `[2026, 2027, 2028]`.
- Generated non-empty plots: `constellation.png`, `ber_curve.png`, `system_ber_curve.png`, and `sync_peak.png`.

## Final Documentation Consistency Cleanup

User prompt summary:

- Review `DESIGN.md`, `TEST_PLAN.md`, `MOCK_TEST_REPORT.md`, and `AI_LOG.md` for final submission consistency.
- Remove misleading Phase 1-only wording from the top of final documents.
- Preserve RED/GREEN TDD history while clarifying that early failures were intentional process records.
- Align Rayleigh documentation with preamble-based channel estimation and one-tap equalization.
- Clarify that the GUI is optional and does not affect CLI grading.
- Clarify the difference between the QPSK reference BER curve and the end-to-end repetition-coded system BER curve.

AI changes:

- Updated final status statements in `DESIGN.md`, `TEST_PLAN.md`, `MOCK_TEST_REPORT.md`, and `AI_LOG.md`.
- Replaced outdated implementation-status wording near the tops of final documents.
- Added final verification summaries and current test results.
- Corrected Rayleigh receiver descriptions from ideal true-`h` equalization to preamble-estimated `h_hat` equalization.
- Added GUI testing and optional-display explanation.
- Added BER visualization documentation where applicable.

Human adoption rationale:

- The code was already in a final Level 3 state, but several documents still looked like early Phase 1 or RED-stage artifacts.
- The cleanup prevents graders from misreading historical TDD failures as current failures.
- The updated Rayleigh and BER descriptions better match the implemented system and improve answer quality for oral defense.

## End-to-End System BER Curve Update

User prompt summary:

- Add a complete repetition-coded end-to-end BER-SNR curve in addition to the existing QPSK reference BER curve.

AI changes:

- Added and documented system BER sweep logic that runs the full pipeline over multiple SNR values and seeds.
- Generated and documented `results/system_ber_curve.png`.
- Preserved the official `results/received.txt` and `results/metrics.json` for the fixed AWGN grading command.
- Updated tests and documentation to distinguish the uncoded QPSK reference BER curve from the end-to-end repetition-coded system BER curve.

Adoption rationale:

- The reference BER curve explains modulation-layer behavior.
- The system BER curve better reflects the actual coded file-transmission chain.

## Classroom Review Hardening Update

User prompt summary:

- Use the teacher's classroom review summary to harden the final repository before submission.
- Focus on hidden-test robustness, CLI parameter validation, UTF-8/emoji recovery, result evidence, and GUI presentation.
- Keep the official CLI entry unchanged and preserve existing Level 3 features.

AI changes:

- Added finite-SNR validation in `main.py` and `src/pipeline.py`.
- Rejected non-finite SNR values such as `nan`, `inf`, and `-inf` before the channel model runs.
- Kept finite low-SNR values valid as stress-test inputs.
- Added `tests/test_teacher_review_hardening.py` for invalid SNR, mixed UTF-8/emoji, empty text, long text, and custom output directories.
- Documented the classroom-review evidence chain in `README.md`, `TEST_PLAN.md`, and `MOCK_TEST_REPORT.md`.
- Preserved the official command-line interface, public-test behavior, Rayleigh extension, GUI, and result artifacts.

TDD and debugging record:

- RED: the new invalid-SNR test initially failed because `--snr nan` entered the full pipeline and returned a receiver failure instead of a clear CLI error.
- GREEN: CLI parsing now rejects non-finite SNR values with an explicit finite-number error, and pipeline-level validation protects direct API calls.
- The hardening tests then passed without weakening any existing tests.

Adoption rationale:

- The classroom review emphasized hidden tests that change text, SNR, seed, synchronization offset, file paths, and invalid parameters.
- These changes strengthen the repository against those checks while keeping the communication chain explainable and preserving the official grading entry.
