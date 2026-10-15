# Run Falcon 3.0 under the instrumented dosbox-staging build with tracing.
# Usage (from anywhere):
#   powershell -File tools\run_falcon_traced.ps1 [-Name menu] [-ReadMin 64]
# Output (default <repo>\memdump\, gitignored):
#   <name>_fileio.jsonl    INT 21h open/read/seek/close (filename, offset, buf seg:off)
#   <name>_fartrans.jsonl  far CALL/JMP targets + entry DS/ES histograms
#   <name>_meta.json       counters + config
param(
    [string]$Name = "",                       # trace prefix; default trace_<timestamp>
    [string]$GameDir = "",                    # default <repo>\game
    [string]$Exe = "",                        # default instrumented build
    [string]$GameExe = "FALCONCD.EXE",
    [string]$OutDir = "",                     # default <repo>\memdump
    [int]$ReadMin = -1,                       # FALCON_TRACE_READ_MIN; -1 = leave default (512)
    [int]$ThrottleMs = -1,                    # FALCON_TRACE_THROTTLE_MS; -1 = leave default (1)
    [string]$ExtraConfArgs = "",              # extra dosbox args, e.g. "-noconsole"
    [switch]$DryRun                           # print the command, don't launch
)
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
if (-not $GameDir) { $GameDir = Join-Path $root "game" }
if (-not $Exe)     { $Exe = Join-Path $root "src\dosbox-staging\build\falcon\dosbox_with_debugger.exe" }
if (-not $OutDir)  { $OutDir = Join-Path $root "memdump" }
if (-not $Name)    { $Name = "trace_" + (Get-Date -Format "yyyyMMdd_HHmmss") }

foreach ($p in @($Exe, $GameDir)) {
    if (-not (Test-Path $p)) { throw "not found: $p" }
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$env:FALCON_TRACE = Join-Path $OutDir $Name
if ($ReadMin -ge 0) { $env:FALCON_TRACE_READ_MIN = "$ReadMin" }
else { Remove-Item Env:FALCON_TRACE_READ_MIN -ErrorAction SilentlyContinue }
if ($ThrottleMs -ge 0) { $env:FALCON_TRACE_THROTTLE_MS = "$ThrottleMs" }
else { Remove-Item Env:FALCON_TRACE_THROTTLE_MS -ErrorAction SilentlyContinue }

$dosboxArgs = @(
    "-c", "config -set cpu core=normal",
    "-c", "mount c `"$GameDir`"",
    "-c", "c:",
    "-c", $GameExe
)
if ($ExtraConfArgs) { $dosboxArgs = @($ExtraConfArgs) + $dosboxArgs }

Write-Host "FALCON_TRACE = $env:FALCON_TRACE"
Write-Host "running: $Exe $($dosboxArgs -join ' ')"
if ($DryRun) { exit 0 }

& $Exe @dosboxArgs
$code = $LASTEXITCODE

Remove-Item Env:FALCON_TRACE -ErrorAction SilentlyContinue
Remove-Item Env:FALCON_TRACE_READ_MIN -ErrorAction SilentlyContinue
Remove-Item Env:FALCON_TRACE_THROTTLE_MS -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "dosbox exited with code $code; trace files:"
Get-ChildItem "$OutDir\$Name*" -ErrorAction SilentlyContinue |
    Select-Object Name, Length | Format-Table -AutoSize
