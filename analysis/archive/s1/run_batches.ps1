# run_batches.ps1: run plan/dry/apply/gates for findings 157-160 in sequence
$ROOT = "C:\Users\ybarnoy\projects\falcon3"
$IDAT = "C:\Program Files\IDA Professional 9.1\idat.exe"
$TOOL = "$ROOT\tools\apply_orphan_funcs.py"
$IDB  = "$ROOT\analysis\ida_falconcd\FALCONCD.EXE.i64"
$PROBE = "$ROOT\analysis\s1\probe.i64"

function Fix-CRLF {
    $p = "$ROOT\registry\orphan_funcs_expected.json"
    $bytes = [System.IO.File]::ReadAllBytes($p)
    $fixed = @()
    for ($i = 0; $i -lt $bytes.Length; $i++) {
        if ($bytes[$i] -eq 13 -and ($i+1) -lt $bytes.Length -and $bytes[$i+1] -eq 13) {
            # skip the extra CR
        } else {
            $fixed += $bytes[$i]
        }
    }
    [System.IO.File]::WriteAllBytes($p, $fixed)
}

foreach ($finding in 157, 158, 159, 160) {
    $step = "S1c-4 split merged functions (findings 145-$finding batches 1-$([int]($finding-144))) + orphan code registered (findings 126-144)"

    Write-Host "=== Finding $finding ==="

    # update finding number in manifest write
    $tool_content = Get-Content $TOOL -Raw
    $tool_content = $tool_content -replace '"finding": \d+, "step": "S1c-4 split merged functions \(findings 145-\d+ batches 1-\d+\)', "`"finding`": $finding, `"step`": `"$step"
    Set-Content $TOOL $tool_content -NoNewline

    # plan
    Remove-Item $PROBE -ErrorAction SilentlyContinue
    Copy-Item $IDB $PROBE
    $env:OFMODE = "plan"
    $env:OFLOG = "$ROOT\analysis\s1\of_plan_$finding.log"
    & $IDAT -A "-S$TOOL" $PROBE
    $r = $LASTEXITCODE
    Get-Content $env:OFLOG | Select-Object -Last 2
    if ($r -ne 0) { Write-Host "PLAN FAILED"; exit 1 }

    # fix CRLF
    Fix-CRLF

    # dry
    Remove-Item $PROBE -ErrorAction SilentlyContinue
    Copy-Item $IDB $PROBE
    Remove-Item env:OFMODE
    $env:OFDRY = "1"
    $env:OFLOG = "$ROOT\analysis\s1\of_dry_$finding.log"
    & $IDAT -A "-S$TOOL" $PROBE
    Get-Content $env:OFLOG | Select-Object -First 2
    if ($LASTEXITCODE -ne 0) { Write-Host "DRY FAILED"; exit 1 }

    # apply
    Remove-Item $PROBE -ErrorAction SilentlyContinue
    Remove-Item env:OFDRY
    Copy-Item $IDB "$ROOT\analysis\ida_falconcd\FALCONCD.EXE.i64.bak_split$finding"
    $env:OFLOG = "$ROOT\analysis\s1\of_apply_$finding.log"
    & $IDAT -A "-S$TOOL" $IDB
    if ($LASTEXITCODE -ne 0) { Write-Host "APPLY FAILED"; exit 1 }
    Get-Content $env:OFLOG | Select-Object -Last 1

    # idempotent
    Copy-Item $IDB $PROBE
    $env:OFDRY = "1"
    $env:OFLOG = "$ROOT\analysis\s1\of_idem_$finding.log"
    & $IDAT -A "-S$TOOL" $PROBE
    Get-Content $env:OFLOG | Select-Object -First 2
    if ($LASTEXITCODE -ne 0) { Write-Host "IDEM FAILED"; exit 1 }

    # gates
    Remove-Item $PROBE -ErrorAction SilentlyContinue
    Remove-Item env:OFDRY
    Copy-Item $IDB $PROBE
    & $IDAT -A "-S$ROOT\tools\extract_ida_bytes.py" $PROBE
    $env:ILOG = "$ROOT\analysis\s1\integrity_$finding.log"
    & $IDAT -A "-S$ROOT\analysis\s1\verify_idb_s1.py" $PROBE
    Write-Host "integrity exit $LASTEXITCODE"
    Get-Content $env:ILOG | Select-Object -Last 2
    Remove-Item $PROBE

    & python "$ROOT\tools\naming.py" check
    & python "$ROOT\tools\verify_rebuild.py" 2>&1 | Select-Object -First 15
    & python "$ROOT\tools\verify_rebuild.py" 2>&1 | Select-Object -Last 2

    Write-Host "=== Finding $finding DONE ==="
}
