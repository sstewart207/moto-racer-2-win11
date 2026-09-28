# memscan.ps1 - find Moto Racer 2's controller-binding table in the live process.
# Searches for Player 1's known keyboard bindings (LEFT RIGHT UP DOWN SPACE Q W E TAB)
# as either DirectInput scan codes or Windows VK codes, at any stride 1..64 bytes.
#   .\memscan.ps1                 -> list hits
#   .\memscan.ps1 -Dump 0xADDR -Len 512   -> hex dump
param([string]$Dump = "", [int]$Len = 512)

Add-Type @'
using System; using System.Collections.Generic; using System.Runtime.InteropServices;
public static class MS {
  [DllImport("kernel32.dll")] static extern IntPtr OpenProcess(int a, bool i, int pid);
  [DllImport("kernel32.dll")] static extern bool ReadProcessMemory(IntPtr h, IntPtr a, byte[] b, int n, out int r);
  [DllImport("kernel32.dll")] static extern int VirtualQueryEx(IntPtr h, IntPtr a, out MBI m, int l);
  [StructLayout(LayoutKind.Sequential)] public struct MBI { public IntPtr Base, AllocBase; public int AllocProt; public IntPtr Size; public int State, Protect, Type; }
  public static IntPtr Open(int pid) { return OpenProcess(0x0410 | 0x0020 | 0x0008, false, pid); }
  public static byte[] Read(IntPtr h, long a, int n) { var b = new byte[n]; int r; ReadProcessMemory(h, (IntPtr)a, b, n, out r); return b; }
  public static List<string> Scan(IntPtr h, byte[] pat) {
    var hits = new List<string>(); long a = 0x10000; MBI m;
    while (a < 0x7FFF0000 && VirtualQueryEx(h, (IntPtr)a, out m, Marshal.SizeOf(typeof(MBI))) != 0) {
      long sz = (long)m.Size;
      if (m.State == 0x1000 && (m.Protect & 0xEE) != 0 && (m.Protect & 0x100) == 0 && sz < 0x10000000) {
        var b = new byte[sz]; int r; ReadProcessMemory(h, m.Base, b, (int)sz, out r);
        for (int s = 1; s <= 64; s++)
          for (long i = 0; i + 8 * s < r; i++) {
            bool ok = true;
            for (int k = 0; k < pat.Length && ok; k++) ok = b[i + k * s] == pat[k];
            if (ok) hits.Add(string.Format("0x{0:X8} stride={1}", (long)m.Base + i, s));
          }
      }
      a = (long)m.Base + sz;
    }
    return hits;
  }
}
'@
$p = Get-Process moto -EA Stop
$h = [MS]::Open($p.Id)
if ($Dump) {
    $a = [Convert]::ToInt64($Dump, 16); $b = [MS]::Read($h, $a, $Len)
    for ($i = 0; $i -lt $Len; $i += 16) { "{0:X8}  {1}" -f ($a + $i), (($b[$i..($i + 15)] | % { '{0:X2}' -f $_ }) -join ' ') }
    exit
}
"DInput scan codes:"; [MS]::Scan($h, [byte[]](0xCB, 0xCD, 0xC8, 0xD0, 0x39, 0x10, 0x11, 0x12, 0x0F))
"VK codes:";          [MS]::Scan($h, [byte[]](0x25, 0x27, 0x26, 0x28, 0x20, 0x51, 0x57, 0x45, 0x09))
