import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import shutil
import sys
import ctypes
import subprocess
import time
from pathlib import Path
from datetime import datetime


# ── Constantes de diseño ────────────────────────────────────────────────────
BG          = "#0f1117"
SURFACE     = "#1a1d27"
SURFACE2    = "#22263a"
ACCENT      = "#4f8ef7"
ACCENT2     = "#3dd68c"
DANGER      = "#f7604f"
WARNING     = "#f7c94f"
TEXT        = "#e8eaf0"
TEXT_DIM    = "#6b7280"
BORDER      = "#2d3148"
FONT_TITLE  = ("Segoe UI", 22, "bold")
FONT_SUB    = ("Segoe UI", 10)
FONT_BODY   = ("Segoe UI", 10)
FONT_MONO   = ("Consolas", 9)
FONT_SMALL  = ("Segoe UI", 8)

# ── Rutas a limpiar ─────────────────────────────────────────────────────────
TEMP_PATHS = [
    os.path.expandvars(r"%LOCALAPPDATA%\Temp"),
    r"C:\Windows\Temp",
    os.path.expandvars(r"%TEMP%"),
]

LOG_PATHS = [
    r"C:\Windows\Logs",
    r"C:\Windows\inf",
]

PREFETCH_PATH = r"C:\Windows\Prefetch"


# ── Utilidades ───────────────────────────────────────────────────────────────
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def request_admin():
    """Relanza el proceso con privilegios de administrador."""
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )


def human_size(num_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(num_bytes) < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


def scan_size(path: str) -> int:
    """Calcula el tamaño total de una carpeta."""
    total = 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat().st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += scan_size(entry.path)
            except (PermissionError, OSError):
                pass
    except (PermissionError, OSError):
        pass
    return total


def delete_path(path: str) -> tuple[int, int]:
    """Elimina archivos/carpetas en path. Devuelve (eliminados, omitidos)."""
    deleted = 0
    skipped = 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_file(follow_symlinks=False) or entry.is_symlink():
                    os.unlink(entry.path)
                    deleted += 1
                elif entry.is_dir(follow_symlinks=False):
                    shutil.rmtree(entry.path, ignore_errors=False)
                    deleted += 1
            except (PermissionError, OSError):
                skipped += 1
    except (PermissionError, OSError):
        skipped += 1
    return deleted, skipped


def empty_recycle_bin() -> bool:
    try:
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x0007)
        return True
    except Exception:
        return False


def get_disk_usage(path="C:\\") -> dict:
    try:
        usage = shutil.disk_usage(path)
        return {
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "pct": usage.used / usage.total * 100,
        }
    except Exception:
        return {}


def get_large_folders(path="C:\\Users", top_n=10) -> list[tuple[str, int]]:
    results = []
    try:
        for entry in os.scandir(path):
            if entry.is_dir(follow_symlinks=False):
                size = scan_size(entry.path)
                results.append((entry.path, size))
    except (PermissionError, OSError):
        pass
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_n]


# ── Widget personalizado: Toggle Checkbox ────────────────────────────────────
class ToggleCheck(tk.Frame):
    def __init__(self, parent, text, description="", variable=None, **kwargs):
        super().__init__(parent, bg=SURFACE, **kwargs)
        self.var = variable or tk.BooleanVar(value=True)
        self._active = True

        self.configure(cursor="hand2")
        self._build(text, description)
        self.bind("<Button-1>", self._toggle)
        for child in self.winfo_children():
            child.bind("<Button-1>", self._toggle)

    def _build(self, text, description):
        # Indicador cuadrado
        self.indicator = tk.Canvas(
            self, width=20, height=20, bg=SURFACE,
            highlightthickness=0, cursor="hand2"
        )
        self.indicator.grid(row=0, column=0, rowspan=2, padx=(12, 10), pady=10, sticky="ns")
        self._draw_indicator()

        # Texto principal
        tk.Label(
            self, text=text, bg=SURFACE, fg=TEXT,
            font=("Segoe UI", 10, "bold"), anchor="w", cursor="hand2"
        ).grid(row=0, column=1, sticky="w", pady=(10, 0))

        if description:
            tk.Label(
                self, text=description, bg=SURFACE, fg=TEXT_DIM,
                font=FONT_SMALL, anchor="w", cursor="hand2"
            ).grid(row=1, column=1, sticky="w", pady=(0, 10))

        self.columnconfigure(1, weight=1)

    def _draw_indicator(self):
        self.indicator.delete("all")
        c = self.indicator
        if self.var.get():
            c.create_rectangle(1, 1, 19, 19, fill=ACCENT, outline=ACCENT, width=0)
            c.create_line(4, 10, 8, 14, fill="white", width=2.5, capstyle="round")
            c.create_line(8, 14, 16, 6, fill="white", width=2.5, capstyle="round")
        else:
            c.create_rectangle(1, 1, 19, 19, fill="", outline=BORDER, width=2)

    def _toggle(self, _=None):
        self.var.set(not self.var.get())
        self._draw_indicator()

    def get(self):
        return self.var.get()


# ── Log panel con scroll ─────────────────────────────────────────────────────
class LogPanel(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self._build()

    def _build(self):
        self.text = tk.Text(
            self, bg="#0a0c12", fg=TEXT_DIM, font=FONT_MONO,
            relief="flat", bd=0, wrap="word",
            selectbackground=ACCENT, insertbackground=ACCENT,
            padx=12, pady=10
        )
        sb = tk.Scrollbar(self, orient="vertical", command=self.text.yview,
                          bg=SURFACE, troughcolor=BG, relief="flat", bd=0, width=8)
        self.text.configure(yscrollcommand=sb.set)
        self.text.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Colores de log
        self.text.tag_config("ok",      foreground=ACCENT2)
        self.text.tag_config("warn",    foreground=WARNING)
        self.text.tag_config("err",     foreground=DANGER)
        self.text.tag_config("info",    foreground=ACCENT)
        self.text.tag_config("dim",     foreground=TEXT_DIM)
        self.text.tag_config("header",  foreground=TEXT, font=("Consolas", 9, "bold"))

    def log(self, msg: str, tag: str = "dim"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.text.configure(state="normal")
        self.text.insert("end", f"[{ts}] ", "dim")
        self.text.insert("end", msg + "\n", tag)
        self.text.see("end")
        self.text.configure(state="disabled")

    def clear(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")


# ── Barra de progreso personalizada ─────────────────────────────────────────
class FancyProgress(tk.Canvas):
    def __init__(self, parent, **kwargs):
        h = kwargs.pop("height", 6)
        super().__init__(parent, height=h, bg=SURFACE2, highlightthickness=0, **kwargs)
        self._val = 0
        self.bind("<Configure>", lambda _: self._draw())

    def set(self, val: float):  # 0.0 – 1.0
        self._val = max(0.0, min(1.0, val))
        self._draw()

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        r = h // 2
        # Track
        self.create_rectangle(0, 0, w, h, fill=SURFACE2, outline="")
        # Fill
        fw = int(w * self._val)
        if fw > 0:
            self.create_rectangle(0, 0, fw, h, fill=ACCENT, outline="")


# ── Pestaña: Limpieza ────────────────────────────────────────────────────────
class CleanTab(tk.Frame):
    def __init__(self, parent, log: LogPanel, status_cb, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self._log = log
        self._status_cb = status_cb
        self._running = False
        self._build()

    def _build(self):
        # Título sección
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=24, pady=(20, 8))
        tk.Label(hdr, text="Selecciona qué limpiar", bg=BG, fg=TEXT,
                 font=("Segoe UI", 13, "bold")).pack(side="left")

        # Opciones con checkbox
        options_frame = tk.Frame(self, bg=BG)
        options_frame.pack(fill="x", padx=24, pady=4)

        self._checks = {}

        items = [
            ("temp",     "🗂  Archivos temporales",       "Carpetas Temp de usuario y sistema"),
            ("recycle",  "🗑  Papelera de reciclaje",     "Vacía la papelera de reciclaje"),
            ("prefetch", "⚡ Prefetch de Windows",        "Archivos de precarga del sistema"),
            ("logs",     "📋 Logs del sistema",           "Registros de eventos de Windows"),
        ]

        for key, label, desc in items:
            var = tk.BooleanVar(value=True)
            card = ToggleCheck(options_frame, label, desc, variable=var)
            card.pack(fill="x", pady=3, ipady=0)
            card.configure(relief="flat", highlightthickness=1,
                           highlightbackground=BORDER)
            self._checks[key] = var

        # Separador
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, pady=16)

        # Previsualización de espacio
        prev = tk.Frame(self, bg=SURFACE, pady=14)
        prev.pack(fill="x", padx=24)
        self._space_lbl = tk.Label(prev, text="Pulsa 'Analizar' para ver el espacio recuperable",
                                   bg=SURFACE, fg=TEXT_DIM, font=FONT_BODY)
        self._space_lbl.pack()

        # Botones
        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.pack(fill="x", padx=24, pady=16)

        self._btn_scan = self._make_btn(btn_frame, "🔍  Analizar", SURFACE2, TEXT,
                                        self._scan, border=True)
        self._btn_scan.pack(side="left", padx=(0, 10))

        self._btn_clean = self._make_btn(btn_frame, "✨  Limpiar ahora", ACCENT, "white",
                                         self._clean)
        self._btn_clean.pack(side="left")

        # Progress
        self._progress = FancyProgress(self, height=6)
        self._progress.pack(fill="x", padx=24, pady=(0, 8))

    def _make_btn(self, parent, text, bg, fg, cmd, border=False):
        b = tk.Label(
            parent, text=text, bg=bg, fg=fg,
            font=("Segoe UI", 10, "bold"),
            padx=18, pady=9, cursor="hand2",
            relief="flat"
        )
        if border:
            b.configure(highlightthickness=1, highlightbackground=BORDER)
        b.bind("<Button-1>", lambda _: cmd())
        b.bind("<Enter>", lambda _: b.configure(bg=self._hover(bg)))
        b.bind("<Leave>", lambda _: b.configure(bg=bg))
        return b

    def _hover(self, color):
        # Aclara ligeramente el color
        mapping = {ACCENT: "#6ba3ff", SURFACE2: "#2d3148", BG: SURFACE}
        return mapping.get(color, color)

    def _get_selected(self):
        return {k: v.get() for k, v in self._checks.items()}

    def _scan(self):
        if self._running:
            return
        self._running = True
        self._log.clear()
        self._log.log("Iniciando análisis…", "info")
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        total = 0
        sel = self._get_selected()
        if sel["temp"]:
            for p in TEMP_PATHS:
                s = scan_size(p)
                total += s
                self._log.log(f"Temp {p}  →  {human_size(s)}", "dim")
        if sel["prefetch"] and os.path.exists(PREFETCH_PATH):
            s = scan_size(PREFETCH_PATH)
            total += s
            self._log.log(f"Prefetch  →  {human_size(s)}", "dim")
        if sel["logs"]:
            for p in LOG_PATHS:
                if os.path.exists(p):
                    s = scan_size(p)
                    total += s
                    self._log.log(f"Logs {p}  →  {human_size(s)}", "dim")

        msg = f"Espacio recuperable estimado: {human_size(total)}"
        self._space_lbl.configure(text=msg, fg=ACCENT2)
        self._log.log(msg, "ok")
        self._running = False

    def _clean(self):
        if self._running:
            return
        if not messagebox.askyesno(
            "Confirmar limpieza",
            "¿Estás seguro de que quieres limpiar los elementos seleccionados?\n"
            "Esta acción no se puede deshacer."
        ):
            return
        self._running = True
        self._log.clear()
        self._log.log("Iniciando limpieza…", "header")
        threading.Thread(target=self._clean_worker, daemon=True).start()

    def _clean_worker(self):
        sel = self._get_selected()
        steps = []
        if sel["temp"]:
            steps += [(p, "Temp") for p in TEMP_PATHS]
        if sel["prefetch"] and os.path.exists(PREFETCH_PATH):
            steps.append((PREFETCH_PATH, "Prefetch"))
        if sel["logs"]:
            steps += [(p, "Logs") for p in LOG_PATHS if os.path.exists(p)]

        total_del = 0
        total_skip = 0
        total_steps = len(steps) + (1 if sel["recycle"] else 0)
        done = 0

        for path, label in steps:
            self._log.log(f"Limpiando {label}: {path}", "info")
            d, s = delete_path(path)
            total_del += d
            total_skip += s
            self._log.log(f"  ✓ {d} eliminados  ·  {s} omitidos", "ok" if d > 0 else "warn")
            done += 1
            self._progress.set(done / total_steps)

        if sel["recycle"]:
            self._log.log("Vaciando papelera de reciclaje…", "info")
            ok = empty_recycle_bin()
            self._log.log("  ✓ Papelera vaciada" if ok else "  ✗ No se pudo vaciar la papelera",
                           "ok" if ok else "err")
            done += 1
            self._progress.set(1.0)

        self._log.log("─" * 48, "dim")
        self._log.log(f"Limpieza completada  ·  {total_del} eliminados  ·  {total_skip} omitidos", "ok")
        self._space_lbl.configure(text="Limpieza completada ✓", fg=ACCENT2)
        self._status_cb(f"Limpieza completada — {total_del} elementos eliminados")
        self._running = False


# ── Pestaña: Análisis de disco ───────────────────────────────────────────────
class DiskTab(tk.Frame):
    def __init__(self, parent, log: LogPanel, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self._log = log
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=24, pady=(20, 16))
        tk.Label(hdr, text="Análisis de disco  C:\\", bg=BG, fg=TEXT,
                 font=("Segoe UI", 13, "bold")).pack(side="left")

        # Tarjeta de uso
        self._disk_card = tk.Frame(self, bg=SURFACE, pady=20)
        self._disk_card.pack(fill="x", padx=24, pady=(0, 16))
        tk.Label(self._disk_card, text="Pulsa 'Analizar disco' para cargar datos",
                 bg=SURFACE, fg=TEXT_DIM, font=FONT_BODY).pack()

        # Lista de carpetas grandes
        list_frame = tk.Frame(self, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        tk.Label(list_frame, text="Carpetas más grandes en C:\\Users",
                 bg=BG, fg=TEXT_DIM, font=FONT_SMALL).pack(anchor="w", pady=(0, 6))

        # Treeview estilizado
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview",
                         background=SURFACE, foreground=TEXT,
                         fieldbackground=SURFACE, borderwidth=0,
                         rowheight=28, font=FONT_BODY)
        style.configure("Custom.Treeview.Heading",
                         background=SURFACE2, foreground=TEXT_DIM,
                         font=("Segoe UI", 9, "bold"), borderwidth=0)
        style.map("Custom.Treeview", background=[("selected", ACCENT)])

        self._tree = ttk.Treeview(
            list_frame, columns=("path", "size"), show="headings",
            style="Custom.Treeview", height=8
        )
        self._tree.heading("path", text="Ruta")
        self._tree.heading("size", text="Tamaño")
        self._tree.column("path", width=380, anchor="w")
        self._tree.column("size", width=100, anchor="e")
        self._tree.pack(fill="both", expand=True)

        # Botón
        btn = tk.Label(self, text="🔍  Analizar disco", bg=ACCENT, fg="white",
                        font=("Segoe UI", 10, "bold"), padx=18, pady=9,
                        cursor="hand2", relief="flat")
        btn.pack(pady=(0, 20))
        btn.bind("<Button-1>", lambda _: self._analyze())
        btn.bind("<Enter>", lambda _: btn.configure(bg="#6ba3ff"))
        btn.bind("<Leave>", lambda _: btn.configure(bg=ACCENT))

    def _analyze(self):
        self._log.clear()
        self._log.log("Analizando disco C:\\ …", "info")
        threading.Thread(target=self._analyze_worker, daemon=True).start()

    def _analyze_worker(self):
        # Uso general
        usage = get_disk_usage("C:\\")
        if usage:
            pct = usage["pct"]
            self._update_disk_card(usage)
            self._log.log(
                f"Disco C:\\  Total {human_size(usage['total'])}  "
                f"Usado {human_size(usage['used'])} ({pct:.1f}%)  "
                f"Libre {human_size(usage['free'])}", "ok"
            )

        # Carpetas grandes
        self._log.log("Escaneando carpetas en C:\\Users …", "info")
        folders = get_large_folders("C:\\Users", top_n=10)
        self._tree.delete(*self._tree.get_children())
        for path, size in folders:
            self._tree.insert("", "end", values=(path, human_size(size)))
            self._log.log(f"  {path}  →  {human_size(size)}", "dim")
        self._log.log("Análisis completado.", "ok")

    def _update_disk_card(self, usage):
        for w in self._disk_card.winfo_children():
            w.destroy()
        pct = usage["pct"]

        # Barra de uso
        bar_bg = tk.Canvas(self._disk_card, height=12, bg=SURFACE,
                            highlightthickness=0)
        bar_bg.pack(fill="x", padx=24, pady=(8, 4))

        def draw_bar(e=None):
            bar_bg.delete("all")
            w = bar_bg.winfo_width()
            h = 12
            color = DANGER if pct > 85 else WARNING if pct > 65 else ACCENT2
            bar_bg.create_rectangle(0, 0, w, h, fill=SURFACE2, outline="")
            bar_bg.create_rectangle(0, 0, int(w * pct / 100), h, fill=color, outline="")

        bar_bg.bind("<Configure>", draw_bar)

        row = tk.Frame(self._disk_card, bg=SURFACE)
        row.pack(fill="x", padx=24, pady=(4, 8))
        tk.Label(row, text=f"Usado: {human_size(usage['used'])} ({pct:.1f}%)",
                 bg=SURFACE, fg=TEXT, font=FONT_BODY).pack(side="left")
        tk.Label(row, text=f"Libre: {human_size(usage['free'])}",
                 bg=SURFACE, fg=ACCENT2, font=FONT_BODY).pack(side="right")


# ── Ventana principal ────────────────────────────────────────────────────────
class WinCleaner(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WinCleaner")
        self.geometry("740x640")
        self.minsize(680, 560)
        self.configure(bg=BG)
        self.resizable(True, True)
        self._center()
        self._build_ui()

    def _center(self):
        self.update_idletasks()
        w, h = 740, 640
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=SURFACE, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="⚡", bg=SURFACE, fg=ACCENT,
                 font=("Segoe UI", 18)).pack(side="left", padx=(20, 6), pady=16)
        tk.Label(header, text="WinCleaner", bg=SURFACE, fg=TEXT,
                 font=("Segoe UI", 16, "bold")).pack(side="left", pady=16)
        tk.Label(header, text="v1.0", bg=SURFACE, fg=TEXT_DIM,
                 font=("Segoe UI", 9)).pack(side="left", padx=8, pady=20)

        # Admin badge
        admin = is_admin()
        badge_color = ACCENT2 if admin else DANGER
        badge_text = "✓ Admin" if admin else "✗ Sin admin"
        tk.Label(header, text=badge_text, bg=badge_color, fg="white",
                 font=("Segoe UI", 8, "bold"), padx=8, pady=3).pack(
            side="right", padx=20, pady=20)

        # ── Navegación lateral ───────────────────────────────────────────────
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True)

        sidebar = tk.Frame(main, bg=SURFACE, width=160)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        self._content = tk.Frame(main, bg=BG)
        self._content.pack(side="left", fill="both", expand=True)

        # Log panel (parte inferior)
        log_frame = tk.Frame(self, bg=BG)
        log_frame.pack(fill="x", side="bottom")
        tk.Frame(log_frame, bg=BORDER, height=1).pack(fill="x")
        self._log = LogPanel(log_frame, height=140)
        self._log.pack(fill="x")

        # Tabs content
        self._tabs = {}
        self._tabs["clean"] = CleanTab(self._content, self._log, self._set_status)
        self._tabs["disk"]  = DiskTab(self._content, self._log)

        # Botones sidebar
        self._nav_btns = {}
        nav_items = [
            ("clean", "🧹  Limpiar"),
            ("disk",  "💾  Disco"),
        ]
        tk.Frame(sidebar, bg=SURFACE, height=16).pack()
        for key, label in nav_items:
            b = tk.Label(sidebar, text=label, bg=SURFACE, fg=TEXT_DIM,
                          font=("Segoe UI", 10), anchor="w", padx=18, pady=12,
                          cursor="hand2")
            b.pack(fill="x")
            b.bind("<Button-1>", lambda _, k=key: self._switch_tab(k))
            b.bind("<Enter>", lambda _, btn=b: btn.configure(
                bg=SURFACE2 if btn.cget("fg") == str(TEXT_DIM) else SURFACE2))
            b.bind("<Leave>", lambda _, btn=b: btn.configure(
                bg=SURFACE if btn.cget("fg") == str(TEXT_DIM) else SURFACE2))
            self._nav_btns[key] = b

        # Status bar
        self._status_var = tk.StringVar(value="Listo")
        status_bar = tk.Frame(self, bg=SURFACE2, height=24)
        status_bar.pack(fill="x", side="bottom")
        tk.Label(status_bar, textvariable=self._status_var, bg=SURFACE2,
                  fg=TEXT_DIM, font=FONT_SMALL, anchor="w", padx=12).pack(fill="x")

        self._switch_tab("clean")

    def _switch_tab(self, key: str):
        for k, frame in self._tabs.items():
            frame.pack_forget()
            self._nav_btns[k].configure(fg=TEXT_DIM, bg=SURFACE)

        self._tabs[key].pack(fill="both", expand=True)
        self._nav_btns[key].configure(fg=TEXT, bg=SURFACE2)

    def _set_status(self, msg: str):
        self._status_var.set(msg)


# ── Entrada principal ────────────────────────────────────────────────────────
if __name__ == "__main__":
    # En Windows, pedir admin si no lo tenemos
    if sys.platform == "win32" and not is_admin():
        respuesta = messagebox.askyesno(
            "WinCleaner — Privilegios requeridos",
            "WinCleaner necesita privilegios de administrador para limpiar "
            "archivos del sistema.\n\n¿Deseas relanzar como administrador?"
        )
        if respuesta:
            request_admin()
            sys.exit()

    app = WinCleaner()
    app.mainloop()
