# padprofile.ps1 - write a Player-1 controller layout into the running Moto Racer 2.
# Table: 9 records x 24 bytes @ 0x6421CB (P1). Record: [+0 type 1=kbd 4=joy][+4 device#]
#   [+12 code: button# or axis#][+15 C0 = axis negative, A0 = axis positive, 00 = button]
# Order: LEFT RIGHT ACCEL BRAKE TURBO GEARUP GEARDOWN VIEW BACKVIEW
#   .\padprofile.ps1 -Profile auto|xbox|dualsense|keyboard [-Show]   (auto: Xbox VID 045E, DualSense 054C, else keyboard)
param([string]$Profile = "auto", [switch]$Show)

Add-Type @'
using System; using System.Runtime.InteropServices;
public static class PP {
  [DllImport("kernel32.dll")] public static extern IntPtr OpenProcess(int a, bool i, int pid);
  [DllImport("kernel32.dll")] public static extern bool ReadProcessMemory(IntPtr h, IntPtr a, byte[] b, int n, out int r);
  [DllImport("kernel32.dll")] public static extern bool WriteProcessMemory(IntPtr h, IntPtr a, byte[] b, int n, out int w);
  [StructLayout(LayoutKind.Sequential)] public struct I { public int Size, Flags, X, Y, Z, R, U, V, Buttons, BN, POV, a, b; }
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Auto)] public struct C { public ushort Mid, Pid; [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string Name;
    public int Xmin,Xmax,Ymin,Ymax,Zmin,Zmax,NumButtons,Pmin,Pmax,Rmin,Rmax,Umin,Umax,Vmin,Vmax,Caps,MaxAxes,NumAxes,MaxButtons;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string Reg; [MarshalAs(UnmanagedType.ByValTStr, SizeConst=260)] public string Oem; }
  [DllImport("winmm.dll")] public static extern int joyGetPosEx(int id, ref I i);
  [DllImport("winmm.dll", CharSet=CharSet.Auto)] public static extern int joyGetDevCaps(int id, ref C c, int sz);
  public static int FirstPadVid() {
    for (int id = 0; id < 16; id++) { var i = new I(); i.Size = Marshal.SizeOf(i); i.Flags = 255;
      if (joyGetPosEx(id, ref i) == 0) { var c = new C(); joyGetDevCaps(id, ref c, Marshal.SizeOf(c)); return c.Mid; } }
    return -1;
  }
}
'@
$P1 = 0x6421CB
# [code, flag] per function; flag C0/A0 = axis -/+, 0 = button
$layouts = @{
  # DirectInput DualSense: 1 Sq 2 X 3 O 4 Tri 5 L1 6 R1 7 L2 8 R2
  # as seen THROUGH the dinput.dll proxy (Xbox order): 1 Cross 2 Circle 3 Square 4 Tri - matches the launcher
  dualsense = @(@(1,0xC0),@(1,0xA0),@(8,0),@(7,0),@(1,0),@(6,0),@(5,0),@(4,0),@(3,0))
  # DirectInput Xbox: 1 A 2 B 3 X 4 Y 5 LB 6 RB 7 View 8 Menu. ACCEL/BRAKE entries here are replaced below.
  xbox      = @(@(1,0xC0),@(1,0xA0),@(3,0xC0),@(3,0xA0),@(1,0),@(6,0),@(5,0),@(4,0),@(3,0))
}
if ($Profile -eq 'auto') {
    $vid = [PP]::FirstPadVid()
    $Profile = switch ($vid) { 0x045E { 'xbox' } 0x054C { 'dualsense' } default { '' } }
    if (-not $Profile) { $Profile = 'keyboard' }   # no pad: original keyboard layout
}
$p = Get-Process moto -EA Stop
# 0x6421CB is only valid for the GOG build (moto.exe MD5 598D38990563...). Refuse anything else.
$md5 = (Get-FileHash $p.Path -Algorithm MD5).Hash
if (-not $md5.StartsWith("598D38990563")) { "REFUSED: $($p.Path) MD5 $md5 is not the GOG build - binding table address unknown"; exit 3 }
$h = [PP]::OpenProcess(0x0438, $false, $p.Id); $r = 0
if ($Profile -eq 'keyboard') { $b = [IO.File]::ReadAllBytes("$PSScriptRoot\p1-keyboard-bindings.bin") }
else { $b = New-Object byte[] 216 }
for ($f = 0; $f -lt 9 -and $Profile -ne 'keyboard'; $f++) {
    $o = $f * 24; $b[$o] = 4; $b[$o + 4] = 1
    $b[$o + 12] = [byte]$layouts[$Profile][$f][0]; $b[$o + 15] = [byte]$layouts[$Profile][$f][1]
}
# Xbox triggers: GAS/BRAKE become keyboard UP/DOWN records; padhelper.ps1 holds those keys from XInput RT/LT
# (DirectInput merges both triggers into one Z axis - direction ambiguous, both-pressed cancels).
if ($Profile -eq 'xbox') {
    $kb = [IO.File]::ReadAllBytes("$PSScriptRoot\p1-keyboard-bindings.bin")
    [Array]::Copy($kb, 2 * 24, $b, 2 * 24, 48)       # records 2,3 = ACCEL (UP), BRAKE (DOWN)
}
[void][PP]::WriteProcessMemory($h, [IntPtr]$P1, $b, 216, [ref]$r)
"profile $Profile written ($r bytes)"
if ($Show) {
    $c = New-Object byte[] 216; [void][PP]::ReadProcessMemory($h, [IntPtr]$P1, $c, 216, [ref]$r)
    $n = 'LEFT','RIGHT','ACCEL','BRAKE','TURBO','GEARUP','GEARDN','VIEW','BACKVW'
    for ($f = 0; $f -lt 9; $f++) { $o = $f * 24; "{0,-7} type={1} dev={2} code={3} flag={4:X2}" -f $n[$f], $c[$o], $c[$o + 4], $c[$o + 12], $c[$o + 15] }
}
