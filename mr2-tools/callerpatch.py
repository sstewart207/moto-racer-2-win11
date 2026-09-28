# Session 4 (Claude): instrument Moto.exe so the "Cannot open file" dialog shows
# which caller of Load (0x437012) triggered it, plus FileMoto / FileLand / MotoCarac[0..1].
# Always patches from the clean backup. Restore: copy Moto.exe.pre-callerpatch.bak over Moto.exe.
import struct, hashlib
EXE = r"C:\Games\Moto Racer 2\Moto.exe"
CLEAN = EXE + ".pre-callerpatch.bak"  # md5 c54012b4044a...
BASE = 0x400000                      # .text: VA 0x401000 <-> file 0x1000, so off = va - BASE
GLOBAL = 0x90EFF0                    # tail of .data's bss page (VirtualSize ends 0x90EA54, page to 0x90F000)
CAVE1, CAVE2, FMT = 0x4E1980, 0x4E19A0, 0x4E19E0   # zero padding at end of .text (0x4E1972..0x4E2000)

def rel(src, dst): return struct.pack("<i", dst - (src + 5))

d = bytearray(open(CLEAN, "rb").read())
assert hashlib.md5(d).hexdigest().startswith("c54012b4044a")
def put(va, b, expect=None):
    o = va - BASE
    if expect is not None: assert d[o:o+len(expect)] == expect, (hex(va), d[o:o+len(expect)].hex())
    d[o:o+len(b)] = b

# Hook Load wrapper: 0x437012 ff742408 | 0x437016 6a01 -> jmp cave1 (the jmp also eats the 6a of push 1)
put(0x437012, b"\xE9" + rel(0x437012, CAVE1), bytes.fromhex("ff7424086a"))
c1  = b"\x8B\x04\x24"                       # mov eax,[esp]        ; return addr = call site
c1 += b"\xA3" + struct.pack("<I", GLOBAL)   # mov [GLOBAL],eax
c1 += b"\xFF\x74\x24\x08"                   # push [esp+8]         ; replay
c1 += b"\x6A\x01"                           # push 1               ; replay
c1 += b"\xE9" + rel(CAVE1 + len(c1), 0x437018)
assert CAVE1 + len(c1) <= CAVE2
put(CAVE1, c1, bytes(len(c1)))

# Error site: 0x427217 push ebx; push 0x4f8cc0; call 0x426873; pop ecx; pop ecx  (13 bytes)
put(0x427217, b"\xE9" + rel(0x427217, CAVE2) + b"\x90" * 8,
    bytes.fromhex("5368c08c4f00e851f6ffff5959"))
c2 = b""
for g in (0x657BFC, 0x657BBC, 0x655578, 0x6555B8):  # MotoCarac[1], MotoCarac[0], FileLand, FileMoto
    c2 += b"\x68" + struct.pack("<I", g)       # push offset g
c2 += b"\xFF\x35" + struct.pack("<I", GLOBAL)  # push [GLOBAL]   (Load caller)
c2 += b"\x53"                                  # push ebx        (filename)
c2 += b"\x68" + struct.pack("<I", FMT)         # push fmt
c2 += b"\xE8" + rel(CAVE2 + len(c2), 0x426873) # call dialog (vsprintf-style)
c2 += b"\x83\xC4\x1C"                          # add esp,0x1C
c2 += b"\xE9" + rel(CAVE2 + len(c2), 0x427224) # jmp back (retry loop)
assert CAVE2 + len(c2) <= FMT
put(CAVE2, c2, bytes(len(c2)))
fmt = (b"Cannot open file %s !\nLoad caller ret=%08X\nFileMoto=[%s]\nFileLand=[%s]\n"
       b"MotoCarac0=[%s]\nMotoCarac1=[%s]\nPlease insert CDROM in drive.\x00")
assert FMT + len(fmt) <= 0x4E2000
put(FMT, fmt, bytes(len(fmt)))

# CD check (0x408650) does _strnicmp(volumeLabel, "motorace", 8). The mounted disc image is
# labelled "Moto_Racer_2", so accept that label instead (the disc is still required).
put(0x4ED4A0, b"moto_rac", b"motorace")

# CD getStatus (0x4087B5) queries MCI cdaudio mode. The disc image has no audio tracks, so the
# drive always reports 0x20C (not ready) and the menu shows "PLEASE, INSERT YOUR CDROM".
# Report 0x20D (MCI_MODE_STOP = disc present, idle) instead: mov eax,0x20D; ret
put(0x4087B5, b"\xB8\x0D\x02\x00\x00\xC3", bytes.fromhex("558bec83ec10"))

# CD-audio TOC protection ("Illegal TOC"): 0x42870C reads every audio track length via
# getTrackLen (0x408921, MCI_STATUS_LENGTH in MSF) and seeds the PRNG with them; wrong
# lengths silently corrupt later .BPT reads (the garbage MotoCarac filename). The exe holds
# the expected MSF per track at 0x414A1F(track) (two tables, picked by registry Version).
# Make getTrackLen(track, &out) return exactly that:
#   mov eax,[esp+4]; push eax; call 0x414A1F; mov ecx,[esp+8]; mov [ecx],eax; xor eax,eax; ret 8
g  = b"\x8B\x44\x24\x04\x50"
g += b"\xE8" + rel(0x408921 + len(g), 0x414A1F)
g += b"\x8B\x4C\x24\x08\x89\x01\x33\xC0\xC2\x08\x00"
put(0x408921, g, bytes.fromhex("558bec83ec1c5356"))  # checks the first 8 original bytes; rest becomes dead code

# Edition flag [0x6594D0] is read from registry value "Version" (0x485EB5). Version=1 makes
# non-theme .BPT files (MOTOSPD, CARAC...) use seed 0x13364964, but this disc's files are all
# encrypted with 0x39481532 (the Version=0 edition), and Version also picks the TOC table.
# The value must exist (else "PROGRAM INCORRECTLY INSTALLED"), so keep the read but store it
# in a spare bss dword: push 0x6594D0 -> push GLOBAL+4. The flag keeps its .bss default of 0.
put(0x485EB5, b"\x68" + struct.pack("<I", GLOBAL + 4), b"\x68\xD0\x94\x65\x00")

open(EXE, "wb").write(d)
print("patched, md5", hashlib.md5(d).hexdigest())
