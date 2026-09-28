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
    if end < 1: return None
    return b[:end].decode("latin1")

for va in (0x4ed360, 0x4f9100, 0x4f9758, 0x4f9104, 0x4f8aac, 0x4f8bac, 0x4f8cac, 0x4f8cb0, 0x4f8cb4):
    off = pe.get_offset_from_rva(va - IB)
    print("0x%08X = raw %r" % (va, raw[off:off+16]))

# find prologue: 55 89 E5 (push ebp; mov ebp,esp)
tgt = 0x436d00
off = pe.get_offset_from_rva(tgt - IB)
start = None
for i in range(off, off - 0x800, -1):
    if raw[i] == 0x55 and raw[i+1] == 0x89 and raw[i+2] == 0xE5:
        prev = raw[i-1]
        if prev in (0xC3, 0xCC, 0x90, 0xC2, 0xC9):
            start = IB + pe.get_rva_from_offset(i)
            break
print("\nfunction start: 0x%08X" % (start or 0))

HILITE = {0x436d19,0x436d60,0x436d7b,0x436d8e,0x436d9b,0x436dac,0x436dc5,0x436dcb}
if start:
    print("\n===== dump 0x%08X .. 0x436DD0 =====" % start)
    for insn in md.disasm(pe.get_data(start - IB, 0x436de0 - start), start):
        txt = "%s %s" % (insn.mnemonic, insn.op_str)
        for tok in insn.op_str.replace("["," ").replace("]"," ").replace(","," ").replace("+"," ").split():
            if tok.startswith("0x"):
                try: v = int(tok,16)
                except Exception: continue
                s = s_at(v)
                if s and len(s) >= 2: txt += '   ; "%s"' % s.replace("\n","\\n")[:52]
        m = ">>" if insn.address in HILITE else "  "
        print("%s 0x%08X: %s" % (m, insn.address, txt))
