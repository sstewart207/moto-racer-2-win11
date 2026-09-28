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

def dump(lo, hi, label=''):
    print('\n' + '=' * 74)
    print('== %s   0x%08X .. 0x%08X' % (label, lo, hi))
    print('=' * 74)
    i = next((idx[a] for a in sorted(idx) if a >= lo), None)
    if i is None:
        i = max(k for k, (a, _, _) in enumerate(instrs) if a <= lo)
    while i < len(instrs) and instrs[i][0] <= hi:
        a, mn, op = instrs[i]
        txt = '%s %s' % (mn, op)
        for tok in op.replace('[', ' ').replace(']', ' ').replace(',', ' ') \
                     .replace('+', ' ').replace('*', ' ').replace('-', ' ').split():
            if tok.startswith('0x') and len(tok) <= 10:
                try: v = int(tok, 16)
                except Exception: continue
                s = s_at(v)
                if s and len(s) >= 2:
                    txt += '   ; "%s"' % s.replace('\n', '\\n')[:58]
        print('  0x%08X: %s' % (a, txt))
        i += 1

# fread-like wrapper used by ReadString
dump(0x4273D4, 0x427470, '0x4273d4 fread-like wrapper')
# tail of ReadString where decode would happen
dump(0x437510, 0x4375E0, 'ReadString tail (0x437510-0x4375E0)')
# candidate decode helper
dump(0x414540, 0x414610, '0x414540 candidate decoder')
