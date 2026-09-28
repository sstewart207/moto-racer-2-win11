# shot.ps1 - screenshot WITH the mouse cursor composited in
#   .\shot.ps1 C:\Games\mr2-tools\x.png
param([string]$Out = "C:\Games\mr2-tools\shot.png")

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class CAP {
    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int x; public int y; }
    [StructLayout(LayoutKind.Sequential)]
    public struct CURSORINFO {
        public int cbSize;
        public int flags;
        public IntPtr hCursor;
        public POINT ptScreenPos;
    }
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool GetCursorInfo(ref CURSORINFO pci);
    [DllImport("user32.dll")] public static extern bool DrawIcon(IntPtr hdc, int x, int y, IntPtr hIcon);
    public const int CURSOR_SHOWING = 0x00000001;
}
'@

[CAP]::SetProcessDPIAware() | Out-Null
$b = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap($b.Width, $b.Height)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($b.X, $b.Y, 0, 0, $bmp.Size)

$ci = New-Object CAP+CURSORINFO
$ci.cbSize = [System.Runtime.InteropServices.Marshal]::SizeOf($ci)
$cursorInfo = $null
$drawn = $false
if ([CAP]::GetCursorInfo([ref]$ci)) {
    if (($ci.flags -band [CAP]::CURSOR_SHOWING) -ne 0 -and $ci.hCursor -ne [IntPtr]::Zero) {
        $hdc = $g.GetHdc()
        # cursor hotspot is at ptScreenPos; icons draw from top-left, offset by ~half size is wrong,
        # DrawIcon places the icon's top-left at (x,y) - use the documented cursor position directly
        $ok = [CAP]::DrawIcon($hdc, $ci.ptScreenPos.x - $b.X, $ci.ptScreenPos.y - $b.Y, $ci.hCursor)
        $g.ReleaseHdc($hdc)
        $drawn = $ok
        $cursorInfo = "cursor @ ({0},{1})  hCursor={2}  drawn={3}" -f $ci.ptScreenPos.x, $ci.ptScreenPos.y, $ci.hCursor, $ok
    } else { $cursorInfo = "cursor hidden" }
} else { $cursorInfo = "GetCursorInfo failed" }

$bmp.Save($Out)
$g.Dispose(); $bmp.Dispose()
Write-Output "saved $Out ($($b.Width)x$($b.Height))  $cursorInfo"
