@echo off
chcp 65001 >nul
cd /d "%~dp0"
where docker >nul 2>nul
if errorlevel 1 set "PATH=%ProgramFiles%\Docker\Docker\resources\bin;%LOCALAPPDATA%\Programs\DockerDesktop\resources\bin;%PATH%"
docker info >nul 2>nul
if errorlevel 1 (
  echo Open Docker Desktop and wait until the engine is running, then run this file again.
  pause
  exit /b 1
)
if not exist ".env.ngrok" (
  echo Missing .env.ngrok. Read DOCKER-NGROK.md.
  pause
  exit /b 1
)
set "EXTRA_PROFILE="
findstr /r "^CLOUDPUB_TOKEN=." ".env.ngrok" >nul 2>nul
if not errorlevel 1 set "EXTRA_PROFILE=--profile cloudpub"
docker compose --env-file .env.ngrok -f compose.ngrok.yaml %EXTRA_PROFILE% config --quiet
if errorlevel 1 (
  pause
  exit /b 1
)
docker compose --env-file .env.ngrok -f compose.ngrok.yaml %EXTRA_PROFILE% up -d --build --wait --wait-timeout 180
if errorlevel 1 (
  echo Startup is incomplete. Check Docker Desktop and the container logs.
  pause
  exit /b 1
)
docker compose --env-file .env.ngrok -f compose.ngrok.yaml ps
echo Local site: http://127.0.0.1:4174/
echo Check the public URL and MAX webhook using the instructions in DOCKER-NGROK.md.
echo Containers run in the background. Closing this window does not stop them.
pause
