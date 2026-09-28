import struct, os

def hx(b, base=0):
    lines = []
    for i in range(0, len(b), 16):
        chunk = b[i:i+16]
        hexs = ' '.join('%02x' % c for c in chunk)
        asc = ''.join(chr(c) if 32 <= c < 127 else '.' for c in chunk)
        lines.append('%08x  %-47s  %s' % (base + i, hexs, asc))
    return '\n'.join(lines)

p = r'C:\Games\Moto Racer 2\data\GENERIC.BKF'
d = open(p, 'rb').read()
print('size', len(d))
print(hx(d[:320]))
print()

# try record sizes
magic, nfiles, namesz = struct.unpack_from('<III', d, 0)
print('magic=%x nfiles=%d namesz=%d' % (magic, nfiles, namesz))

for rec in (48, 52, 56, 64, 128, 192):
    ok = []
    for i in range(nfiles):
        off = 12 + i * rec
        if off + 48 > len(d): break
        raw = d[off:off+48]
        z = raw.find(b'\x00')
        nm = raw[:z if z >= 0 else 48]
        ok.append(nm)
    printable = sum(1 for n in ok
                    if n and all(32 <= c < 127 for c in n) and len(n) >= 4)
    print('rec=%-4d printable=%d/%d  first=%r' %
          (rec, printable, len(ok), ok[0][:40]))
