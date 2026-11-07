@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Chua cai dat. Hay chay file "cai-dat-windows.bat" truoc.
  pause
  exit /b 1
)
echo Tool se mo tai http://127.0.0.1:7860 - giu cua so nay mo khi dang dung, dong la tat tool.
.venv\Scripts\python.exe app.py
pause
