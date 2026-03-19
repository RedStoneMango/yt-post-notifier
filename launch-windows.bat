@echo off
SET SCRIPT_DIR=%~dp0

CALL "%SCRIPT_DIR%venv\Scripts\activate.bat"
python "%SCRIPT_DIR%main.py" %*
SET res=%ERRORLEVEL%
CALL "%SCRIPT_DIR%venv\Scripts\deactivate.bat"
EXIT /B %res%
