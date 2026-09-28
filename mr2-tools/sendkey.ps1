# sendkey.ps1 - inject keys into the running Moto Racer 2 window, optionally screenshot
#   .\sendkey.ps1 -Key ENTER
#   .\sendkey.ps1 -Key DOWN,DOWN,ENTER -Shot C:\Games\mr2-tools\s1.png -Wait 2
param(
    [string[]]$Key = @(),
    [string]$Shot = "",
    [int]$Wait = 1,
    [int]$Gap = 350
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Text;
using System.Runtime.InteropServices;
public class INJ {
    [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern IntPtr FindWindow(string cls, string title);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern IntPtr SetFocus(IntPtr h);
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr a, IntPtr b, int x, int y, int cx, int cy, uint f);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, IntPtr p);
    [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
    [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint idAttach, uint idAttachTo, bool fAttach);
    [DllImport("user32.dll")]
    public static extern uint MapVirtualKey(uint uCode, uint uMapType);
    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);

    public const int SW_RESTORE = 9;

    // vkeys that are "extended" and need KEYEVENTF_EXTENDEDKEY (arrows, and most
    // of the right-hand cluster). Missing this makes DirectInput ignore the press.
    private static bool IsExtended(byte vk) {
        return vk == 0x25 || vk == 0x26 || vk == 0x27 || vk == 0x28   // LEFT UP RIGHT DOWN
            || vk == 0x24 || vk == 0x23 || vk == 0x2E                 // HOME END DELETE
            || vk == 0x2D                                            // INSERT
            || vk == 0x5B || vk == 0x5C;                             // LWIN RWIN
    }

    // Press+release WITH a real scan code. v1 passed scan=0, which the game (DirectInput)
    // did not accept — the menu never advanced even though focus was correct.
    public static void Tap(byte vk, int holdMs) {
        uint scan = MapVirtualKey((uint)vk, 0);              // MAPVK_VK_TO_VSC
        if (scan == 0) scan = 0x46;                          // F15-ish fallback, never 0
        uint down = IsExtended(vk) ? 0x0001u : 0u;           // KEYEVENTF_EXTENDEDKEY
        uint up   = down | 0x0002u;                          // + KEYEVENTF_KEYUP

        keybd_event(vk, (byte)scan, down, UIntPtr.Zero);
        System.Threading.Thread.Sleep(holdMs);
        keybd_event(vk, (byte)scan, up,   UIntPtr.Zero);
    }

    // Return the foreground window's title, or "" on failure.
    public static string ForegroundTitle() {
        var sb = new StringBuilder(256);
        GetWindowText(GetForegroundWindow(), sb, 256);
        return sb.ToString();
    }
}
'@

$VK = @{
    ENTER=0x0D; ESC=0x1B; ESCAPE=0x1B
    UP=0x26; DOWN=0x28; LEFT=0x25; RIGHT=0x27
    SPACE=0x20; TAB=0x09
    A=0x41; B=0x42; C=0x43; D=0x44; E=0x45; F=0x46; G=0x47
    H=0x48; I=0x49; J=0x4A; K=0x4B; L=0x4C; M=0x4D; N=0x4E
    O=0x4F; P=0x50; Q=0x51; R=0x52; S=0x53; T=0x54; U=0x55
    V=0x56; W=0x57; X=0x58; Y=0x59; Z=0x5A
    F1=0x70; F2=0x71; F3=0x72; F4=0x73; F5=0x74
}

# focus the game window
$proc = Get-Process moto -EA SilentlyContinue
if (-not $proc) { Write-Output "moto.exe not running"; exit 1 }
[INJ]::SetProcessDPIAware() | Out-Null

$gh = $proc.MainWindowHandle
if ($gh -eq [IntPtr]::Zero) { Write-Output "ABORT: game has no main window"; exit 1 }

# restore first if minimized, then raise (Note: .MainHandle does not exist - was the old bug)
if ([INJ]::IsIconic($gh)) {
    [INJ]::ShowWindow($gh, [INJ]::SW_RESTORE) | Out-Null
    Start-Sleep -Milliseconds 500
}

# Windows foreground-lock blocks SetForegroundWindow() when the caller is a background
# process - that is why the first ENTER went to the browser instead of the game.
# Attaching to the foreground thread's input queue is what actually makes the raise work.
$fg = [INJ]::GetForegroundWindow()
if ($fg -ne [IntPtr]::Zero -and $fg -ne $gh) {
    $fgT = [INJ]::GetWindowThreadProcessId($fg, [IntPtr]::Zero)
    $myT = [INJ]::GetCurrentThreadId()
    [INJ]::AttachThreadInput($myT, $fgT, $true) | Out-Null
    [INJ]::SetWindowPos($gh, [IntPtr]::Zero, 0, 0, 0, 0, 0x0001 -bor 0x0002) | Out-Null  # HWND_TOP, NOMOVE|NOSIZE
    [INJ]::SetForegroundWindow($gh) | Out-Null
    [INJ]::BringWindowToTop($gh) | Out-Null
    [INJ]::SetFocus($gh) | Out-Null
    [INJ]::AttachThreadInput($myT, $fgT, $false) | Out-Null
} else {
    [INJ]::SetForegroundWindow($gh) | Out-Null
    [INJ]::BringWindowToTop($gh) | Out-Null
}
Start-Sleep -Milliseconds 700

# SAFETY: never inject keys unless the GAME owns the foreground.
# Windows foreground-lock can silently leave focus where it was (e.g. a
# browser playing a video), which would send the keys there instead.
$fgNow = [INJ]::GetForegroundWindow()
if ($fgNow -ne $gh) {
    Write-Output "ABORT: could not focus the game (foreground now = `"$( [INJ]::ForegroundTitle() )`"). Keys NOT sent."
    exit 2
}

foreach ($k in $Key) {
    $code = $VK[$k.ToUpper()]
    if (-not $code) { Write-Output "unknown key: $k"; continue }
    [INJ]::Tap([byte]$code, 90) | Out-Null
    Start-Sleep -Milliseconds $Gap
}

Start-Sleep -Seconds $Wait

if ($Shot) {
    $b = [System.Windows.Forms.SystemInformation]::VirtualScreen
    $bmp = New-Object System.Drawing.Bitmap($b.Width, $b.Height)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($b.X, $b.Y, 0, 0, $bmp.Size)
    $bmp.Save($Shot)
    $g.Dispose(); $bmp.Dispose()
    Write-Output "keys sent: $($Key -join ',')  -> $Shot ($($b.Width)x$($b.Height))"
} else {
    Write-Output "keys sent: $($Key -join ',')"
}
