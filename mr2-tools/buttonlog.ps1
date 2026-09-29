Add-Type @"
using System; using System.Runtime.InteropServices;
public class JR { [StructLayout(LayoutKind.Sequential)] public struct I { public int Size, Flags, X, Y, Z, R, U, V, Buttons, BN, POV, a, b; }
 [DllImport("winmm.dll")] public static extern int joyGetPosEx(int id, ref I i); }
"@
$log="C:\Games\mr2-tools\buttons-bt.log"; "" | Set-Content $log; $prev=0; $sw=[Diagnostics.Stopwatch]::StartNew()
while($sw.ElapsedMilliseconds -lt 120000){ $i=New-Object JR+I; $i.Size=52; $i.Flags=255; [void][JR]::joyGetPosEx(0,[ref]$i)
  $new=$i.Buttons -band -bnot $prev; for($b=0;$b -lt 16;$b++){ if($new -band (1 -shl $b)){ "{0:N1}s  button {1} (bit {2})" -f ($sw.ElapsedMilliseconds/1000),($b+1),$b | Add-Content $log } }
  $prev=$i.Buttons; Start-Sleep -m 15 }
