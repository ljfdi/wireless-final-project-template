from __future__ import annotations

import json
import py_compile
import subprocess
import sys
import threading
from http.server import ThreadingHTTPServer
from urllib.parse import urlencode
from urllib.request import urlopen


def test_web_gui_compiles_and_import_has_no_server_side_effect(project_root):
    web_gui_path = project_root / "web_gui.py"
    py_compile.compile(str(web_gui_path), doraise=True)

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import web_gui; print('imported')",
        ],
        cwd=project_root,
        text=True,
        capture_output=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "imported"


def test_web_gui_state_api_reports_text_comparison(tmp_path):
    import web_gui

    input_path = tmp_path / "input with spaces.txt"
    output_path = tmp_path / "received with spaces.txt"
    input_path.write_text("HTML dashboard text comparison 测试", encoding="utf-8")
    output_path.write_text("HTML dashboard text comparison 测试", encoding="utf-8")

    server = ThreadingHTTPServer(("127.0.0.1", 0), web_gui.DashboardHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        params = urlencode(
            {
                "input_path": str(input_path),
                "output_path": str(output_path),
            }
        )
        with urlopen(f"http://127.0.0.1:{server.server_port}/api/state?{params}", timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert payload["ok"] is True
    assert payload["text_match"] is True
    assert payload["input_chars"] == payload["output_chars"]
    assert payload["input_text"] == payload["output_text"]
    assert set(payload["plots"]) == {"constellation", "ber_curve", "system_ber_curve", "sync_peak"}


def test_web_gui_serves_result_png(project_root):
    import web_gui

    png_path = project_root / "results" / "constellation.png"
    assert png_path.exists() and png_path.stat().st_size > 0

    server = ThreadingHTTPServer(("127.0.0.1", 0), web_gui.DashboardHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/results/constellation.png", timeout=10) as response:
            content_type = response.headers["Content-Type"]
            body = response.read(16)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert content_type == "image/png"
    assert body.startswith(b"\x89PNG")
