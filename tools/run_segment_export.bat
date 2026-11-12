@echo off
REM Run IDA script to export segment map and multi-entry functions

set IDA_PATH=C:\Program Files\IDA Professional 9.1\idat.exe
set IDB_PATH=C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64
set SCRIPT_PATH=C:\Users\ybarnoy\projects\falcon3\tools\export_segment_map.py
set OUTPUT_PATH=C:\Users\ybarnoy\projects\falcon3\analysis\s4\segment_map.json

echo Running IDA segment export script...
echo IDB: %IDB_PATH%
echo Script: %SCRIPT_PATH%
echo Output: %OUTPUT_PATH%
echo.

"%IDA_PATH%" -A -S"%SCRIPT_PATH% %OUTPUT_PATH%" "%IDB_PATH%"

echo.
echo Done! Check %OUTPUT_PATH% for results.
pause
