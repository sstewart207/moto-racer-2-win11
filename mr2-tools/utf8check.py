import sys

files = [
    r"C:\Games\CLAUDE.md",
    r"C:\Games\GRAPHICS-PLAN.md",
    r"C:\Games\mr2-tools\SESSION5-NOTES.md",
    r"C:\Games\FINDINGS.md",
]

bad = 0
for p in files:
    raw = open(p, "rb").read()
    try:
        t = raw.decode("utf-8")
        enc = "utf-8 ok"
    except UnicodeDecodeError as e:
        enc = "DECODE FAIL: %s" % e
        t = raw.decode("utf-8", "replace")
        bad += 1
    repl = t.count("\ufffd")
    moj = sum(t.count(s) for s in ("â€™", "â€œ", "Ã©", "ï»¿"))
    name = p.split("\\")[-1]
    print("%-24s %7d bytes  %-12s  replacement=%d  mojibake=%d"
          % (name, len(raw), enc, repl, moj))
    if repl or moj:
        bad += 1

print()
print("RESULT:",
      "CLEAN - all UTF-8, no corruption" if bad == 0
      else "%d FILE(S) PROBLEMATIC" % bad)

t = open(files[0], encoding="utf-8").read()
print()
print("CLAUDE.md  headings=%d  'WRONG' markers=%d  strikethrough spans=%d  SESSION5 ref=%d"
      % (t.count("\n#"), t.count("WRONG"), t.count("~~"), t.count("SESSION5")))
