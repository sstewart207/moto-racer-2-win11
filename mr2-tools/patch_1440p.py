#!/usr/bin/env python3
"""
patch_1440p.py - Patches Moto Racer 2 (moto.exe) DirectDraw mode enumeration
to support modern display resolutions up to 4K (e.g., 2560x1440 @ 144Hz).

Disassembly at VA 0x41A8C5 (Cdd::enumVideoModes callback):
  0x41A912: 81 78 0C 00 04 00 00  (cmp dword ptr [eax+0xC], 1024)
  0x41A91F: 81 78 08 00 03 00 00  (cmp dword ptr [eax+0x8], 768)

Replaces 0x400 (1024) and 0x300 (768) with 0x1000 (4096).
Resulting Patched MD5: 302EFC8762F80E1CDCD4D1553190159B
"""

import sys
import os
import hashlib

TARGET_DIR = r"C:\GOG Games\Moto Racer 2"
TARGET_EXE = os.path.join(TARGET_DIR, "moto.exe")
ORIG_EXE   = os.path.join(TARGET_DIR, "moto.exe.orig")

GOG_MD5     = "598D3899056340EBCE7EBFC0183F15E0"
PATCHED_MD5 = "302EFC8762F80E1CDCD4D1553190159B"

def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def patch_file(exe_path):
    if not os.path.exists(exe_path):
        print(f"Error: {exe_path} not found.")
        sys.exit(1)
        
    current_hash = md5(exe_path)
    print(f"Target: {exe_path}")
    print(f"Current MD5: {current_hash}")
    
    if current_hash == PATCHED_MD5:
        print("Binary is already patched for 1440p/4K!")
        return

    with open(exe_path, "rb") as f:
        data = bytearray(f.read())

    # Signatures
    sig1 = bytes.fromhex("81 78 0C 00 04 00 00 0F 87 DF 00 00 00 81 78 08 00 03 00 00")
    rep1 = bytes.fromhex("81 78 0C 00 10 00 00 0F 87 DF 00 00 00 81 78 08 00 10 00 00")

    pos = data.find(sig1)
    if pos == -1:
        print("Error: Could not find DirectDraw mode filter signature in binary.")
        sys.exit(1)

    print(f"Found signature at file offset 0x{pos:X}. Applying patch...")
    data[pos:pos+len(rep1)] = rep1

    # Save backup if not already present
    backup_path = exe_path + ".orig"
    if not os.path.exists(backup_path):
        with open(backup_path, "wb") as bf:
            with open(exe_path, "rb") as orig_f:
                bf.write(orig_f.read())
        print(f"Backup saved to: {backup_path}")

    # Write patched binary
    with open(exe_path, "wb") as f:
        f.write(data)

    new_hash = md5(exe_path)
    print(f"Patched successfully! New MD5: {new_hash}")
    if new_hash == PATCHED_MD5:
        print("MD5 matches verified build 302EFC8762F8.")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else TARGET_EXE
    patch_file(target)
