@echo off
echo Installing dependencies...
pip install -r requirements.txt > install_log.txt 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error installing dependencies. Check install_log.txt.
    pause
    exit /b %ERRORLEVEL%
)

echo Starting Build (output saved to build_log.txt)...
python build.py > build_log.txt 2>&1

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =================================================
    echo Build Successful! 
    echo Executable is located in the 'dist' folder.
    echo =================================================
) else (
    echo.
    echo =================================================
    echo Build FAILED! 
    echo Please check 'build_log.txt' for error details.
    echo =================================================
)
pause
