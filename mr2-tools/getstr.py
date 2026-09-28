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

# sweep .text once, keep boundaries
text = pe.sections[0]
base = IB + text.VirtualAddress
instrs = []
for ins in md.disasm(text.get_data(), base):
    instrs.append((ins.address, ins.mnemonic, ins.op_str))
idx = {a: i for i, (a, mn, op) in enumerate(instrs)}
print('instrs', len(instrs))

def dump(target, back=0, fwd=0x110, label=''):
    if target not in idx:
        # nearest
        cand = max(i for i, (a, _, _) in enumerate(instrs) if a <= target)
        print('(0x%08X not boundary; nearest 0x%08X)' % (target, instrs[cand][0]))
        i = cand
    else:
        i = idx[target]
    j = i
    end = instrs[i][0] + fwd
    print('\n' + '=' * 74)
    print('== %s  @ 0x%08X' % (label, target))
    print('=' * 74)
    while j < len(instrs) and instrs[j][0] <= end:
        a, mn, op = instrs[j]
        txt = '%s %s' % (mn, op)
        for tok in op.replace('[', ' ').replace(']', ' ').replace(',', ' ') \
                     .replace('+', ' ').replace('*', ' ').replace('-', ' ').split():
            if tok.startswith('0x') and len(tok) <= 10:
                try: v = int(tok, 16)
                except Exception: continue
                s = s_at(v)
                if s and len(s) >= 2:
                    txt += '   ; "%s"' % s.replace('\n', '\\n')[:58]
        mk = '>>' if a == target else '  '
        print('%s0x%08X: %s' % (mk, a, txt))
        if mn in ('ret', 'retn') and j > i + 3:
            break
        j += 1

dump(0x437ECE, label='GetString(key, buf)')
dump(0x43749B, label='ReadString(buf)')
dump(0x438048, label='parse/reset (called before Get)')
dump(0x436C46, fwd=0x40, label='.BPT open builder (head)')

# find enclosing-function starts for the Get callers by scanning back to a prologue
def find_func(t):
    i = max(k for k, (a, _, _) in enumerate(instrs) if a <= t)
    best = None
    while i > 0:
        a, mn, op = instrs[i]
        if mn == 'mov' and op == 'ebp, esp' and instrs[i-1][1] == 'push' \
           and instrs[i-1][2] == 'ebp':
            best = instrs[i-1][0]
        if best and t - best < 0x4000:
            # verify boundaries fall on t
            for k in range(i, i + 4000):
                if k < len(instrs) and instrs[k][0] == t:
                    return best
            best = None
        i -= 1
    return None

for t in (0x438195, 0x438E5B):
    print('func containing 0x%08X -> %s' % (t, hex(find_func(t) or 0)))
