@echo off
echo Cleaning __pycache__ and log files...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.log
echo Done.
pause
