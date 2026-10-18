import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Callable, Optional, Dict, Tuple
from core.audio_manager import AudioDevice

DARK_BG = "#202024"
DARK_CARD = "#2A2A30"
ACCENT_COLOR = "#0078D4"
ACCENT_HOVER = "#1E90FF"
TEXT_WHITE = "#FFFFFF"
TEXT_MUTED = "#CCCCCC"
BORDER_COLOR = "#3E3E46"


def set_window_center(win: tk.Toplevel, width: int, height: int):
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw - width) // 2
    y = (sh - height) // 2
    win.geometry(f"{width}x{height}+{x}+{y}")


class DeviceSelectionDialog:
    """Dialog allowing user to choose which audio devices participate in the hotkey cycle."""

    def __init__(
        self,
        active_devices: List[AudioDevice],
        selected_ids: List[str],
        on_save: Callable[[List[str]], None]
    ):
        self.active_devices = active_devices
        self.selected_ids = set(selected_ids)
        self.on_save = on_save

        self.root = tk.Tk()
        self.root.withdraw()

        self.win = tk.Toplevel(self.root)
        self.win.title("Döngüye Dahil Edilecek Ses Aygıtları")
        self.win.configure(bg=DARK_BG)
        self.win.attributes("-topmost", True)
        self.win.resizable(False, False)

        self.vars: Dict[str, tk.BooleanVar] = {}
        self.tip_label: Optional[tk.Label] = None

        self._build_ui()
        set_window_center(self.win, 480, 420)
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        self.win.mainloop()

    def _build_ui(self):
        # Header
        header = tk.Frame(self.win, bg=DARK_BG, padx=20, pady=14)
        header.pack(fill="x")

        title = tk.Label(
            header,
            text="🎧 Ses Çıkış Aygıtı Seçimi",
            font=("Segoe UI", 12, "bold"),
            fg=TEXT_WHITE,
            bg=DARK_BG
        )
        title.pack(anchor="w")

        desc = tk.Label(
            header,
            text="Kısayol tuşuna bastığınızda yalnızca seçili aygıtlar arasında geçiş yapılır.\n2 aygıt seçilirse otomatik olarak A/B iki yönlü geçiş modu çalışır.",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=DARK_BG,
            justify="left"
        )
        desc.pack(anchor="w", pady=(4, 0))

        # Device List Frame (Scrollable)
        list_container = tk.Frame(self.win, bg=DARK_CARD, padx=10, pady=10)
        list_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        canvas = tk.Canvas(list_container, bg=DARK_CARD, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=DARK_CARD)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        if len(self.active_devices) > 4:
            scrollbar.pack(side="right", fill="y")

        # Populate devices
        for dev in self.active_devices:
            # If no saved IDs previously, default to all checked
            is_checked = (dev.id in self.selected_ids) if self.selected_ids else True
            var = tk.BooleanVar(value=is_checked)
            self.vars[dev.id] = var

            row = tk.Frame(scrollable_frame, bg=DARK_CARD, pady=4)
            row.pack(fill="x", anchor="w")

            status_icon = "✓ (Varsayılan)" if dev.is_default else ""
            chk = tk.Checkbutton(
                row,
                text=f"{dev.name} {status_icon}".strip(),
                variable=var,
                command=self._update_tip,
                font=("Segoe UI", 10),
                fg=TEXT_WHITE,
                bg=DARK_CARD,
                selectcolor="#1C1C20",
                activebackground=DARK_CARD,
                activeforeground=TEXT_WHITE,
                highlightthickness=0,
                bd=0
            )
            chk.pack(anchor="w")

        # Tip / Status badge
        self.tip_label = tk.Label(
            self.win,
            text="",
            font=("Segoe UI", 9, "italic"),
            fg="#4CC2FF",
            bg=DARK_BG
        )
        self.tip_label.pack(fill="x", padx=20, pady=(0, 10))
        self._update_tip()

        # Action Buttons
        btn_frame = tk.Frame(self.win, bg=DARK_BG, padx=20, pady=14)
        btn_frame.pack(fill="x", side="bottom")

        btn_select_all = tk.Button(
            btn_frame,
            text="Tümünü Seç",
            command=self._select_all,
            font=("Segoe UI", 9),
            bg="#3E3E46",
            fg=TEXT_WHITE,
            activebackground="#50505A",
            activeforeground=TEXT_WHITE,
            relief="flat",
            padx=10,
            pady=4
        )
        btn_select_all.pack(side="left")

        btn_save = tk.Button(
            btn_frame,
            text="Kaydet",
            command=self._save,
            font=("Segoe UI", 9, "bold"),
            bg=ACCENT_COLOR,
            fg=TEXT_WHITE,
            activebackground=ACCENT_HOVER,
            activeforeground=TEXT_WHITE,
            relief="flat",
            padx=18,
            pady=4
        )
        btn_save.pack(side="right")

        btn_cancel = tk.Button(
            btn_frame,
            text="İptal",
            command=self._on_close,
            font=("Segoe UI", 9),
            bg="#3E3E46",
            fg=TEXT_WHITE,
            activebackground="#50505A",
            activeforeground=TEXT_WHITE,
            relief="flat",
            padx=12,
            pady=4
        )
        btn_cancel.pack(side="right", padx=(0, 8))

    def _select_all(self):
        for var in self.vars.values():
            var.set(True)
        self._update_tip()

    def _update_tip(self):
        checked_count = sum(1 for v in self.vars.values() if v.get())
        if checked_count == 2:
            self.tip_label.config(text="⚡ 2 aygıt seçildi: A / B hızlı geçiş modu aktif.")
        elif checked_count > 2:
            self.tip_label.config(text=f"🔄 {checked_count} aygıt seçildi: Sıralı döngü modu aktif.")
        elif checked_count == 1:
            self.tip_label.config(text="⚠️ Yalnızca 1 aygıt seçildi. Geçiş için en az 2 aygıt önerilir.")
        else:
            self.tip_label.config(text="⚠️ Hiçbir aygıt seçilmedi. Tüm aktif aygıtlar döngüye alınacak.")

    def _save(self):
        selected = [did for did, var in self.vars.items() if var.get()]
        self.on_save(selected)
        self._on_close()

    def _on_close(self):
        try:
            self.win.destroy()
            self.root.destroy()
        except Exception:
            pass


class HotkeyConfigDialog:
    """Dialog allowing user to configure the global shortcut key combination."""

    def __init__(
        self,
        current_modifiers: List[str],
        current_key: str,
        on_save: Callable[[List[str], str], None]
    ):
        self.current_modifiers = [m.lower() for m in current_modifiers]
        self.current_key = current_key.upper()
        self.on_save = on_save

        self.root = tk.Tk()
        self.root.withdraw()

        self.win = tk.Toplevel(self.root)
        self.win.title("Global Kısayol Tuşu Belirle")
        self.win.configure(bg=DARK_BG)
        self.win.attributes("-topmost", True)
        self.win.resizable(False, False)

        self.ctrl_var = tk.BooleanVar(value="ctrl" in self.current_modifiers)
        self.shift_var = tk.BooleanVar(value="shift" in self.current_modifiers)
        self.alt_var = tk.BooleanVar(value="alt" in self.current_modifiers)
        self.win_var = tk.BooleanVar(value="win" in self.current_modifiers)
        self.key_var = tk.StringVar(value=self.current_key)
        self.preview_label: Optional[tk.Label] = None

        self._build_ui()
        set_window_center(self.win, 420, 360)
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        self.win.mainloop()

    def _build_ui(self):
        header = tk.Frame(self.win, bg=DARK_BG, padx=20, pady=16)
        header.pack(fill="x")

        title = tk.Label(
            header,
            text="⌨️ Kısayol Tuşu Yapılandırması",
            font=("Segoe UI", 12, "bold"),
            fg=TEXT_WHITE,
            bg=DARK_BG
        )
        title.pack(anchor="w")

        desc = tk.Label(
            header,
            text="Ses çıkışını değiştirmek için kullanılacak global kısayolu belirleyin:",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=DARK_BG
        )
        desc.pack(anchor="w", pady=(4, 0))

        # Modifiers Box
        mod_box = tk.LabelFrame(
            self.win,
            text=" Değiştirici Tuşlar (Modifiers) ",
            font=("Segoe UI", 9, "bold"),
            fg=TEXT_MUTED,
            bg=DARK_CARD,
            padx=14,
            pady=10
        )
        mod_box.pack(fill="x", padx=20, pady=(0, 10))

        checks_frame = tk.Frame(mod_box, bg=DARK_CARD)
        checks_frame.pack(fill="x")

        for label_text, var in [
            ("Ctrl", self.ctrl_var),
            ("Shift", self.shift_var),
            ("Alt", self.alt_var),
            ("Win", self.win_var)
        ]:
            chk = tk.Checkbutton(
                checks_frame,
                text=label_text,
                variable=var,
                command=self._update_preview,
                font=("Segoe UI", 10),
                fg=TEXT_WHITE,
                bg=DARK_CARD,
                selectcolor="#1C1C20",
                activebackground=DARK_CARD,
                activeforeground=TEXT_WHITE,
                highlightthickness=0,
                bd=0
            )
            chk.pack(side="left", padx=(0, 14))

        # Main Key Box
        key_box = tk.LabelFrame(
            self.win,
            text=" Ana Tuş ",
            font=("Segoe UI", 9, "bold"),
            fg=TEXT_MUTED,
            bg=DARK_CARD,
            padx=14,
            pady=10
        )
        key_box.pack(fill="x", padx=20, pady=(0, 10))

        key_options = [f"F{i}" for i in range(1, 13)] + [
            "Space", "Tab", "Insert", "Delete", "Home", "End", "PageUp", "PageDown"
        ] + [chr(c) for c in range(ord('A'), ord('Z')+1)] + [str(i) for i in range(10)]

        cb = ttk.Combobox(
            key_box,
            textvariable=self.key_var,
            values=key_options,
            state="readonly",
            font=("Segoe UI", 10),
            width=15
        )
        cb.pack(anchor="w")
        cb.bind("<<ComboboxSelected>>", lambda e: self._update_preview())

        # Live Preview
        preview_frame = tk.Frame(self.win, bg=DARK_BG, padx=20)
        preview_frame.pack(fill="x", pady=6)

        self.preview_label = tk.Label(
            preview_frame,
            text="",
            font=("Segoe UI", 11, "bold"),
            fg="#4CC2FF",
            bg=DARK_BG
        )
        self.preview_label.pack(anchor="w")
        self._update_preview()

        # Action Buttons
        btn_frame = tk.Frame(self.win, bg=DARK_BG, padx=20, pady=16)
        btn_frame.pack(fill="x", side="bottom")

        btn_save = tk.Button(
            btn_frame,
            text="Kaydet",
            command=self._save,
            font=("Segoe UI", 9, "bold"),
            bg=ACCENT_COLOR,
            fg=TEXT_WHITE,
            activebackground=ACCENT_HOVER,
            activeforeground=TEXT_WHITE,
            relief="flat",
            padx=18,
            pady=4
        )
        btn_save.pack(side="right")

        btn_cancel = tk.Button(
            btn_frame,
            text="İptal",
            command=self._on_close,
            font=("Segoe UI", 9),
            bg="#3E3E46",
            fg=TEXT_WHITE,
            activebackground="#50505A",
            activeforeground=TEXT_WHITE,
            relief="flat",
            padx=12,
            pady=4
        )
        btn_cancel.pack(side="right", padx=(0, 8))

    def _get_current_combination(self) -> Tuple[List[str], str]:
        mods = []
        if self.ctrl_var.get():
            mods.append("Ctrl")
        if self.shift_var.get():
            mods.append("Shift")
        if self.alt_var.get():
            mods.append("Alt")
        if self.win_var.get():
            mods.append("Win")
        k = self.key_var.get().strip()
        return mods, k

    def _update_preview(self):
        mods, k = self._get_current_combination()
        parts = list(mods)
        if k:
            parts.append(k)
        text = " + ".join(parts) if parts else "(Seçim Yapılmadı)"
        self.preview_label.config(text=f"Önizleme: {text}")

    def _save(self):
        mods, k = self._get_current_combination()
        if not mods and not k:
            messagebox.showwarning("Geçersiz Kısayol", "Lütfen en az bir değiştirici veya tuş belirleyin.")
            return
        self.on_save(mods, k)
        self._on_close()

    def _on_close(self):
        try:
            self.win.destroy()
            self.root.destroy()
        except Exception:
            pass
