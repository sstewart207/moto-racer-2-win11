"""Isolate the config.bin volume byte.

Trick: config.bin churns (checksum/seed) on EVERY save, so comparing two files
saved at different times cancels nothing.  But `version1` (21:11) and
`session5-live.bak` (22:57) are BOTH volume=0% AND saved hours apart - so any
byte where they AGREE while the known-good file DISAGREES cannot be churn.
That leaves only stable settings that changed between 17:44 (vol 100%) and
21:11 (vol 0%).  The volume is among them.
"""

GOOD    = r"C:\Games\mr2-state-backup\config.bin.bak"              # 735E.. vol 100%
V1      = r"C:\Games\mr2-state-backup\config.bin.version1"         # E28E.. vol 0%
BROKEN  = r"C:\Games\mr2-state-backup\config.bin.session5-live.bak"# 6DAD.. vol 0%
LIVE    = r"C:\GOG Games\Moto Racer 2\data\config.bin"             # current

good   = open(GOOD,   "rb").read()
v1     = open(V1,     "rb").read()
broken = open(BROKEN, "rb").read()
live   = open(LIVE,   "rb").read()

n = min(len(good), len(v1), len(broken), len(live))
cands = [i for i in range(n)
         if v1[i] == broken[i] and good[i] != v1[i]]

print("bytes where both broken configs AGREE and GOOD differs: %d" % len(cands))
print("(churn cancels because they were saved 2h apart)\n")

print("%-12s %-6s %-6s %-6s %-6s" % ("offset", "GOOD", "V1", "BROKEN", "LIVE"))
print("-" * 44)
for i in cands:
    tag = ""
    if live[i] == good[i]:
        tag = "  <- LIVE matches GOOD (vol 100)"
    elif live[i] == broken[i]:
        tag = "  <- LIVE matches BROKEN (vol 0)"
    else:
        tag = "  <- LIVE matches NEITHER"
    print("0x%08X 0x%02X   0x%02X   0x%02X   0x%02X%s"
          % (i, good[i], v1[i], broken[i], live[i], tag))

print()
m_good = sum(1 for i in cands if live[i] == good[i])
m_bad = sum(1 for i in cands if live[i] == broken[i])
m_none = len(cands) - m_good - m_bad
print("LIVE == GOOD  (volume normal): %d / %d" % (m_good, len(cands)))
print("LIVE == BROKEN(volume 0)     : %d / %d" % (m_bad, len(cands)))
print("LIVE == neither              : %d / %d" % (m_none, len(cands)))
