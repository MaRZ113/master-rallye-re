param(
    [string]$PublicIniPath,
    [switch]$G2
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$outputDir = Join-Path $repoRoot '.research-output\r-mod1'
$suffix = if ($G2) { '-g2' } else { '' }
$outputExe = Join-Path $outputDir ("core-tests-x86{0}.exe" -f $suffix)
$outputObj = Join-Path $outputDir ("core-tests-x86{0}.obj" -f $suffix)
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
$publicIni = if ($PublicIniPath) { (Resolve-Path -LiteralPath $PublicIniPath).Path } else { Join-Path $repoRoot 'research\r-mod1\MRallyeRandomizer.release.ini' }
$defines = if ($G2) { '/DRMOD3_G1_DUPLICATE_REPEAT_FALLBACK=1 /DRMOD3_G2_PLAYER_OVERRIDE=1' } else { '' }
$buildAndRun = 'call "{0}" x86 >nul && cl /nologo /EHsc /std:c++17 /W4 /WX {1} "{2}" /Fo:"{3}" /Fe:"{4}" && "{4}" "{5}"' -f $vcvars, $defines, $source, $outputObj, $outputExe, $publicIni
& cmd.exe /d /s /c $buildAndRun
if ($LASTEXITCODE -ne 0) {
    throw "R-MOD1 x86 shared-core test failed with exit code $LASTEXITCODE."
}
