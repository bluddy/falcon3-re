# Smoke-run the instrumented libdosbox build (CMake, DOSBOX_CUSTOM=1,
# instrument profile) against Falcon 3.0 and capture custom-instrumentation
# output (stderr CUSTOM: lines).
# Usage (from anywhere):
#   powershell -File tools\run_libdosbox_smoke.ps1 [-Sec 25] [-Name smoke]
# Output (default <repo>\memdump\, gitignored):
#   <name>_stderr.txt / <name>_stdout.txt
param(
    [string]$Name = "",                       # output prefix; default smoke_<timestamp>
    [string]$GameDir = "",                    # default <repo>\game
    [string]$Exe = "",                        # default CMake instrument build
    [string]$GameExe = "FALCONCD.EXE",
    [string]$OutDir = "",                     # default <repo>\memdump
    [int]$Sec = 25,                           # how long to let dosbox run
    [switch]$DryRun                           # print the command, don't launch
)
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
if (-not $GameDir) { $GameDir = Join-Path $root "game" }
if (-not $Exe)     { $Exe = Join-Path $root "src\libdosbox\build\custom-instrument\Release\dosbox.exe" }
if (-not $OutDir)  { $OutDir = Join-Path $root "memdump" }
if (-not $Name)    { $Name = "smoke_" + (Get-Date -Format "yyyyMMdd_HHmmss") }

foreach ($p in @($Exe, $GameDir)) {
    if (-not (Test-Path $p)) { throw "not found: $p" }
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$errFile = Join-Path $OutDir "${Name}_stderr.txt"
$outFile = Join-Path $OutDir "${Name}_stdout.txt"

$dosboxArgs = @(
    "-c", "config -set cpu core=normal",
    "-c", "mount c `"$GameDir`"",
    "-c", "c:",
    "-c", $GameExe
)

# Run with CWD = build root so the copy_assets tree (glshaders/,
# translations/, ...) is found, matching scripts/build_custom.sh.
$workDir = Split-Path (Split-Path $Exe -Parent) -Parent
if (-not (Test-Path (Join-Path $workDir "glshaders"))) {
    $workDir = Split-Path $Exe -Parent
}

Write-Host "running: $Exe $($dosboxArgs -join ' ') (cwd=$workDir, ${Sec}s)"
if ($DryRun) { exit 0 }

$p = Start-Process -FilePath $Exe -ArgumentList $dosboxArgs `
    -WorkingDirectory $workDir -PassThru `
    -RedirectStandardError $errFile -RedirectStandardOutput $outFile
Start-Sleep -Seconds $Sec
if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force }
$p.WaitForExit(10000) | Out-Null

Write-Host ""
Write-Host "stderr ($((Get-Item $errFile).Length) bytes):"
Get-Content $errFile -ErrorAction SilentlyContinue |
    Select-String -Pattern 'CUSTOM|instrument|FATAL|assert' |
    Select-Object -First 40 | ForEach-Object { "  " + $_.Line }
Write-Host ""
Write-Host "stdout tail:"
Get-Content $outFile -Tail 8 -ErrorAction SilentlyContinue | ForEach-Object { "  " + $_ }
