# padhelper.ps1 - PlayStation-style menu/pause control for Moto Racer 2 with a DualSense.
# The game can only bind RACE controls to a gamepad; menus and pause are keyboard-only.
# This turns pad presses into keys, ONLY while moto.exe is the foreground window:
#   DualSense: Options/Circle -> ESC, Cross -> ENTER   Xbox: Menu/B -> ESC, A -> ENTER   D-pad -> arrows
#   Xbox only: RT held -> UP held (gas), LT held -> DOWN held (brake), read via XInput (padprofile binds ACCEL/BRAKE to UP/DOWN)
# Race controls (R2/L2/X/R1/L1/Tri/Square/stick) are read by the game itself - untouched.
# Waits up to 60 s for moto.exe, exits when it closes. Started by launch-mr2.ps1.
Add-Type @'
using System; using System.Runtime.InteropServices; using System.Diagnostics; using System.Threading;
public static class Pad {
  [StructLayout(LayoutKind.Sequential)] struct JI { public int Size, Flags, X, Y, Z, R, U, V, Buttons, ButtonNumber, POV, R1, R2; }
  [DllImport("winmm.dll")] static extern int joyGetPosEx(int id, ref JI i);
  [DllImport("user32.dll")] static extern void keybd_event(byte vk, byte scan, uint f, UIntPtr e);
  [DllImport("user32.dll")] static extern uint MapVirtualKey(uint c, uint t);
  [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Auto)] struct JC { public ushort Mid, Pid; [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string Name;
    public int a1,a2,a3,a4,a5,a6,NumButtons,a8,a9,a10,a11,a12,a13,a14,a15,Caps,MaxAxes,NumAxes,MaxButtons;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string Reg; [MarshalAs(UnmanagedType.ByValTStr, SizeConst=260)] public string Oem; }
  [DllImport("winmm.dll", CharSet=CharSet.Auto)] static extern int joyGetDevCaps(int id, ref JC c, int sz);
  [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  // XInput: real, separate RT/LT (DirectInput merges them into one ambiguous Z axis).
  [StructLayout(LayoutKind.Sequential)] struct XS { public uint Packet; public ushort Buttons; public byte LT, RT; public short LX, LY, RX, RY; }
  [DllImport("xinput1_4.dll")] static extern int XInputGetState(int user, out XS s);
  static bool gasDown, brakeDown;
  static void Hold(byte vk, byte sc, ref bool state, bool want) {       // extended arrow key down/up on change
    if (want == state) return; keybd_event(vk, sc, want ? 1u : 3u, UIntPtr.Zero); state = want;
  }
  static void Tap(byte vk, bool ext) {
    byte sc = (byte)MapVirtualKey(vk, 0); uint f = ext ? 1u : 0u;
    keybd_event(vk, sc, f, UIntPtr.Zero); Thread.Sleep(60); keybd_event(vk, sc, f | 2u, UIntPtr.Zero);
  }
  static bool GameFocused(int pid) { uint p; GetWindowThreadProcessId(GetForegroundWindow(), out p); return p == pid; }
  public static void Run(int pid) {
    var ji = new JI(); ji.Size = Marshal.SizeOf(ji); ji.Flags = 0xFF;
    int prevB = 0, prevPov = -1; int joy = -1;
    int bPause = 1 << 9, bBack = 1 << 2, bOk = 1 << 1;                   // DualSense: Options, Circle, Cross
    bool xbox = false;
    Process game = Process.GetProcessById(pid);
    while (!game.HasExited) {
      if (joy < 0) { for (int i = 0; i < 4; i++) if (joyGetPosEx(i, ref ji) == 0) { joy = i;
          var jc = new JC(); joyGetDevCaps(i, ref jc, Marshal.SizeOf(jc));
          xbox = jc.Mid == 0x045E;
          if (xbox) { bPause = 1 << 7; bBack = 1 << 1; bOk = 1 << 0; }   // Xbox: Menu, B, A
          else { bPause = 1 << 9; bBack = 1 << 2; bOk = 1 << 1; }
          break; } if (joy < 0) { Thread.Sleep(1000); continue; } }
      if (joyGetPosEx(joy, ref ji) != 0) { joy = -1; continue; }           // unplugged: rescan
      int b = ji.Buttons, pressed = b & ~prevB;
      int pov = ji.POV == 0xFFFF ? -1 : ji.POV / 100;                      // degrees, -1 = centred
      bool focused = GameFocused(pid);
      if (xbox) {                                                         // RT = gas (UP), LT = brake (DOWN)
        int rt = 0, lt = 0; for (int u = 0; u < 4; u++) { XS s; if (XInputGetState(u, out s) == 0) { rt = s.RT; lt = s.LT; break; } }
        Hold(0x26, 0x48, ref gasDown,   focused && rt > 30);
        Hold(0x28, 0x50, ref brakeDown, focused && lt > 30);
      }
      if (focused) {
        if ((pressed & bPause) != 0) Tap(0x1B, false);                      // Options / Menu -> ESC
        if ((pressed & bBack) != 0) Tap(0x1B, false);                       // Circle / B -> ESC
        if ((pressed & bOk) != 0) Tap(0x0D, false);                         // Cross / A -> ENTER
        if (pov != prevPov && pov >= 0) {
          if (pov >= 315 || pov <= 45) Tap(0x26, true);                    // up
          else if (pov < 135) Tap(0x27, true);                             // right
          else if (pov <= 225) Tap(0x28, true);                            // down
          else Tap(0x25, true);                                            // left
        }
      }
      prevB = b; prevPov = pov; Thread.Sleep(10);
    }
    Hold(0x26, 0x48, ref gasDown, false); Hold(0x28, 0x50, ref brakeDown, false);   // never leave a key stuck
  }
}
'@
$deadline = (Get-Date).AddSeconds(60)
while (-not ($g = Get-Process moto -EA 0) -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 500 }
if ($g) { [Pad]::Run(@($g)[0].Id) }
