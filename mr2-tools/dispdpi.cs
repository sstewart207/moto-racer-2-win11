// dispdpi.cs - monitor DPI / cursor size reporting + display-config DPI scale probe
// Add-Type -Path .\dispdpi.cs   (then [DISP]::Report())
using System;
using System.Text;
using System.Runtime.InteropServices;

public class DISP
{
    // ---------- monitor enumeration ----------
    public delegate bool MonitorEnumProc(IntPtr hMonitor, IntPtr hdc, ref RECT rc, IntPtr data);

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int left, top, right, bottom; }

    [DllImport("user32.dll")]
    static extern bool EnumDisplayMonitors(IntPtr hdc, IntPtr clip, MonitorEnumProc cb, IntPtr data);

    [DllImport("shcore.dll")]
    static extern int GetDpiForMonitor(IntPtr hMonitor, int dpiType, out uint dpiX, out uint dpiY);

    [DllImport("user32.dll")]
    static extern bool SetProcessDPIAware();

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    static extern int GetMonitorInfo(IntPtr hMonitor, ref MONITORINFOEX info);

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
    public struct MONITORINFOEX
    {
        public int cbSize;
        public RECT rcMonitor;
        public RECT rcWork;
        public int dwFlags;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]
        public string szDevice;
    }

    // ---------- cursor ----------
    [StructLayout(LayoutKind.Sequential)]
    public struct POINT { public int x, y; }

    [StructLayout(LayoutKind.Sequential)]
    public struct CURSORINFO { public int cbSize; public int flags; public IntPtr hCursor; public POINT pt; }

    [StructLayout(LayoutKind.Sequential)]
    public struct ICONINFO { public bool fIcon; public int xHotspot; public int yHotspot; public IntPtr hbmMask; public IntPtr hbmColor; }

    [StructLayout(LayoutKind.Sequential)]
    public struct BITMAP { public int bmType; public int bmWidth; public int bmHeight; public int bmWidthBytes; public short bmPlanes; public short bmBitsPixel; public IntPtr bmBits; }

    [DllImport("user32.dll")] static extern bool GetCursorInfo(ref CURSORINFO c);
    [DllImport("user32.dll")] static extern bool GetIconInfo(IntPtr h, out ICONINFO i);
    [DllImport("user32.dll")] static extern bool GetCursorPos(out POINT p);
    [DllImport("gdi32.dll")] static extern int GetObject(IntPtr h, int n, out BITMAP b);
    [DllImport("gdi32.dll")] static extern bool DeleteObject(IntPtr h);

    // ---------- display config ----------
    [StructLayout(LayoutKind.Sequential)]
    public struct LUID { public uint LowPart; public int HighPart; }

    [StructLayout(LayoutKind.Sequential)]
    public struct RATIONAL { public uint Numerator; public uint Denominator; }

    [StructLayout(LayoutKind.Sequential)]
    public struct PATH_SOURCE { public LUID adapterId; public uint id; public uint modeInfoIdx; public uint statusFlags; }

    [StructLayout(LayoutKind.Sequential)]
    public struct PATH_TARGET
    {
        public LUID adapterId; public uint id; public uint modeInfoIdx;
        public int outputTechnology; public int rotation; public int scaling;
        public RATIONAL refreshRate; public int scanLineOrdering;
        public int targetAvailable; public uint statusFlags;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct PATH { public PATH_SOURCE sourceInfo; public PATH_TARGET targetInfo; public uint flags; }

    [StructLayout(LayoutKind.Sequential)]
    public struct DEVINFO_HDR { public uint type; public uint size; public LUID adapterId; public uint id; }

    [StructLayout(LayoutKind.Sequential)]
    public struct DPI_GET { public DEVINFO_HDR header; public int minScaleRel; public int curScaleRel; public int maxScaleRel; }

    [StructLayout(LayoutKind.Sequential)]
    public struct DPI_SET { public DEVINFO_HDR header; public int scale; }

    [DllImport("user32.dll")]
    static extern int GetDisplayConfigBufferSizes(uint flags, ref uint paths, ref uint modes);

    [DllImport("user32.dll")]
    static extern int QueryDisplayConfig(uint flags, ref uint numPaths, [Out] PATH[] paths,
                                         ref uint numModes, [Out] byte[] modes, IntPtr topologyId);

    [DllImport("user32.dll")]
    static extern int DisplayConfigGetDeviceInfo(ref DPI_GET info);

    [DllImport("user32.dll")]
    static extern int DisplayConfigSetDeviceInfo(ref DPI_SET info);

    public const uint QDC_ONLY_ACTIVE_PATHS = 0x2;
    public const int GET_DPI_SCALE = -3;
    public const int SET_DPI_SCALE = -4;

    static DISP() { try { SetProcessDPIAware(); } catch { } }

    // ---------- report ----------
    public static string Report()
    {
        var sb = new StringBuilder();
        sb.AppendLine("struct sizes: PATH=" + Marshal.SizeOf(typeof(PATH))
             + " (expect 72)   PATH_TARGET=" + Marshal.SizeOf(typeof(PATH_TARGET))
             + " (48)   PATH_SOURCE=" + Marshal.SizeOf(typeof(PATH_SOURCE)) + " (20)");

        sb.AppendLine("--- monitors (effective DPI) ---");
        EnumDisplayMonitors(IntPtr.Zero, IntPtr.Zero,
            delegate (IntPtr hMon, IntPtr hdc, ref RECT rc, IntPtr data)
            {
                var mi = new MONITORINFOEX();
                mi.cbSize = Marshal.SizeOf(mi);
                GetMonitorInfo(hMon, ref mi);
                uint dx, dy;
                int hr = GetDpiForMonitor(hMon, 0 /*MDT_EFFECTIVE_DPI*/, out dx, out dy);
                sb.AppendLine(string.Format("  {0,-14} {1}x{2}+{3}+{4}  effectiveDPI={5} ({6}%)  hr={7}",
                    mi.szDevice, mi.rcMonitor.right - mi.rcMonitor.left,
                    mi.rcMonitor.bottom - mi.rcMonitor.top,
                    mi.rcMonitor.left, mi.rcMonitor.top, dx,
                    (dx * 100) / 96, hr));
                return true;
            }, IntPtr.Zero);

        sb.AppendLine("--- cursor ---");
        var ci = new CURSORINFO();
        ci.cbSize = Marshal.SizeOf(ci);
        if (GetCursorInfo(ref ci))
        {
            POINT p; GetCursorPos(out p);
            sb.AppendLine(string.Format("  showing={0}  pos=({1},{2})  hCursor={3}",
                (ci.flags & 1) != 0, p.x, p.y, ci.hCursor));
            ICONINFO ii;
            if (GetIconInfo(ci.hCursor, out ii))
            {
                if (ii.hbmColor != IntPtr.Zero)
                {
                    BITMAP b; GetObject(ii.hbmColor, Marshal.SizeOf(typeof(BITMAP)), out b);
                    sb.AppendLine("  cursor bitmap (color) = " + b.bmWidth + "x" + b.bmHeight + "   <-- rendered px");
                }
                if (ii.hbmMask != IntPtr.Zero)
                {
                    BITMAP b; GetObject(ii.hbmMask, Marshal.SizeOf(typeof(BITMAP)), out b);
                    sb.AppendLine("  cursor bitmap (mask)  = " + b.bmWidth + "x" + b.bmHeight);
                }
                DeleteObject(ii.hbmColor); DeleteObject(ii.hbmMask);
            }
        }

        return sb.ToString();
    }

    // ---------- read-only: GET_DPI_SCALE for every active path ----------
    public static string ProbeScale()
    {
        var sb = new StringBuilder();
        uint nP = 0, nM = 0;
        int hr = GetDisplayConfigBufferSizes(QDC_ONLY_ACTIVE_PATHS, ref nP, ref nM);
        if (hr != 0) { return "GetDisplayConfigBufferSizes hr=" + hr + "\n"; }
        sb.AppendLine("active paths=" + nP + "  modes=" + nM);

        var paths = new PATH[nP];
        var modes = new byte[checked(nM * 64)];
        uint pc = nP, mc = nM;
        hr = QueryDisplayConfig(QDC_ONLY_ACTIVE_PATHS, ref pc, paths, ref mc, modes, IntPtr.Zero);
        if (hr != 0) { return sb + "QueryDisplayConfig hr=" + hr + "\n"; }
        sb.AppendLine("queried paths=" + pc);

        for (int i = 0; i < pc; i++)
        {
            // try source id first, then target id
            foreach (var use in new[] { "source", "target" })
            {
                var g = new DPI_GET();
                g.header.type = unchecked((uint)GET_DPI_SCALE);
                g.header.size = (uint)Marshal.SizeOf(typeof(DPI_GET));
                g.header.adapterId = use == "source" ? paths[i].sourceInfo.adapterId : paths[i].targetInfo.adapterId;
                g.header.id = use == "source" ? paths[i].sourceInfo.id : paths[i].targetInfo.id;
                int r = DisplayConfigGetDeviceInfo(ref g);
                sb.AppendLine(string.Format(
                    "  path[{0}] via {1,-6} id={2}  hr={3}  min={4} cur={5} max={6}",
                    i, use, g.header.id, r, g.minScaleRel, g.curScaleRel, g.maxScaleRel));
            }
            sb.AppendLine(string.Format(
                "  path[{0}] src adapter=LUID({1},{2}) id={3}   tgt adapter=LUID({4},{5}) id={6}  {7}x{8}",
                i,
                paths[i].sourceInfo.adapterId.HighPart, paths[i].sourceInfo.adapterId.LowPart, paths[i].sourceInfo.id,
                paths[i].targetInfo.adapterId.HighPart, paths[i].targetInfo.adapterId.LowPart, paths[i].targetInfo.id,
                paths[i].sourceInfo.modeInfoIdx, paths[i].targetInfo.modeInfoIdx));
        }
        return sb.ToString();
    }

    // ---------- write: SET_DPI_SCALE (rel = index relative to recommended) ----------
    public static string SetScale(int rel, bool useSource)
    {
        var sb = new StringBuilder();
        uint nP = 0, nM = 0;
        int hr = GetDisplayConfigBufferSizes(QDC_ONLY_ACTIVE_PATHS, ref nP, ref nM);
        if (hr != 0) { return "GetDisplayConfigBufferSizes hr=" + hr + "\n"; }
        var paths = new PATH[nP];
        var modes = new byte[checked(nM * 64)];
        uint pc = nP, mc = nM;
        hr = QueryDisplayConfig(QDC_ONLY_ACTIVE_PATHS, ref pc, paths, ref mc, modes, IntPtr.Zero);
        if (hr != 0) { return "QueryDisplayConfig hr=" + hr + "\n"; }

        for (int i = 0; i < pc; i++)
        {
            var s = new DPI_SET();
            s.header.type = unchecked((uint)SET_DPI_SCALE);
            s.header.size = (uint)Marshal.SizeOf(typeof(DPI_SET));
            s.header.adapterId = useSource ? paths[i].sourceInfo.adapterId : paths[i].targetInfo.adapterId;
            s.header.id = useSource ? paths[i].sourceInfo.id : paths[i].targetInfo.id;
            s.scale = rel;
            int r = DisplayConfigSetDeviceInfo(ref s);
            sb.AppendLine(string.Format("  path[{0}] {1} rel={2} -> hr={3} ({4})",
                i, useSource ? "source" : "target", rel, r, r == 0 ? "OK" : "FAILED"));
        }
        return sb.ToString();
    }
}
