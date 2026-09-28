import struct, os, re, math, collections

ROOT = r'C:\Games\Moto Racer 2\data'

def read_bkf(path):
    d = open(path, 'rb').read()
    magic, nfiles, namesz = struct.unpack_from('<III', d, 0)
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

def hx(b, n=None):
    if n: b = b[:n]
    out = []
    for i in range(0, len(b), 16):
        c = b[i:i+16]
        out.append('%04x  %-47s  %s' % (i, ' '.join('%02x' % x for x in c),
                   ''.join(chr(x) if 32 <= x < 127 else '.' for x in c)))
    return '\n'.join(out)

def ent_of(blob):
    c = collections.Counter(blob); n = len(blob)
    return -sum(v / n * math.log2(v / n) for v in c.values())

d, ent = read_bkf(os.path.join(ROOT, 'THEMES.BKF'))
pick = ['AMAZONIA.D\\LEVEL.BPT', 'AMAZONIA.D\\THEME.BPT', 'AMAZONIA.D\\SOUND.BPT']
for name, off, size in ent:
    if name not in pick: continue
    blob = d[off:off+size]
    print('=' * 74)
    print('%s  (%d bytes)  entropy=%.3f' % (name, size, ent_of(blob)))
    print(hx(blob, 256))
    runs = [m.group().decode('latin1') for m in re.finditer(rb'[ -~]{4,}', blob)]
    print('  strings(%d): %r' % (len(runs), runs[:40]))
    for kw in (b'MotoCarac', b'FileMoto', b'FileLand', b'FileBank', b'Version', b'VERSION'):
        print('   %-10s -> %s' % (kw.decode(), kw in blob or kw.lower() in blob.lower()))
    print()

# Also dump CARAC1 and one from KTMCROSS for comparison, plus disk files
print('=' * 74)
print('DISK .BPT files')
print('=' * 74)
for f in ('CONFIG.BPT', 'COURSEAI.BPT', 'CROSSAI.BPT', 'MOTOSPD.BPT', 'MOTOKTM.BPT'):
    p = os.path.join(ROOT, f)
    b = open(p, 'rb').read()
    print('%-14s %6d entropy=%.3f header=%s' % (f, len(b), ent_of(b),
          ' '.join('%02x' % x for x in b[:8])))
    runs = [m.group().decode('latin1') for m in re.finditer(rb'[ -~]{4,}', b)]
    print('   strings: %r' % (runs[:20],))
