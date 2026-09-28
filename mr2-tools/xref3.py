import struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

PATH = r"C:\Games\Moto Racer 2\Moto.exe"
pe = pefile.PE(PATH)
IB = pe.OPTIONAL_HEADER.ImageBase
raw = open(PATH, "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_32)

def rva2off(rva):
    return pe.get_offset_from_rva(rva)

def dump_str(va, n=96):
    off = rva2off(va - IB)
    b = raw[off:off+n]
    return b

print("=== raw region 0x4f8a80 .. 0x4f8be0 ===")
region = dump_str(0x4f8a80, 0x160)
for i in range(0, len(region), 32):
    chunk = region[i:i+32]
    print("0x%08X  %-48s %s" % (0x4f8a80+i, chunk.hex(" "),
          "".join(chr(c) if 32 <= c < 127 else "." for c in chunk)))

# ---- find callers of a target VA via E8 rel32 ----
def callers(target_va):
    tgt_rva = target_va - IB
    out = []
    for s in pe.sections:
        d = s.get_data()
        for j in range(0, len(d) - 5):
            if d[j] != 0xE8:
                continue
            rel = struct.unpack_from("<i", d, j + 1)[0]
            disp = (s.VirtualAddress + j + 5 + rel)
            if disp == tgt_rva:
                out.append(IB + s.VirtualAddress + j)
    return out

for name, va in (("open_helper 0x427100", 0x427100),
                 ("archive_open? 0x4279ff", 0x4279ff)):
    cl = callers(va)
    print("\n=== callers of %s : %d ===" % (name, len(cl)))
    for c in cl[:20]:
        print("   0x%08X" % c)
