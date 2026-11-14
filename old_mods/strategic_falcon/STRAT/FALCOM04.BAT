@echo off
@echo.
REM } Modify this file as appropriate for the pathnames of the 
REM } system(s) you're using, or set the FALCONDIR environment 
REM } variable before running it.  

if not exist %FALCONDIR%\falconcd.exe goto next
goto copyfile

:next              
if not exist %FALCONDIR%\falcon3.exe goto next0
goto copyfile             

:next0
if not exist c:\falconcd\falconcd.exe goto next1
SET FALCONDIR=C:\FALCONCD
goto copyfile
             
:next1       
if not exist c:\falconcd\falcon3.exe goto next2
SET FALCONDIR=C:\FALCONCD 
goto copyfile 
                     
:next2                    
if not exist c:\falcon3\falconcd.exe goto next3
SET FALCONDIR=C:\FALCON3 
goto copyfile 

:next3                    
if not exist c:\falcon3\falcon3.exe goto next4
SET FALCONDIR=C:\FALCON3 
goto copyfile 

:next4         
if not exist d:\falconcd\falconcd.exe goto next5
SET FALCONDIR=D:\FALCONCD 
goto copyfile 

:next5                                          
if not exist d:\falconcd\falcon3.exe goto next6
SET FALCONDIR=D:\FALCONCD 
goto copyfile 

:next6                    
if not exist d:\falcon3\falconcd.exe goto next7
SET FALCONDIR=D:\FALCON3 
goto copyfile 

:next7                    
if not exist d:\falcon3\falcon3.exe goto next8
SET FALCONDIR=D:\FALCON3 
goto copyfile 

:next8
@echo.
@echo I've looked in 8 likely directories; that's about as heroic as I get. 
@echo I can't find your FALCON 3.0 installation.
@echo.
@echo You're going to have to copy SQUAD6.MIS there yourself and then set its
@echo read-only bit (ATTRIB +R SQUAD6.MIS). You may want to set the environment
@echo variable FALCONDIR on this machine to make my life easier the next time.
@echo Use the syntax SET FALCONDIR=C:\FALCON3 from the DOS prompt, or better
@echo yet, place it in your AUTOEXEC.BAT file.
@echo.
goto end                                                                 
        
:copyfile  
if not exist squad6.mis goto baddisk
attrib -r -h %FALCONDIR%\squad6.mis       
copy squad6.mis %FALCONDIR%
attrib +r %FALCONDIR%\squad6.mis       
goto report                     

:baddisk
@echo There is no SQUAD6.MIS on this disk!  I've got nothing to do!
goto end
                                                                 
:report                                                                  
@echo.
@echo SQUAD6.MIS has been copied to %FALCONDIR%. 
@echo.
@echo If you have more than one copy of Falcon installed, this may not be 
@echo the correct directory.
@echo.                                                                     
@echo This system is ready for the next COMMS mission.
@echo.
goto end
        
:end
