import struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

PATH = r"C:\Games\Moto Racer 2\Moto.exe"
pe = pefile.PE(PATH)
IB = pe.OPTIONAL_HEADER.ImageBase
raw = open(PATH, "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_32)

def s_at(va, n=64):
    try:
        off = pe.get_offset_from_rva(va - IB)
    except Exception:
        return None
    b = raw[off:off+n]
    # must be printable-ish
    end = 0
    while end < len(b) and b[end] != 0 and (32 <= b[end] < 127 or b[end] in (9,10,13)):
        end += 1
    if end < 3:
        return None
    return b[:end].decode("latin1")

def disasm(va, length, title):
    print("\n===== %s =====" % title)
    for insn in md.disasm(pe.get_data(va - IB, length), va):
        txt = "%s %s" % (insn.mnemonic, insn.op_str)
        for tok in insn.op_str.replace("[", " ").replace("]", " ").replace(",", " ").replace("+", " ").split():
            if tok.startswith("0x"):
                try:
                    v = int(tok, 16)
                except Exception:
                    continue
                s = s_at(v)
                if s:
                    txt += '   ; "%s"' % s.replace("\n", "\\n")[:60]
        mark = ">> " if insn.address in HILITE else "   "
        print("%s0x%08X: %s" % (mark, insn.address, txt))

HILITE = set()

# the theme-scanning function
disasm(0x489000, 0x700, "theme scan 0x489000")
