# launch-mr2.ps1 - one double-click: Moto Racer 2, widescreen 2560x1440 @ 144 Hz,
# auto controller layout (Xbox or DualSense, whichever is plugged in) + PS/Xbox-style menus.
$wd = "C:\GOG Games\Moto Racer 2"
$tools = "C:\Games\mr2-tools"
$g = Start-Process -FilePath "$wd\moto.exe" -ArgumentList "-skipintro","-DontLimitFrameRate","-D3D","-FullScreen" -WorkingDirectory $wd -PassThru
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile","-WindowStyle","Hidden","-ExecutionPolicy","Bypass","-File","$tools\padhelper.ps1" -WindowStyle Hidden

# Race layout: write the matching Player-1 bindings once the game has loaded its settings.
# Written twice (4 s, 8 s) so a late settings load can't overwrite it. No controller = untouched.
for ($i = 0; $i -lt 30 -and -not $g.HasExited -and $g.MainWindowHandle -eq 0; $i++) { Start-Sleep 1; $g.Refresh() }
foreach ($wait in 4, 4) {
    Start-Sleep $wait
    if ($g.HasExited) { break }
    & "$tools\padprofile.ps1" -Profile auto | Out-File "$tools\padprofile-last.log"
}
