from __future__ import annotations

"""Optional Tkinter GUI for the wireless baseband simulation."""

import json
import math
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from src.pipeline import run_pipeline


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = PROJECT_ROOT / "Test.txt"
DEFAULT_OUTPUT = PROJECT_ROOT / "results" / "received.txt"
PLOT_FILES = {
    "Constellation": "constellation.png",
    "BER Curve": "ber_curve.png",
    "System BER": "system_ber_curve.png",
    "Sync Peak": "sync_peak.png",
}
METRIC_FIELDS = (
    "channel",
    "snr_db",
    "seed",
    "ber",
    "fer",
    "text_match_rate",
    "checksum_pass",
    "sync_start_index",
)


class WirelessGui:
    """Small desktop wrapper around the existing run_pipeline API."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Wireless Baseband Simulation")
        self.root.minsize(980, 680)

        self.input_var = tk.StringVar(value=str(DEFAULT_INPUT))
        self.output_var = tk.StringVar(value=str(DEFAULT_OUTPUT))
        self.snr_var = tk.StringVar(value="12")
        self.seed_var = tk.StringVar(value="2026")
        self.channel_var = tk.StringVar(value="awgn")
        self.status_var = tk.StringVar(value="Ready")
        self.match_var = tk.StringVar(value="Not run")
        self.metric_vars = {field: tk.StringVar(value="-") for field in METRIC_FIELDS}
        self.plot_images: dict[str, tk.PhotoImage] = {}
        self.plot_labels: dict[str, ttk.Label] = {}

        self._build_layout()
        self._load_existing_outputs()

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        controls = ttk.LabelFrame(self.root, text="Simulation")
        controls.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        controls.columnconfigure(1, weight=1)
        controls.columnconfigure(4, weight=1)

        ttk.Label(controls, text="Input").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(controls, textvariable=self.input_var).grid(
            row=0, column=1, columnspan=4, sticky="ew", padx=8, pady=6
        )
        ttk.Button(controls, text="Browse", command=self._browse_input).grid(
            row=0, column=5, sticky="ew", padx=8, pady=6
        )

        ttk.Label(controls, text="Output").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(controls, textvariable=self.output_var).grid(
            row=1, column=1, columnspan=4, sticky="ew", padx=8, pady=6
        )
        ttk.Button(controls, text="Browse", command=self._browse_output).grid(
            row=1, column=5, sticky="ew", padx=8, pady=6
        )

        ttk.Label(controls, text="SNR dB").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(controls, textvariable=self.snr_var, width=10).grid(
            row=2, column=1, sticky="w", padx=8, pady=6
        )
        ttk.Label(controls, text="Seed").grid(row=2, column=2, sticky="w", padx=8, pady=6)
        ttk.Entry(controls, textvariable=self.seed_var, width=10).grid(
            row=2, column=3, sticky="w", padx=8, pady=6
        )
        ttk.Label(controls, text="Channel").grid(row=2, column=4, sticky="e", padx=8, pady=6)
        channel_box = ttk.Combobox(
            controls,
            textvariable=self.channel_var,
            values=("awgn", "rayleigh"),
            state="readonly",
            width=12,
        )
        channel_box.grid(row=2, column=5, sticky="ew", padx=8, pady=6)

        button_row = ttk.Frame(controls)
        button_row.grid(row=3, column=0, columnspan=6, sticky="ew", padx=8, pady=(4, 8))
        button_row.columnconfigure(3, weight=1)
        self.run_button = ttk.Button(button_row, text="Run Simulation", command=self._run)
        self.run_button.grid(row=0, column=0, padx=(0, 8))
        ttk.Button(button_row, text="Refresh Outputs", command=self._load_existing_outputs).grid(
            row=0, column=1, padx=8
        )
        ttk.Button(button_row, text="Open Results Folder", command=self._open_results_folder).grid(
            row=0, column=2, padx=8
        )
        ttk.Label(button_row, textvariable=self.status_var).grid(
            row=0, column=3, sticky="e", padx=8
        )

        metrics = ttk.LabelFrame(self.root, text="Metrics")
        metrics.grid(row=1, column=0, sticky="ew", padx=12, pady=8)
        for index, field in enumerate(METRIC_FIELDS):
            col = (index % 4) * 2
            row = index // 4
            ttk.Label(metrics, text=f"{field}:").grid(row=row, column=col, sticky="w", padx=8, pady=4)
            ttk.Label(metrics, textvariable=self.metric_vars[field]).grid(
                row=row, column=col + 1, sticky="w", padx=8, pady=4
            )
        ttk.Label(metrics, text="text_match:").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        ttk.Label(metrics, textvariable=self.match_var).grid(row=2, column=1, sticky="w", padx=8, pady=4)

        plots = ttk.LabelFrame(self.root, text="Plots")
        plots.grid(row=2, column=0, sticky="nsew", padx=12, pady=(8, 12))
        plots.columnconfigure(0, weight=1)
        plots.rowconfigure(0, weight=1)
        self.notebook = ttk.Notebook(plots)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        for title in PLOT_FILES:
            frame = ttk.Frame(self.notebook)
            frame.columnconfigure(0, weight=1)
            frame.rowconfigure(0, weight=1)
            label = ttk.Label(frame, text="Plot not loaded", anchor="center")
            label.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
            self.notebook.add(frame, text=title)
            self.plot_labels[title] = label

    def _browse_input(self) -> None:
        path = filedialog.askopenfilename(
            initialdir=str(PROJECT_ROOT),
            title="Select input text file",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*")),
        )
        if path:
            self.input_var.set(path)

    def _browse_output(self) -> None:
        path = filedialog.asksaveasfilename(
            initialdir=str(PROJECT_ROOT / "results"),
            title="Select output text file",
            defaultextension=".txt",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*")),
        )
        if path:
            self.output_var.set(path)

    def _resolve_path(self, value: str) -> Path:
        clean_value = value.strip().strip('"')
        if not clean_value:
            raise ValueError("Path cannot be empty")
        path = Path(clean_value).expanduser()
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path

    def _run(self) -> None:
        self.run_button.configure(state="disabled")
        self.status_var.set("Running...")
        self.root.update_idletasks()

        try:
            input_path = self._resolve_path(self.input_var.get())
            output_path = self._resolve_path(self.output_var.get())
            snr_db = float(self.snr_var.get())
            seed = int(self.seed_var.get())
            channel = self.channel_var.get().strip().lower()

            metrics = run_pipeline(
                input_path=input_path,
                output_path=output_path,
                snr_db=snr_db,
                seed=seed,
                modulation="qpsk",
                channel=channel,
            )
            self._show_metrics(metrics)
            self._show_text_match(input_path, output_path)
            self._load_plots(output_path.parent)
            if metrics.get("checksum_pass") and metrics.get("text_match_rate") == 1.0:
                self.status_var.set("Complete: recovered text matches input")
            else:
                self.status_var.set("Complete with receiver warnings")
        except Exception as exc:
            self.status_var.set("Error")
            messagebox.showerror("Simulation failed", f"{type(exc).__name__}: {exc}")
        finally:
            self.run_button.configure(state="normal")

    def _show_metrics(self, metrics: dict[str, object]) -> None:
        for field in METRIC_FIELDS:
            value = metrics.get(field, "-")
            if isinstance(value, float):
                value = f"{value:.6g}"
            self.metric_vars[field].set(str(value))

    def _show_text_match(self, input_path: Path, output_path: Path) -> None:
        try:
            input_text = input_path.read_text(encoding="utf-8")
            output_text = output_path.read_text(encoding="utf-8")
        except Exception as exc:
            self.match_var.set(f"unavailable ({type(exc).__name__})")
            return
        self.match_var.set("MATCH" if input_text == output_text else "DIFFER")

    def _load_existing_outputs(self) -> None:
        try:
            output_path = self._resolve_path(self.output_var.get())
            metrics_path = output_path.parent / "metrics.json"
            if metrics_path.exists():
                metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
                self._show_metrics(metrics)
                self._show_text_match(self._resolve_path(self.input_var.get()), output_path)
            self._load_plots(output_path.parent)
            self.status_var.set("Ready")
        except Exception as exc:
            self.status_var.set(f"Refresh failed: {type(exc).__name__}")

    def _load_plots(self, results_dir: Path) -> None:
        self.plot_images.clear()
        for title, filename in PLOT_FILES.items():
            label = self.plot_labels[title]
            path = results_dir / filename
            if not path.exists() or path.stat().st_size == 0:
                label.configure(image="", text=f"{filename} not found")
                continue
            try:
                image = tk.PhotoImage(file=str(path))
                image = self._fit_image(image, max_width=680, max_height=360)
                self.plot_images[title] = image
                label.configure(image=image, text="")
            except Exception:
                label.configure(image="", text=f"{filename} generated in results folder")

    def _fit_image(self, image: tk.PhotoImage, max_width: int, max_height: int) -> tk.PhotoImage:
        scale = max(image.width() / max_width, image.height() / max_height, 1)
        factor = max(1, int(math.ceil(scale)))
        if factor == 1:
            return image
        return image.subsample(factor, factor)

    def _open_results_folder(self) -> None:
        try:
            output_path = self._resolve_path(self.output_var.get())
            folder = output_path.parent
            folder.mkdir(parents=True, exist_ok=True)
            if hasattr(os, "startfile"):
                os.startfile(str(folder))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(["open", str(folder)], check=False)
            else:
                subprocess.run(["xdg-open", str(folder)], check=False)
        except Exception as exc:
            messagebox.showerror("Open folder failed", f"{type(exc).__name__}: {exc}")


def main() -> int:
    root = tk.Tk()
    WirelessGui(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
