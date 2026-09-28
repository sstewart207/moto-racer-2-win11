import ctypes
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


user32 = ctypes.windll.user32
EnumDisplaySettingsW = user32.EnumDisplaySettingsW
EnumDisplaySettingsW.argtypes = [
    ctypes.c_wchar_p, ctypes.c_ulong, ctypes.POINTER(DEVMODEW)
]
EnumDisplaySettingsW.restype = ctypes.c_int

print("sizeof(DEVMODEW) =", ctypes.sizeof(DEVMODEW))

dm = DEVMODEW()
dm.dmSize = ctypes.sizeof(DEVMODEW)
if EnumDisplaySettingsW(None, -1, ctypes.byref(dm)):
    print("CURRENT : %dx%d  %d Hz  %d bpp" % (
        dm.dmPelsWidth, dm.dmPelsHeight,
        dm.dmDisplayFrequency, dm.dmBitsPerPel))
else:
    print("CURRENT : <EnumDisplaySettings failed>")

modes = set()
i = 0
while i < 800:
    dm = DEVMODEW()
    dm.dmSize = ctypes.sizeof(DEVMODEW)
    if not EnumDisplaySettingsW(None, i, ctypes.byref(dm)):
        break
    modes.add((dm.dmPelsWidth, dm.dmPelsHeight,
               dm.dmDisplayFrequency, dm.dmBitsPerPel))
    i += 1

print("\n%d unique modes enumerated:" % len(modes))
for w, h, hz, bpp in sorted(modes):
    print("   %4dx%-4d %4d Hz %2d bpp" % (w, h, hz, bpp))

print("\nRefresh rates available:",
      sorted({m[2] for m in modes if m[2]}))
print("Max refresh:", max((m[2] for m in modes), default=0))
