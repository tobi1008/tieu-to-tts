@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo === Cai dat Tieu To TTS (Windows) ===

set PY=
py -3.12 -c "import sys" 2>nul && set PY=py -3.12
if not defined PY py -3.11 -c "import sys" 2>nul && set PY=py -3.11
if not defined PY py -3.10 -c "import sys" 2>nul && set PY=py -3.10
if not defined PY python -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)" 2>nul && set PY=python

if not defined PY (
  echo.
  echo KHONG tim thay Python 3.10 tro len tren may.
  echo Hay tai Python 3.12 tai https://www.python.org/downloads/windows/
  echo LUU Y: khi cai, nho tich vao o "Add python.exe to PATH" o man hinh dau tien.
  echo Cai xong chay lai file nay.
  start https://www.python.org/downloads/windows/
  pause
  exit /b 1
)

echo Dung Python: %PY%
%PY% --version

%PY% -m venv .venv
if errorlevel 1 (
  echo Tao moi truong ao that bai.
  pause
  exit /b 1
)

echo Dang cai VieNeu (mat vai phut)...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
  echo Cai vieneu that bai - kiem tra mang roi chay lai file nay.
  pause
  exit /b 1
)

echo.
echo === Tai model + kiem tra giong Tieu To (lan dau mat vai phut) ===
.venv\Scripts\python.exe tai-model.py

echo.
echo === CAI XONG ===
echo Tu gio chi can nhap dup file "mo-tool-windows.bat" de mo tool doc text.
pause
