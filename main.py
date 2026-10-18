import os
import sys
import ctypes
from ctypes import wintypes
import threading

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.audio_manager import AudioManager
from core.config_manager import ConfigManager
from core.hotkey_manager import HotkeyListener
from ui.osd import OSDWindow
from ui.tray import TrayManager
from ui.icons import ensure_ico_file

# Win32 Mutex for single-instance check
kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32
ERROR_ALREADY_EXISTS = 183
MUTEX_NAME = "Global\\AudioDeviceSwitcher_SingleInstance_Mutex_99F3"


class Application:
    """Main Application orchestrator coordinating Audio, Hotkey, OSD and Tray UI."""

    def __init__(self):
        self.mutex_handle = None
        self._ensure_single_instance()

        # Generate app icon file for Windows shortcuts & assets
        ico_path = os.path.join(BASE_DIR, "icon.ico")
        ensure_ico_file(ico_path)

        # Initialize Managers
        self.config_mgr = ConfigManager()
        self.audio_mgr = AudioManager()
        self.osd = OSDWindow(duration_ms=self.config_mgr.osd_duration_ms)
        self.osd.start()

        self.hotkey_listener = HotkeyListener(
            callback=self.on_hotkey_triggered,
            modifiers=self.config_mgr.hotkey_modifiers,
            key=self.config_mgr.hotkey_key
        )

        self.tray = TrayManager(
            audio_manager=self.audio_mgr,
            config_manager=self.config_mgr,
            on_toggle_request=self.on_hotkey_triggered,
            on_hotkey_changed=self.on_hotkey_changed,
            on_exit=self.shutdown
        )

    def _ensure_single_instance(self):
        """Prevents multiple instances from running simultaneously."""
        self.mutex_handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
        last_error = kernel32.GetLastError()
        if last_error == ERROR_ALREADY_EXISTS:
            MB_ICONINFORMATION = 0x40
            MB_OK = 0x0
            user32.MessageBoxW(
                None,
                "Ses Çıkış Değiştirici zaten arka planda çalışıyor.\nLütfen ekranın sağ altındaki Sistem Tepsisi (System Tray) simgesini kontrol edin.",
                "Ses Çıkış Değiştirici",
                MB_ICONINFORMATION | MB_OK
            )
            sys.exit(0)

    def on_hotkey_triggered(self):
        """Called when the global hotkey is pressed."""
        result = self.audio_mgr.toggle_next_device(self.config_mgr.selected_device_ids)
        if result:
            target_device, current_idx, total_count = result
            # Display OSD if enabled
            if self.config_mgr.show_osd:
                self.osd.show(target_device.name, current_idx, total_count)
            # Update Tray checkmark
            self.tray.update_menu()

    def on_hotkey_changed(self, modifiers: list, key: str):
        """Updates hotkey listener dynamically when user changes settings."""
        if self.hotkey_listener:
            self.hotkey_listener.update_hotkey(modifiers, key)

    def run(self):
        """Starts background hotkey listener and runs the System Tray event loop."""
        self.hotkey_listener.start()
        print("[AudioDeviceSwitcher] Uygulama başlatıldı. Sistem tepsisinde çalışıyor.")
        try:
            self.tray.run()
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        """Gracefully cleans up threads and resources on exit."""
        print("[AudioDeviceSwitcher] Kapatılıyor...")
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        if self.osd:
            self.osd.stop()
        if self.mutex_handle:
            kernel32.CloseHandle(self.mutex_handle)
            self.mutex_handle = None
        os._exit(0)


def main():
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
