# build.ps1 - compile MotoRacer2Launcher.exe (needs only the .NET Framework 4 csc.exe that ships with Windows)
Set-Location $PSScriptRoot
if (-not (Test-Path moto.ico)) {
    Add-Type -AssemblyName System.Drawing
    $i = [System.Drawing.Icon]::ExtractAssociatedIcon("C:\GOG Games\Moto Racer 2\moto.exe"); $f = [IO.File]::Create("$PSScriptRoot\moto.ico"); $i.Save($f); $f.Close()
}
& "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /nologo /target:winexe /optimize+ /win32icon:moto.ico /r:System.Windows.Forms.dll /out:MotoRacer2Launcher.exe MotoRacer2Launcher.cs
if ($LASTEXITCODE -eq 0) { Copy-Item MotoRacer2Launcher.exe "C:\GOG Games\Moto Racer 2\" -Force; "built + installed to the game folder" }
