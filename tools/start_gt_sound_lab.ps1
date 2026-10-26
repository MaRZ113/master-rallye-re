param(
    [string]$SourceRoot = 'E:\Games\GT_Model-Tools',
    [string]$PitchCore = '',
    [int]$Port = 0
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$privateRun = Join-Path $repoRoot ('scratch\gt_sound_lab\browser-' + [guid]::NewGuid().ToString('N'))
$arguments = @(
    (Join-Path $PSScriptRoot 'gt_sound_lab.py'),
    '--gt4-root', (Join-Path $SourceRoot 'VOL\GT4-Beta_Extracted\extracted'),
    '--gt3-volume', (Join-Path $SourceRoot 'VOL\GT3_Extracted\GT3.VOL')
)
if ($PitchCore) { $arguments += @('--pitch-core', $PitchCore) }
$arguments += @('serve', '--output', $privateRun, '--port', $Port)
& python @arguments
exit $LASTEXITCODE
