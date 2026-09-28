# SESSION 4 NOTES — 2026-09-27 (Claude, Opus 5.5)

## TL;DR
1. **`.BPT` files ARE encrypted.** MiMo's §14.1 disassembly of `0x414540` was wrong. It is an
   XOR stream cipher, and `arg2 == 0` means *decrypt in place*, not "return".
   `mr2-tools/bptdecrypt.py` now decrypts every `.BPT` fully.
2. **The failing load is `MotoCarac`, proven at runtime:** the patched exe reported
   `Load caller ret=0x00440492` (call site `0x44048D`).
3. The source data is fine: every `LEVEL.BPT` / `MOTOSPD.BPT` / `MOTOKTM.BPT` decrypts to sane
   values. So the garbage is produced **at runtime**, not by bad files.

## Corrections to MiMo's notes
| MiMo claim | actual (verified by disassembly) |
|---|---|
| §14.1 `0x414540` starts `sub esp,0x10`; `arg2==0` → return | starts `push ebx; push esi`. `(buf, dst, len)`: if `dst==0`, XOR `buf` in place with `rand6() & 0xFF` per byte; else write to `dst` |
| §14.4 `Data\Carac.Spt` 5,489 B plaintext exists | **no `.SPT` file exists anywhere** in the install |
| §14.3 `0x44048D` = `mov esi,[edi+0x10]; push esi` | `push 1; push edi` with `edi = 0x657BBC` (slot loop, `edi += 0x40` up to `0x657DBC`) |
| CLAUDE.md patch recipe: replay `FF 74 24 08`, `jmp 0x437016` | a 5-byte jmp at `0x437012` eats the `6A` of `push 1` → replay `push [esp+8]; push 1`, `jmp 0x437018` |
| §13.3 "no decrypt step on read" | there is one on every string **and** every number read |

## Cipher
- PRNG `0x4A89EE(stream)`: Park–Miller minimal standard, `s = 16807*s mod (2^31-1)`,
  per-stream state at `0x5476C8 + 4*stream`. Output `s` (masked `&0x7FFF` if larger); key byte = `s & 0xFF`.
- `.BPT` uses **stream 6**. Reseeded on every `.BPT` open inside `0x436C46` (`0x436E42` / `0x436F51`):
  `0x39481532` (works for LEVEL/MOTOSPD/MOTOKTM) or `0x13364964`, depending on the name.
  The Config path seeds `0x4A6C5D7F` / `0x4B6D5E7E` (`0x488E8E`).
- Binary layout: string = `[u32 len, plaintext][len encrypted bytes]`; number = `[4 encrypted bytes]`.
  One keystream across the whole file. No keys stored: in binary mode `GetString/GetNumber` ignore
  the key name and just read the next value, so **the parser relies on reading values in exact order**.
- `MOTOKTM.BPT` decrypted: `MotoCarac` then `data\ktmcross\carac1.spt` … `carac8.spt`, then numbers.
  `MOTOSPD.BPT`: `data\speed\carac1.spt` … (21 chars, **the same length as the garbage name**).

## Garbage-name analysis (negative results, don't redo)
The garbage `48 5C C7 …` is **not** any 21-byte string from MOTOSPD/MOTOKTM/LEVEL XORed with *any*
Park–Miller state. That was an exhaustive 2^23-candidate state search per string, as ciphertext and as plaintext.
So it isn't simply "right bytes, wrong keystream position".

## Runtime patch (`mr2-tools/callerpatch.py`)
- Clean backup: `Moto Racer 2\Moto.exe.pre-callerpatch.bak` (md5 `c54012b4044a…`).
- **Current `Moto.exe` = patch v2** (md5 `cb6ec15e54d0…`). The error dialog now also prints
  `FileMoto`, `FileLand`, `MotoCarac0`, `MotoCarac1`. Cave in `.text` padding at `0x4E1980`,
  scratch global `0x90EFF0`.
- **v2 has not been observed yet.** Automated input is flaky: one Enter+click run exited the game cleanly
  (config.bin regenerated) without hitting the error. Needs a human to press START once and read the dialog.

## Next
1. Press START manually and read the v2 dialog. `FileMoto=[data\motoSpd.spt]` + `MotoCarac0=[<garbage>]`
   ⇒ the MOTO file parse is misaligned. Also note whether `MotoCarac1` is sane.
2. Then trace the parse between `Load(FileMoto)` (`0x44036E`) and the `MotoCarac` read (`0x438E5B`) for a
   read-count mismatch (e.g. a version-dependent field this exe expects but the 1998 data lacks, or vice versa).
   The XP patch exe paired with retail data is a prime suspect.

---
## UPDATE (late session 4) — PROTECTION FULLY UNDERSTOOD, ALL PATCHES IN `callerpatch.py`
Root cause of the garbage `.BPT` name = **Delphine CD-audio "Illegal TOC" protection** + edition flag.
The disc image at D: is data-only (no audio tracks 2-15), so:
1. Menu CD check: `_strnicmp(label,"motorace",8)` — image label is `Moto_Racer_2` → patched string to `moto_rac` (0x4ED4A0).
2. Menu "PLEASE INSERT YOUR CDROM": MCI getStatus (0x4087B5) always 0x20C not-ready → patched to return 0x20D (stop).
3. TOC check 0x42870C: getTrackLen (0x408921) lengths of tracks 2..15 seed PRNG stream 1. Patched getTrackLen
   to return the exe's own expected MSF table `0x414A1F(track)` (two tables, chosen by edition flag).
4. Edition flag [0x6594D0] (registry `Version`): 1 ⇒ MOTOSPD/CARAC use seed 0x13364964, but THIS disc's files
   are all seed 0x39481532 (proved: game's MotoCarac slots = MOTOSPD records decrypted at draw 521 of 0x13364964).
   Value must exist (else "PROGRAM INCORRECTLY INSTALLED"), so the read at 0x485EB5 now stores into spare
   0x90EFF4; flag stays 0. Registry untouched.
Hidden check also opens `D:\data\moto.ex_` (string obfuscated via stream-1 XOR, seed 0x1A3D5E7F) — present, passes.
Runtime memory inspection works via ctypes ReadProcessMemory: `mr2-tools/memsnap.py` (waits for error dialog).
Status at save: intro plays, main menu OK, flag=0, prot err=0. **START→LOCAL not yet confirmed.**
Also still in exe: diagnostic dialog patch (caller/FileMoto/MotoCarac) — harmless, remove later.
config.bin was moved aside to mr2-state-backup (config.bin.s4*); game regenerates it.

## NEXT
- Confirm START→LOCAL loads a race. If a new error: run memsnap.py first, then click.
- 2560x1440/high refresh: dgVoodoo.conf FPSLimit 60→0, [DirectX] Resolution=2560x1440 (or desktop),
  OutputAPI=d3d11_fl11_0; launch without -Windowed for fullscreen.
- DualSense: game uses DirectInput (DINPUT.dll). Try native in OPTIONS; else Steam Input / DS4Windows (needs ViGEmBus).
- Music: image has no CD-audio. Options: bin/cue rip + WinCDEmu, or ogg-winmm wrapper with Track02..15 files.

---
## ✅ 2026-09-27 ~21:35 — GAME WORKS (user confirmed: START → LOCAL → race plays)
Current exe = all patches from `callerpatch.py` (clean backup `Moto.exe.pre-callerpatch.bak`).
Launch used: `-skipintro -DontLimitFrameRate -NoSound -Windowed` → that's why it's a SMALL WINDOW.

## TODO NEXT PASS (user's priorities)
1. **Graphics: fullscreen 2560x1440 + high refresh.** Drop `-Windowed`. dgVoodoo.conf: FPSLimit 60→0,
   [DirectX] Resolution → 2560x1440 (or `desktop`), OutputAPI → d3d11_fl11_0, check ScalingMode (4:3 pillarbox
   vs stretch). Test -D3D vs DirectDraw path, -ZBuffer32, -TripleBuffer. Also fix DirectDraw 0x88760096 spam.
   Consider a desktop shortcut with the final flags (keep -NoSound optional; user watches movies).
2. **DualSense controls.** Game uses DirectInput. Try OPTIONS → controls natively first; fallback Steam Input
   (add Moto.exe as non-Steam game) or DS4Windows + ViGEmBus (driver install needs user OK).
3. **CD AUDIO MISSING — user wants the real soundtrack.** D: image is data-only (UDF, 296 MB); original PC disc
   has audio tracks 2–15 (redump disc 6068, "Illegal TOC", tracks 14/15 duplicate 12/13). Options:
   a) proper .bin/.cue (or .ccd) rip of the user's disc incl. audio, mount with WinCDEmu;
   b) soundtrack as Track02..Track15 files + ogg-winmm (winmm.dll wrapper that serves MCI cdaudio from files).
   Note: getTrackLen/getStatus are patched — with a real audio drive, playback via MCI still works; with ogg-winmm
   MCI calls go to the wrapper. Track→music map is data\cdTrack.txt.
4. Cleanup: remove diagnostic dialog patch; update CLAUDE.md/PROGRESS-REPORT with final state.

---
## 🎯 SWITCHED TO GOG (user, 2026-09-27 ~21:45) — `C:\GOG Games\Moto Racer 2\`
User bought/installed GOG Moto Racer 2; it runs. Use it for everything from now on.
- Launcher `MotoRacer2.exe` (+ `motoracer2.ini`), game `moto.exe` md5 598D38990563.
- Music solved: `02.wav`..`15.wav` + GOG `winmm.dll` wrapper → TODO item 3 (CD audio) is DONE.
- Remaining: (1) fullscreen 2560x1440/high refresh — copy dgVoodoo (DDraw.dll, D3DImm.dll, dgVoodoo.conf) from
  `C:\Games\Moto Racer 2\` or `C:\Games\dgVoodoo2_87_5.zip` into the GOG folder, then tune; (2) DualSense.
- Check the shared HKLM DelphineSoft key after GOG install (GOG may have rewritten DataPath/Version).

---
## GOG graphics attempt (2026-09-27 ~21:50) — UNFINISHED, GOG folder restored to original
Tried in `C:\GOG Games\Moto Racer 2\`: copied dgVoodoo (DDraw.dll, D3DImm.dll, dgVoodoo.conf) + ini D3D=true.
**Every direct launch of GOG `moto.exe` failed with "Cannot initialise screen mode"** — with AND without dgVoodoo,
D3D or not, fullscreen or `-Windowed`. So the failure is not dgVoodoo's settings.
Clue: without dgVoodoo the log shows NEGATIVE VRAM (`Txt:-14811136 Primary:-1073741824 Total:-65536`) = 32-bit
overflow from the RTX's large VRAM → screen-mode init fails. dgVoodoo (VRAM=256) should fix that, yet it also failed,
so check next: does the user's GOG launch (`MotoRacer2.exe` → Play) actually work in fullscreen right now? Compare.
Other facts: GOG set AppCompat Layers `moto.exe = DWM8And16BitMitigation HIGHDPIAWARE` (HKCU+HKLM);
GOG rewrote HKLM DelphineSoft key (DataPath/SavingPath = GOG folder, Version=1).
Restored: GOG motoracer2.ini (original backed up in mr2-state-backup\gog-original\); dgVoodoo files parked in
mr2-state-backup\gog-dgv-parked\ (my tuned conf: d3d11_fl11_0→reverted to bestavailable, FPSLimit 0,
[DirectX] Resolution max_isf (refrate:170 broke it? untested alone), Filtering 16, VSync on).
Next: 1) reproduce user's working launch path; 2) re-add dgVoodoo one change at a time; 3) DualSense.
