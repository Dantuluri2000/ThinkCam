@echo off
REM ThinkCam Home Setup for Windows
REM Run this in PowerShell or Command Prompt on your home Windows laptop

echo === ThinkCam Home Setup (Windows) ===

REM Create credential files
echo Creating wyze.env...
(
echo WYZE_EMAIL=sridhar.dantuluri@gmail.com
echo WYZE_PASSWORD=qg6,.Cn-p8LVhac
echo API_ID=06310c1e-1115-4122-814d-209f3b17d742
echo API_KEY=WPwnoZ0e1tQlMvZ6XDgesVkUl9wzOX0AkOHSdxCjYC1V0VbJSYPDSrsWUHvs
echo WB_AUTH=false
echo ENABLE_AUDIO=false
echo ON_DEMAND=false
) > wyze.env

echo Creating .env.local...
(
echo WYZE_EMAIL=sridhar.dantuluri@gmail.com
echo WYZE_PASSWORD=qg6,.Cn-p8LVhac
echo WYZE_KEY_ID=06310c1e-1115-4122-814d-209f3b17d742
echo WYZE_API_KEY=WPwnoZ0e1tQlMvZ6XDgesVkUl9wzOX0AkOHSdxCjYC1V0VbJSYPDSrsWUHvs
echo WYZE_RTSP_URL=rtsp://localhost:8554/front-porch-cam
echo WYZE_MOCK=false
echo ONEDRIVE_MOCK=true
echo FIREBASE_MOCK=true
) > .env.local

REM Start Wyze Bridge
echo Starting Wyze Bridge...
if not exist wyze-storage mkdir wyze-storage
docker rm -f wyze-bridge-thinkcam 2>nul
docker run -d --name wyze-bridge-thinkcam --restart unless-stopped -p 8554:8554 -p 5050:5000 -v "%cd%\wyze-storage:/tokens" --env-file wyze.env mrlt8/wyze-bridge:latest

echo Waiting 30s for camera...
timeout /t 30 /nobreak

REM Setup Python
echo Setting up Python...
python -m venv venv
venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel -q
venv\Scripts\python.exe -m pip install -r requirements.txt -q

REM Start backend
echo Starting ThinkCam backend...
set PYTHONUTF8=1
start "ThinkCam Backend" venv\Scripts\python.exe main.py

timeout /t 5 /nobreak
echo.
echo === Setup Complete ===
echo Wyze Bridge UI:  http://localhost:5050
echo ThinkCam API:    http://localhost:8000
echo.
pause
