import ctypes, time, sys
from ctypes import wintypes

CCHDEVICENAME = 32


class POINTL(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class DEVMODEW(ctypes.Structure):
    _fields_ = [
        ("dmDeviceName", ctypes.c_wchar * CCHDEVICENAME),
        ("dmSpecVersion", ctypes.c_ushort),
        ("dmDriverVersion", ctypes.c_ushort),
        ("dmSize", ctypes.c_ushort),
        ("dmDriverExtra", ctypes.c_ushort),
        ("dmFields", ctypes.c_ulong),
        ("dmPosition", POINTL),
        ("dmDisplayOrientation", ctypes.c_ulong),
        ("dmDisplayFixedOutput", ctypes.c_ulong),
        ("dmColor", ctypes.c_short),
        ("dmDuplex", ctypes.c_short),
        ("dmYResolution", ctypes.c_short),
        ("dmTTOption", ctypes.c_short),
        ("dmCollate", ctypes.c_short),
        ("dmFormName", ctypes.c_wchar * CCHDEVICENAME),
        ("dmLogPixels", ctypes.c_ushort),
        ("dmBitsPerPel", ctypes.c_ulong),
        ("dmPelsWidth", ctypes.c_ulong),
        ("dmPelsHeight", ctypes.c_ulong),
        ("dmDisplayFlags", ctypes.c_ulong),
        ("dmDisplayFrequency", ctypes.c_ulong),
        ("dmICMMethod", ctypes.c_ulong),
        ("dmICMIntent", ctypes.c_ulong),
        ("dmMediaType", ctypes.c_ulong),
        ("dmDitherType", ctypes.c_ulong),
        ("dmReserved1", ctypes.c_ulong),
        ("dmReserved2", ctypes.c_ulong),
        ("dmPanningWidth", ctypes.c_ulong),
        ("dmPanningHeight", ctypes.c_ulong),
    ]


f = ctypes.windll.user32.EnumDisplaySettingsW
f.argtypes = [ctypes.c_wchar_p, ctypes.c_ulong, ctypes.POINTER(DEVMODEW)]
f.restype = ctypes.c_int


def current():
    dm = DEVMODEW()
    dm.dmSize = ctypes.sizeof(DEVMODEW)
    if f(None, -1, ctypes.byref(dm)):
        return (dm.dmPelsWidth, dm.dmPelsHeight, dm.dmDisplayFrequency)
    return None


seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 8.0
seen = []
t0 = time.time()
while time.time() - t0 < seconds:
    m = current()
    if m:
        seen.append(m)
    time.sleep(0.25)

from collections import Counter
c = Counter(seen)
print("polled %d samples over %.1fs" % (len(seen), seconds))
print("observed display modes (count):")
for m, n in c.most_common():
    print("   %dx%d  %d Hz   x%d" % (m[0], m[1], m[2], n))
hz = {m[2] for m in seen}
print("distinct refresh rates seen:", sorted(hz))
