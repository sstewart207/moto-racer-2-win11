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

# sweep .text linearly, record boundaries
text = pe.sections[0]
base = IB + text.VirtualAddress
data = text.get_data()
bnds = set()
prev_term = set()
i = 0
instrs = []
for ins in md.disasm(data, base):
    bnds.add(ins.address)
    instrs.append((ins.address, ins.size, ins.mnemonic, ins.op_str))

print("instructions:", len(instrs))

def enclosing(target):
    """find nearest prologue at an instruction boundary at/before target"""
    best = None
    for addr, size, mn, op in instrs:
        if addr > target: break
        if mn == "push" and op == "ebp":
            # check next is mov ebp, esp
            pass
        if mn == "mov" and op == "ebp, esp":
            best = addr
    return best

# faster: build map of 'mov ebp, esp' preceded by push ebp
cands = []
for idx in range(1, len(instrs)):
    a, s, mn, op = instrs[idx]
    pa, ps, pmn, pop = instrs[idx-1]
    if pmn == "push" and pop == "ebp" and mn == "mov" and op == "ebp, esp":
        cands.append(pa)

def find_func(target):
    lo = None
    for c in cands:
        if c <= target: lo = c
        else: break
    return lo

for t in (0x438E45, 0x4381EC, 0x44048D, 0x44036E, 0x4402FA, 0x4132E6, 0x489666, 0x488E41):
    f = find_func(t)
    print("target 0x%08X -> func 0x%08X" % (t, f or 0))

# dump the function containing 0x438e45
f = find_func(0x438E45)
print("\n===== func 0x%08X .. 0x438e45 =====" % (f or 0))
if f:
    for addr, size, mn, op in instrs:
        if addr < f or addr > 0x438e60: continue
        txt = "%s %s" % (mn, op)
        for tok in op.replace("["," ").replace("]"," ").replace(","," ").replace("+"," ").replace("*"," ").replace("-"," ").split():
            if tok.startswith("0x") and len(tok) <= 10:
                try: v = int(tok,16)
                except Exception: continue
                s = s_at(v)
                if s and len(s) >= 2: txt += '   ; "%s"' % s.replace("\n","\\n")[:56]
        print("   0x%08X: %s" % (addr, txt))
