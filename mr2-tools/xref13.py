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
        for tok in insn.op_str.replace("["," ").replace("]","," ).replace(","," ").replace("+"," ").replace("*"," ").split():
            pass
        toks = insn.op_str.replace("["," ").replace("]"," ").replace(","," ").replace("+"," ").replace("*"," ").replace("-"," ").split()
        for tok in toks:
            if tok.startswith("0x") and len(tok) <= 10:
                try: v = int(tok,16)
                except Exception: continue
                s = s_at(v)
                if s and len(s) >= 2: txt += '   ; "%s"' % s.replace("\n","\\n")[:56]
        m = ">>" if insn.address in hilite else "   "
        print("%s0x%08X: %s" % (m, insn.address, txt))

def callers(target_va):
    tgt_rva = target_va - IB
    out = []
    for s in pe.sections:
        d = s.get_data()
        for j in range(0, len(d) - 5):
            if d[j] != 0xE8: continue
            rel = struct.unpack_from("<i", d, j + 1)[0]
            if (s.VirtualAddress + j + 5 + rel) == tgt_rva:
                out.append(IB + s.VirtualAddress + j)
    return out

# dump 0x436FF0..0x437036 to find the wrapper entry
dis(0x436FF0, 0x50, "region before 0x43701C")
for va in (0x437012, 0x437000, 0x436FF0):
    print("callers of 0x%X -> %s" % (va, [hex(x) for x in callers(va)]))
