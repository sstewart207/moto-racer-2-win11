// MotoRacer2Launcher.exe - one double-click: Moto Racer 2 (GOG) in widescreen 1440p/144 Hz with
// DualSense / Xbox / keyboard controls. Replaces launch-mr2.ps1 + padprofile.ps1 + padhelper.ps1.
//
//  1. Starts moto.exe (with its intro movie) -DontLimitFrameRate -D3D -FullScreen (dgVoodoo does the 1440p/144 Hz).
//  2. Writes the Player-1 binding table for whichever pad is plugged in (re-written if you swap pads;
//     a change takes effect at the next race start).
//  3. While the game is in front: pad -> menu keys (D-pad arrows, A/Cross = ENTER, B/Circle/Menu/Options
//     = ESC) and, for Xbox, RT/LT via XInput -> held gas/brake keys (DirectInput merges the triggers).
//  4. Exits when the game exits. Never patches moto.exe; refuses to write memory for any other build.
//
// Build: csc /target:winexe /win32icon:moto.ico /out:MotoRacer2Launcher.exe MotoRacer2Launcher.cs
using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Threading;
using System.Windows.Forms;

static class Launcher
{
    const string GameDir = @"C:\GOG Games\Moto Racer 2";
    const string GameExe = GameDir + @"\moto.exe";
    const string GogMd5Prefix = "598D38990563";          // binding table address below is only valid for this build
    const int P1Table = 0x6421CB;                          // 9 records x 24 bytes

    // ---- Win32 ---------------------------------------------------------------------------------
    [DllImport("kernel32.dll")] static extern IntPtr OpenProcess(int access, bool inherit, int pid);
    // nSize / lpNumberOfBytesWritten are SIZE_T: must be pointer-sized on 64-bit Windows.
    [DllImport("kernel32.dll")] static extern bool WriteProcessMemory(IntPtr h, IntPtr a, byte[] b, UIntPtr n, out UIntPtr w);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
    [DllImport("user32.dll")] static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
    [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);

    [StructLayout(LayoutKind.Sequential)] struct JoyInfo { public int Size, Flags, X, Y, Z, R, U, V, Buttons, ButtonNumber, POV, Res1, Res2; }
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)] struct JoyCaps
    {
        public ushort Mid, Pid; [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string Name;
        public int Xmin, Xmax, Ymin, Ymax, Zmin, Zmax, NumButtons, PeriodMin, PeriodMax, Rmin, Rmax, Umin, Umax, Vmin, Vmax, Caps, MaxAxes, NumAxes, MaxButtons;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string RegKey; [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)] public string OemVxD;
    }
    [DllImport("winmm.dll")] static extern int joyGetPosEx(int id, ref JoyInfo info);
    [DllImport("winmm.dll", CharSet = CharSet.Auto)] static extern int joyGetDevCaps(int id, ref JoyCaps caps, int size);

    [StructLayout(LayoutKind.Sequential)] struct XState { public uint Packet; public ushort Buttons; public byte LT, RT; public short LX, LY, RX, RY; }
    [DllImport("xinput1_4.dll")] static extern int XInputGetState(int user, out XState s);

    // ---- binding table --------------------------------------------------------------------------
    // Order: LEFT RIGHT ACCEL BRAKE TURBO GEARUP GEARDOWN VIEW BACKVIEW
    // Keyboard record: [+0 type=1][+4 dev=1][+12 DIK code][+16 1][+18 scan][+19 extended]
    static readonly int[,] Keys = { { 0xCB, 0x4B, 1 }, { 0xCD, 0x4D, 1 }, { 0xC8, 0x48, 1 }, { 0xD0, 0x50, 1 },
                                    { 0x39, 0x39, 0 }, { 0x10, 0x10, 0 }, { 0x11, 0x11, 0 }, { 0x12, 0x12, 0 }, { 0x0F, 0x0F, 0 } };
    // Joystick record: [+0 type=4][+4 dev = game joystick #, 1-based][+12 button# or axis#][+15 C0 axis-, A0 axis+, 0 button]
    // DualSense AS THE GAME SEES IT through dinput.dll proxy (Xbox order): 1 Cross 2 Circle 3 Square 4 Tri 5 L1 6 R1 7 L2 8 R2
    static readonly int[,] DualSense = { { 1, 0xC0 }, { 1, 0xA0 }, { 8, 0 }, { 7, 0 }, { 1, 0 }, { 6, 0 }, { 5, 0 }, { 4, 0 }, { 3, 0 } };
    // Xbox (DirectInput): 1 A 2 B 3 X 4 Y 5 LB 6 RB. ACCEL/BRAKE (-1) stay keyboard UP/DOWN, fed from XInput RT/LT.
    static readonly int[,] Xbox = { { 1, 0xC0 }, { 1, 0xA0 }, { -1, 0 }, { -1, 0 }, { 1, 0 }, { 6, 0 }, { 5, 0 }, { 4, 0 }, { 3, 0 } };

    enum Pad { None, Xbox, DualSense }

    static byte[] BuildTable(Pad pad, int gameJoy)
    {
        var t = new byte[216];
        int[,] joy = pad == Pad.Xbox ? Xbox : pad == Pad.DualSense ? DualSense : null;
        for (int f = 0; f < 9; f++)
        {
            int o = f * 24;
            if (joy == null || joy[f, 0] < 0)
            {
                t[o] = 1; t[o + 4] = 1; t[o + 12] = (byte)Keys[f, 0];
                t[o + 16] = 1; t[o + 18] = (byte)Keys[f, 1]; t[o + 19] = (byte)Keys[f, 2];
            }
            else { t[o] = 4; t[o + 4] = (byte)gameJoy; t[o + 12] = (byte)joy[f, 0]; t[o + 15] = (byte)joy[f, 1]; }
        }
        return t;
    }

    static int FindJoystick(out Pad pad, out int gameJoy)
    {
        pad = Pad.None; gameJoy = 0;
        for (int id = 0; id < 16; id++)
        {
            var ji = new JoyInfo { Size = Marshal.SizeOf(typeof(JoyInfo)), Flags = 0xFF };
            if (joyGetPosEx(id, ref ji) != 0) continue;
            var jc = new JoyCaps(); joyGetDevCaps(id, ref jc, Marshal.SizeOf(typeof(JoyCaps)));
            gameJoy++;                                       // the game numbers present joysticks 1, 2, ...
            if (jc.Mid == 0x045E) { pad = Pad.Xbox; return id; }
            if (jc.Mid == 0x054C) { pad = Pad.DualSense; return id; }
            // unsupported device (wheel, vJoy, ...): keep scanning for a supported pad
        }
        return -1;
    }

    static bool WriteTable(Process game, Pad pad, int gameJoy)
    {
        IntPtr h = OpenProcess(0x0438, false, game.Id);
        if (h == IntPtr.Zero) return false;
        UIntPtr w; var t = BuildTable(pad, gameJoy);
        bool ok = WriteProcessMemory(h, (IntPtr)P1Table, t, (UIntPtr)t.Length, out w) && w.ToUInt64() == (ulong)t.Length;
        CloseHandle(h); return ok;
    }

    // ---- input helper ---------------------------------------------------------------------------
    static void Key(byte vk, byte scan, bool ext, bool down) { keybd_event(vk, scan, (ext ? 1u : 0u) | (down ? 0u : 2u), UIntPtr.Zero); }
    static void Tap(byte vk, byte scan, bool ext) { Key(vk, scan, ext, true); Thread.Sleep(60); Key(vk, scan, ext, false); }
    static bool Focused(Process game) { uint p; GetWindowThreadProcessId(GetForegroundWindow(), out p); return p == game.Id; }

    static readonly string LogPath = Path.Combine(Path.GetTempPath(), "MotoRacer2Launcher.log");
    static void Log(string msg) { try { File.AppendAllText(LogPath, DateTime.Now.ToString("HH:mm:ss.fff ") + msg + Environment.NewLine); } catch { } }

    static void Fail(string msg) { MessageBox.Show(msg, "Moto Racer 2 launcher", MessageBoxButtons.OK, MessageBoxIcon.Error); }

    [STAThread]
    static void Main(string[] args)
    {
        if (args.Length == 2 && args[0] == "--selftest")        // dump the three tables for byte-for-byte checks
        {
            File.WriteAllBytes(Path.Combine(args[1], "table-keyboard.bin"), BuildTable(Pad.None, 1));
            File.WriteAllBytes(Path.Combine(args[1], "table-xbox.bin"), BuildTable(Pad.Xbox, 1));
            File.WriteAllBytes(Path.Combine(args[1], "table-dualsense.bin"), BuildTable(Pad.DualSense, 1));
            return;
        }
        if (!File.Exists(GameExe)) { Fail("Can't find " + GameExe); return; }
        bool knownBuild;
        using (var md5 = MD5.Create()) using (var s = File.OpenRead(GameExe))
            knownBuild = BitConverter.ToString(md5.ComputeHash(s)).Replace("-", "").StartsWith(GogMd5Prefix);
        if (Process.GetProcessesByName("moto").Length > 0) { Fail("Moto Racer 2 is already running."); return; }

        var game = Process.Start(new ProcessStartInfo(GameExe, "-DontLimitFrameRate -D3D -FullScreen") { WorkingDirectory = GameDir, UseShellExecute = false });
        for (int i = 0; i < 300 && !game.HasExited && game.MainWindowHandle == IntPtr.Zero; i++) { Thread.Sleep(100); game.Refresh(); }

        var started = Stopwatch.StartNew();
        Pad pad; int gameJoy; int joy = FindJoystick(out pad, out gameJoy);
        try { File.Delete(LogPath); } catch { }
        Log("start: knownBuild=" + knownBuild + " pad=" + pad + " joy=" + joy + " gameJoy=" + gameJoy + " window=" + game.MainWindowHandle);
        Pad written = (Pad)(-1); int writes = 0;
        int prevButtons = 0, prevPov = -1;
        bool gas = false, brake = false; long lastDetect = 0;

        while (!game.HasExited)
        {
            // Re-detect the pad every ~2 s (hot-plug / swap), and write the table at 4 s and 8 s after start
            // (a late settings load must not overwrite it) and whenever the pad type changes.
            if (started.ElapsedMilliseconds - lastDetect > 2000) { joy = FindJoystick(out pad, out gameJoy); lastDetect = started.ElapsedMilliseconds; }
            long ms = started.ElapsedMilliseconds;
            if (knownBuild && ((writes == 0 && ms > 4000) || (writes == 1 && ms > 8000) || (writes >= 2 && pad != written)))
            { bool ok = WriteTable(game, pad, gameJoy); Log("write #" + writes + " pad=" + pad + " at " + ms + " ms ok=" + ok); if (ok) { written = pad; writes++; } else writes++; }

            bool focus = Focused(game);
            int buttons = 0, pov = -1;
            if (joy >= 0)
            {
                var ji = new JoyInfo { Size = Marshal.SizeOf(typeof(JoyInfo)), Flags = 0xFF };
                if (joyGetPosEx(joy, ref ji) == 0) { buttons = ji.Buttons; pov = ji.POV == 0xFFFF ? -1 : ji.POV / 100; }
            }
            int pressed = buttons & ~prevButtons;
            int bPause = pad == Pad.Xbox ? 1 << 7 : 1 << 9;   // Menu / Options
            int bBack  = pad == Pad.Xbox ? 1 << 1 : 1 << 2;   // B / Circle


            if (pad == Pad.Xbox)
            {
                int rt = 0, lt = 0;
                for (int u = 0; u < 4; u++) { XState s; if (XInputGetState(u, out s) == 0) { rt = s.RT; lt = s.LT; break; } }
                bool wantGas = focus && rt > 30, wantBrake = focus && lt > 30;
                if (wantGas != gas) { Key(0x26, 0x48, true, wantGas); gas = wantGas; }          // UP = gas
                if (wantBrake != brake) { Key(0x28, 0x50, true, wantBrake); brake = wantBrake; } // DOWN = brake
            }
            if (focus && pad != Pad.None)
            {
                if ((pressed & bPause) != 0 || (pressed & bBack) != 0) Tap(0x1B, 0x01, false); // ESC
                // OK (A / Cross) is NOT sent: the game natively treats joystick button 1 as OK, and the
                // dinput.dll proxy makes Cross = button 1. Sending ENTER too would double-select.
                if (pov >= 0 && pov != prevPov)
                {
                    if (pov >= 315 || pov <= 45) Tap(0x26, 0x48, true);
                    else if (pov < 135) Tap(0x27, 0x4D, true);
                    else if (pov <= 225) Tap(0x28, 0x50, true);
                    else Tap(0x25, 0x4B, true);
                }
            }
            prevButtons = buttons; prevPov = pov;
            Thread.Sleep(10);
        }
        if (gas) Key(0x26, 0x48, true, false);
        if (brake) Key(0x28, 0x50, true, false);
    }
}
