import struct, sys, os, glob, re, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

# ---------- 1. parse BKF index ----------
def parse_bkf(path, limit=40):
    d = open(path, 'rb').read()
    magic, nfiles, namesz = struct.unpack_from('<III', d, 0)
    out = dict(file=os.path.basename(path), magic=hex(magic),
               nfiles=nfiles, namesz=namesz, size=len(d))
    # guess: header 12 bytes, then nfiles entries of namesz bytes, then data?
    names = []
    off = 12
    for i in range(nfiles):
        if off + namesz > len(d): break
        raw = d[off:off+namesz]
        z = raw.find(b'\x00')
        nm = raw[:z] if z >= 0 else raw
        try: nm = nm.decode('latin1')
        except Exception: nm = repr(nm)
        names.append(nm)
        off += namesz
    out['names'] = names
    out['table_end'] = off
    return out

print("=" * 70)
print("BKF INDEX PARSING")
print("=" * 70)
for p in sorted(glob.glob(r'C:\Games\Moto Racer 2\data\*.BKF')):
    try:
        r = parse_bkf(p)
        print("\n%-16s magic=%s nfiles=%d namesz=%d(0x%x) size=%d table_end=%d"
              % (r['file'], r['magic'], r['nfiles'], r['namesz'], r['namesz'],
                 r['size'], r['table_end']))
        for n in r['names'][:14]:
            print("     %r" % n)
        if len(r['names']) > 14:
            print("     ... %d more" % (len(r['names']) - 14))
        # sanity: does table fit?
        calc = 12 + r['nfiles'] * r['namesz']
        print("     [12 + n*namesz = %d   vs file size %d]" % (calc, r['size']))
    except Exception as e:
        print("%s -> ERR %s" % (os.path.basename(p), e))

# ---------- 2. xref the BKF loader strings ----------
print("\n" + "=" * 70)
print("BKF LOADER XREFS in Moto.exe")
print("=" * 70)
PATH = r"C:\Games\Moto Racer 2\Moto.exe"
pe = pefile.PE(PATH)
IB = pe.OPTIONAL_HEADER.ImageBase
raw = open(PATH, 'rb').read()
md = Cs(CS_ARCH_X86, CS_MODE_32)

def refs(va):
    pat = struct.pack('<I', va)
    out = []
    for s in pe.sections:
        d = s.get_data(); st = 0
        while True:
            j = d.find(pat, st)
            if j < 0: break
            out.append(IB + s.VirtualAddress + j); st = j + 1
    return out

def s_at(va, n=80):
    try: off = pe.get_offset_from_rva(va - IB)
    except Exception: return None
    b = raw[off:off+n]
    end = 0
    while end < len(b) and b[end] != 0 and (32 <= b[end] < 127 or b[end] in (9,10,13)):
        end += 1
    if end < 2: return None
    return b[:end].decode('latin1')

for va, lbl in ((0x4F8E60, 'DATA\\%s.BKF corrupted/bad filename size'),
                (0x4F8EBC, 'DATA\\%s.BKF corrupted/bad num files'),
                (0x4F8F44, '".BKF"')):
    r = refs(va)
    print("\n0x%08X  %-42s -> %s" % (va, lbl, [hex(x) for x in r]))

# disasm around each ref
def window(target, back=0x50, fwd=0x40, label=""):
    print("\n--- %s : ref 0x%08X ---" % (label, target))
    start = target - back
    for insn in md.disasm(pe.get_data(start - IB, back + fwd), start):
        txt = "%s %s" % (insn.mnemonic, insn.op_str)
        toks = insn.op_str.replace('[', ' ').replace(']', ' ').replace(',', ' ') \
                          .replace('+', ' ').replace('*', ' ').replace('-', ' ').split()
        for tok in toks:
            if tok.startswith('0x') and len(tok) <= 10:
                try: v = int(tok, 16)
                except Exception: continue
                s = s_at(v)
                if s and len(s) >= 2:
                    txt += '   ; "%s"' % s.replace('\n', '\\n')[:56]
        m = ">>" if insn.address == target else "  "
        print("%s0x%08X: %s" % (m, insn.address, txt))

for va, lbl in ((0x4F8E60, 'bad filename size'),
                (0x4F8EBC, 'bad num files'),
                (0x4F8F44, '".BKF" ext')):
    for r in refs(va)[:2]:
        window(r, label=lbl)
