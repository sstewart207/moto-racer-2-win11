import struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

PATH = r"C:\Games\Moto Racer 2\Moto.exe"
pe = pefile.PE(PATH)
IB = pe.OPTIONAL_HEADER.ImageBase
raw = open(PATH, "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_32)

# ---- strings around the message block ----
def s_at(va, n=64):
    off = pe.get_offset_from_offset if False else None
    try:
        off = pe.get_offset_from_rva(va - IB)
    except Exception:
        return "?"
    b = raw[off:off+n]
    b = b.split(b"\x00")[0]
    return b.decode("latin1")

for va in (0x4f8aac, 0x4f8cb0, 0x4f8cc0, 0x4f8cd6, 0x4f896e, 0x4f8ca0, 0x4f8c90, 0x4f8c80):
    print("VA 0x%08X -> %r" % (va, s_at(va)))

# ---- disassemble 0x427100 .. 0x4272D0 fully ----
print("\n===== function 0x427100 =====")
start = 0x427100
for insn in md.disasm(pe.get_data(start - IB, 0x200), IB + start):
    txt = "%s %s" % (insn.mnemonic, insn.op_str)
    # annotate immediates that look like string VAs
    for tok in insn.op_str.replace("[", " ").replace("]", " ").replace(",", " ").split():
        try:
            v = int(tok, 16)
        except Exception:
            continue
        if 0x4F0000 <= v < 0x560000:
            txt += '   ; "%s"' % s_at(v)
    print("0x%08X: %s" % (insn.address, txt))

# ---- find callers of 0x427100 (push/call imm32) ----
print("\n===== callers of 0x427100 =====")
target = struct.pack("<I", 0x427100)
for s in pe.sections:
    d = s.get_data()
    st = 0
    while True:
        j = d.find(target, st)
        if j < 0:
            break
        # candidate call: byte before is 0xE8, immediate is relative
        if j >= 1 and d[j-1] == 0xE8:
            rva = s.VirtualAddress + j - 1
            rel = struct.unpack_from("<i", d, j)[0]
            callva = IB + rva
            disp = IB + s.VirtualAddress + j + 4 + rel
            print("  call at 0x%08X  -> target 0x%08X" % (callva, disp))
        st = j + 1
