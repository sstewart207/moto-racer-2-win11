import struct, os, glob, re

ROOT = r'C:\Games\Moto Racer 2\data'
OUT  = r'C:\Games\mr2-tools\extracted'
os.makedirs(OUT, exist_ok=True)

def read_bkf(path):
    d = open(path, 'rb').read()
    magic, nfiles, namesz = struct.unpack_from('<III', d, 0)
    assert magic == 0xfffffffe
    recsz = namesz + 16
    ent = []
    for i in range(nfiles):
        o = 12 + i * recsz
        raw = d[o:o+namesz]
        z = raw.find(b'\x00')
        name = raw[:z if z >= 0 else namesz].decode('latin1')
        off, size = struct.unpack_from('<II', d, o + namesz)
        ent.append((name, off, size))
    return d, ent

def hx(b, base=0, n=None):
    if n: b = b[:n]
    out = []
    for i in range(0, len(b), 16):
        c = b[i:i+16]
        out.append('%08x  %-47s  %s' % (base + i,
                   ' '.join('%02x' % x for x in c),
                   ''.join(chr(x) if 32 <= x < 127 else '.' for x in c)))
    return '\n'.join(out)

targets = []
for bname in ('SPEED.BKF', 'KTMCROSS.BKF', 'THEMES.BKF'):
    p = os.path.join(ROOT, bname)
    d, ent = read_bkf(p)
    for name, off, size in ent:
        if re.search(r'(?i)\.(bpt)$', name) and (
                'CARAC' in name.upper() or 'LEVEL' in name.upper()
                or 'THEME' in name.upper()):
            targets.append((bname, d, name, off, size))

print('extracting %d files\n' % len(targets))
seen = set()
for bname, d, name, off, size in targets:
    blob = d[off:off+size]
    key = (os.path.basename(bname), name, size)
    if key in seen: continue
    seen.add(key)
    safe = name.replace('\\', '__')
    with open(os.path.join(OUT, safe), 'wb') as f:
        f.write(blob)
    print('=' * 72)
    print('%s :: %s   (%d bytes)' % (bname, name, size))
    print('  header: ' + ' '.join('%02x' % c for c in blob[:32]))
    print(hx(blob, 0, 192))
    # printable runs
    runs = [m.group().decode('latin1')
            for m in re.finditer(rb'[ -~]{5,}', blob)]
    print('  strings: %r' % (runs[:25],))
    # entropy
    import math, collections
    c = collections.Counter(blob); n = len(blob)
    H = -sum(v / n * math.log2(v / n) for v in c.values())
    print('  entropy=%.3f unique=%d' % (H, len(c)))
    print()
