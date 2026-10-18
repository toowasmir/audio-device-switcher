import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config_manager import ConfigManager
from core.audio_manager import AudioManager, AudioDevice
from core.hotkey_manager import parse_hotkey, MOD_CONTROL, MOD_SHIFT, MOD_ALT
from ui.icons import create_audio_icon, ensure_ico_file

class TestAudioDeviceSwitcher(unittest.TestCase):

    def test_config_manager(self):
        cfg = ConfigManager(config_dir=os.path.join(BASE_DIR, "test_config"))
        self.assertEqual(cfg.hotkey_modifiers, ["Ctrl", "Shift"])
        self.assertEqual(cfg.hotkey_key, "F11")
        self.assertEqual(cfg.get_hotkey_string(), "Ctrl + Shift + F11")

        cfg.set_hotkey(["Alt", "Ctrl"], "F9")
        self.assertEqual(cfg.hotkey_modifiers, ["Alt", "Ctrl"])
        self.assertEqual(cfg.hotkey_key, "F9")

        # Clean up
        if os.path.exists(cfg.config_path):
            os.remove(cfg.config_path)
        if os.path.exists(cfg.config_dir):
            os.rmdir(cfg.config_dir)

    def test_hotkey_parsing(self):
        mod_flags, vk = parse_hotkey(["Ctrl", "Shift"], "F11")
        self.assertEqual(mod_flags, MOD_CONTROL | MOD_SHIFT)
        self.assertEqual(vk, 0x7A)

        mod_flags, vk = parse_hotkey(["Alt"], "A")
        self.assertEqual(mod_flags, MOD_ALT)
        self.assertEqual(vk, ord('A'))

    def test_audio_manager_enumeration(self):
        mgr = AudioManager()
        devices = mgr.get_active_devices()
        self.assertIsInstance(devices, list)
        self.assertGreater(len(devices), 0, "En az bir ses aygıtı bulunmalı")
        print(f"\nBulunan Aktif Cihazlar ({len(devices)}):")
        for d in devices:
            print(f"  - {d.name} {'(Varsayılan)' if d.is_default else ''}")

    def test_icon_generation(self):
        ico_test_path = os.path.join(BASE_DIR, "test_icon.ico")
        ensure_ico_file(ico_test_path)
        self.assertTrue(os.path.exists(ico_test_path))
        self.assertGreater(os.path.getsize(ico_test_path), 0)
        os.remove(ico_test_path)

if __name__ == "__main__":
    unittest.main()
