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

def dis(va, length, title, hilite=()):
    print("\n===== %s =====" % title)
    for insn in md.disasm(pe.get_data(va - IB, length), va):
        txt = "%s %s" % (insn.mnemonic, insn.op_str)
        for tok in insn.op_str.replace("["," ").replace("]"," ").replace(","," ").replace("+"," ").replace("*"," ").split():
            if tok.startswith("0x") and len(tok) <= 10:
                try: v = int(tok,16)
                except Exception: continue
                s = s_at(v)
                if s and len(s) >= 2: txt += '   ; "%s"' % s.replace("\n","\\n")[:56]
        m = ">>" if insn.address in hilite else "   "
        print("%s0x%08X: %s" % (m, insn.address, txt))

# find prologue of the init function containing 0x426cdb
def find_pro(target, limit=0x1000):
    off = pe.get_offset_from_rva(target - IB)
    for i in range(off, off - limit, -1):
        if raw[i] == 0x81 and raw[i+1] == 0xEC and raw[i-5] == 0xE8 and raw[i-10] == 0xB8:
            return IB + pe.get_rva_from_offset(i-10)
        if raw[i] == 0x55 and raw[i+1] == 0x89 and raw[i+2] == 0xE5 and raw[i-1] in (0xC3,0xCC,0x90,0xC2):
            return IB + pe.get_rva_from_offset(i)
    return None

st = find_pro(0x426cdb)
print("init prologue: 0x%08X" % (st or 0))
if st:
    dis(st, 0x427100 - st, "INIT/PATH function 0x%08X" % st,
        hilite={0x426cdb,0x426ce7,0x42707c,0x4270b5})
