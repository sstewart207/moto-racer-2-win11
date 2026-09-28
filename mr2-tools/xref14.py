import struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

PATH = r"C:\Games\Moto Racer 2\Moto.exe"
pe = pefile.PE(PATH)
IB = pe.OPTIONAL_HEADER.ImageBase
raw = open(PATH, "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_32)

def s_at(va, n=80):
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

SITES = [0x4132e6, 0x4402fa, 0x44036e, 0x44048d, 0x4404ff, 0x4449f1, 0x488e41, 0x489666]

for c in SITES:
    start = c - 0x50
    print("\n-- call to wrapper at 0x%08X --" % c)
    rows = []
    for insn in md.disasm(pe.get_data(start - IB, 0x50 + 6), start):
        txt = "%s %s" % (insn.mnemonic, insn.op_str)
        toks = insn.op_str.replace("["," ").replace("]"," ").replace(","," ").replace("+"," ").replace("*"," ").replace("-"," ").split()
        for tok in toks:
            if tok.startswith("0x") and len(tok) <= 10:
                try: v = int(tok,16)
                except Exception: continue
                s = s_at(v)
                if s and len(s) >= 2: txt += '   ; "%s"' % s.replace("\n","\\n")[:56]
        if insn.address >= c - 0x40:
            rows.append((insn.address, txt))
    for a, t in rows[-16:]:
        print("   0x%08X: %s" % (a, t))
