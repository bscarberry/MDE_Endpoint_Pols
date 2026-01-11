@echo off
REM Production startup script for Windows using Waitress

echo Starting Defender XDR Endpoint Policy Manager in PRODUCTION mode...

REM Check if .env file exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please create a .env file with your Azure AD credentials
    exit /b 1
)

REM Set production environment
set FLASK_ENV=production

REM Start Waitress server
waitress-serve --host=0.0.0.0 --port=5000 --threads=8 wsgi:app
