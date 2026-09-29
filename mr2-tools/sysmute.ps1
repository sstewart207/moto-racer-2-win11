# sysmute.ps1 - mute/unmute EVERY active playback device at the Windows endpoint level.
# The game never sees endpoint mute, so it cannot leak into config.bin (unlike -NoSound
# or per-app session volume - see CLAUDE.md Rules 5 and 7).
#   .\sysmute.ps1 -Mute      -> records current state to sysmute-state.json, mutes all
#   .\sysmute.ps1 -Restore   -> puts each device back exactly as recorded
#   .\sysmute.ps1            -> report only
param([switch]$Mute, [switch]$Restore)

$src = @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] public class MMDevEnum { }

[ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IMMDevEnum {
    [PreserveSig] int EnumAudioEndpoints(int flow, int mask, out IMMDevColl devs);
}
[ComImport, Guid("0BD7A1BE-7A1A-44DB-8397-CC5392387B5E"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IMMDevColl {
    [PreserveSig] int GetCount(out int n);
    [PreserveSig] int Item(int i, out IMMDev d);
}
[ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IMMDev {
    [PreserveSig] int Activate(ref Guid iid, int ctx, IntPtr p, [MarshalAs(UnmanagedType.IUnknown)] out object o);
    int OpenPropertyStore(int a, out IntPtr p);
    [PreserveSig] int GetId([MarshalAs(UnmanagedType.LPWStr)] out string id);
}
[ComImport, Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IEPVol {
    int RegisterControlChangeNotify(IntPtr p); int UnregisterControlChangeNotify(IntPtr p);
    int GetChannelCount(out int n);
    int SetMasterVolumeLevel(float l, IntPtr e); int SetMasterVolumeLevelScalar(float l, IntPtr e);
    int GetMasterVolumeLevel(out float l); int GetMasterVolumeLevelScalar(out float l);
    int SetChannelVolumeLevel(int c, float l, IntPtr e); int SetChannelVolumeLevelScalar(int c, float l, IntPtr e);
    int GetChannelVolumeLevel(int c, out float l); int GetChannelVolumeLevelScalar(int c, out float l);
    [PreserveSig] int SetMute([MarshalAs(UnmanagedType.Bool)] bool m, IntPtr e);
    [PreserveSig] int GetMute([MarshalAs(UnmanagedType.Bool)] out bool m);
}
public static class SysMute {
    static IEPVol Vol(IMMDev d) {
        Guid g = typeof(IEPVol).GUID; object o; d.Activate(ref g, 23, IntPtr.Zero, out o); return (IEPVol)o;
    }
    public static List<string[]> List() {
        var r = new List<string[]>(); IMMDevColl c;
        ((IMMDevEnum)new MMDevEnum()).EnumAudioEndpoints(0, 1, out c);   // eRender, ACTIVE
        int n; c.GetCount(out n);
        for (int i = 0; i < n; i++) {
            IMMDev d; c.Item(i, out d); string id; d.GetId(out id);
            bool m; float v; var ev = Vol(d); ev.GetMute(out m); ev.GetMasterVolumeLevelScalar(out v);
            r.Add(new[] { id, m ? "1" : "0", ((int)Math.Round(v * 100)).ToString() });
        }
        return r;
    }
    public static int Set(string id, bool mute) {
        IMMDevColl c; ((IMMDevEnum)new MMDevEnum()).EnumAudioEndpoints(0, 1, out c);
        int n; c.GetCount(out n);
        for (int i = 0; i < n; i++) {
            IMMDev d; c.Item(i, out d); string x; d.GetId(out x);
            if (x == id) return Vol(d).SetMute(mute, IntPtr.Zero);
        }
        return -1;
    }
}
'@
Add-Type -TypeDefinition $src
$state = Join-Path $PSScriptRoot 'sysmute-state.json'

if ($Mute) {
    # Keep the ORIGINAL pre-mute state of devices already recorded, but add any device plugged in
    # since the last -Mute (e.g. a DualSense speaker), so -Restore covers it too.
    $known = @(); if (Test-Path $state) { $known = @((Get-Content $state -Raw | ConvertFrom-Json) | % { $_ }) }
    $ids = $known | % { $_.Id }
    $added = [SysMute]::List() | ? { $ids -notcontains $_[0] } | % { [pscustomobject]@{ Id = $_[0]; Muted = $_[1] -eq '1'; Vol = [int]$_[2] } }
    if ($added) { "recording new device(s): " + (($added | % { $_.Id }) -join ', ') }
    ConvertTo-Json -InputObject @($known + @($added)) | Set-Content $state
    [SysMute]::List() | % { "mute {0} -> hr={1}" -f $_[0], [SysMute]::Set($_[0], $true) }
}
elseif ($Restore) {
    if (-not (Test-Path $state)) { Write-Host "no state file; unmuting all"; [SysMute]::List() | % { [void][SysMute]::Set($_[0], $false) } }
    else { (Get-Content $state -Raw | ConvertFrom-Json) | % { $_ } | % { "restore {0} muted={1} -> hr={2}" -f $_.Id, $_.Muted, [SysMute]::Set($_.Id, [bool]$_.Muted) }; Remove-Item $state }
}
[SysMute]::List() | % { "{0}  muted={1}  vol={2}%" -f $_[0], $_[1], $_[2] }
