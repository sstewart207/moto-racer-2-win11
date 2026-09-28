import re, struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

PATH = r"C:\Games\Moto Racer 2\Moto.exe"
pe = pefile.PE(PATH)
IB = pe.OPTIONAL_HEADER.ImageBase
raw = open(PATH, 'rb').read()
md = Cs(CS_ARCH_X86, CS_MODE_32)

def s_at(va, n=100):
    try: off = pe.get_offset_from_rva(va - IB)
    except Exception: return None
    b = raw[off:off+n]
    end = 0
    while end < len(b) and b[end] != 0 and (32 <= b[end] < 127 or b[end] in (9,10,13)):
        end += 1
    if end < 2: return None
    return b[:end].decode('latin1')

print('=== strings mentioning CARAC / Themes / .BPT path formats ===')
for m in re.finditer(rb'[ -~]{3,}', raw):
    s = m.group().decode('latin1')
    if re.search(r'(?i)carac|themes\\|themes|%s.*\.(bpt|spt)|file(moto|land|bank)', s) and len(s) < 70:
        print('  0x%08X  %r' % (IB + m.start(), s))

def refs(va):
    pat = struct.pack('<I', va); out = []
    for s in pe.sections:
        d = s.get_data(); st = 0
        while True:
            j = d.find(pat, st)
            if j < 0: break
            out.append(IB + s.VirtualAddress + j); st = j+1
    return out

# "MotoCarac" @ 0x4f9c1c, "FileLand" @ 0x4f9ba8
for va, lbl in ((0x4F9C1C, 'MotoCarac'), (0x4F9BA8, 'FileLand')):
    r = refs(va)
    print('\nrefs to %-10s 0x%08X -> %s' % (lbl, va, [hex(x) for x in r]))

# Build a boundary map of .text so we can find enclosing functions
text = pe.sections[0]
base = IB + text.VirtualAddress
instrs = []
for ins in md.disasm(text.get_data(), base):
    instrs.append((ins.address, ins.mnemonic, ins.op_str))
print('\ninstrs', len(instrs))
starts = []
for i in range(1, len(instrs)):
    a, mn, op = instrs[i]
    pa, pmn, pop = instrs[i-1]
    if pmn == 'push' and pop == 'ebp' and mn == 'mov' and op == 'ebp, esp':
        starts.append(pa)

def find_func(t):
    lo = None
    for c in starts:
        if c <= t: lo = c
        else: break
    return lo

# For the object-reading function containing 0x438195, find callers
def callers_of(target):
    tgt_rva = target - IB; out = []
    for s in pe.sections:
        d = s.get_data()
        for j in range(0, len(d)-5):
            if d[j] != 0xE8: continue
            rel = struct.unpack_from('<i', d, j+1)[0]
            if (s.VirtualAddress + j + 5 + rel) == tgt_rva:
                out.append(IB + s.VirtualAddress + j)
    return out

# find where the script object gets its file: look for func containing 0x438195
f = find_func(0x438195)
print('\nfunc containing 0x438195 -> 0x%08X' % (f or 0))
if f:
    print('  callers of that func ->', [hex(x) for x in callers_of(f)][:20])

# dump strings near that function (format strings used to open files)
print('\n=== window 0x438000..0x438200 (aligned sweep) ===')
for a, mn, op in instrs:
    if a < 0x437F80 or a > 0x438210: continue
    txt = '%s %s' % (mn, op)
    for tok in op.replace('[', ' ').replace(']', ' ').replace(',', ' ') \
                 .replace('+', ' ').replace('*', ' ').replace('-', ' ').split():
        if tok.startswith('0x') and len(tok) <= 10:
            try: v = int(tok, 16)
            except Exception: continue
            s = s_at(v)
            if s and len(s) >= 2:
                txt += '   ; "%s"' % s.replace('\n', '\\n')[:60]
    print('  0x%08X: %s' % (a, txt))
