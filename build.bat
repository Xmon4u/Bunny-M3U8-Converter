@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  set PY=py -3
) else (
  set PY=python
)
%PY% -m pip install --upgrade customtkinter pyinstaller pillow
if errorlevel 1 goto :fail
%PY% make_icon.py
if errorlevel 1 goto :fail
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name BunnyM3U8 --icon assets\app.ico --add-data "assets\app.ico;assets" --collect-all customtkinter --hidden-import gui_app bunny_m3u8.py
if errorlevel 1 goto :fail
echo.
echo EXE ready: %~dp0dist\BunnyM3U8.exe
goto :eof
:fail
echo Build failed.
pause
exit /b 1
