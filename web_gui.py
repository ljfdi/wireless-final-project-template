from __future__ import annotations

"""Optional HTML dashboard for the wireless baseband simulation.

Run with:
    python web_gui.py

Then open:
    http://127.0.0.1:8000
"""

import argparse
import json
import mimetypes
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from src.pipeline import run_pipeline


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = PROJECT_ROOT / "Test.txt"
DEFAULT_OUTPUT = PROJECT_ROOT / "results" / "received.txt"
RESULTS_DIR = PROJECT_ROOT / "results"
PLOT_FILES = {
    "constellation": "constellation.png",
    "ber_curve": "ber_curve.png",
    "system_ber_curve": "system_ber_curve.png",
    "sync_peak": "sync_peak.png",
}
MAX_TEXT_PREVIEW_CHARS = 20000


HTML_PAGE = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Wireless Baseband File Transmission Dashboard</title>
  <style>
    :root {
      --bg: #f4f7fb;
      --panel: #ffffff;
      --ink: #172033;
      --muted: #64748b;
      --line: #d9e2ef;
      --blue: #2563eb;
      --green: #16a34a;
      --red: #dc2626;
      --amber: #d97706;
      --shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", Arial, sans-serif;
      background: var(--bg);
      color: var(--ink);
    }
    header {
      background: linear-gradient(135deg, #10213f, #163f75);
      color: white;
      padding: 24px 32px 20px;
    }
    header h1 {
      margin: 0 0 8px;
      font-size: 30px;
      letter-spacing: 0;
    }
    header p {
      margin: 4px 0;
      color: #dbeafe;
      font-size: 14px;
    }
    main {
      max-width: 1440px;
      margin: 0 auto;
      padding: 22px;
    }
    .link-flow {
      display: grid;
      grid-template-columns: repeat(9, minmax(88px, 1fr));
      gap: 8px;
      margin-top: 18px;
    }
    .flow-step {
      border: 1px solid rgba(255, 255, 255, 0.25);
      border-radius: 8px;
      padding: 8px 6px;
      text-align: center;
      background: rgba(255, 255, 255, 0.12);
      font-size: 12px;
    }
    .grid {
      display: grid;
      grid-template-columns: 360px minmax(0, 1fr);
      gap: 18px;
      align-items: start;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      box-shadow: var(--shadow);
    }
    .panel h2 {
      margin: 0;
      padding: 16px 18px 0;
      font-size: 18px;
    }
    .panel-body { padding: 16px 18px 18px; }
    label {
      display: block;
      margin: 13px 0 6px;
      color: var(--muted);
      font-weight: 600;
      font-size: 13px;
    }
    input, select {
      width: 100%;
      padding: 10px 11px;
      border: 1px solid var(--line);
      border-radius: 7px;
      font-size: 14px;
      background: white;
      color: var(--ink);
    }
    .row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    .button-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 16px;
    }
    button {
      border: 0;
      border-radius: 7px;
      padding: 10px 13px;
      font-weight: 700;
      cursor: pointer;
      background: #e2e8f0;
      color: #0f172a;
    }
    button.primary {
      background: var(--blue);
      color: white;
      flex: 1;
    }
    button:disabled {
      cursor: wait;
      opacity: 0.65;
    }
    .status-strip {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }
    .status-card {
      border: 1px solid var(--line);
      border-radius: 10px;
      background: white;
      padding: 14px 16px;
      box-shadow: var(--shadow);
    }
    .status-card .label {
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }
    .status-card .value {
      margin-top: 8px;
      font-size: 22px;
      font-weight: 800;
      overflow-wrap: anywhere;
    }
    .success { color: var(--green); }
    .danger { color: var(--red); }
    .warning { color: var(--amber); }
    .metric-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }
    .metric {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px 12px;
      background: #fbfdff;
    }
    .metric .name {
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }
    .metric .number {
      margin-top: 6px;
      font-size: 18px;
      font-weight: 800;
      overflow-wrap: anywhere;
    }
    .text-compare {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
    }
    pre {
      margin: 0;
      min-height: 240px;
      max-height: 420px;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-word;
      background: #0f172a;
      color: #e5e7eb;
      border-radius: 8px;
      padding: 14px;
      line-height: 1.55;
      font-family: Consolas, "Courier New", monospace;
      font-size: 13px;
    }
    .subhead {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      font-weight: 800;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 5px 10px;
      font-size: 12px;
      font-weight: 800;
      background: #e2e8f0;
    }
    .badge.success { background: #dcfce7; }
    .badge.danger { background: #fee2e2; }
    .badge.warning { background: #fef3c7; }
    .plots {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }
    .plot-card {
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 12px;
      background: white;
    }
    .plot-card h3 {
      margin: 0 0 6px;
      font-size: 16px;
    }
    .plot-card p {
      margin: 0 0 10px;
      color: var(--muted);
      font-size: 13px;
    }
    .plot-card img {
      display: block;
      width: 100%;
      max-height: 360px;
      object-fit: contain;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #f8fafc;
    }
    .chain {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }
    .chain div {
      border: 1px solid var(--line);
      background: #fbfdff;
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 13px;
      line-height: 1.45;
    }
    .chain strong { display: block; margin-bottom: 4px; }
    .message {
      margin-top: 12px;
      color: var(--muted);
      font-size: 13px;
      min-height: 20px;
    }
    section { margin-bottom: 18px; }
    @media (max-width: 1100px) {
      .grid, .text-compare, .plots { grid-template-columns: 1fr; }
      .status-strip, .metric-grid, .chain, .link-flow { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
  </style>
</head>
<body>
  <header>
    <h1>Wireless Baseband File Transmission Dashboard</h1>
    <p>Official grading entry remains: python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn</p>
    <p>This HTML GUI is an optional Level 3 demonstration layer for the same pipeline.</p>
    <div class="link-flow">
      <div class="flow-step">Text</div><div class="flow-step">Bits</div><div class="flow-step">Scramble</div>
      <div class="flow-step">Repetition Code</div><div class="flow-step">Frame</div><div class="flow-step">QPSK</div>
      <div class="flow-step">Channel</div><div class="flow-step">Sync</div><div class="flow-step">Decode Text</div>
    </div>
  </header>
  <main>
    <div class="grid">
      <aside class="panel">
        <h2>Simulation Setup</h2>
        <div class="panel-body">
          <label for="inputPath">Input path</label>
          <input id="inputPath">
          <label for="outputPath">Output path</label>
          <input id="outputPath">
          <div class="row">
            <div>
              <label for="snrDb">SNR dB</label>
              <input id="snrDb" type="number" step="0.5">
            </div>
            <div>
              <label for="seed">Seed</label>
              <input id="seed" type="number" step="1">
            </div>
          </div>
          <label for="channel">Channel</label>
          <select id="channel">
            <option value="awgn">awgn</option>
            <option value="rayleigh">rayleigh</option>
          </select>
          <div class="button-row">
            <button onclick="presetAwgn()">AWGN Baseline</button>
            <button onclick="presetRayleigh()">Rayleigh Demo</button>
            <button onclick="presetLowSnr()">Low SNR Stress</button>
          </div>
          <div class="button-row">
            <button id="runButton" class="primary" onclick="runSimulation()">Run Simulation</button>
            <button onclick="refreshState()">Refresh Outputs</button>
          </div>
          <div id="message" class="message"></div>
        </div>
      </aside>

      <section>
        <div class="status-strip">
          <div class="status-card"><div class="label">Mode</div><div id="modeValue" class="value">-</div></div>
          <div class="status-card"><div class="label">Recovery</div><div id="recoveryValue" class="value">-</div></div>
          <div class="status-card"><div class="label">Checksum</div><div id="checksumValue" class="value">-</div></div>
          <div class="status-card"><div class="label">Text Match</div><div id="matchValue" class="value">-</div></div>
        </div>

        <div class="panel">
          <h2>Core Metrics</h2>
          <div class="panel-body">
            <div id="metricGrid" class="metric-grid"></div>
          </div>
        </div>
      </section>
    </div>

    <section class="panel">
      <h2>Input / Recovered Text Comparison</h2>
      <div class="panel-body">
        <div class="text-compare">
          <div>
            <div class="subhead">Input Text <span id="inputCount" class="badge">0 chars</span></div>
            <pre id="inputText">Loading...</pre>
          </div>
          <div>
            <div class="subhead">Recovered Output <span id="outputCount" class="badge">0 chars</span></div>
            <pre id="outputText">Run simulation first.</pre>
          </div>
        </div>
      </div>
    </section>

    <section class="panel">
      <h2>Generated Plots</h2>
      <div class="panel-body">
        <div class="plots" id="plotGrid"></div>
      </div>
    </section>

    <section class="panel">
      <h2>Communication Chain Notes</h2>
      <div class="panel-body">
        <div class="chain">
          <div><strong>Source Encode</strong>UTF-8 text is converted into a bitstream, preserving Chinese text by byte-level coding.</div>
          <div><strong>Scramble</strong>PN XOR scrambling uses the seed to make the payload reproducible and less patterned.</div>
          <div><strong>Channel Encode</strong>A repetition code adds redundancy and uses majority voting at the receiver.</div>
          <div><strong>Frame</strong>The frame contains preamble, raw length, coded length, CRC/checksum, and coded payload.</div>
          <div><strong>QPSK</strong>Gray-coded QPSK maps every two bits to one unit-power complex symbol.</div>
          <div><strong>Channel</strong>AWGN adds complex noise; Rayleigh adds block-flat fading plus noise.</div>
          <div><strong>Synchronization</strong>Preamble correlation gives a coarse start, then checksum-assisted candidate search selects the final frame.</div>
          <div><strong>Decode</strong>Demodulation, repetition decoding, descrambling, length truncation, and UTF-8 decoding recover the text.</div>
        </div>
      </div>
    </section>
  </main>

  <script>
    const defaults = {
      input_path: "__DEFAULT_INPUT__",
      output_path: "__DEFAULT_OUTPUT__",
      snr_db: 12,
      seed: 2026,
      channel: "awgn"
    };

    const metrics = [
      "ber", "fer", "text_match_rate", "checksum_pass",
      "sync_start_index", "sync_error_symbols", "payload_bits", "channel",
      "estimated_channel_abs", "channel_estimation_error", "equalization"
    ];

    const plotInfo = [
      ["constellation", "QPSK Constellation", "Received QPSK clusters show channel noise and decision separation."],
      ["ber_curve", "QPSK BER Reference", "Reference BER-SNR trend explains modulation-layer behavior under AWGN."],
      ["system_ber_curve", "End-to-End System BER", "Full pipeline BER includes scrambling, coding, framing, sync, decoding, and text recovery."],
      ["sync_peak", "Synchronization Peak", "Preamble correlation proves the receiver searches for frame start instead of assuming it."]
    ];

    function el(id) { return document.getElementById(id); }
    function setMessage(text, cls) {
      const msg = el("message");
      msg.textContent = text || "";
      msg.className = "message " + (cls || "");
    }
    function fmt(value) {
      if (value === null || value === undefined || value === "") return "-";
      if (typeof value === "number") return Math.abs(value) < 1e-4 && value !== 0 ? value.toExponential(3) : String(Number(value.toPrecision(6)));
      return String(value);
    }
    function setClass(node, status) {
      node.classList.remove("success", "danger", "warning");
      if (status) node.classList.add(status);
    }
    function currentPayload() {
      return {
        input_path: el("inputPath").value,
        output_path: el("outputPath").value,
        snr_db: Number(el("snrDb").value),
        seed: Number(el("seed").value),
        channel: el("channel").value
      };
    }
    function presetAwgn() {
      el("inputPath").value = defaults.input_path;
      el("outputPath").value = defaults.output_path;
      el("snrDb").value = "12";
      el("seed").value = "2026";
      el("channel").value = "awgn";
      refreshState();
    }
    function presetRayleigh() {
      el("inputPath").value = defaults.input_path;
      el("outputPath").value = "__PROJECT_ROOT__/results/rayleigh_received.txt";
      el("snrDb").value = "18";
      el("seed").value = "2026";
      el("channel").value = "rayleigh";
      refreshState();
    }
    function presetLowSnr() {
      el("inputPath").value = defaults.input_path;
      el("outputPath").value = "__PROJECT_ROOT__/results/low_snr_received.txt";
      el("snrDb").value = "0";
      el("seed").value = "2026";
      el("channel").value = "awgn";
      refreshState();
    }
    async function runSimulation() {
      const button = el("runButton");
      button.disabled = true;
      setMessage("Running the full transmitter-channel-receiver pipeline...", "warning");
      try {
        const response = await fetch("/api/run", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(currentPayload())
        });
        const data = await response.json();
        if (!response.ok || !data.ok) throw new Error(data.error || "Simulation failed");
        renderState(data);
        setMessage("Simulation complete. Metrics, text comparison, and plots have been refreshed.", "success");
      } catch (err) {
        setMessage(err.message, "danger");
      } finally {
        button.disabled = false;
      }
    }
    async function refreshState() {
      try {
        const params = new URLSearchParams(currentPayload());
        const response = await fetch("/api/state?" + params.toString());
        const data = await response.json();
        renderState(data);
        if (data.error) setMessage(data.error, "warning");
      } catch (err) {
        setMessage(err.message, "danger");
      }
    }
    function renderState(data) {
      const m = data.metrics || {};
      el("modeValue").textContent = m.channel === "rayleigh" ? "Rayleigh Level 3" : "AWGN Baseline";
      const textMatch = data.text_match === true || Number(m.text_match_rate) === 1;
      const checksum = m.checksum_pass === true;
      el("recoveryValue").textContent = textMatch ? "Recovered" : "Warning";
      el("checksumValue").textContent = checksum ? "Passed" : "Check";
      el("matchValue").textContent = data.text_match === true ? "MATCH" : (data.output_exists ? "DIFFER" : "No output");
      setClass(el("recoveryValue"), textMatch ? "success" : "warning");
      setClass(el("checksumValue"), checksum ? "success" : "danger");
      setClass(el("matchValue"), data.text_match === true ? "success" : (data.output_exists ? "danger" : "warning"));

      const grid = el("metricGrid");
      grid.innerHTML = "";
      metrics.forEach(name => {
        const card = document.createElement("div");
        card.className = "metric";
        const label = document.createElement("div");
        label.className = "name";
        label.textContent = name;
        const value = document.createElement("div");
        value.className = "number";
        value.textContent = fmt(m[name]);
        if (name === "ber" || name === "fer") setClass(value, Number(m[name]) === 0 ? "success" : "warning");
        if (name === "checksum_pass") setClass(value, m[name] === true ? "success" : "danger");
        if (name === "text_match_rate") setClass(value, Number(m[name]) === 1 ? "success" : "warning");
        card.appendChild(label);
        card.appendChild(value);
        grid.appendChild(card);
      });

      el("inputText").textContent = data.input_text || "(input unavailable)";
      el("outputText").textContent = data.output_text || "Run simulation first.";
      el("inputCount").textContent = String(data.input_chars || 0) + " chars";
      el("outputCount").textContent = String(data.output_chars || 0) + " chars";
      setClass(el("inputCount"), "");
      setClass(el("outputCount"), data.text_match === true ? "success" : (data.output_exists ? "danger" : "warning"));
      renderPlots(data.plots || {});
    }
    function renderPlots(plots) {
      const grid = el("plotGrid");
      grid.innerHTML = "";
      plotInfo.forEach(([key, title, desc]) => {
        const card = document.createElement("div");
        card.className = "plot-card";
        const h = document.createElement("h3");
        h.textContent = title;
        const p = document.createElement("p");
        p.textContent = desc;
        card.appendChild(h);
        card.appendChild(p);
        if (plots[key] && plots[key].exists) {
          const img = document.createElement("img");
          img.alt = title;
          img.src = plots[key].url + "?t=" + Date.now();
          card.appendChild(img);
        } else {
          const missing = document.createElement("div");
          missing.className = "badge warning";
          missing.textContent = "Run simulation first or check results folder";
          card.appendChild(missing);
        }
        grid.appendChild(card);
      });
    }
    function initialize() {
      el("inputPath").value = defaults.input_path;
      el("outputPath").value = defaults.output_path;
      el("snrDb").value = String(defaults.snr_db);
      el("seed").value = String(defaults.seed);
      el("channel").value = defaults.channel;
      refreshState();
    }
    initialize();
  </script>
</body>
</html>
"""


def _display_path(path: Path) -> str:
    return str(path).replace("\\", "/")


def _resolve_path(value: object, default: Path | None = None) -> Path:
    text = str(value if value not in (None, "") else default or "").strip().strip('"')
    if not text:
        raise ValueError("path cannot be empty")
    path = Path(text).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def _safe_read_text(path: Path) -> tuple[str, bool, str]:
    if not path.exists():
        return "", False, f"{path.name} not found"
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:  # pragma: no cover - defensive UI path
        return "", False, f"{type(exc).__name__}: {exc}"
    if len(text) > MAX_TEXT_PREVIEW_CHARS:
        text = text[:MAX_TEXT_PREVIEW_CHARS] + "\n\n[preview truncated]"
    return text, True, ""


def _load_metrics(results_dir: Path) -> dict[str, object]:
    metrics_path = results_dir / "metrics.json"
    if not metrics_path.exists():
        return {}
    try:
        return json.loads(metrics_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive UI path
        return {"failure_reason": f"metrics read failed: {type(exc).__name__}: {exc}"}


def _plot_state(results_dir: Path) -> dict[str, dict[str, object]]:
    plots: dict[str, dict[str, object]] = {}
    for key, filename in PLOT_FILES.items():
        path = results_dir / filename
        plots[key] = {
            "filename": filename,
            "exists": path.exists() and path.stat().st_size > 0,
            "url": f"/results/{filename}",
            "size": path.stat().st_size if path.exists() else 0,
        }
    return plots


def _state(input_path: Path, output_path: Path) -> dict[str, object]:
    input_text, input_exists, input_error = _safe_read_text(input_path)
    output_text, output_exists, output_error = _safe_read_text(output_path)
    metrics = _load_metrics(output_path.parent)
    text_match = input_exists and output_exists and input_text == output_text
    error = "; ".join(part for part in (input_error, output_error) if part)
    return {
        "ok": True,
        "input_path": _display_path(input_path),
        "output_path": _display_path(output_path),
        "input_text": input_text,
        "output_text": output_text,
        "input_exists": input_exists,
        "output_exists": output_exists,
        "input_chars": len(input_text),
        "output_chars": len(output_text),
        "text_match": text_match,
        "metrics": metrics,
        "plots": _plot_state(output_path.parent),
        "error": error,
    }


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "WirelessDashboard/1.0"

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_bytes(self, body: bytes, content_type: str, status: int = HTTPStatus.OK) -> None:
        self.send_response(int(status))
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: dict[str, object], status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self._send_bytes(body, "application/json; charset=utf-8", status)

    def _read_json(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/":
                html = (
                    HTML_PAGE.replace("__DEFAULT_INPUT__", _display_path(DEFAULT_INPUT))
                    .replace("__DEFAULT_OUTPUT__", _display_path(DEFAULT_OUTPUT))
                    .replace("__PROJECT_ROOT__", _display_path(PROJECT_ROOT))
                )
                self._send_bytes(html.encode("utf-8"), "text/html; charset=utf-8")
                return
            if parsed.path == "/api/state":
                query = parse_qs(parsed.query)
                input_path = _resolve_path(query.get("input_path", [""])[0], DEFAULT_INPUT)
                output_path = _resolve_path(query.get("output_path", [""])[0], DEFAULT_OUTPUT)
                self._send_json(_state(input_path, output_path))
                return
            if parsed.path.startswith("/results/"):
                filename = Path(unquote(parsed.path[len("/results/") :])).name
                path = RESULTS_DIR / filename
                if not path.exists() or not path.is_file():
                    self._send_json({"ok": False, "error": "result file not found"}, HTTPStatus.NOT_FOUND)
                    return
                content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
                self._send_bytes(path.read_bytes(), content_type)
                return
            self._send_json({"ok": False, "error": "not found"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self._send_json({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, HTTPStatus.BAD_REQUEST)

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        if urlparse(self.path).path != "/api/run":
            self._send_json({"ok": False, "error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        try:
            payload = self._read_json()
            input_path = _resolve_path(payload.get("input_path"), DEFAULT_INPUT)
            output_path = _resolve_path(payload.get("output_path"), DEFAULT_OUTPUT)
            snr_db = float(payload.get("snr_db", 12))
            seed = int(payload.get("seed", 2026))
            channel = str(payload.get("channel", "awgn")).lower()
            metrics = run_pipeline(
                input_path=input_path,
                output_path=output_path,
                snr_db=snr_db,
                seed=seed,
                modulation="qpsk",
                channel=channel,
            )
            state = _state(input_path, output_path)
            state["metrics"] = metrics
            self._send_json(state)
        except Exception as exc:
            self._send_json({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, HTTPStatus.BAD_REQUEST)


def run_server(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True) -> None:
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    url = f"http://{host}:{port}"
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    print(f"Wireless HTML dashboard running at {url}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the optional HTML dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-open", action="store_true", help="Do not open a browser automatically")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    run_server(host=args.host, port=args.port, open_browser=not args.no_open)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
