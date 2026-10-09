$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$outputDir = Join-Path $repoRoot '.research-output\r-mod1'
$outputExe = Join-Path $outputDir 'core-tests-x86.exe'
$outputObj = Join-Path $outputDir 'core-tests-x86.obj'
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'

if (-not (Test-Path -LiteralPath $vswhere)) {
    throw 'Visual Studio vswhere.exe is required for the x86 core check.'
}

$installPath = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if ($LASTEXITCODE -ne 0 -or -not $installPath) {
    throw 'Visual Studio x86/x64 C++ tools were not found.'
}

$vcvars = Join-Path $installPath 'VC\Auxiliary\Build\vcvarsall.bat'
if (-not (Test-Path -LiteralPath $vcvars)) {
    throw 'vcvarsall.bat was not found in the selected Visual Studio installation.'
}

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
$source = Join-Path $repoRoot 'tests\rmod1\core_tests.cpp'
$buildAndRun = 'call "{0}" x86 >nul && cl /nologo /EHsc /std:c++17 /W4 /WX "{1}" /Fo:"{2}" /Fe:"{3}" && "{3}"' -f $vcvars, $source, $outputObj, $outputExe
& cmd.exe /d /s /c $buildAndRun
if ($LASTEXITCODE -ne 0) {
    throw "R-MOD1 x86 shared-core test failed with exit code $LASTEXITCODE."
}
