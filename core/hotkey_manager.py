import ctypes
from ctypes import wintypes
import threading
from typing import Callable, List, Optional, Tuple

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Modifiers
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

# Windows Messages
WM_HOTKEY = 0x0312
WM_USER = 0x0400
WM_STOP_HOTKEY = WM_USER + 1
WM_CHANGE_HOTKEY = WM_USER + 2

# Common Virtual Key Codes
KEY_MAP = {
    # Function keys
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
    "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
    # Navigation / Editing
    "space": 0x20, "tab": 0x09, "enter": 0x0D, "return": 0x0D,
    "esc": 0x1B, "escape": 0x1B, "backspace": 0x08,
    "insert": 0x2D, "delete": 0x2E, "home": 0x24, "end": 0x23,
    "pageup": 0x21, "pagedown": 0x22,
    "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28,
    # Media keys
    "media_next": 0xB0, "media_prev": 0xB1,
    "media_stop": 0xB2, "media_play_pause": 0xB3,
    "volume_mute": 0xAD, "volume_down": 0xAE, "volume_up": 0xAF,
}

# Add 0-9 and A-Z
for i in range(10):
    KEY_MAP[str(i)] = 0x30 + i
for c in "abcdefghijklmnopqrstuvwxyz":
    KEY_MAP[c] = ord(c.upper())


def parse_hotkey(modifiers: List[str], key: str) -> Tuple[int, int]:
    """Converts string modifier list and key name to Win32 mod flags and virtual key code."""
    mod_flags = 0
    for m in modifiers:
        norm = m.strip().lower()
        if "ctrl" in norm or "control" in norm:
            mod_flags |= MOD_CONTROL
        elif "shift" in norm:
            mod_flags |= MOD_SHIFT
        elif "alt" in norm:
            mod_flags |= MOD_ALT
        elif "win" in norm:
            mod_flags |= MOD_WIN

    key_norm = key.strip().lower()
    vk_code = KEY_MAP.get(key_norm)
    if vk_code is None:
        if len(key) == 1:
            res = user32.VkKeyScanW(ord(key[0]))
            if res != -1:
                vk_code = res & 0xFF
        if vk_code is None:
            # Default fallback to F11
            vk_code = 0x7A

    return mod_flags, vk_code


class HotkeyListener(threading.Thread):
    """
    Background worker running a native Win32 message loop to listen for global hotkeys
    via RegisterHotKey without requiring high CPU polling or system-wide keyboard hooks.
    """

    def __init__(self, callback: Callable[[], None], modifiers: List[str], key: str):
        super().__init__(daemon=True, name="HotkeyListenerThread")
        self.callback = callback
        self.modifiers = modifiers
        self.key = key
        self.thread_id: Optional[int] = None
        self.ready_event = threading.Event()
        self.hotkey_id = 1
        self._is_registered = False

    def run(self):
        self.thread_id = kernel32.GetCurrentThreadId()
        mod_flags, vk = parse_hotkey(self.modifiers, self.key)

        res = user32.RegisterHotKey(None, self.hotkey_id, mod_flags | MOD_NOREPEAT, vk)
        self._is_registered = bool(res)
        if not self._is_registered:
            err = kernel32.GetLastError()
            print(f"[HotkeyListener] Kısayol tuşu kaydedilemedi! Hata kodu: {err}. Başka bir uygulama bu kısayolu kullanıyor olabilir.")
        else:
            print(f"[HotkeyListener] Global kısayol kaydedildi: {self.modifiers} + {self.key}")

        self.ready_event.set()

        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == WM_HOTKEY and msg.wParam == self.hotkey_id:
                try:
                    if self.callback:
                        # Invoke callback in non-blocking thread to keep message loop responsive
                        threading.Thread(target=self.callback, daemon=True).start()
                except Exception as e:
                    print(f"[HotkeyListener] Callback çalıştırma hatası: {e}")

            elif msg.message == WM_CHANGE_HOTKEY:
                # Re-register hotkey with new modifiers and VK
                if self._is_registered:
                    user32.UnregisterHotKey(None, self.hotkey_id)
                    self._is_registered = False

                new_mod = msg.wParam
                new_vk = msg.lParam
                res = user32.RegisterHotKey(None, self.hotkey_id, new_mod | MOD_NOREPEAT, new_vk)
                self._is_registered = bool(res)
                if not self._is_registered:
                    print(f"[HotkeyListener] Yeni kısayol kaydedilemedi! Hata: {kernel32.GetLastError()}")
                else:
                    print(f"[HotkeyListener] Kısayol güncellendi: mod={new_mod}, vk={new_vk}")

            elif msg.message == WM_STOP_HOTKEY:
                if self._is_registered:
                    user32.UnregisterHotKey(None, self.hotkey_id)
                    self._is_registered = False
                break

            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def update_hotkey(self, modifiers: List[str], key: str):
        """Dynamically updates the active hotkey registration."""
        self.modifiers = modifiers
        self.key = key
        mod_flags, vk = parse_hotkey(modifiers, key)
        if self.thread_id:
            user32.PostThreadMessageW(self.thread_id, WM_CHANGE_HOTKEY, mod_flags, vk)

    def stop(self):
        """Stops listener thread and cleans up hotkey registration."""
        if self.thread_id:
            user32.PostThreadMessageW(self.thread_id, WM_STOP_HOTKEY, 0, 0)
            self.join(timeout=1.5)
