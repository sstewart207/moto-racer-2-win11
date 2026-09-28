import struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

PATH = r"C:\Games\Moto Racer 2\Moto.exe"
pe = pefile.PE(PATH)
IB = pe.OPTIONAL_HEADER.ImageBase
raw = open(PATH, "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_32)

def s_at(va, n=72):
    try:
        off = pe.get_offset_from_rva(va - IB)
    except Exception:
        return None
    b = raw[off:off+n]
    end = 0
    while end < len(b) and b[end] != 0 and (32 <= b[end] < 127 or b[end] in (9,10,13)):
        end += 1
    if end < 2: return None
    return b[:end].decode("latin1")

def refs(va):
    pat = struct.pack("<I", va); out = []
    for s in pe.sections:
        d = s.get_data(); st = 0
        while True:
            j = d.find(pat, st)
            if j < 0: break
            out.append(IB + s.VirtualAddress + j); st = j+1
    return out

for nm, va in (("BUF1 0x4f8aac",0x4f8aac), ("BUF2 0x4f8bac",0x4f8bac),
               ("sel 0x4f8cac",0x4f8cac), ("errflag 0x4f8cb4",0x4f8cb4),
               ("flag 0x4f8cb0",0x4f8cb0), ("init 0x5b9678",0x5b9678)):
    r = refs(va)
    print("%-18s -> %s" % (nm, [hex(x) for x in r[:25]]))

# callers of save func 0x436C46
print("\n=== callers of 0x436C46 ===")
for s in pe.sections:
    d = s.get_data()
    for j in range(len(d)-5):
        if d[j] != 0xE8: continue
        rel = struct.unpack_from("<i", d, j+1)[0]
        if (s.VirtualAddress + j + 5 + rel) == (0x436C46 - IB):
            print("   call at 0x%08X" % (IB + s.VirtualAddress + j))
