@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PYTHONNOUSERSITE=1
cd /d "%~dp0"
title Tieu To TTS
if not exist "python\python.exe" (
  echo Thieu thu muc "python". Hay giai nen lai TOAN BO file zip roi chay lai.
  pause
  exit /b 1
)
echo Tool se mo tai http://127.0.0.1:7860 - giu cua so nay mo khi dang dung, dong la tat tool.
echo Lan dau mo se tai model (khoang 550MB), can internet va doi vai phut.
:run
"python\python.exe" app.py
rem ma thoat 3 = vua cap nhat xong, chay lai tool
if %errorlevel%==3 goto restart
pause
exit /b
:restart
set TIEUTO_RESTART=1
goto run
