import re, struct, os, glob, pefile

EXE = r"C:\Games\Moto Racer 2\Moto.exe"
pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
raw = open(EXE, 'rb').read()

print('=== candidate archive base-names in exe ===')
want = re.compile(r'^(THEMES|SPEED|KTMCROSS|PODIUM|FINAL|DEFCHAMP|GENERIC|SFX|VRAM|ILE01|Ile01|CARAC|Carac)$')
found = {}
for m in re.finditer(rb'[ -~]{3,}', raw):
    s = m.group().decode('latin1')
    if want.match(s):
        found.setdefault(s, []).append(hex(IB + m.start()))
for k, v in found.items():
    print('   %-12s %s' % (k, v))

print('\n=== strings containing "Ile" or "Carac" (case-insens) ===')
for m in re.finditer(rb'[ -~]{4,}', raw):
    s = m.group().decode('latin1')
    if re.search(r'(?i)ile0|carac\.|%s.*spt|\.spt"', s) and len(s) < 60:
        print('   0x%08X %r' % (IB + m.start(), s))

# how many times is "DATA\\" used, and what precedes .BKF construction
def refs(va):
    pat = struct.pack('<I', va); out = []
    for s in pe.sections:
        d = s.get_data(); st = 0
        while True:
            j = d.find(pat, st)
            if j < 0: break
            out.append(IB + s.VirtualAddress + j); st = j+1
    return out

print('\nrefs to "DATA\\" 0x4F8F4C ->', [hex(x) for x in refs(0x4F8F4C)])

# Search all BKF indexes for ILE01 / CARAC entries
ROOT = r'C:\Games\Moto Racer 2\data'
print('\n=== BKF entries matching ILE01 / CARAC / LEVEL / CARAC ===')
for p in sorted(glob.glob(os.path.join(ROOT, '*.BKF'))):
    d = open(p, 'rb').read()
    magic, nfiles, namesz = struct.unpack_from('<III', d, 0)
    recsz = namesz + 16
    hits = []
    dirs = set()
    for i in range(nfiles):
        o = 12 + i * recsz
        raw2 = d[o:o+namesz]
        z = raw2.find(b'\x00')
        nm = raw2[:z if z >= 0 else namesz].decode('latin1')
        dirs.add(nm.split('\\')[0] if '\\' in nm else '(root)')
        if re.search(r'(?i)ile01|carac', nm):
            hits.append(nm)
    if hits:
        print('\n  %s -> %d hits' % (os.path.basename(p), len(hits)))
        for h in hits[:30]:
            print('     ', h)
    else:
        print('  %-16s (no ile01/carac)  dirs/root: %s'
              % (os.path.basename(p), sorted(dirs)[:12]))
