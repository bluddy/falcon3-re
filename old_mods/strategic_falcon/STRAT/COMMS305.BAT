@echo off                                                     
REM }  Copy this file to \STRAT\USER.BAT and run it by pressing the 
REM }  F6 key in StratFalc after making desired changes.  It is
REM }  assumed all machines involved have already run 305FIX and
REM }  COMMHACK ALTER, and you are playing with SQUAD0.* files.
REM }  Other assumptions:  your Falcon directory (FALCONDIR) is on the
REM }  same drive as \STRAT, and the floppy drive you're using for 
REM }  "Sneakernet" transfers is a:.
                         
if not exist %FALCONDIR%\falconcd.exe goto next
goto work

:next              
if not exist %FALCONDIR%\falcon3.exe goto next0
goto work             

:next0
if not exist c:\falconcd\falconcd.exe goto next1
SET FALCONDIR=C:\FALCONCD
goto work
             
:next1       
if not exist c:\falconcd\falcon3.exe goto next2
SET FALCONDIR=C:\FALCONCD 
goto work 
                     
:next2                    
if not exist c:\falcon3\falconcd.exe goto next3
SET FALCONDIR=C:\FALCON3 
goto work 

:next3                    
if not exist c:\falcon3\falcon3.exe goto next4
SET FALCONDIR=C:\FALCON3 
goto work 

:next4         
if not exist d:\falconcd\falconcd.exe goto next5
SET FALCONDIR=D:\FALCONCD 
goto work 

:next5                                          
if not exist d:\falconcd\falcon3.exe goto next6
SET FALCONDIR=D:\FALCONCD 
goto work 

:next6                    
if not exist d:\falcon3\falconcd.exe goto next7
SET FALCONDIR=D:\FALCON3 
goto work 

:next7                    
if not exist d:\falcon3\falcon3.exe goto next8
SET FALCONDIR=D:\FALCON3 
goto work 

:next8
@echo.
@echo I've looked in 8 likely directories; that's about as heroic as I get. 
@echo I can't find your FALCON 3.0 installation.
@echo.
@echo You're going to have to set the environment variable FALCONDIR 
@echo on this machine to make this file work. Use the syntax 
@echo              SET FALCONDIR=C:\FALCON3 
@echo from the DOS prompt (and place it in your AUTOEXEC.BAT file).
@echo.
@echo Hit CTRL-C to cancel;  you'll end up back in StratFalc if you
pause
goto end                                                                 

:work                         
@echo Insert "Sneakernet" disk into drive a:, hit CTRL-C to abort or
pause                 
if not exist a:\falcom.bat copy falcom.bat a:
CD %FALCONDIR%

attrib -h squad0.mis
attrib -h squad6.mis

copy squad0.mis squad6.mis 

copy squad6.mis a:\
@echo.      
@echo Now run the FALCOM batch file on the floppy in all users' machine(s). 
@echo.
@echo You do that, while I finish here.
@echo.

attrib +h squad6.mis

@echo About to start Falcon.  Hit CTRL-C to abort or
pause                 

@REM Adjust the following line for your installation (remove the wrong name):
FALCON3.EXE
FALCONCD.EXE

attrib -h squad6.mis
copy squad6.mis squad0.mis
copy squad6.war squad0.war
copy squad6.cam squad0.cam                    
copy squad6.squ squad0.squ                    
copy squad6.mtv squad0.mtv                    
copy mission.6 mission.0

:end
CD \STRAT
STRAT.BAT %1 %2 %3 %4 %5 %6 %7 %8 %9
                          


                          
                   
