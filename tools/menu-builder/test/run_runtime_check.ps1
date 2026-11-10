<#
  Runs an in-game Menu Builder check in an isolated game host and collects evidence.
    run_runtime_check.ps1 -Host <game dir> -Test <file.autotest> -Out <evidence dir> [-TimeoutSec 240]
  The host must already contain dinput8.dll (Menu Builder runtime) and an installed layout
  (mrmenu install). The script arms [Diagnostics] AutoTest, starts MRallye.exe, captures every
  screenshot the runtime requests (PrintWindow, no focus change, no synthetic OS input), waits for
  TEST_DONE, stops the game and copies MenuBuilder.log, live dumps and screenshots to -Out.
#>
param([Parameter(Mandatory)][string]$GameHost, [Parameter(Mandatory)][string]$Test, [Parameter(Mandatory)][string]$Out, [int]$TimeoutSec = 240,
      [string]$Launcher = "")   # optional: start through a launcher command (e.g. the SDK candidate's Launch-Extra-Options.cmd)
$ErrorActionPreference = "Stop"
$mb = Join-Path $GameHost "MenuBuilder"
$driver = Join-Path $PSScriptRoot "mrdrive.ps1"
Copy-Item $Test (Join-Path $mb (Split-Path $Test -Leaf)) -Force
$ini = Join-Path $mb "MenuBuilder.ini"
$text = (Get-Content $ini -Raw) -replace "(?m)^AutoTest=.*\r?\n?", ""
$text = $text.TrimEnd() + "`r`nAutoTest=$(Split-Path $Test -Leaf)`r`n"
Set-Content $ini $text -Encoding ASCII
Remove-Item (Join-Path $mb "MenuBuilder.log"), (Join-Path $mb "shots"), (Join-Path $mb "live") -Recurse -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force (Join-Path $mb "shots"), $Out | Out-Null
if ($Launcher) {
  $l = Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"$Launcher`"" -WorkingDirectory (Split-Path $Launcher) -PassThru -WindowStyle Hidden
  $p = $null; $t0 = Get-Date
  while (-not $p -and ((Get-Date) - $t0).TotalSeconds -lt 60) { Start-Sleep -Milliseconds 500; $p = Get-Process MRallye -ErrorAction SilentlyContinue | Select-Object -First 1 }
  if (-not $p) { "RESULT launcher did not start MRallye.exe"; exit 2 }
} else {
  $p = Start-Process -FilePath (Join-Path $GameHost "MRallye.exe") -WorkingDirectory $GameHost -PassThru
}
$deadline = (Get-Date).AddSeconds($TimeoutSec); $done = $false
while ((Get-Date) -lt $deadline -and -not $p.HasExited) {
  Start-Sleep -Milliseconds 200
  foreach ($req in Get-ChildItem (Join-Path $mb "shots") -Filter *.req -ErrorAction SilentlyContinue) {
    $png = Join-Path $Out ($req.BaseName + ".png")
    & powershell -NoProfile -ExecutionPolicy Bypass -File $driver shot $png | Out-Null
    Remove-Item $req.FullName -ErrorAction SilentlyContinue
  }
  $log = Join-Path $mb "MenuBuilder.log"
  if ((Test-Path $log) -and ((Get-Content $log -Raw) -match "TEST_DONE")) { $done = $true; break }
}
$crashed = $p.HasExited
if (-not $p.HasExited) { Start-Sleep -Milliseconds 500; Stop-Process -Id $p.Id -Force }
Copy-Item (Join-Path $mb "MenuBuilder.log") $Out -Force -ErrorAction SilentlyContinue
if (Test-Path (Join-Path $mb "live")) { Copy-Item (Join-Path $mb "live") (Join-Path $Out "live") -Recurse -Force }
$lines = if (Test-Path (Join-Path $Out "MenuBuilder.log")) { Get-Content (Join-Path $Out "MenuBuilder.log") } else { @() }
$pass = ($lines | Select-String "TEST PASS").Count; $fail = ($lines | Select-String "TEST FAIL").Count
"RESULT done=$done crashed=$crashed pass=$pass fail=$fail evidence=$Out"
$lines | Select-String "TEST FAIL" | ForEach-Object { $_.Line }
