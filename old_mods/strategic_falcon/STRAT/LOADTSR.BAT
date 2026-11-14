@echo off
@lt.exe %1 %2 %3 %4 %5 %6 %7 %8 %9
@if exist STRTTEMP.BAT call STRTTEMP.BAT
@if exist STRTTEMP.BAT del STRTTEMP.BAT
