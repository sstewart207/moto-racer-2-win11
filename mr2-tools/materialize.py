import struct, os, re, shutil

ROOT = r'C:\Games\Moto Racer 2\data'

ARCH2DISK = {
    'AMAZONIA.D': 'Amazonia.D', 'AMAZONIA.S': 'Amazonia.S',
    'BRITANY.D':  'Britany.D',  'BRITANY.S':  'Britany.S',
    'GRANDPRI':   'GrandPri',   'OUTDOOR':    'OutDoor',
    'SAHARA.D':   'Sahara.D',   'SAHARA.S':   'Sahara.S',
}

def read_bkf(path):
    d = open(path, 'rb').read()
    magic, nfiles, namesz = struct.unpack_from('<III', d, 0)
    recsz = namesz + 16
    ent = []
    for i in range(nfiles):
        o = 12 + i * recsz
        raw = d[o:o+namesz]
        z = raw.find(b'\x00')
        nm = raw[:z if z >= 0 else namesz].decode('latin1')
        off, size = struct.unpack_from('<II', d, o + namesz)
        ent.append((nm, off, size))
    return d, ent

log = []

# 1) THEMES.BKF -> data\Themes\<diskdir>\*.BPT
d, ent = read_bkf(os.path.join(ROOT, 'THEMES.BKF'))
for nm, off, size in ent:
    if not re.search(r'(?i)\.bpt$', nm):
        continue
    arch_dir, fname = nm.split('\\')[0], nm.split('\\')[1]
    disk_dir = ARCH2DISK.get(arch_dir, arch_dir)
    dst_dir = os.path.join(ROOT, 'Themes', disk_dir)
    if not os.path.isdir(dst_dir):
        log.append('MISSING DIR %s' % dst_dir)
        continue
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, fname)
    if not os.path.exists(dst):
        with open(dst, 'wb') as f:
            f.write(d[off:off+size])
        log.append('WROTE %-58s %d bytes' % (dst.replace(ROOT, 'data'), size))

# 2) CARAC1..8.BPT from SPEED.BKF -> data\ root
d, ent = read_bkf(os.path.join(ROOT, 'SPEED.BKF'))
for nm, off, size in ent:
    if re.match(r'(?i)CARAC\d\.BPT$', nm):
        dst = os.path.join(ROOT, nm)
        if not os.path.exists(dst):
            with open(dst, 'wb') as f:
                f.write(d[off:off+size])
            log.append('WROTE %-58s %d bytes' % (dst.replace(ROOT, 'data'), size))

# 3) also place CARAC copies under data\Themes\ in case path is theme-relative
for nm, off, size in ent:
    if re.match(r'(?i)CARAC\d\.BPT$', nm):
        for sub in ARCH2DISK.values():
            dst = os.path.join(ROOT, 'Themes', sub, nm)
            if os.path.isdir(os.path.dirname(dst)) and not os.path.exists(dst):
                with open(dst, 'wb') as f:
                    f.write(d[off:off+size])
                log.append('WROTE %-58s %d bytes' % (dst.replace(ROOT, 'data'), size))

print('\n'.join(log) if log else 'nothing to do')
print('\n--- data\Themes\*.BPT now ---')
for sub in sorted(os.listdir(os.path.join(ROOT, 'Themes'))):
    p = os.path.join(ROOT, 'Themes', sub)
    if os.path.isdir(p):
        bpts = [f for f in os.listdir(p) if f.lower().endswith('.bpt')]
        print('  %-14s %d bpt: %s' % (sub, len(bpts), bpts))
print('\n--- data\*.BPT ---')
print('  ', sorted(f for f in os.listdir(ROOT) if f.lower().endswith('.bpt')))
