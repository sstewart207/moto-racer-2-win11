import re, struct, pefile
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

print('=== strings around BLAIREAU ===')
target = None
for m in re.finditer(rb'[ -~\x80-\xff]{3,}', raw):
    s = m.group().decode('latin1', 'replace')
    if 'BLAIREAU' in s.upper() or 'BLAIREAU' in s:
        target = IB + m.start()
        print('  HIT 0x%08X  %r' % (IB + m.start(), s))

if target:
    # neighbours within +/-0x200
    lo, hi = target - 0x180, target + 0x180
    print('\n--- string neighbourhood ---')
    for m in re.finditer(rb'[ -~\x80-\xff]{4,}', raw):
        va = IB + m.start()
        if lo <= va <= hi:
            print('  0x%08X  %r' % (va, m.group().decode('latin1', 'replace')[:80]))

    def refs(v):
        pat = struct.pack('<I', v); out = []
        for s in pe.sections:
            d = s.get_data(); st = 0
            while True:
                j = d.find(pat, st)
                if j < 0: break
                out.append(IB + s.VirtualAddress + j); st = j+1
        return out
    rr = refs(target)
    print('\nrefs ->', [hex(x) for x in rr])

    if rr:
        text = pe.sections[0]
        base = IB + text.VirtualAddress
        instrs = []
        for ins in md.disasm(text.get_data(), base):
            instrs.append((ins.address, ins.mnemonic, ins.op_str))
        idx = {a: i for i, (a, mn, op) in enumerate(instrs)}
        t = rr[0]
        i = max(k for k, (a, _, _) in enumerate(instrs) if a <= t)
        print('\n--- code around ref ---')
        for k in range(i - 24, i + 10):
            if 0 <= k < len(instrs):
                a, mn, op = instrs[k]
                txt = '%s %s' % (mn, op)
                for tok in op.replace('[', ' ').replace(']', ' ').replace(',', ' ') \
                             .replace('+', ' ').replace('*', ' ').replace('-', ' ').split():
                    if tok.startswith('0x') and len(tok) <= 10:
                        try: v = int(tok, 16)
                        except Exception: continue
                        s = s_at(v)
                        if s and len(s) >= 2:
                            txt += '   ; "%s"' % s.replace('\n', '\\n')[:56]
                mk = '>>' if a == t else '  '
                print('%s0x%08X: %s' % (mk, a, txt))

print('\n=== strings containing "protection"/"cdrom"/"CDROM" (excl. generic) ===')
for m in re.finditer(rb'[ -~]{4,}', raw):
    s = m.group().decode('latin1')
    if re.search(r'(?i)protect|nocd|no-cd|cdrom in drive|insert cd', s) and len(s) < 70:
        print('  0x%08X  %r' % (IB + m.start(), s))
