Add-Type @"
using System; using System.Runtime.InteropServices;
public class J9 { [StructLayout(LayoutKind.Sequential)] public struct I { public int Size, Flags, X, Y, Z, R, U, V, Buttons, BN, POV, a, b; }
 [DllImport("winmm.dll")] public static extern int joyGetPosEx(int id, ref I i); }
"@
$log="C:\Games\mr2-tools\trigger-test.log"; "t_ms Z buttons" | Set-Content $log
$sw=[Diagnostics.Stopwatch]::StartNew(); $last=-1
while($sw.ElapsedMilliseconds -lt 180000){ $i=New-Object J9+I; $i.Size=52; $i.Flags=255; [void][J9]::joyGetPosEx(0,[ref]$i)
  $z=[int]($i.Z/4096); if($z -ne $last -or $i.Buttons){ "$($sw.ElapsedMilliseconds) $($i.Z) $($i.Buttons)" | Add-Content $log; $last=$z }; Start-Sleep -m 50 }

