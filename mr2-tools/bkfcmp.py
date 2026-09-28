import sys, struct

def read(path):
    d = open(path, "rb").read()
    magic, count, namelen = struct.unpack_from("<III", d, 0)
    recsz = namelen + 16
    names = []
    for i in range(count):
        off = 12 + i * recsz
        raw = d[off:off + namelen]
        nm = raw.split(b"\x00", 1)[0].decode("latin-1")
        foff, size = struct.unpack_from("<II", d, off + namelen)
        names.append((nm, foff, size))
    return magic, count, namelen, names

for p in sys.argv[1:]:
    m, c, nl, names = read(p)
    print("%s" % p)
    print("   magic=0x%08X files=%d nameFieldLen=%d" % (m, c, nl))
    for nm, o, s in names[:8]:
        vis = "".join(ch if 32 <= ord(ch) < 127 else "." for ch in nm)
        print("     %-34s off=%-9d size=%d" % (vis, o, s))
    gears = [n for n in names if "gear" in n[0].lower() and n[0].upper().startswith("SPEED")]
    print("     SPEED\\GEAR* -> %s" % ([g[0] for g in gears] or "NONE"))
    # is the whole table plain ascii?
    bad = sum(1 for nm, o, s in names
              if any(ord(c) < 32 or ord(c) > 126 for c in nm))
    print("     non-ascii names: %d / %d" % (bad, len(names)))
    print()
