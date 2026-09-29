# aabench.ps1 - measure frame rate + render->display latency for each dgVoodoo [DirectX]
# Antialiasing value, using the game's self-playing title-screen demo race (no input needed).
# Restores dgVoodoo.conf and config.bin afterwards. Mute first (sysmute.ps1 -Mute).
#   .\aabench.ps1 -Values 4x,2x,off -Seconds 8
param([string[]]$Values = @('4x', '2x', 'off'), [int]$Seconds = 8, [int]$DemoWait = 24)
$wd = "C:\GOG Games\Moto Racer 2"; $t = $PSScriptRoot
$conf = "$wd\dgVoodoo.conf"; $orig = Get-Content $conf; $cfg = [IO.File]::ReadAllBytes("$wd\data\config.bin")
$dx = ($orig | Select-String '^\[DirectX\]').LineNumber
$aa = ($orig | Select-String '^Antialiasing\s*=' | ? LineNumber -gt $dx | select -First 1).LineNumber - 1
try {
  foreach ($v in $Values) {
    $c = $orig.Clone(); $c[$aa] = "Antialiasing                        = $v"; $c | Set-Content $conf
    $g = Start-Process "$wd\moto.exe" -ArgumentList "-skipintro","-DontLimitFrameRate","-D3D","-FullScreen" -WorkingDirectory $wd -PassThru
    Start-Sleep $DemoWait                                            # title screen -> demo race starts by itself
    $csv = "$t\fps-aa-$v.csv"; Remove-Item $csv -EA 0
    $pm = Start-Process "$t\PresentMon.exe" -ArgumentList "--process_name","moto.exe","--output_file",$csv,"--no_console_stats","--stop_existing_session" -PassThru -WindowStyle Hidden
    Start-Sleep $Seconds; Stop-Process -Id $pm.Id -Force -EA 0
    & "$t\shot.ps1" -Out "$t\aa-$v.png" | Out-Null
    Stop-Process -Id $g.Id -Force -EA 0; Start-Sleep 2
    $r = & C:\Python314\python.exe "$t\fpsreport.py" $csv 2>&1
    $fps = ($r | Select-String 'displayed to screen').Line -replace '.*median=\s*([\d.]+).*', '$1'
    $lat = ($r | Select-String 'render->display latency').Line -replace '.*median=\s*([\d.]+) ms.*', '$1'
    $gpu = ($r | Select-String 'GPU time').Line -replace '.*median=\s*([\d.]+) ms.*', '$1'
    "AA={0,-5} fps={1,6}  latency={2,6} ms  gpu={3,6} ms" -f $v, $fps, $lat, $gpu
  }
} finally {
  $orig | Set-Content $conf; [IO.File]::WriteAllBytes("$wd\data\config.bin", $cfg)
  "restored dgVoodoo.conf + config.bin"
}
