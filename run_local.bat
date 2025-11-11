@echo off
setlocal
REM Activa el entorno virtual si existe
IF EXIST .venv\Scripts\activate.bat CALL .venv\Scripts\activate.bat
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
