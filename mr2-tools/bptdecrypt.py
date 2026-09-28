# Session 4 (Claude): decrypt Delphine .BPT script files.
# Format: repeated [u32 len][len bytes]; each string XORed with a Park-Miller (16807, 2^31-1)
# keystream on PRNG stream 6, low byte of each output. Stream is reseeded when the file is
# opened (0x436E42 / 0x436F51 in Moto.exe): 0x13364964 or 0x39481532 depending on the name.
import sys, struct

class PM:
    def __init__(self, seed): self.s = seed & 0xFFFFFFFF
    def next(self):                                  # mirrors 0x4A89EE exactly (32-bit signed)
        s = self.s - (1 << 32) if self.s & 0x80000000 else self.s
        hi = (s >> 16) * 16807
        lo = (s & 0xFFFF) * 16807
        x = (lo + ((hi & 0x7FFF) << 16) + (hi >> 15)) & 0xFFFFFFFF
        if x & 0x80000000: x = (x - 0x7FFFFFFF) & 0xFFFFFFFF
        self.s = x
        return x & 0x7FFF if x > 0x7FFF else x

def decrypt(data, seed):
    """Yield ('s', bytes) for strings ([u32 plain len][enc bytes]) and ('n', int) for numbers
    ([4 enc bytes]). A raw u32 < 0x400 can only be a string length (encrypted data is random)."""
    pm, i = PM(seed), 0
    while i + 4 <= len(data):
        n = struct.unpack_from("<I", data, i)[0]
        if n < 0x400 and i + 4 + n <= len(data):
            yield "s", bytes(b ^ (pm.next() & 0xFF) for b in data[i+4:i+4+n]); i += 4 + n
        else:
            v = bytes(b ^ (pm.next() & 0xFF) for b in data[i:i+4]); i += 4
            yield "n", struct.unpack("<i", v)[0]

if __name__ == "__main__":
    seed = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x39481532
    for k, v in decrypt(open(sys.argv[1], "rb").read(), seed):
        print(("  %s" % repr(v.rstrip(b"\0"))[2:-1]) if k == "s" else "# %d" % v)
