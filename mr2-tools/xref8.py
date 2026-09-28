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

tgt = 0x436d19
off = pe.get_offset_from_rva(tgt - IB)
start = None
for i in range(off, off - 0x900, -1):
    if raw[i] == 0x55 and raw[i+1] == 0x89 and raw[i+2] == 0xE5 and raw[i+3] in (0x81, 0x83):
        if raw[i-1] in (0xC3, 0xCC, 0x90, 0xC2, 0xC9, 0x5D):
            start = IB + pe.get_rva_from_offset(i)
            break
print("function start: 0x%08X" % (start or 0))

HILITE = {0x436d19,0x436d60,0x436d7b,0x436d8e,0x436d9b,0x436dac,0x436dc5,0x436dcb}
if start:
    print("===== dump 0x%08X .. 0x436DD0 =====" % start)
    for insn in md.disasm(pe.get_data(start - IB, 0x436de0 - start), start):
        txt = "%s %s" % (insn.mnemonic, insn.op_str)
        for tok in insn.op_str.replace("["," ").replace("]"," ").replace(","," ").replace("+"," ").replace("*"," ").split():
            if tok.startswith("0x") and len(tok) <= 10:
                try: v = int(tok,16)
                except Exception: continue
                s = s_at(v)
                if s and len(s) >= 2: txt += '   ; "%s"' % s.replace("\n","\\n")[:50]
        m = ">>" if insn.address in HILITE else "  "
        print("%s 0x%08X: %s" % (m, insn.address, txt))
