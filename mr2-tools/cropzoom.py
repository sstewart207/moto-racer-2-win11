import sys, struct, zlib

sys.path.insert(0, r"C:\Games\mr2-tools")
from pngdiff import read_png


def write_png(path, w, h, ch, rgb):
    """rgb: bytes, 3 channels per pixel"""
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
    print("wrote %s  %dx%d" % (path, w, h))


src, dst = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = (int(v) for v in sys.argv[3:7])
zoom = int(sys.argv[7]) if len(sys.argv) > 7 else 1

w, h, c, data = read_png(src)
cw, ch_ = x1 - x0, y1 - y0
ow, oh = cw * zoom, ch_ * zoom
out = bytearray(ow * oh * 3)
for oy in range(oh):
    sy = y0 + oy // zoom
    for ox in range(ow):
        sx = x0 + ox // zoom
        i = (sy * w + sx) * c
        o = (oy * ow + ox) * 3
        out[o] = data[i]
        out[o + 1] = data[i + 1]
        out[o + 2] = data[i + 2]
write_png(dst, ow, oh, 3, bytes(out))
