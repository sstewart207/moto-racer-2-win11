# audiocheck.ps1 - Core Audio probe
#   .\audiocheck.ps1              -> default endpoint per role, volume, mute
#   .\audiocheck.ps1 -Proc moto   -> also list that process's audio sessions
param(
    [string]$Proc = "",
    [double]$SetVol = -1
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
'@

Add-Type -TypeDefinition $src -ErrorAction Stop

"`n=== default audio endpoint per role ==="
try { [AudioProbe]::Defaults() | ForEach-Object { "  " + $_ } }
catch { "  ERR: " + $_.Exception.Message }

if ($Proc -and $SetVol -ge 0) {
    "`n=== SETTING '$Proc' session volume to $SetVol% ==="
    try { "  " + [AudioProbe]::SetSessionVolume($Proc, [float]($SetVol / 100.0)) }
    catch { "  ERR: " + $_.Exception.Message }
}

if ($Proc) {
    "`n=== audio sessions matching '$Proc' ==="
    try { [AudioProbe]::Sessions($Proc) | ForEach-Object { "  " + $_ } }
    catch { "  ERR: " + $_.Exception.Message }
}
""
