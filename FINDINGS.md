# Moto Racer 2 on Windows 11: findings (session 4, Claude Opus 5.5, 2026-09-27)

For any future Claude session. Details and addresses: `mr2-tools/SESSION4-NOTES.md`.
Earlier sessions 1–3 were by MiMo-V2.6-Flash (OpenCode). Their notes contain errors, corrected below.

## Disc version and its copy protection (SOLVED: disc install at `C:\Games\Moto Racer 2\` plays races)
1. **`.BPT` files ARE encrypted.** Each value is XORed with a Park–Miller keystream (`16807*s mod 2^31-1`, PRNG
   stream 6, state table `0x5476C8`), reseeded on every file open. `mr2-tools/bptdecrypt.py` decrypts them.
   String = `[u32 plain len][enc bytes]`, number = `[4 enc bytes]`.
2. **The garbage `.BPT` filename was Delphine's CD-audio "Illegal TOC" protection** (redump disc 6068). `0x42870C`
   reads the lengths of audio tracks 2–15 via `getTrackLen` (`0x408921`, MCI, MSF) and seeds the PRNG with them.
   A data-only image has no audio tracks, so bike data (`MotoCarac`) decrypts to garbage. No error is shown.
3. The exe stores the **expected track lengths** at `0x414A1F(track)`, two tables, one per edition.
   Patch: `getTrackLen` returns that table value.
4. Registry `Version` → edition flag `[0x6594D0]`. `Version=1` uses seed `0x13364964` for non-theme files. This disc's
   files all use `0x39481532` (the Version=0 scheme). The value must still exist (else "PROGRAM INCORRECTLY
   INSTALLED"), so the read at `0x485EB5` is redirected to a spare dword. The flag stays 0.
5. Menu CD check: `_strnicmp(label, "motorace", 8)`, but the image label is `Moto_Racer_2`, so the string is
   patched to `moto_rac`. The MCI status query (`0x4087B5`) never reports ready on an image, so it's patched to
   return "stopped".
6. The hidden check opens `D:\data\moto.ex_` (name obfuscated with stream 1, seed `0x1A3D5E7F`). The file is present.
7. All patches: `mr2-tools/callerpatch.py`. Clean exe: `Moto.exe.pre-callerpatch.bak`.
   Live memory reads via ctypes: `mr2-tools/memsnap.py`.

### MiMo errors (corrected inline in its notes)
- `0x414540` is an XOR decrypt (`arg2==0` = in place), not a no-op.
- No `.SPT` files exist. The claimed `Data\Carac.Spt` etc. were never on disk.
- `0x44048D` is `push 1; push edi`, not `mov esi,[edi+0x10]`.
- Its patch recipe had an off-by-one: a 5-byte jmp at `0x437012` eats `push 1`, so return to `0x437018`.
- `-noprotection` → "BLAIREAU !" (French for badger/idiot). Never use it.

## GOG version (PROJECT TARGET NOW: `C:\GOG Games\Moto Racer 2\`)
8. Soundtrack included: `02.wav`–`15.wav` + GOG `winmm.dll` (CD audio → wav). Music is solved.
   Launcher `MotoRacer2.exe` runs `moto.exe` (md5 `598D38990563`) with `motoracer2.ini` `Params` (+ ` -D3D` if `D3D=true`).
9. The user's launch through `MotoRacer2.exe` works. **Starting `moto.exe` directly fails with "Cannot initialise
   screen mode"**, with or without dgVoodoo, D3D or not, windowed or not. Without dgVoodoo the log shows negative VRAM
   (`Txt:-14811136 Primary:-1073741824`): a 32-bit overflow on the RTX's large VRAM. Cause of the difference unknown.
10. The GOG install repointed HKLM `DelphineSoft\MotoRacer2\...\Moto` (`DataPath`/`SavingPath` = GOG folder,
    `Version=1`) and registered AppCompat `moto.exe = DWM8And16BitMitigation HIGHDPIAWARE`.
11. The GOG folder is in its original state. Tuned dgVoodoo files are parked in `mr2-state-backup\gog-dgv-parked\`.

## Still open
- Fullscreen 2560x1440 at high refresh (monitor MSI G274QPF E2, ~170 Hz): reproduce the user's working launch, then
  add dgVoodoo one change at a time. `refrate:170` and `OutputAPI` changes are untested on their own.
- DualSense: the game uses DirectInput. Try in-game OPTIONS first, then Steam Input or DS4Windows.

## Rules
Launch with **sound** — ~~launch muted (`-NoSound`): the user watches movies on this machine~~
**[Rule REVOKED by the user, 2026-09-27 — `-NoSound` is now optional only, not a default.]**
Back up before patching.
