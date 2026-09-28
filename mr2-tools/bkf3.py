import struct, os, glob, re, sys

ROOT = r'C:\Games\Moto Racer 2\data'

def read_index(path):
    d = open(path, 'rb').read()
    magic, nfiles, namesz = struct.unpack_from('<III', d, 0)
    assert magic == 0xfffffffe, hex(magic)
    recsz = namesz + 16          # name[namesz] + offset(4) + size(4) + cksum(8)
    assert namesz == 48, namesz
    entries = []
    base = 12
    for i in range(nfiles):
        o = base + i * 64
        raw = d[o:o+48]
        z = raw.find(b'\x00')
        name = raw[:z if z >= 0 else 48].decode('latin1')
        off, size = struct.unpack_from('<II', d, o + 48)
        ck = d[o+56:o+64]
        entries.append((name, off, size, ck))
    return d, entries

allnames = {}
for p in sorted(glob.glob(os.path.join(ROOT, '*.BKF'))):
    try:
        d, ent = read_index(p)
    except Exception as e:
        print('%-16s ERR %s' % (os.path.basename(p), e)); continue
    data_start = 12 + len(ent) * 64
    bad = [e for e in ent if e[1] + e[2] > len(d) or e[1] < data_start]
    print('\n=== %-16s %d files, data@%d, size=%d, bad=%d ==='
          % (os.path.basename(p), len(ent), data_start, len(d), len(bad)))
    allnames[os.path.basename(p)] = ent
    ext = {}
    for n, o, s, c in ent:
        e = os.path.splitext(n)[1].upper()
        ext[e] = ext.get(e, 0) + 1
    print('   exts:', dict(sorted(ext.items(), key=lambda kv: -kv[1])))
    for n, o, s, c in ent:
        if re.search(r'(?i)\.(bpt|spt)$', n):
            print('   ** SCRIPT/BPT: %-50s off=%d size=%d' % (n, o, s))

# full listing of THEMES.BKF (the important one)
print('\n' + '=' * 72)
print('THEMES.BKF — entries containing theme/bpt/spt/config/level')
print('=' * 72)
d, ent = allnames.get('THEMES.BKF', (None, []))
if ent:
    for n, o, s, c in ent:
        if re.search(r'(?i)(theme|\.bpt|\.spt|config|level|carac|moto|file)', n):
            print('   %-56s off=%-9d size=%d' % (n, o, s))

# also: dump any *.Spt-like from ALL archives
print('\n' + '=' * 72)
print('ALL .BPT / .Spt across every BKF')
print('=' * 72)
for k, ent in allnames.items():
    for n, o, s, c in ent:
        if re.search(r'(?i)\.(bpt|spt)$', n):
            print('   %-16s %-56s off=%-9d size=%d' % (k, n, o, s))

# how many distinct directories
print('\n' + '=' * 72)
print('THEMES.BKF top-level dirs')
print('=' * 72)
if ent:
    dirs = {}
    for n, o, s, c in ent:
        d0 = n.split('\\')[0] if '\\' in n else '(root)'
        dirs[d0] = dirs.get(d0, 0) + 1
    for k in sorted(dirs):
        print('   %-20s %d' % (k, dirs[k]))
