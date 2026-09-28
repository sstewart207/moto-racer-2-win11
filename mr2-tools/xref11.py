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

def dis(va, length, title):
    print("\n===== %s =====" % title)
    for insn in md.disasm(pe.get_data(va - IB, length), va):
        txt = "%s %s" % (insn.mnemonic, insn.op_str)
        for tok in insn.op_str.replace("["," ").replace("]"," ").replace(","," ").replace("+"," ").replace("*"," ").split():
            if tok.startswith("0x") and len(tok) <= 10:
                try: v = int(tok,16)
                except Exception: continue
                s = s_at(v)
                if s and len(s) >= 2: txt += '   ; "%s"' % s.replace("\n","\\n")[:50]
        print("   0x%08X: %s" % (insn.address, txt))

dis(0x43A3C0, 0x90, "caller 0x43A421")
dis(0x436FC0, 0x60, "caller 0x43701C/0x43702E")
dis(0x437000, 0x50, "function around 0x437012")

# what are helpers
for va in (0x4c67b0, 0x4c6e24, 0x4c65f0, 0x4c6110, 0x4c6100, 0x428540):
    off = pe.get_offset_from_rva(va - IB)
    print("\nhelper 0x%08X first bytes: %s" % (va, raw[off:off+24].hex(" ")))
