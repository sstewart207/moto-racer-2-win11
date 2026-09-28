# volcheck.ps1 - mute a process's Windows audio session IMMEDIATELY (default), or
#                optionally read its volume accurately first.
#
#   .\volcheck.ps1              -> mute the instant the session appears (SILENT, default)
#   .\volcheck.ps1 -NoMute      -> read only
#   .\volcheck.ps1 -Accurate    -> wait for a stable reading BEFORE muting.
#                                  *** DELAYS THE MUTE ~1-2s => PLAYS MUSIC AT FULL
#                                  VOLUME. ONLY WHEN THE MACHINE IS FREE. ***
param(
    [string]$Proc = "moto",
    [int]$TimeoutMs = 45000,
    [switch]$NoMute,
    [switch]$Accurate
)

$src = @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
public class MMDeviceEnumerator { }

[ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"),
 InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IMMDeviceEnumerator {
    int EnumAudioEndpoints(int dataFlow, int stateMask, out IntPtr ppDevices);
    [PreserveSig] int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice ppDevice);
    [PreserveSig] int GetDevice([MarshalAs(UnmanagedType.LPWStr)] string id, out IMMDevice ppDevice);
    int Reg(IntPtr c); int Unreg(IntPtr c);
}

[ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"),
 InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IMMDevice {
    [PreserveSig] int Activate(ref Guid iid, int clsCtx, IntPtr act,
        [MarshalAs(UnmanagedType.IUnknown)] out object pp);
    int OpenPropertyStore(int a, out IntPtr p);
    [PreserveSig] int GetId([MarshalAs(UnmanagedType.LPWStr)] out string id);
    [PreserveSig] int GetState(out int s);
}

[ComImport, Guid("77AA99A0-1BD6-484F-8BC7-2C654C9A9B6F"),
 InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IAudioSessionManager2 {
    int GetAudioSessionControl(IntPtr g, int f, out IntPtr c);
    int Initialize(IntPtr c);
    [PreserveSig] int GetSessionEnumerator(out IAudioSessionEnumerator e);
    int Reg(IntPtr n); int Unreg(IntPtr n); int RegD(IntPtr n); int UnregD(IntPtr n);
}

[ComImport, Guid("E2F5BB11-0570-40CA-ACDD-3AA01277DEE8"),
 InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IAudioSessionEnumerator {
    [PreserveSig] int GetCount(out int c);
    [PreserveSig] int GetSession(int i, out IAudioSessionControl2 s);
}

[ComImport, Guid("BFB7FF88-7239-4FC9-8FA2-07C950BE9C6D"),
 InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IAudioSessionControl2 {
    [PreserveSig] int GetState(out int s);
    int GetDisplayName(IntPtr s); int SetDisplayName(IntPtr s);
    int GetIconPath(IntPtr s); int SetIconPath(IntPtr s);
    int GetGroupingParam(out Guid g); int SetGroupingParam(ref Guid g);
    int Reg(IntPtr n); int Unreg(IntPtr n);
    int GetSessionIdentifier(IntPtr s);
    int GetSessionInstanceIdentifier(IntPtr s);
    [PreserveSig] int GetProcessId(out uint pid);
    [PreserveSig] int IsSystemSoundsSession();
    int SetDuckingPreference(int d);
}

[ComImport, Guid("87CE5498-68D6-44E5-9215-6DA47EF883D8"),
 InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface ISimpleAudioVolume {
    [PreserveSig] int SetMasterVolume(float level, IntPtr eventCtx);
    [PreserveSig] int GetMasterVolume(out float level);
    [PreserveSig] int SetMute(int mute, IntPtr eventCtx);
    [PreserveSig] int GetMute(out int mute);
}

public static class VolCheck {
    static ISimpleAudioVolume Find(string procName) {
        var en = (IMMDeviceEnumerator)new MMDeviceEnumerator();
        IMMDevice dev;
        if (en.GetDefaultAudioEndpoint(0, 1, out dev) != 0 || dev == null) return null;
        object o;
        Guid im = typeof(IAudioSessionManager2).GUID;
        if (dev.Activate(ref im, 23, IntPtr.Zero, out o) != 0 || o == null) return null;
        var mgr = (IAudioSessionManager2)o;
        IAudioSessionEnumerator se;
        if (mgr.GetSessionEnumerator(out se) != 0 || se == null) return null;
        int n; se.GetCount(out n);
        for (int i = 0; i < n; i++) {
            IAudioSessionControl2 s;
            if (se.GetSession(i, out s) != 0 || s == null) continue;
            uint pid; s.GetProcessId(out pid);
            string nm = "";
            try { nm = System.Diagnostics.Process.GetProcessById((int)pid).ProcessName; } catch { }
            if (!string.Equals(nm, procName, StringComparison.OrdinalIgnoreCase)) continue;
            IntPtr unk = Marshal.GetIUnknownForObject(s);
            IntPtr simp;
            Guid iq = new Guid("87CE5498-68D6-44E5-9215-6DA47EF883D8");
            int hr = Marshal.QueryInterface(unk, ref iq, out simp);
            Marshal.Release(unk);
            if (hr != 0 || simp == IntPtr.Zero) continue;
            var sv = (ISimpleAudioVolume)Marshal.GetObjectForIUnknown(simp);
            Marshal.Release(simp);
            return sv;
        }
        return null;
    }

    // Read the session volume, then optionally mute it.
    //
    // accurate = FALSE (DEFAULT): mute the INSTANT the session appears. Never delays.
    //            This is the only mode that is safe when the user may be listening to
    //            something else - it is what you want ~always.
    // accurate = TRUE  (OPT-IN, `-Accurate`): wait for two consecutive matching reads
    //            before acting, so the value reported is the one config.bin produced.
    //            *** THIS DELAYS THE MUTE BY ~1-2 SECONDS AND WILL PLAY MUSIC AT FULL
    //            VOLUME. DO NOT USE IT UNLESS THE USER HAS SAID THE MACHINE IS FREE. ***
    //            It exists only for the Rule 5 volume question, which needs an accurate
    //            reading rather than a fast one.
    public static string ReadThenMute(string procName, int timeoutMs, bool mute, bool accurate) {
        var sw = System.Diagnostics.Stopwatch.StartNew();
        ISimpleAudioVolume sv = null;
        while (sw.ElapsedMilliseconds < timeoutMs) {
            sv = Find(procName);
            if (sv != null) break;
            System.Threading.Thread.Sleep(50);
        }
        if (sv == null)
            return "TIMEOUT: no session for '" + procName + "' after " + timeoutMs + " ms";

        // ---- DEFAULT PATH: silence first, ask questions later. ----
        if (mute && !accurate) {
            sv.SetMasterVolume(0f, IntPtr.Zero);
            float v2; int m2;
            sv.GetMasterVolume(out v2); sv.GetMute(out m2);
            return String.Format("MUTED IMMEDIATELY at {0} ms  (now vol={1}%{2})",
                sw.ElapsedMilliseconds, (int)Math.Round(v2 * 100), m2 == 1 ? " MUTED" : "");
        }

        // ---- OPT-IN ACCURATE PATH (silent machines only) ----
        float last = -1f;
        int stable = 0;
        string trace = "";
        int guard = 0;
        while (sw.ElapsedMilliseconds < timeoutMs && guard++ < 40) {
            float v; int m;
            if (sv.GetMasterVolume(out v) != 0 || sv.GetMute(out m) != 0) {
                System.Threading.Thread.Sleep(200); continue;
            }
            trace += String.Format("[{0}ms {1}%{2}] ", sw.ElapsedMilliseconds,
                                   (int)Math.Round(v * 100), m == 1 ? " MUT" : "");
            if (Math.Abs(v - last) < 0.001f) stable++; else stable = 0;
            last = v;
            if (stable >= 2) break;
            System.Threading.Thread.Sleep(400);
        }

        int fm;
        string before = "vol=" + (int)Math.Round(last * 100) + "%";
        if (sv.GetMute(out fm) == 0) before += (fm == 1 ? " MUTED" : " unmuted");

        string after = "";
        if (mute) {
            sv.SetMasterVolume(0f, IntPtr.Zero);
            float v3; int m3;
            sv.GetMasterVolume(out v3);
            sv.GetMute(out m3);
            after = "  ->  after: vol=" + (int)Math.Round(v3 * 100) + "%" + (m3 == 1 ? " MUTED" : " unmuted");
        }
        return before + after + String.Format("   (settled {0} ms; {1})", sw.ElapsedMilliseconds, trace);
    }
}
'@

Add-Type -TypeDefinition $src -ErrorAction Stop
[VolCheck]::ReadThenMute($Proc, $TimeoutMs, (-not $NoMute), [bool]$Accurate)
