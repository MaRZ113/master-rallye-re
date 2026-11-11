<#
  Widescreen matrix for the Menu Builder runtime (Windows PowerShell 5.1).
    run_ws_matrix.ps1 -GameHost <host with renderer + layout> -Out <evidence dir> [-Cli <mrmenu.exe>] [-Project <demo>]
  For every renderer configuration the host's MRRRenderer.ini is changed (restored at the end), ws.autotest runs,
  the real OS mouse clicks VEHICLE CONFIG > MODEL SOURCE (mrdrive.ps1) and the editor renders the same screens at the
  same client size and interface mode for comparison (<case>/editor-*.png).
#>
param([Parameter(Mandatory)][string]$GameHost, [Parameter(Mandatory)][string]$Out, [string]$Cli = "", [string]$Project = "")
$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$GameHost = (Resolve-Path $GameHost).Path
New-Item -ItemType Directory -Force $Out | Out-Null; $Out = (Resolve-Path $Out).Path
if (-not $Cli) { $Cli = Join-Path $here "..\MenuBuilder.Cli\bin\Release\net8.0\mrmenu.exe" }
if (-not $Project) { $Project = Join-Path $here "..\..\..\examples\menu-builder\demo.mrmenu.json" }
$ini = Join-Path $GameHost "MRRRenderer.ini"
$backup = Get-Content $ini -Raw
$cases = @(
  @{ name = "margins-16x9-borderless"; mode = 2; w = 0; h = 0; ws = 2; ui = 2 },
  @{ name = "centered-16x9-borderless"; mode = 2; w = 0; h = 0; ws = 1; ui = 1 },
  @{ name = "stock-16x9-borderless"; mode = 2; w = 0; h = 0; ws = 0; ui = 0 },
  @{ name = "margins-4x3-window-1024x768"; mode = 1; w = 1024; h = 768; ws = 2; ui = 2 },
  @{ name = "margins-21x9-window-1680x720"; mode = 1; w = 1680; h = 720; ws = 2; ui = 2 }
)
function SetIni([string]$text, [string]$key, [string]$value) { return [regex]::Replace($text, "(?m)^$key\s*=.*$", "$key = $value") }
$summary = @()
try {
  foreach ($c in $cases) {
    $dir = Join-Path $Out $c.name; New-Item -ItemType Directory -Force $dir | Out-Null
    $t = SetIni $backup "Mode" $c.mode; $t = SetIni $t "Width" $c.w; $t = SetIni $t "Height" $c.h; $t = SetIni $t "Widescreen" $c.ws
    Set-Content $ini $t -Encoding ASCII -NoNewline
    $job = Start-Job -ArgumentList $GameHost, $here -ScriptBlock {
      param($GameHost, $here)
      $log = Join-Path $GameHost "MenuBuilder\MenuBuilder.log"; $t0 = Get-Date
      while (((Get-Date) - $t0).TotalSeconds -lt 90) {
        Start-Sleep -Milliseconds 300
        if ((Test-Path $log) -and ((Get-Content $log -Raw) -match "TEST note ready-for-os-mouse")) { break }
      }
      Start-Sleep -Milliseconds 800
      $mode = if ((Get-Content $log -Raw) -match "variant=\S+ mode=(\d)") { $Matches[1] } else { "0" }
      & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $here "mrdrive.ps1") info
      & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $here "mrdrive.ps1") click 150 392 $mode
    }
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $here "run_runtime_check.ps1") -GameHost $GameHost -Test (Join-Path $here "ws.autotest") -Out $dir -TimeoutSec 150 | Tee-Object -Variable res | Out-Null
    $mouse = Receive-Job $job -Wait; Remove-Job $job
    $lines = Get-Content (Join-Path $dir "MenuBuilder.log")
    $click = ($lines | Select-String "MOUSE_CLICK scene=MB_VehicleConfig button=1 egg=VC_Model").Count -gt 0
    $action = ($lines | Select-String "ACTION vehicle.model_source").Count -gt 0
    $info = ($mouse | Select-String "client=") -replace ".*client=(\S+).*", '$1'
    $size = if ($info) { $info } else { "1920x1080" }
    $redirect = ($lines | Select-String "REDIRECT scene=MB_VehicleConfig" | Select-Object -First 1).Line
    foreach ($s in @("MainMenu", "QuickRace", "VehicleConfig")) {
      $aspect = $size -replace "x", "x"
      & $Cli render --game $GameHost --project $Project --screen $s --aspect $aspect --size $size --mode $c.ui --out (Join-Path $dir "editor-$s.png") | Out-Null
    }
    $summary += [pscustomobject]@{ case = $c.name; result = ($res -join " "); client = $size; os_click_hit = $click; os_click_action = $action; served = ($redirect -replace ".*variant=(\S+) mode=(\d) ratio=(\S+).*", 'variant=$1 mode=$2 ratio=$3') }
  }
} finally {
  Set-Content $ini $backup -Encoding ASCII -NoNewline
}
$summary | Format-Table -AutoSize | Out-String -Width 250
$summary | ConvertTo-Json | Set-Content (Join-Path $Out "matrix.json") -Encoding UTF8
