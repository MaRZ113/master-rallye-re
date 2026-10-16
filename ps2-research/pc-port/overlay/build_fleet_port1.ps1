$ErrorActionPreference='Stop'
$port=Split-Path $PSScriptRoot -Parent
$fixtures=@{
 MRR_FRONTEND_MODEL_ASSET='XTRAIL-COMPLETE.ps2model';MRR_RACE_MODEL_ASSET='XTRAIL-CAR.ps2model';MRR_WHEEL_MODEL_ASSET='XTRAIL-WHEEL-DRAW.ps2model';MRR_NATIVE_LAMP_FIXTURES='crew-port1-native-lamps.bin';MRR_DAMAGE_FIXTURES='xtrail-damage-fixtures.bin';MRR_HEADLIGHT_DAMAGE_FIXTURES='headlight-damage-fixtures.bin';MRR_FRONT_LAMP_DAMAGE_FIXTURES='front-lamp-damage-fixtures.bin';MRR_FLEET_GLOW_FIXTURES='fleet-port1-native-glow.bin';MRR_FLEET_CAR_FIXTURES='fleet-port1-native-car.bin';MRR_KIA_WHEEL_FIXTURES='kia-wheel-fixtures.bin';MRR_KIA_LAMP_FIXTURES='kia-off-on-glow-native.bin';MRR_KIA_DAMAGE_REPLAY='kia-damage-replay.bin';MRR_PORT3_LAMP_FIXTURES='port3-lamps-compact.bin';MRR_FLEET_OFF_LAMP_FIXTURES='fleet-off-lamp-native.bin';MRR_KIA_GLOW_HEALTHY='kia-glow-1226.bin';MRR_KIA_GLOW_DAMAGED='kia-glow-2800.bin';MRR_KIA_ON_GXI='KIA-BREAKLIGHTSON-TGA.GXI';MRR_PS2_GLOW_GXI='KIA-BREAKLIGHTSONGLOW-TGA.GXI'
}
foreach($entry in $fixtures.GetEnumerator()){
 $fixture=Join-Path $port ('.assets/vehicles/'+$entry.Value)
 if(!(Test-Path -LiteralPath $fixture)){throw ('Missing required local fixture: '+$fixture)}
 [Environment]::SetEnvironmentVariable($entry.Key,$fixture,'Process')
}
python (Join-Path $PSScriptRoot 'build_overlay.py')
if($LASTEXITCODE){throw ('Overlay build failed: '+$LASTEXITCODE)}
