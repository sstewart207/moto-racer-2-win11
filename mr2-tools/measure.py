import sys, struct, zlib
sys.path.insert(0, r"C:\Games\mr2-tools")
from pngdiff import read_png

def bbox(data, W, C, x0, y0, x1, y1, thr=235):
    xs, ys = [], []
    for y in range(y0, y1):
        for x in range(x0, x1):
            i = (y * W + x) * C
            if data[i] > thr and data[i+1] > thr and data[i+2] > thr:
                xs.append(x); ys.append(y)
    if not xs:
        return None
    return (min(xs), max(xs), min(ys), max(ys), len(xs))

src = sys.argv[1]
W, H, C, d = read_png(src)

# cursor parked at (995,995): search a tight window around it
cb = bbox(d, W, C, 960, 960, 1040, 1040)
print("%s" % src)
if cb:
    x0, x1, y0, y1, n = cb
    print("  CURSOR bbox: x=%d..%d (w=%d)  y=%d..%d (h=%d)  white=%d"
          % (x0, x1, x1-x0+1, y0, y1, y1-y0+1, n))
else:
    print("  cursor bbox: none found in window")

# find menu text block (bright pixels, lower-right quadrant where menu sits)
mb = bbox(d, W, C, 1050, 700, 1550, 1120)
if mb:
    x0, x1, y0, y1, n = mb
    print("  MENU text bbox: x=%d..%d (w=%d)  y=%d..%d (h=%d)  white=%d"
          % (x0, x1, x1-x0+1, y0, y1, y1-y0+1, n))
