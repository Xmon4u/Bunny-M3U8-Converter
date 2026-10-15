"""Desktop window for the Bunny → M3U8 converter."""

from __future__ import annotations

import queue
import sys
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from bunny_m3u8 import Result, convert_job, parse_inputs

WAITING = "Waiting…"

BG = "#070b14"
CARD = "#101828"
CARD_BORDER = "#1e293b"
INPUT_BG = "#0b1220"
ROW = "#0d1526"
ROW_BORDER = "#243049"
TEXT = "#e8eef9"
MUTED = "#93a0b8"
ACCENT = "#ff7a45"
ACCENT_HOVER = "#ff9468"
OK = "#3dd68c"
OK_SOFT = "#b7f3d4"
BAD = "#ff8fa3"
GHOST = "#1a2438"
GHOST_HOVER = "#243049"


def _asset(name: str) -> Path:
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base = Path(__file__).resolve().parent
    return base / "assets" / name


class ResultRow(ctk.CTkFrame):
    def __init__(self, master, index: int, source: str, on_copy) -> None:
        super().__init__(
            master,
            fg_color=ROW,
            corner_radius=12,
            border_width=1,
            border_color=ROW_BORDER,
        )
        self._on_copy = on_copy
        self._m3u8 = ""
        self.grid_columnconfigure(1, weight=1)

        self.badge = ctk.CTkLabel(
            self,
            text=str(index),
            width=32,
            font=("Segoe UI", 13, "bold"),
            text_color=MUTED,
        )
        self.badge.grid(row=0, column=0, rowspan=2, padx=(10, 4), pady=10, sticky="n")

        self.title = ctk.CTkLabel(
            self,
            text=source,
            font=("Segoe UI", 13, "bold"),
            text_color=TEXT,
            anchor="w",
            justify="left",
        )
        self.title.grid(row=0, column=1, padx=(4, 8), pady=(10, 0), sticky="ew")

        self.detail = ctk.CTkLabel(
            self,
            text=WAITING,
            font=("Segoe UI", 12),
            text_color=MUTED,
            anchor="w",
            justify="left",
        )
        self.detail.grid(row=1, column=1, padx=(4, 8), pady=(2, 10), sticky="ew")

        self.copy_btn = ctk.CTkButton(
            self,
            text="Copy",
            width=68,
            height=28,
            corner_radius=8,
            font=("Segoe UI", 12, "bold"),
            fg_color=GHOST,
            hover_color=GHOST_HOVER,
            text_color=TEXT,
            state="disabled",
            command=self._copy,
        )
        self.copy_btn.grid(row=0, column=2, rowspan=2, padx=(0, 10), pady=10)

        self.bind("<Configure>", self._reflow)

    def _reflow(self, event) -> None:
        self.title.configure(wraplength=max(180, event.width - 130))
        self.detail.configure(wraplength=max(180, event.width - 130))

    def _copy(self) -> None:
        if self._m3u8:
            self._on_copy(self._m3u8)

    def show(self, result: Result) -> None:
        if result.ok:
            self.configure(border_color="#14532d")
            self.badge.configure(text="✓", text_color=OK)
            self.title.configure(text=result.title or "Converted", text_color=TEXT)
            self.detail.configure(text=result.m3u8, text_color=OK_SOFT, font=("Consolas", 12))
            self._m3u8 = result.m3u8
            self.copy_btn.configure(state="normal", fg_color="#143026", hover_color="#1c4334", text_color=OK)
            return
        self.configure(border_color="#4c1d2a")
        self.badge.configure(text="!", text_color=BAD)
        self.title.configure(text=result.source, text_color=TEXT)
        self.detail.configure(text=result.error, text_color=BAD, font=("Segoe UI", 12))
        self.copy_btn.configure(state="disabled", fg_color=GHOST, text_color=MUTED)


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__(fg_color=BG)
        self.title("Bunny → M3U8")
        self.minsize(920, 620)
        self._center(1080, 720)
        self._apply_icon()

        self._queue: queue.Queue = queue.Queue()
        self._cancel = threading.Event()
        self._running = False
        self._gen = 0
        self._results: list[Result] = []
        self._rows: list[ResultRow] = []

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_header()
        self._build_body()
        self._build_footer()
        self.bind("<Control-Return>", lambda _e: self.on_primary())

    def _center(self, width: int, height: int) -> None:
        self.update_idletasks()
        x = max(0, (self.winfo_screenwidth() - width) // 2)
        y = max(0, (self.winfo_screenheight() - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _apply_icon(self) -> None:
        icon = _asset("app.ico")
        if not icon.exists():
            return
        try:
            self.iconbitmap(default=str(icon))
        except Exception:
            pass

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 8))

        logo = ctk.CTkFrame(header, width=48, height=48, corner_radius=14, fg_color=ACCENT)
        logo.pack(side="left")
        logo.pack_propagate(False)
        ctk.CTkLabel(
            logo,
            text="▶",
            font=("Segoe UI", 18),
            text_color="#1a0d07",
        ).place(relx=0.56, rely=0.5, anchor="center")

        words = ctk.CTkFrame(header, fg_color="transparent")
        words.pack(side="left", padx=(14, 0), fill="x", expand=True)
        ctk.CTkLabel(
            words,
            text="Bunny → M3U8",
            font=("Segoe UI", 24, "bold"),
            text_color=TEXT,
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            words,
            text="Paste play links or embed code — as many as you want",
            font=("Segoe UI", 13),
            text_color=MUTED,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(
            header,
            text="v2",
            width=42,
            height=26,
            corner_radius=13,
            fg_color=GHOST,
            text_color=MUTED,
            font=("Segoe UI", 12, "bold"),
        ).pack(side="right")

    def _card(self, parent) -> tuple[ctk.CTkFrame, ctk.CTkFrame]:
        card = ctk.CTkFrame(
            parent,
            fg_color=CARD,
            corner_radius=18,
            border_width=1,
            border_color=CARD_BORDER,
        )
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(14, 8))
        return card, top

    def _build_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=22, pady=6)
        body.grid_columnconfigure(0, weight=5, uniform="col")
        body.grid_columnconfigure(1, weight=6, uniform="col")
        body.grid_rowconfigure(0, weight=1)

        left, left_top = self._card(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(
            left_top,
            text="Links",
            font=("Segoe UI", 15, "bold"),
            text_color=TEXT,
        ).pack(side="left")
        ctk.CTkButton(
            left_top,
            text="Paste",
            width=72,
            height=28,
            corner_radius=8,
            font=("Segoe UI", 12, "bold"),
            fg_color=GHOST,
            hover_color=GHOST_HOVER,
            text_color=TEXT,
            command=self.on_paste,
        ).pack(side="right")
        ctk.CTkLabel(
            left_top,
            text="One link per line",
            font=("Segoe UI", 12),
            text_color=MUTED,
        ).pack(side="right", padx=(0, 10))

        ctk.CTkLabel(
            left,
            text="Play link, embed code, token link, or a playlist.m3u8",
            font=("Segoe UI", 12),
            text_color=MUTED,
            anchor="w",
        ).pack(side="bottom", padx=16, pady=(0, 12), anchor="w")

        self.input_box = ctk.CTkTextbox(
            left,
            font=("Consolas", 13),
            fg_color=INPUT_BG,
            text_color=TEXT,
            border_width=0,
            corner_radius=12,
            wrap="word",
        )
        self.input_box.pack(fill="both", expand=True, padx=14, pady=(0, 8))
        self.input_box.focus_set()

        right, right_top = self._card(body)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ctk.CTkLabel(
            right_top,
            text="Results",
            font=("Segoe UI", 15, "bold"),
            text_color=TEXT,
        ).pack(side="left")
        self.count_label = ctk.CTkLabel(
            right_top,
            text="Nothing yet",
            font=("Segoe UI", 12),
            text_color=MUTED,
        )
        self.count_label.pack(side="right")

        self.results = ctk.CTkScrollableFrame(
            right,
            fg_color="transparent",
            corner_radius=0,
        )
        self.results.pack(fill="both", expand=True, padx=8, pady=(0, 10))
        self.empty = ctk.CTkLabel(
            self.results,
            text="Converted playlists show up here.\nFailed links stay listed — the rest still convert.",
            font=("Segoe UI", 13),
            text_color=MUTED,
            justify="left",
        )
        self.empty.pack(anchor="w", padx=10, pady=12)

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=22, pady=(8, 16))
        footer.grid_columnconfigure(1, weight=1)

        actions = ctk.CTkFrame(footer, fg_color="transparent")
        actions.grid(row=0, column=0, sticky="w")

        self.primary = ctk.CTkButton(
            actions,
            text="Convert",
            width=160,
            height=42,
            corner_radius=12,
            font=("Segoe UI", 15, "bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#1a0d07",
            command=self.on_primary,
        )
        self.primary.pack(side="left")

        for label, command in (
            ("Copy all", self.on_copy_all),
            ("Save", self.on_save),
            ("Clear", self.on_clear),
        ):
            ctk.CTkButton(
                actions,
                text=label,
                width=110,
                height=42,
                corner_radius=12,
                font=("Segoe UI", 14, "bold"),
                fg_color=GHOST,
                hover_color=GHOST_HOVER,
                text_color=TEXT,
                command=command,
            ).pack(side="left", padx=(8, 0))

        self.status = ctk.CTkLabel(
            footer,
            text="Ready",
            font=("Segoe UI", 13),
            text_color=MUTED,
            anchor="e",
        )
        self.status.grid(row=0, column=1, sticky="e", padx=(16, 0))

        self.progress = ctk.CTkProgressBar(
            footer,
            height=5,
            corner_radius=3,
            fg_color="#182033",
            progress_color=ACCENT,
        )
        self.progress.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        self.progress.set(0)

    def _set_status(self, text: str, color: str = MUTED) -> None:
        self.status.configure(text=text, text_color=color)

    def _copy_text(self, text: str, notice: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        self._set_status(notice, OK)

    def on_paste(self) -> None:
        try:
            text = self.clipboard_get()
        except Exception:
            self._set_status("Clipboard is empty", BAD)
            return
        if self.input_box.get("1.0", "end").strip():
            self.input_box.insert("end", "\n")
        self.input_box.insert("end", text.strip())
        self._set_status("Pasted")

    def on_clear(self) -> None:
        if self._running:
            return
        self.input_box.delete("1.0", "end")
        self._reset_results()
        self.progress.set(0)
        self._set_status("Cleared")

    def _reset_results(self) -> None:
        for child in self.results.winfo_children():
            child.destroy()
        self._rows = []
        self._results = []
        self.empty = ctk.CTkLabel(
            self.results,
            text="Converted playlists show up here.\nFailed links stay listed — the rest still convert.",
            font=("Segoe UI", 13),
            text_color=MUTED,
            justify="left",
        )
        self.empty.pack(anchor="w", padx=10, pady=12)
        self.count_label.configure(text="Nothing yet", text_color=MUTED)

    def on_copy_all(self) -> None:
        urls = [item.m3u8 for item in self._results if item.ok and item.m3u8]
        if not urls:
            self._set_status("No successful links to copy", BAD)
            return
        self._copy_text("\n".join(urls), f"Copied {len(urls)} link(s)")

    def on_save(self) -> None:
        urls = [item.m3u8 for item in self._results if item.ok and item.m3u8]
        failed = [item for item in self._results if not item.ok]
        if not urls and not failed:
            self._set_status("Nothing to save", BAD)
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Save results",
            defaultextension=".txt",
            initialfile="bunny-m3u8.txt",
            filetypes=[("Text", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        lines = list(urls)
        if failed:
            lines.append("")
            lines.append("# Failed")
            lines.extend(f"# {item.source} — {item.error}" for item in failed)
        Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
        self._set_status("Saved to file", OK)

    def on_primary(self) -> None:
        if self._running:
            self._cancel.set()
            self.primary.configure(text="Cancelling…")
            self._set_status("Cancelling the rest")
            return
        self._start()

    def _start(self) -> None:
        jobs = parse_inputs(self.input_box.get("1.0", "end"))
        if not jobs:
            self._set_status("Paste a Bunny link first", BAD)
            return

        self._gen += 1
        gen = self._gen
        self._running = True
        self._cancel.clear()
        self.primary.configure(text="Cancel", fg_color="#9f1239", hover_color="#be123c", text_color="white")
        self.progress.set(0)

        for child in self.results.winfo_children():
            child.destroy()
        self._rows = []
        self._results = [
            Result(ok=False, source=job.display, error=WAITING) for job in jobs
        ]
        for index, job in enumerate(jobs, start=1):
            row = ResultRow(self.results, index, job.display, self._copy_text_quiet)
            row.pack(fill="x", pady=4, padx=4)
            self._rows.append(row)
        self._refresh_count()
        self._set_status(f"Converting… 0/{len(jobs)}")

        thread = threading.Thread(
            target=self._worker,
            args=(jobs, gen),
            daemon=True,
        )
        thread.start()
        self.after(80, lambda: self._poll(gen))

    def _copy_text_quiet(self, text: str) -> None:
        self._copy_text(text, "Link copied")

    def _worker(self, jobs, gen: int) -> None:
        from concurrent.futures import ThreadPoolExecutor

        pool = ThreadPoolExecutor(max_workers=4)
        futures = [pool.submit(convert_job, job) for job in jobs]
        try:
            for index, future in enumerate(futures):
                if self._cancel.is_set() or gen != self._gen:
                    break
                try:
                    result = future.result()
                except Exception as err:  # noqa: BLE001
                    result = Result(
                        ok=False,
                        source=jobs[index].display,
                        error=f"Unexpected error: {err}",
                    )
                self._queue.put((gen, index, result))
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
            self._queue.put((gen, None, None))

    def _poll(self, gen: int) -> None:
        if gen != self._gen:
            return
        updated = False
        while True:
            try:
                item_gen, index, result = self._queue.get_nowait()
            except queue.Empty:
                break
            if item_gen != gen:
                continue
            if index is None:
                self._finish(gen)
                return
            self._results[index] = result
            self._rows[index].show(result)
            updated = True
        if updated:
            done = sum(1 for item in self._results if item.error != WAITING)
            total = len(self._results)
            self.progress.set(done / total if total else 0)
            self._refresh_count()
            self._set_status(f"Converting… {done}/{total}")
        if self._running:
            self.after(80, lambda: self._poll(gen))

    def _finish(self, gen: int) -> None:
        if gen != self._gen:
            return
        if self._cancel.is_set():
            for index, item in enumerate(self._results):
                if item.error == WAITING:
                    cancelled = Result(ok=False, source=item.source, error="Cancelled")
                    self._results[index] = cancelled
                    self._rows[index].show(cancelled)
        self._running = False
        self.primary.configure(
            text="Convert",
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#1a0d07",
        )
        ok = sum(1 for item in self._results if item.ok)
        bad = len(self._results) - ok
        self.progress.set(1 if self._results else 0)
        self._refresh_count()
        if bad and ok:
            self._set_status(f"Done — {ok} succeeded, {bad} failed", "#fbbf24")
        elif bad:
            self._set_status(f"Done — {bad} failed", BAD)
        else:
            self._set_status(f"Done — {ok} link(s) ready", OK)

    def _refresh_count(self) -> None:
        if not self._results:
            self.count_label.configure(text="Nothing yet", text_color=MUTED)
            return
        ok = sum(1 for item in self._results if item.ok)
        bad = sum(1 for item in self._results if not item.ok and item.error != WAITING)
        waiting = len(self._results) - ok - bad
        parts = [f"{ok} succeeded"]
        if bad:
            parts.append(f"{bad} failed")
        if waiting:
            parts.append(f"{waiting} left")
        color = OK if ok and not bad and not waiting else TEXT
        self.count_label.configure(text=" · ".join(parts), text_color=color)


def launch() -> int:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = App()
    app.mainloop()
    return 0
