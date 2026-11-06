@echo off
chcp 65001 >nul
cd /d "%~dp0beckend"
if not exist ".venv\Scripts\python.exe" (
  echo Python environment is missing. Read README.md in the project folder.
  pause
  exit /b 1
)
if not exist ".env" (
  .venv\Scripts\python.exe -m scripts.configure
  if errorlevel 1 exit /b 1
)
.venv\Scripts\python.exe -m alembic upgrade head
if errorlevel 1 (
  pause
  exit /b 1
)
echo Open http://127.0.0.1:4174/ in your browser. Ctrl+C stops the server.
.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 4174
pause
