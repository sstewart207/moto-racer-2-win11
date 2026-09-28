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
    if end < 3: return None
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

print("=== refs to extension strings ===")
for nm, va in ((".BPT",0x4f97d0), ("BPT",0x4f97d1), (".SPT",0x4f97dc),
               (".DEM",0x4f97e4), ("THEME.",0x4f97ec),
               ("Data\\Themes\\Britany.D\\Bank\\",0x4f7b98),
               ("Data\\Tracks\\TA_",0x4fab24),
               ("Data\\Ile01\\Level.Spt",None)):
    if va is None: continue
    r = refs(va)
    print("  %-30s -> %s" % (nm, [hex(x) for x in r[:12]]))

# callers of open helper
CALLERS = [0x4023A8,0x402526,0x40255F,0x436DCB,0x436EC5,0x436F8B,0x43D213,
           0x43D23B,0x43D48E,0x44C0FA,0x476B42,0x489065,0x489144,0x489443,
           0x48961B,0x497062,0x49F9D8,0x4A89B6,0x4BD29B,0x4BD778]

print("\n=== context of each open-helper call (looking for .BPT builders) ===")
for c in CALLERS:
    # walk back to find start-ish: print 26 instructions before call
    start = c - 0x80
    buf = []
    for insn in md.disasm(pe.get_data(start - IB, 0x80 + 6), start):
        txt = "%s %s" % (insn.mnemonic, insn.op_str)
        for tok in insn.op_str.replace("["," ").replace("]"," ").replace(","," ").replace("+"," ").split():
            if tok.startswith("0x"):
                try: v = int(tok,16)
                except Exception: continue
                s = s_at(v)
                if s: txt += '   ; "%s"' % s.replace("\n","\\n")[:50]
        buf.append((insn.address, txt))
    keep = [b for b in buf if b[0] >= c - 0x70]
    print("\n-- call site 0x%08X --" % c)
    for a, t in keep[-22:]:
        print("   0x%08X: %s" % (a, t))
