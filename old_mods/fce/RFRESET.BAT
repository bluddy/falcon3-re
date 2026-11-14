@Echo OFF
REM .NWS files are only in Full Install
if exist PANAMA.NWS goto :full

rem Remove Partial install files
for %%1 in ( HPL IPL MAP MFF MFI MFM MPL ) do if exist NELLIS.%%1 DEL NELLIS.%%1
for %%1 in ( MSF MSM NOT STM STR THE THM ) do if exist NELLIS.%%1 DEL NELLIS.%%1
goto :end

:full
rem Full installation
copy fcemap.* nellis.*
:end
