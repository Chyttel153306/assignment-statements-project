@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto use_venv
py -3 -c "import sys; assert sys.version_info >= (3, 10)" >nul 2>&1
if not errorlevel 1 goto use_py
python -c "import sys; assert sys.version_info >= (3, 10)" >nul 2>&1
if not errorlevel 1 goto use_python
echo Python 3.10 or newer was not found. Install Python and reopen this launcher.
echo If the Windows Store alias fails, use the full path to your Python executable.
pause
exit /b 1

:use_venv
set "DFA_PYTHON=%~dp0.venv\Scripts\python.exe"
set "DFA_ARGS="
goto check_dependencies
:use_py
set "DFA_PYTHON=py"
set "DFA_ARGS=-3"
goto check_dependencies
:use_python
set "DFA_PYTHON=python"
set "DFA_ARGS="

:check_dependencies
"%DFA_PYTHON%" %DFA_ARGS% -c "import sys; assert sys.version_info >= (3, 10)" >nul 2>&1
if errorlevel 1 goto invalid_python
"%DFA_PYTHON%" %DFA_ARGS% -c "import flask" >nul 2>&1
if not errorlevel 1 goto launch
echo Flask is not installed for the selected Python.
echo Run this command, then reopen this launcher:
echo "%DFA_PYTHON%" %DFA_ARGS% -m pip install -r requirements.txt
pause
exit /b 1

:invalid_python
echo The selected Python environment must use Python 3.10 or newer.
echo Recreate .venv with a supported Python version. See README.md.
pause
exit /b 1

:launch
echo Opening http://127.0.0.1:5000 when the server is ready.
echo Keep this terminal open. Press Ctrl+C to stop the server.
"%DFA_PYTHON%" %DFA_ARGS% app.py --open
if errorlevel 1 echo The server could not start. Check the output above and whether port 5000 is already in use.
pause
