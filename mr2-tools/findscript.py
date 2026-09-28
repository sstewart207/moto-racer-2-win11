import os, sys, math, collections

ROOTS = [r"C:\Games\Moto Racer 2", "D:\\"]
TARGETS = [b"FileMoto", b"MotoCarac", b"FileLand", b"theme.spt", b"Level.Spt"]

def entropy(b):
    if not b:
        return 0.0
    c = collections.Counter(b)
    n = len(b)
    return -sum((v / n) * math.log2(v / n) for v in c.values())

hits = []
spts = []
scanned = 0

for root in ROOTS:
    if not os.path.isdir(root):
        print("MISSING ROOT", root)
        continue
    for dp, dn, fn in os.walk(root):
        for f in fn:
            p = os.path.join(dp, f)
            try:
                sz = os.path.getsize(p)
                if sz == 0 or sz > 400_000_000:
                    continue
                with open(p, "rb") as fh:
                    data = fh.read()
            except Exception:
                continue
            scanned += 1
            dl = data.lower()
            found = [t.decode(errors="replace") for t in TARGETS if t.lower() in dl]
            is_spt = f.lower().endswith(".spt")
            if is_spt:
                spts.append((p, sz, entropy(data), found,
                             data[:48]))
            if found:
                hits.append((p, sz, entropy(data), found))

print(f"=== scanned {scanned} files ===\n")

print("=== files containing target keys ===")
if not hits:
    print("  NONE FOUND ANYWHERE")
for p, sz, e, found in hits:
    print(f"  H={e:5.2f}  {sz:>10}  {','.join(found):26}  {p}")

print("\n=== every .SPT on disk ===")
if not spts:
    print("  NONE")
for p, sz, e, found, head in sorted(spts):
    print(f"  H={e:5.2f}  {sz:>9}  {','.join(found):26}  {p}")
    print(f"           head={head[:40]!r}")
