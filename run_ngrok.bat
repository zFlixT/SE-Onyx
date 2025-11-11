@echo off
setlocal
IF "%NGROK_AUTHTOKEN%"=="Tu key de API aquí" (
  echo Por favor define la variable de entorno NGROK_AUTHTOKEN.
  exit /b 1
)
start "" ngrok http 8000 --log=stdout
call run_local.bat
