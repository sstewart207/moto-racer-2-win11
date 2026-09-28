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

def find_start(target, maxback=0x1200):
    """scan back for 55 89 E5 that linear-disassembles exactly onto target"""
    off = pe.get_offset_from_rva(target - IB)
    cands = []
    for i in range(off, max(off - maxback, 0), -1):
        if raw[i] == 0x55 and raw[i+1] == 0x89 and raw[i+2] == 0xE5:
            cands.append(i)
    for i in cands:
        st = IB + pe.get_rva_from_offset(i)
        if st >= target: continue
        try:
            addrs = set()
            for ins in md.disasm(pe.get_data(st - IB, target - st + 8), st):
                addrs.add(ins.address)
                if ins.address >= target: break
            if target in addrs:
                return st
        except Exception:
            continue
    return None

def dump(target, extra=0x60, back=0xC0, label=""):
    st = find_start(target)
    print("\n===== %s : target 0x%08X  funcstart 0x%08X =====" % (label, target, st or 0))
    if not st:
        st = target - back
    for insn in md.disasm(pe.get_data(st - IB, target - st + extra), st):
        txt = "%s %s" % (insn.mnemonic, insn.op_str)
        toks = insn.op_str.replace("["," ").replace("]"," ").replace(","," ").replace("+"," ").replace("*"," ").replace("-"," ").split()
        for tok in toks:
            if tok.startswith("0x") and len(tok) <= 10:
                try: v = int(tok,16)
                except Exception: continue
                s = s_at(v)
                if s and len(s) >= 2: txt += '   ; "%s"' % s.replace("\n","\\n")[:56]
        m = ">>" if insn.address == target else "  "
        print("%s0x%08X: %s" % (m, insn.address, txt))

# wrapper entry
print("===== wrapper 0x437012 =====")
for insn in md.disasm(pe.get_data(0x437012 - IB, 0x30), 0x437012):
    print("   0x%08X: %s %s" % (insn.address, insn.mnemonic, insn.op_str))

dump(0x438e78, label="write 0x657bbc")
dump(0x4381ec, label="write 0x6555b8")
