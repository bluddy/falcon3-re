@echo off
REM To use this batch file, follow its invocation with
REM the number of the squad you wish to restore, e.g.,
REM "RESTRCAM 0 <Enter>"

cls
echo.
echo.
IF NOT EXIST C:\SQU%1MIS.BAK GOTO info

echo Running this batch file will overwrite the existing
echo data files for SQUAD%1.  Are you sure you want
echo to do this?
echo.
echo Hit "CTRL-C" to cancel or
pause

COPY C:\SQU%1MIS.BAK C:\SQUAD%1.MIS
COPY C:\SQU%1WAR.BAK C:\SQUAD%1.WAR
COPY C:\SQU%1CAM.BAK C:\SQUAD%1.CAM
COPY C:\SQU%1MTV.BAK C:\SQUAD%1.MTV
COPY C:\SQU%1SQU.BAK C:\SQUAD%1.SQU
COPY C:\MISSION%1.BAK C:\MISSION.%1
IF EXIST C:\STRAT\SQU%1SIM.BAK COPY C:\STRAT\SQU%1SIM.BAK C:\STRAT\SQUAD%1.SFS
echo.
echo RESTRCAM is finished.  As long as you don't see any "File
echo not found" messages above, you can assume it worked
echo successfully.
echo.
goto end

:info
echo This batch file will restore a campaign to the
echo most recent backups created by Strategic Falcon.
echo.
echo To use this file, follow its invocation with the
echo number of the squad you wish to restore, e.g.,
echo "RESTRCAM 0 <Enter>."
echo.
echo See the Strategic Falcon manual or the READ.ME file
echo for instructions on determining which Squad number
echo is applicable.
echo.
echo.
:end
