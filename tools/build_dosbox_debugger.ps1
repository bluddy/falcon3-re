# Configure + build src/dosbox-staging with debugger and Falcon trace hooks.
# Prereqs (2026-10-14): standalone LLVM (clang-cl), VS2022 Community (vcvars +
# MSVC headers/libs), bootstrapped vcpkg at $env:VCPKG_ROOT or default path.
# Usage: powershell -File tools\build_dosbox_debugger.ps1 [-BuildDir build\falcon]
param(
    [string]$StagingDir = "",
    [string]$VcpkgRoot = "",
    [string]$LLVMBin = "C:\Program Files\LLVM\bin",
    [string]$VcVars = "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat",
    [string]$BuildDir = "build\falcon",
    [switch]$ConfigureOnly
)
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
if (-not $StagingDir) { $StagingDir = Join-Path $root "src\dosbox-staging" }
if (-not $VcpkgRoot) {
    if ($env:VCPKG_ROOT) { $VcpkgRoot = $env:VCPKG_ROOT }
    else { $VcpkgRoot = "C:\Users\$env:USERNAME\tools\vcpkg" }
}
$toolchain = Join-Path $VcpkgRoot "scripts\buildsystems\vcpkg.cmake"
if (-not (Test-Path $toolchain)) { throw "vcpkg toolchain not found: $toolchain" }
if (-not (Test-Path $VcVars)) { throw "vcvars not found: $VcVars" }

$cmakeArgs = @(
    "-G", "Ninja",
    "-DCMAKE_BUILD_TYPE=Release",
    "-DOPT_DEBUGGER=ON",
    "-DOPT_TESTS=OFF",
    "-DCMAKE_TOOLCHAIN_FILE=$toolchain",
    "-DCMAKE_C_COMPILER=clang-cl",
    "-DCMAKE_CXX_COMPILER=clang-cl",
    "-S", $StagingDir,
    "-B", (Join-Path $StagingDir $BuildDir)
)
$configure = "set `"PATH=$LLVMBin;%PATH%`" && set `"VCPKG_ROOT=$VcpkgRoot`" && call `"$VcVars`" >nul && cmake $($cmakeArgs -join ' ')"
Write-Host ">> $configure"
cmd /c $configure
if ($LASTEXITCODE -ne 0) { throw "cmake configure failed ($LASTEXITCODE)" }
if ($ConfigureOnly) { exit 0 }

$build = "set `"PATH=$LLVMBin;%PATH%`" && set `"VCPKG_ROOT=$VcpkgRoot`" && call `"$VcVars`" >nul && cmake --build $(Join-Path $StagingDir $BuildDir)"
Write-Host ">> $build"
cmd /c $build
if ($LASTEXITCODE -ne 0) { throw "build failed ($LASTEXITCODE)" }
Write-Host "OK: $(Join-Path $StagingDir $BuildDir)\dosbox_with_debugger.exe"
