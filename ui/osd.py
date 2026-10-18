import ctypes
from ctypes import wintypes
import queue
import threading
import tkinter as tk
from typing import Optional

user32 = ctypes.windll.user32

# Win32 Window Styles
GWL_EXSTYLE = -20
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080


class OSDWindow:
    """Manages the visual OSD notification window in a dedicated UI thread."""

    def __init__(self, duration_ms: int = 1500):
        self.duration_ms = duration_ms
        self.msg_queue: queue.Queue = queue.Queue()
        self.root: Optional[tk.Tk] = None
        self.device_label: Optional[tk.Label] = None
        self.badge_label: Optional[tk.Label] = None
        self.close_timer = None
        self._thread: Optional[threading.Thread] = None
        self._ready_event = threading.Event()

    def start(self):
        """Starts the OSD event loop in a background thread."""
        self._thread = threading.Thread(target=self._run, daemon=True, name="OSDThread")
        self._thread.start()
        self._ready_event.wait()

    def _apply_no_focus_style(self):
        """Ensures the window never steals focus from games or active apps."""
        try:
            hwnd = user32.GetParent(self.root.winfo_id())
            if not hwnd:
                hwnd = self.root.winfo_id()
            old_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            user32.SetWindowLongW(
                hwnd,
                GWL_EXSTYLE,
                old_style | WS_EX_NOACTIVATE | WS_EX_TOPMOST | WS_EX_TOOLWINDOW
            )
        except Exception as e:
            print(f"[OSD] Win32 Style ayarlama hatası: {e}")

    def _setup_ui(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.94)

        # Dark sleek theme colors
        bg_card = "#1C1C20"
        border_color = "#333338"
        accent_color = "#4CC2FF"
        text_white = "#FFFFFF"
        text_muted = "#A0A0A5"

        # Dimensions & positioning
        width = 360
        height = 84
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        pos_x = screen_w - width - 24
        pos_y = screen_h - height - 60 # Above Windows taskbar

        self.root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        self.root.configure(bg=border_color)

        # Inner container for border effect
        inner = tk.Frame(self.root, bg=bg_card, padx=14, pady=10)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        # Header Frame: Icon + Title + Device Counter Badge
        header_frame = tk.Frame(inner, bg=bg_card)
        header_frame.pack(fill="x", anchor="w")

        icon_label = tk.Label(
            header_frame,
            text="🔊",
            font=("Segoe UI Emoji", 11),
            fg=accent_color,
            bg=bg_card
        )
        icon_label.pack(side="left", padx=(0, 6))

        title_label = tk.Label(
            header_frame,
            text="Ses Çıkışı Değiştirildi",
            font=("Segoe UI", 9, "bold"),
            fg=accent_color,
            bg=bg_card
        )
        title_label.pack(side="left")

        self.badge_label = tk.Label(
            header_frame,
            text="[1/2]",
            font=("Segoe UI", 8, "bold"),
            fg=text_muted,
            bg="#2A2A30",
            padx=5,
            pady=1
        )
        self.badge_label.pack(side="right")

        # Device name text
        self.device_label = tk.Label(
            inner,
            text="",
            font=("Segoe UI", 11, "bold"),
            fg=text_white,
            bg=bg_card,
            anchor="w",
            wraplength=330,
            justify="left"
        )
        self.device_label.pack(fill="x", pady=(4, 0))

        # Initially hidden until triggered
        self.root.withdraw()
        self._apply_no_focus_style()

    def _run(self):
        self._setup_ui()
        self._ready_event.set()

        # Start periodic queue polling in the Tk mainloop
        self.root.after(30, self._check_queue)
        self.root.mainloop()

    def _check_queue(self):
        try:
            while not self.msg_queue.empty():
                item = self.msg_queue.get_nowait()
                if item is None: # Shutdown signal
                    self.root.destroy()
                    return
                device_name, current_idx, total_count = item
                self._display_notification(device_name, current_idx, total_count)
        except Exception:
            pass

        if self.root:
            self.root.after(40, self._check_queue)

    def _display_notification(self, device_name: str, current_idx: int, total_count: int):
        if not self.root:
            return

        # Cancel existing close timer if active
        if self.close_timer:
            try:
                self.root.after_cancel(self.close_timer)
            except Exception:
                pass
            self.close_timer = None

        # Update labels
        self.device_label.config(text=device_name)
        if total_count == 2:
            badge_text = "A / B" if current_idx == 1 else "B / A"
        else:
            badge_text = f"{current_idx}/{total_count}"
        self.badge_label.config(text=badge_text)

        # Show window without taking focus
        self.root.deiconify()
        self._apply_no_focus_style()

        # Schedule auto-hide
        self.close_timer = self.root.after(self.duration_ms, self._hide_notification)

    def _hide_notification(self):
        if self.root:
            self.root.withdraw()
        self.close_timer = None

    def show(self, device_name: str, current_idx: int = 1, total_count: int = 1):
        """Thread-safe request to display or refresh the OSD."""
        self.msg_queue.put((device_name, current_idx, total_count))

    def stop(self):
        """Cleanly shuts down the OSD thread."""
        self.msg_queue.put(None)
        if self._thread:
            self._thread.join(timeout=1.0)
