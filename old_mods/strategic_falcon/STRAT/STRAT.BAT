@echo off
sf.exe /OK %1 %2 %3 %4 %5 %6 %7 %8 
if exist TEMPSTRT.BAT call TEMPSTRT /OK %1 %2 %3 %4 %5 %6 %7 %8 
if exist TEMPSTRT.BAT del TEMPSTRT.BAT
