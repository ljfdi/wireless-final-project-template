# 无线通信技术期末项目

本仓库是无线通信技术课程期末项目的教师模板仓库。学生需要 Fork 本仓库到自己的 GitHub 账号，完成项目后向本仓库创建 Pull Request。教师将通过 Pull Request 中的 GitHub Actions 公开测试结果、隐藏验证集和文档检查完成验收。

项目目标：根据 `PRD.docx` 的要求，使用 AI 辅助编程实现一个无线通信基带仿真系统，将 `Test.txt` 的 UTF-8 文本内容通过发送端、无线信道和接收端处理后恢复为 `results/received.txt`。

## 提交流程

1. 点击本仓库右上角 `Fork`，将仓库复制到自己的 GitHub 账号下。
2. Clone 自己 Fork 后的仓库到本地。

```bash
git clone https://github.com/<your-username>/wireless-final-project-template.git
cd wireless-final-project-template
```

3. 按 `PRD.docx` 完成设计、mock 测试和代码实现。
4. 本地运行公开测试。

```bash
pip install -r requirements.txt
pytest public_tests -q
```

5. 提交并推送到自己的 Fork。

```bash
git add .
git commit -m "Complete wireless final project"
git push origin main
```

6. 回到 GitHub 网页，从自己的 Fork 向教师原仓库创建 Pull Request。
7. Pull Request 创建后，GitHub Actions 会自动运行公开测试，并在 PR 页面显示结果。

请不要直接向教师仓库 main 分支提交代码。最终提交以 Pull Request 为准。

## 必须提交的文件

学生最终项目至少应包含：

```text
DESIGN.md
TEST_PLAN.md
MOCK_TEST_REPORT.md
AI_LOG.md
main.py
src/
tests/
results/
```

## 统一运行命令

项目必须支持以下命令：

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

运行后应生成：

```text
results/received.txt
results/metrics.json
```

并至少生成以下图表中的两项：

```text
results/constellation.png
results/ber_curve.png
results/sync_peak.png
```

## 公开测试

本仓库包含 `public_tests/`，用于公开验收和学生调试。这些测试只覆盖部分基础要求，不代表最终全部评分。

运行方式：

```bash
pytest public_tests -q
```

公开测试主要检查：

- 项目结构和文档是否完整
- 统一命令行入口是否可运行
- 源编码、帧结构、扰码或加密、信道编码、QPSK、AWGN、同步等模块是否满足基本要求
- `results/received.txt` 和 `results/metrics.json` 是否生成
- `metrics.json` 字段是否完整
- 是否生成至少两张结果图
- 是否存在明显绕过无线链路的直接复制行为

## 隐藏验证

教师最终评分还会使用隐藏验证集。隐藏验证集不会公开，可能覆盖：

- 不同中文文本
- 不同文本长度
- 不同 SNR
- 不同随机 seed
- 随机同步偏移
- 异常参数
- 反硬编码检查
- 设计文档与代码一致性检查

## AI 使用要求

允许并鼓励使用 AI 辅助编程。建议使用 Claude Code 或 Codex，并加装或启用 Superpowers skills。

必须保留 `AI_LOG.md`，记录关键 prompt、AI 生成内容、人工修改内容、测试失败修复过程和最终采纳理由。

即使程序运行成功，学生仍需能够解释每个模块的通信原理、关键参数、代码逻辑和实验结果。

## Pull Request 要求

创建 Pull Request 时，请填写 PR 模板中的学生信息和检查清单。PR 标题建议使用：

```text
学号-姓名-无线通信期末项目
```

例如：

```text
2023123456-张三-无线通信期末项目
```

## Final Submission Usage Notes

Required AWGN grading command:

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

Optional Level 3 Rayleigh demonstration:

```bash
python main.py --input Test.txt --output results/rayleigh_received.txt --snr 18 --seed 2026 --mod qpsk --channel rayleigh
```

Optional GUI demonstration:

```bash
python gui.py
```

Test commands:

```bash
python -m pytest public_tests -q
python -m pytest tests -q
```

Important outputs:

```text
results/received.txt
results/metrics.json
results/constellation.png
results/ber_curve.png
results/system_ber_curve.png
results/sync_peak.png
results/rayleigh_received.txt
results/rayleigh_metrics.json
```

Design summary:

- The default grading path remains `main.py` with AWGN and QPSK.
- The receiver uses UTF-8 source coding, PN XOR scrambling, repetition channel coding, frame length fields, CRC/checksum, QPSK Gray mapping, AWGN/Rayleigh channel simulation, preamble synchronization, demodulation, decoding, descrambling, and UTF-8 recovery.
- `raw_payload_length` means the source-encoded payload bit count before scrambling and channel coding; it is used to remove padding safely.
- Synchronization uses preamble correlation followed by checksum-assisted candidate search around the coarse peak.
- Rayleigh mode is a course-level flat-fading extension: `y = h*x + n`, preamble-based channel estimation, and one-tap equalization.
- `gui.py` is only an optional Level 3 demo tool and does not replace the CLI grading entry point.

BER curve notes:

- `results/ber_curve.png` contains the uncoded QPSK reference BER curve and the end-to-end repetition-coded system BER overlay.
- `results/system_ber_curve.png` contains only the complete end-to-end system BER-SNR curve.
- The system BER curve is computed by running the full pipeline over multiple SNR values and seeds, including source coding, scrambling, repetition coding, framing, QPSK, AWGN, synchronization, decoding, descrambling, source decoding, and checksum/metrics calculation.
- The BER sweep uses temporary outputs and does not overwrite the formal `results/received.txt` or final `results/metrics.json`.

## Final Hardening Notes After Classroom Review

The final repository was hardened around the three questions emphasized in the classroom review:

- What was transmitted: UTF-8 text from the configured input file, converted to bits, scrambled, repetition-coded, framed, QPSK-modulated, sent through AWGN/Rayleigh, synchronized, decoded, descrambled, and restored as text.
- How many errors occurred: `metrics.json` records `ber`, `fer`, `text_match_rate`, `checksum_pass`, `payload_bits`, and synchronization diagnostics.
- Why errors occur: low SNR, Rayleigh deep fading, ambiguous preamble correlation, checksum failure, or UTF-8 decode failure are recorded through metrics such as `failure_reason`, `sync_error_symbols`, and Rayleigh channel-estimation diagnostics.

Additional hidden-test style checks cover mixed Chinese/English/emoji UTF-8 text, empty text, long text, multiple seeds, low SNR non-crash behavior, custom output directories, and invalid SNR rejection. Non-finite SNR values such as `nan`, `inf`, and `-inf` are rejected before the channel model runs, while finite low SNR values remain valid stress-test inputs.

A local hidden-test simulation was also run outside the repository and is not submitted as project code. It covered 77 cases, including mixed Chinese/English/emoji payloads, empty text, long text, AWGN SNR values `6`, `8`, `12`, and `15`, Rayleigh SNR `18`, multiple seeds including `126` and `2026`, missing input, invalid SNR, invalid modulation, low-SNR non-crash behavior, and custom output directories. The simulation completed with zero failures.

## Optional HTML Dashboard

The project also includes a browser-based demonstration dashboard:

```bash
python web_gui.py --port 8010
```

Open:

```text
http://127.0.0.1:8010/
```

The dashboard shows the same pipeline through a visual interface: input/output text comparison, MATCH/DIFFER status, BER/FER/checksum/synchronization metric cards, Rayleigh equalization diagnostics, four generated plots, and a short communication-chain explanation. It is optional and does not replace `main.py`.

If port `8000` is occupied or the browser shows an HTTP/HTTPS `Bad Request`, choose another port such as `8010`.
