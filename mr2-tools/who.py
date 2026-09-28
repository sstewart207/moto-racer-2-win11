import struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

PATH = r"C:\Games\Moto Racer 2\Moto.exe"
pe = pefile.PE(PATH)
IB = pe.OPTIONAL_HEADER.ImageBase
raw = open(PATH, 'rb').read()
md = Cs(CS_ARCH_X86, CS_MODE_32)

def s_at(va, n=90):
    try: off = pe.get_offset_from_rva(va - IB)
    except Exception: return None
    b = raw[off:off+n]
    end = 0
    while end < len(b) and b[end] != 0 and (32 <= b[end] < 127 or b[end] in (9,10,13)):
        end += 1
    if end < 2: return None
    return b[:end].decode('latin1')

text = pe.sections[0]
base = IB + text.VirtualAddress
instrs = []
for ins in md.disasm(text.get_data(), base):
    instrs.append((ins.address, ins.mnemonic, ins.op_str))
idx = {a: i for i, (a, mn, op) in enumerate(instrs)}
print('instrs', len(instrs))

def func_entry(target):
    """nearest preceding push ebp ; mov ebp, esp on a valid boundary"""
    i = idx.get(target)
    if i is None:
        i = max(k for k, (a, _, _) in enumerate(instrs) if a <= target)
    while i > 0:
        a, mn, op = instrs[i]
        if (mn == 'mov' and op == 'ebp, esp' and i > 0
                and instrs[i-1][1] == 'push' and instrs[i-1][2] == 'ebp'):
            return instrs[i-1][0]
        i -= 1
    return None

def callers_of(addr):
    rva = addr - IB
    out = []
    for s in pe.sections:
        d = s.get_data()
        for j in range(0, len(d) - 5):
            if d[j] != 0xE8:
                continue
            rel = struct.unpack_from('<i', d, j + 1)[0]
            if (s.VirtualAddress + j + 5 + rel) == rva:
                out.append(IB + s.VirtualAddress + j)
    return out

def show(a, b, label=''):
    print('\n' + '=' * 74)
    print('== %s  0x%08X..0x%08X' % (label, a, b))
    print('=' * 74)
    i = idx.get(a) or max(k for k, (x, _, _) in enumerate(instrs) if x <= a)
    while i < len(instrs) and instrs[i][0] <= b:
        ad, mn, op = instrs[i]
        txt = '%s %s' % (mn, op)
        for tok in op.replace('[', ' ').replace(']', ' ').replace(',', ' ') \
                     .replace('+', ' ').replace('*', ' ').replace('-', ' ').split():
            if tok.startswith('0x') and len(tok) <= 10:
                try: v = int(tok, 16)
                except Exception: continue
                s = s_at(v)
                if s and len(s) >= 2:
                    txt += '   ; "%s"' % s.replace('\n', '\\n')[:56]
        print('  0x%08X: %s' % (ad, txt))
        i += 1

for site, lbl in ((0x438195, 'FileLand/FileMoto/FileBank reads'),
                  (0x438E5B, 'MotoCarac read'),
                  (0x44036E, 'Load(raw 0x6555b8) [FileMoto caller]'),
                  (0x44048D, 'Load(raw 0x657bbc) [MotoCarac caller]')):
    fe = func_entry(site)
    print('\n%-42s -> func_entry 0x%08X' % (lbl, fe or 0))
    if fe:
        cs = callers_of(fe)
        print('      callers:', [hex(c) for c in cs][:12])

# show the code just BEFORE the two raw-global Load sites: what filename is built
show(0x440330, 0x440380, 'before Load(0x6555b8) @0x44036E')
show(0x440450, 0x4404A0, 'before Load(0x657bbc) @0x44048D')
