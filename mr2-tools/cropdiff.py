import sys
sys.path.insert(0, r"C:\Games\mr2-tools")
from pngdiff import read_png

a_path, b_path = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = (int(v) for v in sys.argv[3:7])

w, h, c, da = read_png(a_path)
w2, h2, c2, db = read_png(b_path)
assert (w, h, c) == (w2, h2, c2), "size/channel mismatch"

print("crop (%d,%d)-(%d,%d) from %dx%d image" % (x0, y0, x1, y1, w, h))

total = 0
differ = 0
maxd = 0
for y in range(y0, y1):
    base = y * w * c
    for x in range(x0, x1):
        i = base + x * c
        for k in range(3):
            a = da[i + k]
            b = db[i + k]
            total += 1
            d = abs(a - b)
            if d:
                differ += 1
                if d > maxd:
                    maxd = d

print("RGB samples : %d" % total)
print("differing   : %d  (%.4f%%)" % (differ, 100.0 * differ / total))
print("max delta   : %d" % maxd)
print()
if differ == 0:
    print("VERDICT: static region is PIXEL-IDENTICAL -> ImageScaleFactor=3 changed NOTHING here")
elif 100.0 * differ / total < 1.0:
    print("VERDICT: tiny differences only -> likely negligible / edge antialiasing")
else:
    print("VERDICT: substantial difference in static content -> setting DOES have an effect")
