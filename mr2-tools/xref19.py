import pefile
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

text = pe.sections[0]
base = IB + text.VirtualAddress
data = text.get_data()
instrs = []
for ins in md.disasm(data, base):
    instrs.append((ins.address, ins.mnemonic, ins.op_str))
print("instrs", len(instrs))

def window(target, before=45, after=15):
    idx = None
    for i,(a,m,o) in enumerate(instrs):
        if a == target: idx = i; break
    if idx is None:
        # nearest
        best=None
        for i,(a,m,o) in enumerate(instrs):
            if a <= target: best=i
            else: break
        idx = best
        print("(0x%08X not exact boundary; using nearest 0x%08X)" % (target, instrs[idx][0]))
    print("\n===== around 0x%08X =====" % target)
    for a,m,o in instrs[max(0,idx-before): idx+after]:
        txt = "%s %s" % (m,o)
        for tok in o.replace("["," ").replace("]"," ").replace(","," ").replace("+"," ").replace("*"," ").replace("-"," ").split():
            if tok.startswith("0x") and len(tok) <= 10:
                try: v=int(tok,16)
                except Exception: continue
                s = s_at(v)
                if s and len(s) >= 2: txt += '   ; "%s"' % s.replace("\n","\\n")[:56]
        mk = ">>" if a==target else "  "
        print("%s0x%08X: %s" % (mk,a,txt))

window(0x4381EC, before=60, after=12)
window(0x440361, before=8, after=14)
