@echo off
chcp 65001 >nul
echo ========================================================
echo   Audio Device Switcher - PyInstaller Derleme Scripti
echo ========================================================
echo.

echo [1/3] Gerekli bağımlılıklar kontrol ediliyor...
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo.
echo [2/3] Bağımsız tek dosya (.exe) derleniyor...
python -m PyInstaller --noconsole --onefile --clean --name "AudioDeviceSwitcher" --icon "icon.ico" --add-data "icon.ico;." main.py

echo.
echo [3/3] Derleme tamamlandı!
echo Oluşturulan dosya: dist\AudioDeviceSwitcher.exe
echo.
pause
