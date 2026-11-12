@echo off
echo Running graphics pipeline verification in IDA Pro...
echo.

set IDA_PATH=C:\Program Files\IDA Professional 9.1\idat.exe
set IDB_PATH=C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64
set SCRIPT_PATH=C:\Users\ybarnoy\projects\falcon3\analysis\s4\verify_graphics_pipeline.py

cd /d "C:\Users\ybarnoy\projects\falcon3\analysis\s4"

echo IDA: %IDA_PATH%
echo IDB: %IDB_PATH%
echo Script: %SCRIPT_PATH%
echo.
echo Starting IDA in batch mode...
echo.

"%IDA_PATH%" -A -S"%SCRIPT_PATH%" "%IDB_PATH%"

echo.
echo Verification complete. Check ida_verification_results.json for results.
pause
