@echo off
BIN\BCC -c -ml -S probe\T.C > v1_noopt.log 2>&1
if exist T.ASM move /Y T.ASM v1_noopt.ASM >nul
if exist probe\T.ASM move /Y probe\T.ASM v1_noopt.ASM >nul
BIN\BCC -c -ml -1 -S probe\T.C > v2_186.log 2>&1
if exist T.ASM move /Y T.ASM v2_186.ASM >nul
if exist probe\T.ASM move /Y probe\T.ASM v2_186.ASM >nul
BIN\BCC -c -ml -2 -S probe\T.C > v3_286.log 2>&1
if exist T.ASM move /Y T.ASM v3_286.ASM >nul
if exist probe\T.ASM move /Y probe\T.ASM v3_286.ASM >nul
BIN\BCC -c -ml -O -1 -S probe\T.C > v4_O_186.log 2>&1
if exist T.ASM move /Y T.ASM v4_O_186.ASM >nul
if exist probe\T.ASM move /Y probe\T.ASM v4_O_186.ASM >nul
BIN\BCC -c -ml -O -2 -S probe\T.C > v5_O_286.log 2>&1
if exist T.ASM move /Y T.ASM v5_O_286.ASM >nul
if exist probe\T.ASM move /Y probe\T.ASM v5_O_286.ASM >nul
BIN\BCC -c -ml -O -S probe\T.C > v6_O.log 2>&1
if exist T.ASM move /Y T.ASM v6_O.ASM >nul
if exist probe\T.ASM move /Y probe\T.ASM v6_O.ASM >nul
exit