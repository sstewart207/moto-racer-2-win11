import struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

PATH = r"C:\Games\Moto Racer 2\Moto.exe"
pe = pefile.PE(PATH)
IB = pe.OPTIONAL_HEADER.ImageBase
raw = open(PATH, "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_32)

def dump_str(va, n=80):
    off = pe.get_offset_from_rva(va - IB)
    b = raw[off:off+n].split(b"\x00")[0]
    return b.decode("latin1")

# find extension strings
print("=== searching extension / theme strings ===")
strva = {}
for n in [".BPT", "BPT", ".SPT", "SPT", ".DEM", "THEME", "data\\Themes",
          "themes", "%stheme.bpt", "%stheme.spt", "*.*", "Themes",
          "Data\\Themes", "%s", "Data\\Tracks", "Themes\\" ]:
    i = raw.find(n.encode("latin1"))
    if i < 0:
        print("  %-16s NOT FOUND" % n); continue
    try:
        va = IB + pe.get_rva_from_offset(i)
    except Exception:
        va = None
    print("  %-16s VA=%s  next=%r" % (n, hex(va) if va else "?", raw[i:i+len(n)+16]))
    if va: strva[n] = va

def find_va_refs(target_va):
    pat = struct.pack("<I", target_va)
    hits = []
    for s in pe.sections:
        d = s.get_data()
        st = 0
        while True:
            j = d.find(pat, st)
            if j < 0: break
            hits.append(IB + s.VirtualAddress + j)
            st = j + 1
    return hits

print("\n=== refs to key strings ===")
for n in ["data\\Themes", "%stheme.bpt", "Themes", "*.*", "BPT"]:
    if n in strva:
        r = find_va_refs(strva[n])
        print("  %-16s refs: %s" % (n, [hex(x) for x in r[:15]]))
