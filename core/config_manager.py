import json
import os
import sys
import winreg
from typing import List, Dict, Any, Optional

DEFAULT_CONFIG: Dict[str, Any] = {
    "hotkey": {
        "modifiers": ["Ctrl", "Shift"],
        "key": "F11"
    },
    "selected_device_ids": [],
    "show_osd": True,
    "osd_duration_ms": 1500,
    "autostart": False
}

REGISTRY_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "AudioDeviceSwitcher"


class ConfigManager:
    """Manages application settings persistence and Windows autostart integration."""

    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            appdata = os.environ.get("APPDATA")
            if appdata:
                config_dir = os.path.join(appdata, APP_NAME)
            else:
                config_dir = os.path.join(os.path.expanduser("~"), f".{APP_NAME}")

        self.config_dir = config_dir
        self.config_path = os.path.join(self.config_dir, "config.json")
        self._ensure_dir()
        self.config = self.load()

    def _ensure_dir(self):
        try:
            os.makedirs(self.config_dir, exist_ok=True)
        except OSError:
            pass

    def load(self) -> Dict[str, Any]:
        """Loads configuration from JSON file or returns default."""
        if not os.path.exists(self.config_path):
            config = DEFAULT_CONFIG.copy()
            self.save(config)
            return config

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                # Merge loaded keys with defaults to ensure all fields exist
                merged = DEFAULT_CONFIG.copy()
                merged.update(loaded)
                # Keep nested hotkey fields safe
                if "hotkey" in loaded and isinstance(loaded["hotkey"], dict):
                    merged_hotkey = DEFAULT_CONFIG["hotkey"].copy()
                    merged_hotkey.update(loaded["hotkey"])
                    merged["hotkey"] = merged_hotkey
                return merged
        except Exception:
            return DEFAULT_CONFIG.copy()

    def save(self, config: Optional[Dict[str, Any]] = None):
        """Saves current configuration to file."""
        if config is not None:
            self.config = config

        try:
            self._ensure_dir()
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ConfigManager] Ayar kaydetme hatası: {e}")

    # --- Hotkey Accessors ---
    @property
    def hotkey_modifiers(self) -> List[str]:
        return self.config.get("hotkey", {}).get("modifiers", ["Ctrl", "Shift"])

    @property
    def hotkey_key(self) -> str:
        return self.config.get("hotkey", {}).get("key", "F11")

    def set_hotkey(self, modifiers: List[str], key: str):
        if "hotkey" not in self.config:
            self.config["hotkey"] = {}
        self.config["hotkey"]["modifiers"] = modifiers
        self.config["hotkey"]["key"] = key
        self.save()

    def get_hotkey_string(self) -> str:
        mods = self.hotkey_modifiers
        k = self.hotkey_key
        parts = list(mods)
        if k:
            parts.append(k)
        return " + ".join(parts)

    # --- Device Cycle Accessors ---
    @property
    def selected_device_ids(self) -> List[str]:
        return self.config.get("selected_device_ids", [])

    def set_selected_device_ids(self, device_ids: List[str]):
        self.config["selected_device_ids"] = list(device_ids)
        self.save()

    # --- OSD Accessors ---
    @property
    def show_osd(self) -> bool:
        return bool(self.config.get("show_osd", True))

    def set_show_osd(self, show: bool):
        self.config["show_osd"] = bool(show)
        self.save()

    @property
    def osd_duration_ms(self) -> int:
        return int(self.config.get("osd_duration_ms", 1500))

    # --- Windows Autostart Registry ---
    @staticmethod
    def _get_launch_command() -> str:
        """Determines proper command line for Windows Startup."""
        if getattr(sys, "frozen", False):
            # Compiled PyInstaller executable
            return f'"{sys.executable}"'
        else:
            # Running as Python script
            main_script = os.path.abspath(
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "main.py")
            )
            # Use pythonw.exe to prevent terminal window from popping up
            python_exe = sys.executable
            pythonw_exe = python_exe.lower().replace("python.exe", "pythonw.exe")
            if os.path.exists(pythonw_exe):
                return f'"{pythonw_exe}" "{main_script}"'
            return f'"{python_exe}" "{main_script}"'

    def is_autostart_enabled(self) -> bool:
        """Checks if app is registered in HKCU Run key."""
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, REGISTRY_RUN_KEY, 0, winreg.KEY_READ
            ) as key:
                val, _ = winreg.QueryValueEx(key, APP_NAME)
                return bool(val)
        except OSError:
            return False

    def set_autostart(self, enable: bool) -> bool:
        """Enables or disables automatic startup in Windows Registry."""
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, REGISTRY_RUN_KEY, 0, winreg.KEY_SET_VALUE
            ) as key:
                if enable:
                    cmd = self._get_launch_command()
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
                else:
                    try:
                        winreg.DeleteValue(key, APP_NAME)
                    except OSError:
                        pass
            self.config["autostart"] = enable
            self.save()
            return True
        except Exception as e:
            print(f"[ConfigManager] Autostart kayıt hatası: {e}")
            return False
