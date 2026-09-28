import hashlib, os, sys, glob

LIVE = r"C:\GOG Games\Moto Racer 2\data\config.bin"
ROOT = r"C:\Games"

def md5(p):
    try:
        return hashlib.md5(open(p, "rb").read()).hexdigest().upper()
    except Exception:
        return None

# gather candidates: live + every backup-ish file in C:\Games
cands = [LIVE]
for pat in ("**/*config*", "**/*CONFIG*"):
    cands += glob.glob(os.path.join(ROOT, pat), recursive=True)
cands = [c for c in dict.fromkeys(cands) if os.path.isfile(c)]

TARGET = {
    "735ED17DEB7E0827": "ORIGINAL (17:44, pre-session-4)",
    "E28E473E76D8097A": "session4 (21:11, after -NoSound launches)",
    "6DAD67F4ACFDDFEC": "LIVE (22:57, just now)",
}

found = {}
for c in cands:
    h = md5(c)
    if h and h[:16] in TARGET and h[:16] not in found:
        found[h[:16]] = c

print("=== located ===")
for k, label in TARGET.items():
    p = found.get(k)
    print("  %-42s %s" % (label, p if p else "*** NOT FOUND ***"))

if len(found) < 2:
    print("\nnot enough versions to diff")
    sys.exit(0)

order = ["735ED17DEB7E0827", "E28E473E76D8097A", "6DAD67F4ACFDDFEC"]
order = [k for k in order if k in found]
data = {k: open(found[k], "rb").read() for k in order}

def runs(a, b):
    """yield (start, end) of differing byte runs"""
    n = min(len(a), len(b))
    out, start = [], None
    for i in range(n):
        if a[i] != b[i]:
            if start is None:
                start = i
        else:
            if start is not None:
                out.append((start, i))
                start = None
    if start is not None:
        out.append((start, n))
    if len(a) != len(b):
        out.append((n, max(len(a), len(b))))
    return out

print("\n=== byte-level differences ===")
for i in range(len(order) - 1):
    ka, kb = order[i], order[i + 1]
    A, B = data[ka], data[kb]
    r = runs(A, B)
    print("\n  %s  ->  %s" % (TARGET[ka][:24], TARGET[kb][:24]))
    print("   size %d -> %d ; %d differing run(s)" % (len(A), len(B), len(r)))
    if not r:
        print("   IDENTICAL")
        continue
    total = sum(e - s for s, e in r)
    print("   total differing bytes: %d / %d (%.2f%%)" % (total, len(A), 100.0 * total / len(A)))
    for s, e in r[:25]:
        chunkA = A[s:e]
        chunkB = B[s:e]
        print("     off=0x%06X len=%d" % (s, e - s))
        print("        A: %s" % chunkA[:24].hex(" "))
        print("        B: %s" % chunkB[:24].hex(" "))
        # printable view
        pa = "".join(chr(c) if 32 <= c < 127 else "." for c in chunkA[:48])
        pb = "".join(chr(c) if 32 <= c < 127 else "." for c in chunkB[:48])
        print("        A: %s" % pa)
        print("        B: %s" % pb)
    if len(r) > 25:
        print("     ... %d more run(s)" % (len(r) - 25))

# overall: first->last
if len(order) >= 2:
    k0, k1 = order[0], order[-1]
    r = runs(data[k0], data[k1])
    print("\n=== ORIGINAL -> LIVE : %d run(s), %d bytes changed ===" %
          (len(r), sum(e - s for s, e in r)))
    for s, e in r[:40]:
        print("   0x%06X  len=%-4d  %s  ->  %s" % (
            s, e - s,
            data[k0][s:e][:16].hex(" "),
            data[k1][s:e][:16].hex(" ")))
