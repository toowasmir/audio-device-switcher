# 🔊 Windows Audio Device Switcher

[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-blue.svg)](https://microsoft.com/windows)
[![Python](https://img.shields.io/badge/python-3.9+-brightgreen.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Executable](https://img.shields.io/badge/build-standalone%20.exe-orange.svg)]()

A lightweight, standalone desktop utility for **Windows 10 and 11** that lives in the System Tray and toggles your default audio playback devices with a single customizable global hotkey.

Designed with **minimal memory footprint** (~25-30 MB RAM), **0% idle CPU usage**, and **resilient Core Audio COM architecture**.

---

## ✨ Features

- **Direct Core Audio & `IPolicyConfig` COM Integration:**
  Switches default playback devices programmatically across all Windows roles (`eConsole`, `eMultimedia`, and `eCommunications`) without depending on external tools or command-line wrappers.

- **Native Global Hotkey (`RegisterHotKey` API):**
  Uses the native Win32 `RegisterHotKey` message loop rather than polling or heavy low-level keyboard hooks. Triggers reliably even when full-screen games, videos, or other applications are focused. Default: <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>F11</kbd> (fully rebindable).

- **Smart A/B Toggle & Multi-Device Cycling:**
  - **A/B Toggle Mode:** If 2 devices are selected (e.g., Headphones ⇄ Speakers), toggles directly back and forth.
  - **Sequential Cycle Mode:** If 3 or more devices are selected, cycles through them in order.

- **Non-Activating OSD (On-Screen Display):**
  Displays a sleek, modern Fluent-style dark card overlay at the bottom-right corner for 1.5 seconds when the device changes. Uses `WS_EX_NOACTIVATE` and `WS_EX_TOPMOST` to **never steal keyboard or window focus** away from games or typing.

- **Comprehensive System Tray Management:**
  - Displays all active playback devices with a checkmark (`✓`) on the current default.
  - Left/right click to manually select any device instantly.
  - **Select Devices for Cycle:** Include only desired devices (e.g., headphones and speakers, excluding monitor audio).
  - **Change Shortcut Key:** Interactive dialog to configure any custom modifier and key combination.
  - **Run on Windows Startup:** Toggle automatic launch on Windows boot via registry (`HKCU\...\Run`).

- **Hardware Resilient & Persistent:**
  Identifies devices by unique Core Audio Endpoint IDs (GUIDs). Smoothly handles hotplugging (e.g., unplugging a USB headset) by automatically falling back to connected devices without crashing.

- **Single Instance Mutex:**
  Guarantees that only one instance runs at any given time via a Win32 named Mutex.

---

## 📁 Repository Structure

```
├── core/
│   ├── audio_manager.py     # Windows IMMDeviceEnumerator & IPolicyConfig COM implementation
│   ├── hotkey_manager.py    # Win32 RegisterHotKey background worker thread
│   └── config_manager.py    # JSON configuration persistence & Windows Autostart Registry
│
├── ui/
│   ├── osd.py               # Non-activating floating OSD notification overlay
│   ├── tray.py              # pystray dynamic system tray menu & state management
│   ├── dialogs.py           # Device selection and hotkey configuration dialogs
│   └── icons.py             # Programmatic tray & window icon generator (Pillow)
│
├── main.py                  # Application entry point, Mutex, and lifecycle orchestrator
├── requirements.txt         # Project dependencies (pystray, Pillow, comtypes)
├── test_suite.py            # Unit test suite verifying core audio and hotkey functions
├── run.bat                  # Silent background launcher (pythonw)
├── build.bat                # Single-click PyInstaller build script for portable .exe
├── LICENSE                  # MIT License
└── README.md                # Documentation
```

---

## 🚀 Quick Start

### Requirements
- Windows 10 or Windows 11
- Python 3.9+ (if running from source)

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Run Application
Run directly in console:
```powershell
python main.py
```

Or launch silently in the background with no terminal window:
```powershell
.\run.bat
```
*(Runs via `pythonw.exe main.py`)*

---

## 📦 Building a Standalone Executable (.exe)

You can package the application into a single, portable `.exe` file that runs on any Windows PC without needing Python installed:

1. Double-click [`build.bat`](build.bat) or run:
   ```powershell
   pyinstaller --noconsole --onefile --clean --name "AudioDeviceSwitcher" --icon "icon.ico" --add-data "icon.ico;." main.py
   ```
2. The standalone binary will be generated at `dist\AudioDeviceSwitcher.exe`.

---

## ⚙️ Configuration & Storage

- **Settings File:** `%APPDATA%\AudioDeviceSwitcher\config.json`
- **Windows Autostart Entry:** `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run` (`AudioDeviceSwitcher`)
- **Single Instance Mutex:** `Global\AudioDeviceSwitcher_SingleInstance_Mutex_99F3`

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
