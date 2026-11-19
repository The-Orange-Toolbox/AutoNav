@echo off
REM ---------------------------------------------------------------------------
REM Convenience wrapper: set up a local venv and run the Orange Toolbox build.
REM
REM Requires Python 3 and git on PATH. Produces a versioned, zipped package
REM under dist\ containing a standalone one-file exe (built by build.py via
REM totcommon.builder). You can also just run `python build.py` in your own env.
REM ---------------------------------------------------------------------------

setlocal

echo [1/3] Creating virtual environment (.venv)...
python -m venv .venv || goto :error

echo [2/3] Installing dependencies...
call .venv\Scripts\python.exe -m pip install --upgrade pip || goto :error
call .venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller || goto :error

echo [3/3] Building...
call .venv\Scripts\python.exe build.py || goto :error

echo.
echo Done. See dist\
goto :eof

:error
echo.
echo Build failed.
exit /b 1
