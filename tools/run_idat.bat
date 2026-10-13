@echo off
setlocal
set IDA=C:\Program Files\IDA Professional 9.1\idat.exe
set IDB=C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64
set LOG=C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\launch.log
"%IDA%" -A -L"%LOG%" -S"%~1" "%IDB%"
echo EXIT=%ERRORLEVEL%
endlocal