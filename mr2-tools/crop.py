import sys, struct, zlib
sys.path.insert(0, r"C:\Games\mr2-tools")
from pngdiff import read_png


def write_png(path, w, h, ch, rgb):
    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    ct = 2 if ch == 3 else 6
    raw = bytearray()
    stride = w * ch
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, ct, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    open(path, "wb").write(png)


src, dst = sys.argv[1], sys.argv[2]
x, y, w, h = (int(v) for v in sys.argv[3:7])
scale = int(sys.argv[7]) if len(sys.argv) > 7 else 4

W, H, C, data = read_png(src)
print("source %dx%d c=%d" % (W, H, C))

if C >= 4:
    rgb = bytearray(w * h * 3)
    for yy in range(h):
        for xx in range(w):
            si = ((y + yy) * W + (x + xx)) * C
            di = (yy * w + xx) * 3
            rgb[di:di + 3] = data[si:si + 3]
else:
    rgb = bytearray()
    stride = W * C
    for yy in range(h):
        rgb += data[(y + yy) * stride + x * C:(y + yy) * stride + (x + w) * C]

print("cropped (%d,%d %dx%d)" % (x, y, w, h))

ow, oh = w * scale, h * scale
out = bytearray(ow * oh * 3)
for yy in range(oh):
    sy = yy // scale
    for xx in range(ow):
        sx = xx // scale
        si = (sy * w + sx) * 3
        di = (yy * ow + xx) * 3
        out[di:di + 3] = rgb[si:si + 3]
write_png(dst, ow, oh, 3, bytes(out))
print("wrote %s  %dx%d" % (dst, ow, oh))

xs, ys = [], []
for yy in range(h):
    for xx in range(w):
        si = (yy * w + xx) * 3
        r, g, b = rgb[si], rgb[si + 1], rgb[si + 2]
        if r > 235 and g > 235 and b > 235:
            xs.append(xx); ys.append(yy)
if xs:
    print("  white-pixel bbox: x=%d..%d (w=%d)  y=%d..%d (h=%d)  n=%d"
          % (min(xs), max(xs), max(xs) - min(xs) + 1,
             min(ys), max(ys), max(ys) - min(ys) + 1, len(xs)))
else:
    print("  no near-white pixels in crop")
