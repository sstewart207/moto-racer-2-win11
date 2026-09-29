# audiopeak.ps1 - live output level of the game's audio sessions (works while speakers are muted:
# the session meter reads the stream before the endpoint). Prints max peak per second.
#   .\audiopeak.ps1 -Seconds 40 [-Proc moto]
param([int]$Seconds = 30, [string]$Proc = "moto")
Add-Type -TypeDefinition @'
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

[ComImport, Guid("5CD021D7-CD9E-4D34-AE2C-48CDFF45818E"),
 InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IAudioEndpointVolume {
    int A(); int B(); int C();
    int SetMasterVolumeLevel(float l, IntPtr e);
    int SetMasterVolumeLevelScalar(float l, IntPtr e);
    int GetMasterVolumeLevel(out float l);
    [PreserveSig] int GetMasterVolumeLevelScalar(out float l);
    int H(); int I(); int J(); int K();
    int SetMute(int m, IntPtr e);
    [PreserveSig] int GetMute(out int m);
    int N(); int O(); int P(); int Q(); int R();
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

[ComImport, Guid("E2F5BB11-0570-40CA-ACDD-3AA01277DEE8"),
 InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IAudioSessionEnumerator {
    [PreserveSig] int GetCount(out int c);
    [PreserveSig] int GetSession(int i, out IAudioSessionControl2 s);
}

[ComImport, Guid("77AA99A0-1BD6-484F-8BC7-2C654C9A9B6F"),
 InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IAudioSessionManager2 {
    int GetAudioSessionControl(IntPtr g, int f, out IntPtr c);
    int Initialize(IntPtr c);
    [PreserveSig] int GetSessionEnumerator(out IAudioSessionEnumerator e);
    int Reg(IntPtr n); int Unreg(IntPtr n); int RegD(IntPtr n); int UnregD(IntPtr n);
}

[ComImport, Guid("87CE5498-68D6-44E5-9215-6DA47EF883D8"),
 InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface ISimpleAudioVolume {
    [PreserveSig] int SetMasterVolume(float level, IntPtr eventCtx);
    [PreserveSig] int GetMasterVolume(out float level);
    [PreserveSig] int SetMute(int mute, IntPtr eventCtx);
    [PreserveSig] int GetMute(out int mute);
}

public static class AudioProbe {

    public static string SessionVolume(object sessionControl2) {
        try {
            IntPtr unk = Marshal.GetIUnknownForObject(sessionControl2);
            IntPtr simp;
            Guid iq = new Guid("87CE5498-68D6-44E5-9215-6DA47EF883D8");
            int hr = Marshal.QueryInterface(unk, ref iq, out simp);
            Marshal.Release(unk);
            if (hr != 0 || simp == IntPtr.Zero) return "vol=?(QI hr=0x" + hr.ToString("X8") + ")";
            var sv = (ISimpleAudioVolume)Marshal.GetObjectForIUnknown(simp);
            Marshal.Release(simp);
            float lv; int mm;
            string v = "vol=?";
            if (sv.GetMasterVolume(out lv) == 0) v = "vol=" + ((int)Math.Round(lv * 100)) + "%";
            string m = "mute=?";
            if (sv.GetMute(out mm) == 0) m = mm == 1 ? "MUTED" : "unmuted";
            return v + " " + m;
        } catch (Exception e) { return "vol=ERR " + e.Message; }
    }


    public static string[] Defaults() {
        var en = (IMMDeviceEnumerator)new MMDeviceEnumerator();
        var r = new List<string>();
        for (int role = 0; role < 3; role++) {
            IMMDevice dev;
            int hr = en.GetDefaultAudioEndpoint(0, role, out dev);
            if (hr != 0 || dev == null) {
                r.Add("role" + role + ": <none hr=0x" + hr.ToString("X8") + ">");
                continue;
            }
            string id; dev.GetId(out id);
            object o;
            Guid iv = typeof(IAudioEndpointVolume).GUID;
            float vol = -1f; int mute = -1;
            if (dev.Activate(ref iv, 23, IntPtr.Zero, out o) == 0 && o != null) {
                var v = (IAudioEndpointVolume)o;
                v.GetMasterVolumeLevelScalar(out vol);
                v.GetMute(out mute);
            }
            r.Add(String.Format("role{0}: vol={1} mute={2}\n        id={3}",
                role, (vol < 0 ? "?" : ((int)(vol * 100)) + "%"),
                mute == 1 ? "MUTED" : "no", id));
        }
        return r.ToArray();
    }

    public static string SetSessionVolume(string filter, float level) {
        var en = (IMMDeviceEnumerator)new MMDeviceEnumerator();
        IMMDevice dev;
        if (en.GetDefaultAudioEndpoint(0, 1, out dev) != 0 || dev == null) return "no default device";
        object o;
        Guid im = typeof(IAudioSessionManager2).GUID;
        if (dev.Activate(ref im, 23, IntPtr.Zero, out o) != 0 || o == null) return "cannot activate mgr";
        var mgr = (IAudioSessionManager2)o;
        IAudioSessionEnumerator se;
        if (mgr.GetSessionEnumerator(out se) != 0 || se == null) return "cannot enumerate";
        int n; se.GetCount(out n);
        string f = (filter ?? "").ToLower();
        int changed = 0;
        for (int i = 0; i < n; i++) {
            IAudioSessionControl2 s;
            if (se.GetSession(i, out s) != 0 || s == null) continue;
            uint pid; s.GetProcessId(out pid);
            string nm = "";
            try { nm = System.Diagnostics.Process.GetProcessById((int)pid).ProcessName; } catch { }
            if (nm.ToLower() != f) continue;
            IntPtr unk = Marshal.GetIUnknownForObject(s);
            IntPtr simp;
            Guid iq = new Guid("87CE5498-68D6-44E5-9215-6DA47EF883D8");
            int hr = Marshal.QueryInterface(unk, ref iq, out simp);
            Marshal.Release(unk);
            if (hr != 0 || simp == IntPtr.Zero) continue;
            var sv = (ISimpleAudioVolume)Marshal.GetObjectForIUnknown(simp);
            Marshal.Release(simp);
            if (sv.SetMasterVolume(level, IntPtr.Zero) == 0) changed++;
        }
        return changed + " session(s) set to " + ((int)Math.Round(level * 100)) + "%";
    }

    public static string[] Sessions(string filter) {
        var en = (IMMDeviceEnumerator)new MMDeviceEnumerator();
        IMMDevice dev;
        if (en.GetDefaultAudioEndpoint(0, 1, out dev) != 0 || dev == null)
            return new string[] { "no default multimedia device" };
        object o;
        Guid im = typeof(IAudioSessionManager2).GUID;
        if (dev.Activate(ref im, 23, IntPtr.Zero, out o) != 0 || o == null)
            return new string[] { "cannot activate IAudioSessionManager2" };
        var mgr = (IAudioSessionManager2)o;
        IAudioSessionEnumerator se;
        if (mgr.GetSessionEnumerator(out se) != 0 || se == null)
            return new string[] { "cannot enumerate sessions" };
        int n; se.GetCount(out n);
        var r = new List<string>();
        r.Add("total audio sessions on default device: " + n);
        int shown = 0;
        string f = (filter ?? "").ToLower();
        for (int i = 0; i < n; i++) {
            IAudioSessionControl2 s;
            if (se.GetSession(i, out s) != 0 || s == null) continue;
            uint pid; s.GetProcessId(out pid);
            int st; s.GetState(out st);
            string nm = "";
            try { nm = System.Diagnostics.Process.GetProcessById((int)pid).ProcessName; }
            catch { nm = "?"; }
            bool match = (f.Length == 0) || (nm.ToLower() == f);
            if (!match) continue;
            shown++;
            r.Add(String.Format("   pid={0,-7} name={1,-16} state={2} ({3})  {4}",
                pid, nm, st, st == 1 ? "ACTIVE" : st == 0 ? "inactive" : "expired",
                SessionVolume(s)));
        }
        if (shown == 0)
            r.Add("   NO session for '" + filter + "' -> that process is not rendering audio");
        return r.ToArray();
    }
}

[ComImport, Guid("C02216F6-8C67-4B5B-9D00-D008E73E0064"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IAudioMeterInformation { [PreserveSig] int GetPeakValue(out float p); }
public static class Peak {
    // highest current peak (0..1) across all audio sessions owned by the given process name, on the default device
    public static float Of(string proc) {
        var en = (IMMDeviceEnumerator)new MMDeviceEnumerator(); IMMDevice dev;
        if (en.GetDefaultAudioEndpoint(0, 1, out dev) != 0) return -1;
        object o; Guid im = typeof(IAudioSessionManager2).GUID;
        if (dev.Activate(ref im, 23, IntPtr.Zero, out o) != 0) return -1;
        IAudioSessionEnumerator se; ((IAudioSessionManager2)o).GetSessionEnumerator(out se);
        int n; se.GetCount(out n); float best = -1;
        for (int i = 0; i < n; i++) {
            IAudioSessionControl2 s; if (se.GetSession(i, out s) != 0) continue;
            uint pid; s.GetProcessId(out pid); string nm = "";
            try { nm = System.Diagnostics.Process.GetProcessById((int)pid).ProcessName; } catch { }
            if (!nm.Equals(proc, StringComparison.OrdinalIgnoreCase)) continue;
            IntPtr unk = Marshal.GetIUnknownForObject(s), m; Guid g = typeof(IAudioMeterInformation).GUID;
            if (Marshal.QueryInterface(unk, ref g, out m) == 0) {
                var mi = (IAudioMeterInformation)Marshal.GetObjectForIUnknown(m); float p; mi.GetPeakValue(out p);
                if (p > best) best = p; Marshal.Release(m);
            }
            Marshal.Release(unk);
        }
        return best;
    }
}
'@
for ($s = 0; $s -lt $Seconds; $s++) {
    $max = -1; for ($k = 0; $k -lt 20; $k++) { $p = [Peak]::Of($Proc); if ($p -gt $max) { $max = $p }; Start-Sleep -Milliseconds 50 }
    "{0,3}s  peak={1,5:N3}  {2}" -f $s, $max, ('#' * [int]([math]::Max(0,$max) * 40))
}
