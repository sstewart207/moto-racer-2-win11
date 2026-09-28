import sys, struct

path = sys.argv[1] if len(sys.argv) > 1 else r"C:\GOG Games\Moto Racer 2\data\sfx.bkf"

data = open(path, "rb").read()
magic, count, namelen = struct.unpack_from("<III", data, 0)
print("magic=0x%08X  files=%d  nameFieldLen=%d" % (magic, count, namelen))
print("record size = %d" % (namelen + 16))

RECSZ = namelen + 16
names = []
for i in range(count):
    off = 12 + i * RECSZ
    raw = data[off:off + namelen]
    name = raw.split(b"\x00", 1)[0].decode("latin-1")
    foff, size = struct.unpack_from("<II", data, off + namelen)
    names.append((name, foff, size))

print("\n--- all %d names ---" % len(names))
for n, o, s in names:
    print("   %-46s off=%-9d size=%d" % (n, o, s))

print("\n--- search: 'Gear' ---")
hits = [x for x in names if "gear" in x[0].lower()]
if hits:
    for n, o, s in hits:
        print("   FOUND  %-46s size=%d" % (n, s))
else:
    print("   NOT PRESENT in this archive")

print("\n--- name shape (first 3, repr) ---")
for n, o, s in names[:3]:
    print("   ", repr(n))

print("\n--- distinct directories ---")
dirs = sorted({n.rsplit("\\", 1)[0] if "\\" in n else "(root)" for n, o, s in names})
for d in dirs:
    print("   ", d)
