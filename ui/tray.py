import threading
from typing import Callable, Optional, List
import pystray
from pystray import MenuItem as item, Menu
from core.audio_manager import AudioManager, AudioDevice
from core.config_manager import ConfigManager
from ui.icons import create_audio_icon
from ui.dialogs import DeviceSelectionDialog, HotkeyConfigDialog


class TrayManager:
    """Manages the Windows System Tray icon, dynamic menus, and tray actions."""

    def __init__(
        self,
        audio_manager: AudioManager,
        config_manager: ConfigManager,
        on_toggle_request: Callable[[], None],
        on_hotkey_changed: Callable[[List[str], str], None],
        on_exit: Callable[[], None]
    ):
        self.audio_mgr = audio_manager
        self.config_mgr = config_manager
        self.on_toggle_request = on_toggle_request
        self.on_hotkey_changed = on_hotkey_changed
        self.on_exit = on_exit

        self.icon: Optional[pystray.Icon] = None
        self._cached_devices: List[AudioDevice] = []

    def _refresh_device_cache(self):
        self._cached_devices = self.audio_mgr.get_active_devices()

    def _build_menu(self) -> Menu:
        self._refresh_device_cache()
        items = []

        # App title header (informational)
        hotkey_str = self.config_mgr.get_hotkey_string()
        items.append(item(f"🔊 Audio Switcher ({hotkey_str})", action=lambda: None, enabled=False))
        items.append(Menu.SEPARATOR)

        # Device selection section
        if not self._cached_devices:
            items.append(item("Etkin ses aygıtı bulunamadı", action=lambda: None, enabled=False))
        else:
            for dev in self._cached_devices:
                # Helper callback for specific device
                def make_select_action(did: str):
                    return lambda: self._on_device_clicked(did)

                def make_check_condition(did: str):
                    return lambda it: self._is_device_default(did)

                label = dev.name
                items.append(
                    item(
                        label,
                        action=make_select_action(dev.id),
                        checked=make_check_condition(dev.id)
                    )
                )

        items.append(Menu.SEPARATOR)

        # Cycle Selection dialog trigger
        items.append(item("Döngüye Dahil Edilecek Aygıtlar...", action=self._open_device_selection_dialog))

        # Hotkey dialog trigger
        items.append(item(f"Kısayol Tuşu Belirle... [{hotkey_str}]", action=self._open_hotkey_dialog))

        # OSD toggle
        items.append(
            item(
                "OSD Bildirimlerini Göster",
                action=self._toggle_osd,
                checked=lambda it: self.config_mgr.show_osd
            )
        )

        # Run with Windows autostart toggle
        items.append(
            item(
                "Windows ile Birlikte Başlat",
                action=self._toggle_autostart,
                checked=lambda it: self.config_mgr.is_autostart_enabled()
            )
        )

        items.append(Menu.SEPARATOR)

        # Refresh
        items.append(item("Cihaz Listesini Yenile", action=self.update_menu))

        # Exit
        items.append(item("Çıkış", action=self._on_exit_clicked))

        return Menu(*items)

    def _is_device_default(self, device_id: str) -> bool:
        current_def = self.audio_mgr.get_default_device_id()
        return (device_id == current_def)

    def _on_device_clicked(self, device_id: str):
        success = self.audio_mgr.set_default_device(device_id)
        if success:
            self.update_menu()

    def _toggle_osd(self):
        new_val = not self.config_mgr.show_osd
        self.config_mgr.set_show_osd(new_val)
        self.update_menu()

    def _toggle_autostart(self):
        curr = self.config_mgr.is_autostart_enabled()
        self.config_mgr.set_autostart(not curr)
        self.update_menu()

    def _open_device_selection_dialog(self):
        # Open in separate thread to prevent blocking tray icon message queue
        def _run():
            self._refresh_device_cache()
            DeviceSelectionDialog(
                active_devices=self._cached_devices,
                selected_ids=self.config_mgr.selected_device_ids,
                on_save=self._on_device_selection_saved
            )
        threading.Thread(target=_run, daemon=True).start()

    def _on_device_selection_saved(self, selected_ids: List[str]):
        self.config_mgr.set_selected_device_ids(selected_ids)
        self.update_menu()

    def _open_hotkey_dialog(self):
        def _run():
            HotkeyConfigDialog(
                current_modifiers=self.config_mgr.hotkey_modifiers,
                current_key=self.config_mgr.hotkey_key,
                on_save=self._on_hotkey_saved
            )
        threading.Thread(target=_run, daemon=True).start()

    def _on_hotkey_saved(self, modifiers: List[str], key: str):
        self.config_mgr.set_hotkey(modifiers, key)
        self.on_hotkey_changed(modifiers, key)
        self.update_menu()

    def update_menu(self):
        """Forces pystray to rebuild and display updated menu state."""
        if self.icon:
            try:
                self.icon.menu = self._build_menu()
            except Exception as e:
                print(f"[TrayManager] Menü güncelleme hatası: {e}")

    def _on_exit_clicked(self):
        if self.icon:
            self.icon.stop()
        if self.on_exit:
            self.on_exit()

    def run(self):
        """Initializes and runs the tray loop."""
        img = create_audio_icon(64)
        self.icon = pystray.Icon(
            "AudioDeviceSwitcher",
            img,
            "Ses Çıkış Değiştirici",
            menu=self._build_menu()
        )
        self.icon.run()

    def stop(self):
        if self.icon:
            self.icon.stop()
