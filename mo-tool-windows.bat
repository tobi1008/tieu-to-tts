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
:run
.venv\Scripts\python.exe app.py
rem ma thoat 3 = vua cap nhat xong, chay lai tool
if %errorlevel%==3 goto restart
pause
exit /b
:restart
set TIEUTO_RESTART=1
goto run
