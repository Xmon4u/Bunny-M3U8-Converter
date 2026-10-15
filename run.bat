@echo off
cd /d "%~dp0"
if exist "%~dp0dist\BunnyM3U8.exe" (
  start "" "%~dp0dist\BunnyM3U8.exe"
  goto :eof
)
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 bunny_m3u8.py
  goto :eof
)
where python >nul 2>nul
if %ERRORLEVEL%==0 (
  python bunny_m3u8.py
  goto :eof
)
echo Python not found. Install from https://www.python.org/downloads/
echo During setup, tick "Add python.exe to PATH".
pause
