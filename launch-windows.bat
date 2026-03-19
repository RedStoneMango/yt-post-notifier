@echo off

call venv\Scripts\activate.bat
python main.py %*
set res=%ERRORLEVEL%
call deactivate
exit /b %res%
