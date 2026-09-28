# Session 4 (Claude): wait for Moto.exe's "Error in game" dialog, then snapshot key globals
# with ReadProcessMemory (ctypes only, no pywin32). Run BEFORE clicking START.
import ctypes, ctypes.wintypes as wt, time, struct, sys, subprocess
k32, u32 = ctypes.windll.kernel32, ctypes.windll.user32
k32.OpenProcess.restype = wt.HANDLE
k32.ReadProcessMemory.argtypes = [wt.HANDLE, wt.LPCVOID, wt.LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]

def pid_of(name="Moto.exe"):
    out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {name}", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        parts = line.strip('"').split('","')
        if len(parts) > 1 and parts[0].lower() == name.lower(): return int(parts[1])

print("waiting for Error in game dialog ...", flush=True)
t0 = time.time()
while not u32.FindWindowW(None, "Error in game"):
    if time.time() - t0 > 600: sys.exit("timeout")
    time.sleep(0.2)
pid = pid_of(); h = k32.OpenProcess(0x0010 | 0x0400, False, pid)   # VM_READ | QUERY_INFORMATION
def rd(a, n):
    b = ctypes.create_string_buffer(n); got = ctypes.c_size_t()
    if not k32.ReadProcessMemory(h, a, b, n, ctypes.byref(got)): return None
    return b.raw
print("pid", pid)
print("Version flag [0x6594D0] =", struct.unpack("<I", rd(0x6594D0, 4))[0])
print("binary flag [0x4F9220]  =", struct.unpack("<I", rd(0x4F9220, 4))[0])
print("PRNG states 0..9        =", [hex(x) for x in struct.unpack("<10I", rd(0x5476C8, 40))])
for i in range(8):
    print(f"MotoCarac[{i}] =", rd(0x657BBC + i*0x40, 0x40).split(b"\0")[0].hex())
print("FileMoto =", rd(0x6555B8, 0x40).split(b"\0")[0])
print("scratch 0x6515A0 =", rd(0x6515A0, 0x40).hex())
open(r"C:\Games\mr2-tools\memsnap.bin", "wb").write(rd(0x400000 + 0x1000, 0x1000) or b"")
