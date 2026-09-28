import struct, zlib, sys
from pathlib import Path


def read_png(path):
    data = Path(path).read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a png"
    pos = 8
    idat = b""
    w = h = bitdepth = colortype = None
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, bitdepth, colortype = struct.unpack(">IIBB", chunk[:10])
        elif typ == b"IDAT":
            idat += chunk
        elif typ == b"IEND":
            break
        pos += 12 + ln
    raw = zlib.decompress(idat)
    ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[colortype]
    stride = w * ch
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]; p += 1
        line = bytearray(raw[p:p + stride]); p += stride
        if f == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i - ch]) & 0xFF
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                b = prev[i]
                c = prev[i - ch] if i >= ch else 0
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, ch, bytes(out)


if __name__ == "__main__":
    a_path, b_path = sys.argv[1], sys.argv[2]
    print("A:", a_path)
    print("B:", b_path)
    w1, h1, c1, d1 = read_png(a_path)
    w2, h2, c2, d2 = read_png(b_path)
    print("A: %dx%d ch=%d   B: %dx%d ch=%d" % (w1, h1, c1, w2, h2, c2))
    if (w1, h1, c1) != (w2, h2, c2):
        print("dimensions/channels differ -> cannot diff directly")
        sys.exit()

    n = len(d1)
    identical = d1 == d2
    print("byte-identical:", identical)
    if not identical:
        diff = 0
        total = 0
        maxd = 0
        step = c1
        for i in range(0, n, step):
            for k in range(min(3, c1)):
                a = d1[i + k]
                b = d2[i + k]
                total += 1
                d = abs(a - b)
                if d:
                    diff += 1
                    if d > maxd:
                        maxd = d
        print("RGB samples differing: %d / %d  (%.3f%%)" % (diff, total, 100.0 * diff / total))
        print("max channel delta: %d" % maxd)
