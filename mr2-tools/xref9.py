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

def find_prologue(target_va, limit=0x2000):
    off = pe.get_offset_from_rva(target_va - IB)
    for i in range(off, off - limit, -1):
        # sub esp, imm32 : 81 EC xx xx xx xx
        if raw[i] == 0x81 and raw[i+1] == 0xEC:
            # preceded by call rel32 (E8) preceded by mov eax, imm32 (B8)
            if raw[i-5] == 0xE8 and raw[i-10] == 0xB8:
                return IB + pe.get_rva_from_offset(i - 10)
    return None

st = find_prologue(0x436d19)
print("prologue for 0x436d19 function: 0x%08X" % (st or 0))

if st:
    HILITE = {0x436d19,0x436d60,0x436d7b,0x436d8e,0x436d9b,0x436dac,0x436dc5,0x436dcb}
    print("===== dump =====")
    for insn in md.disasm(pe.get_data(st - IB, 0x436de0 - st), st):
        txt = "%s %s" % (insn.mnemonic, insn.op_str)
        for tok in insn.op_str.replace("["," ").replace("]"," ").replace(","," ").replace("+"," ").replace("*"," ").split():
            if tok.startswith("0x") and len(tok) <= 10:
                try: v = int(tok,16)
                except Exception: continue
                s = s_at(v)
                if s and len(s) >= 2: txt += '   ; "%s"' % s.replace("\n","\\n")[:50]
        m = ">>" if insn.address in HILITE else "  "
        print("%s 0x%08X: %s" % (m, insn.address, txt))
