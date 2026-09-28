import sys, hashlib

def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest().upper()[:16]

def runs(a, b):
    n = min(len(a), len(b))
    out, start = [], None
    for i in range(n):
        if a[i] != b[i]:
            if start is None:
                start = i
        else:
            if start is not None:
                out.append((start, i)); start = None
    if start is not None:
        out.append((start, n))
    if len(a) != len(b):
        out.append((n, max(len(a), len(b))))
    return out

a_path, b_path = sys.argv[1], sys.argv[2]
A = open(a_path, "rb").read()
B = open(b_path, "rb").read()
r = runs(A, B)
tot = sum(e - s for s, e in r)
print("%s (%d) vs %s (%d)" % (md5(a_path), len(A), md5(b_path), len(B)))
print("  differing runs: %d   bytes changed: %d / %d (%.2f%%)" % (len(r), tot, len(A), 100.0 * tot / len(A)))

# classify: does it look like a benign re-save (scattered small runs) or a
# structural change (one huge run / different size)?
big = [(s, e) for s, e in r if (e - s) > 200]
print("  runs >200 bytes: %d" % len(big))
if big:
    for s, e in big[:5]:
        print("    0x%06X len=%d" % (s, e - s))
print("  first 12 runs:")
for s, e in r[:12]:
    print("    0x%06X len=%-3d  %s -> %s" % (s, e - s, A[s:e][:10].hex(" "), B[s:e][:10].hex(" ")))

# header region (first 0x60 bytes) - settings-ish
print("  header bytes 0x00-0x5F differing:")
hr = [(s, e) for s, e in r if s < 0x60]
if hr:
    for s, e in hr:
        print("    0x%03X: %s -> %s" % (s, A[s:e].hex(" "), B[s:e].hex(" ")))
else:
    print("    (none)")
