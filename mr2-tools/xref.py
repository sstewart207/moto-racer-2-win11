import struct, pefile, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

PATH = r"C:\Games\Moto Racer 2\Moto.exe"
pe = pefile.PE(PATH)
IMAGE_BASE = pe.OPTIONAL_HEADER.ImageBase

def va2off(va):
    rva = va - IMAGE_BASE
    return pe.get_offset_from_rva(rva)

# Build a table of interesting strings -> VA
raw = open(PATH, "rb").read()
needles = [
    "Cannot open file %s !",
    "Please insert CDROM in drive.",
    "Do you want to continue ?",
    "data\\config.bin",
    "VERSION 3.1",
    "Data\\Config.bpt",
    "Data\\Delphine.err",
]
strva = {}
for n in needles:
    b = n.encode("latin1")
    i = raw.find(b)
    if i < 0:
        print("NOT FOUND STR:", repr(n)); continue
    try:
        rva = pe.get_rva_from_offset(i)
    except Exception:
        rva = None
    if rva is None:
        print("no rva for", n); continue
    strva[IMAGE_BASE + rva] = n
    print("STR %-32s VA=0x%08X" % (n, IMAGE_BASE + rva))

def find_xrefs(target_va):
    pat = struct.pack("<I", target_va)
    hits = []
    for s in pe.sections:
        data = s.get_data()
        start = 0
        while True:
            j = data.find(pat, start)
            if j < 0: break
            rva = s.VirtualAddress + j
            hits.append(rva)
            start = j + 1
    return hits

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False

def annotate(insn):
    txt = insn.mnemonic + " " + insn.op_str
    for v, s in strva.items():
        if ("%08X" % v) in insn.op_str.upper() or ("0x%X" % v) in insn.op_str:
            txt += "    ;-> \"%s\"" % s
    return txt

for label, needle in [
    ("Please insert CDROM", "Please insert CDROM in drive."),
    ("Cannot open file %s !", "Cannot open file %s !"),
]:
    i = raw.find(needle.encode("latin1"))
    if i < 0:
        print("\n### %s : string missing" % label); continue
    va = IMAGE_BASE + pe.get_rva_from_offset(i)
    x = find_xrefs(va)
    print("\n### %s  VA=0x%08X  xrefs=%s" % (label, va, [hex(IMAGE_BASE+r) for r in x]))
    for r in x:
        start = max(0, r - 0x160)
        length = 0x220
        code = pe.get_data(start, length)
        print("--- disasm around xref rva 0x%X ---" % r)
        for insn in md.disasm(code, IMAGE_BASE + start):
            mark = ">>" if insn.address == IMAGE_BASE + r else "  "
            print("%s 0x%08X: %s" % (mark, insn.address, annotate(insn)))
