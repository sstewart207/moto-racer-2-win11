# padinject.ps1 - press virtual joystick buttons / D-pad in Moto Racer 2 through the dinput.dll
# proxy's test hook (shared memory "Local\MR2PadInject"). Button numbers are what the GAME sees
# (1-based, after the proxy's DualSense re-ordering). POV in degrees (0 up, 90 right, 180 down, 270 left).
#   .\padinject.ps1 -Button 1            # tap game button 1 for 150 ms
#   .\padinject.ps1 -Pov 180             # tap D-pad down
#   .\padinject.ps1 -Button 2 -Hold 2000
param([int]$Button = 0, [int]$Pov = -1, [int]$Hold = 150)
$mmf = [IO.MemoryMappedFiles.MemoryMappedFile]::CreateOrOpen("Local\MR2PadInject", 12)
$v = $mmf.CreateViewAccessor()
$mask = if ($Button -gt 0) { [uint32](1 -shl ($Button - 1)) } else { [uint32]0 }
$v.Write(4, $mask); $v.Write(8, [int]($(if ($Pov -ge 0) { $Pov * 100 } else { -1 })))
$v.Write(0, [uint32]0x5032524D)                       # 'MR2P' - arm
Start-Sleep -Milliseconds $Hold
$v.Write(4, [uint32]0); $v.Write(8, [int]-1)          # release
Start-Sleep -Milliseconds 200                         # let the game see the release before the block goes away
$v.Write(0, [uint32]0); $v.Dispose(); $mmf.Dispose()
"injected button=$Button pov=$Pov for $Hold ms"
