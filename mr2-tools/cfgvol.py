import sys

GOOD = r"C:\Games\mr2-state-backup\config.bin.bak"              # vol 100%
BAD  = r"C:\Games\mr2-state-backup\config.bin.session5-live.bak" # vol 0%  (-NoSound)
LIVE = r"C:\GOG Games\Moto Racer 2\data\config.bin"

good = open(GOOD, "rb").read()
bad  = open(BAD,  "rb").read()
live = open(LIVE, "rb").read()


def runs(a, b):
    n = min(len(a), len(b))
    out, st = [], None
    for i in range(n):
        if a[i] != b[i]:
            if st is None:
                st = i
        else:
            if st is not None:
                out.append((st, i)); st = None
    if st is not None:
        out.append((st, n))
    return out


def churn(s, e):
    """Regions that change on EVERY save (header checksum/seed + churn block)."""
    if e <= 0x60:                      # header bytes 0x28-0x4E
        return True
    if s >= 0x5900 and e <= 0x5C00:    # known churn block ~0x593C+
        return True
    return False


print("good(%d) vs broken(%d): %d runs, %d bytes differ"
      % (len(good), len(bad), len(runs(good, bad)), sum(e - s for s, e in runs(good, bad))))

r = runs(good, bad)
stable = [(s, e) for s, e in r if not churn(s, e)]
print("runs outside churn regions: %d" % len(stable))
print()
print("%-10s %-6s %-14s %-14s %-14s" % ("offset", "len", "GOOD(vol100)", "BROKEN(vol0)", "LIVE"))
print("-" * 64)
for s, e in stable:
    print("0x%08X %-6d %-14s %-14s %-14s"
          % (s, e - s, good[s:e].hex(" "), bad[s:e].hex(" "), live[s:e].hex(" ")))

print()
print("== verdict on LIVE ==")
if not stable:
    print("  no stable-region differences between good and broken - "
          "cannot isolate volume this way")
else:
    # a setting differs if LIVE matches BAD at those offsets
    match_good = sum(1 for s, e in stable if live[s:e] == good[s:e])
    match_bad = sum(1 for s, e in stable if live[s:e] == bad[s:e])
    print("  stable settings where LIVE == GOOD (vol 100): %d / %d" % (match_good, len(stable)))
    print("  stable settings where LIVE == BROKEN (vol 0) : %d / %d" % (match_bad, len(stable)))
