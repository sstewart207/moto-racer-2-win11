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

def refs(va):
    pat = struct.pack("<I", va); out = []
    for s in pe.sections:
        d = s.get_data(); st = 0
        while True:
            j = d.find(pat, st)
            if j < 0: break
            out.append(IB + s.VirtualAddress + j); st = j+1
    return out

def show(c, back=0x70, fwd=0x10):
    print("\n-- site 0x%08X --" % c)
    start = c - back
    for insn in md.disasm(pe.get_data(start - IB, back + fwd), start):
        txt = "%s %s" % (insn.mnemonic, insn.op_str)
        toks = insn.op_str.replace("["," ").replace("]"," ").replace(","," ").replace("+"," ").replace("*"," ").replace("-"," ").split()
        for tok in toks:
            if tok.startswith("0x") and len(tok) <= 10:
                try: v = int(tok,16)
                except Exception: continue
                s = s_at(v)
                if s and len(s) >= 2: txt += '   ; "%s"' % s.replace("\n","\\n")[:56]
        m = ">>" if insn.address == c else "  "
        print("  %s0x%08X: %s" % (m, insn.address, txt))

show(0x44036E)
show(0x4449F1)
show(0x44048D, back=0x90)

print("\n=== refs to 0x657bbc ===")
r = refs(0x657bbc)
print(len(r), [hex(x) for x in r[:60]])
