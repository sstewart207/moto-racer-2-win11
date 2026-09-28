# SESSION 3 NOTES — 2026-09-27 (late)

Goal this session: **"fully decrypt the game"** — determine whether `.BPT`/`.SPT` data is
encoded, and whether that encoding is why `FileMoto`/`MotoCarac` come back as garbage.

**Headline result: the "no decrypt step" finding is CONFIRMED, but that conclusion was
reached via a script whose function boundaries are unreliable. Details below.**

---

## 1. `0x414540` — disassembled for real, confirmed a no-op

```
0x414540  sub  esp, 0x10
          push ebx
          push ebp
          push esi
          mov  esi, [esp+0x1C]        ; arg1 = buf
          mov  eax, [esp+0x24]        ; arg3 = len
          test eax, eax
          jz   0x414613               ; <-- len==0 jumps straight to epilogue
          ...byte-copy loop...
0x414613  mov  eax, [esp+0x20]        ; arg2
          test eax, eax
          jz   0x41455f               ; <-- arg2==0 -> return, buffer untouched
```

Called from `ReadString` as `0x414540(buf, 0, len)` → **returns immediately without
touching `buf`.** Not a decryptor, not a decompressor. This is solid.

## 2. ⚠️ CORRECTION — xref18.py / xref19.py produce UNRELIABLE function addresses

Hand-traced `0x437388` to check:

| script says | actual |
|---|---|
| `0x43746a` starts `fopen_wrapper` | that address is `add [ebp+0xC], eax` — **mid-function** |
| `0x43744c` starts `fread_wrapper` | mid-function |
| `0x4373d1` starts `fseek_wrapper` | mid-function |

The script *self-contradicts*: it reported `0x437388` as an entry, then also printed
"fall-through → `0x4373d1`" and "fall-through → `0x43744c`" — i.e. it printed function
starts and their fall-throughs as separate functions.

**Root cause:** `find_func()` accepts an address if
`byte0 ∈ {0x53,0x55,0x56,0x57,0x81,0x83,0x8B,0xB8,0xB9,0xBA,0xE8,0xE9}` **AND**
`byte0+2 ∈ {0xEC,0xE4}` (i.e. `push ebp` / `sub esp,imm8` shape). `.text` is full of
inline data, jump tables and random constants that satisfy this by luck.

**What this means for all prior findings:**
- ✅ **Call sites are reliable** — they're found by scanning for the `E8 rel32` opcode and
  resolving the target. `0x444768`, `0x44036E`, `0x44048D`, `0x4402FA` etc. are real.
- ✅ **The `0x444768 → 0x440181` chain is real** — `0x444768` is `56` (`push esi`) followed
  by `E8` (`call 0x440181`), a genuine call.
- ❌ **Any address obtained by following `find_func()` must be re-verified by hand.**
  This affects `0x4373d1`, `0x43744c`, `0x43746a`, `0x4374a7`, `0x4374d8`, and by the same
  heuristic also `0x4273d4`, `0x436C46`, `0x437012`.

**Before trusting any boundary again:** dump 16 bytes at `addr-16` and confirm a real
prologue (`55 8B EC`, `53 56 57`, `83 EC xx`) rather than a lucky match.

## 3. ✅ Solid — the two bare-global callers really are FileMoto and MotoCarac

Byte-level check of the *call sites themselves* (reliable, opcode-scanned):

```
0x44036E   8B 74 24 60      mov  esi, [esp+0x60]
           FF 76 0C         push dword ptr [esi+0xC]     <- object field (stored string)
           ...
0x44048D   8B 77 10         mov  esi, [edi+0x10]
           56               push esi                     <- object field (stored string)
```

vs. every other caller:

```
0x4402FA   FF 35 E8 A9 4F 00 push dword ptr [0x4FA9E8]   <- string-table constant
```

`0x4FA9E8` sits in the string table and holds `"%sLevel.Spt"` (confirmed by byte scan).
So **all other callers push a format-string from the string table → their filename always
contains `.Spt`. The two suspects push an object field → extensionless name → `.BPT` is
appended by the normaliser.** The failing name has no extension, so it *must* be one of
these two. This deduction does not depend on `find_func()` and is **safe**.

## 4. ❌ Refuted this session

- **"The game reads `Data\Carac.Spt` and gets garbage."** — `Data\Carac.Spt` is 5,489
  bytes of *readable config text*. Also `Data\Config.Spt` 5,410 B, `Data\Cross.Spt`
  3,731 B. All plaintext, all openable. Not the problem.

  > **[Claude, session 4] CORRECTION:** this is wrong. There are **zero `.SPT` files** under
  > `C:\Games\Moto Racer 2` (checked with `find -iname '*.spt'` and `findscript.py`).
  > The Carac/Config/Cross `.Spt` sizes above don't correspond to any file on disk. `findscript.py`
  > (install dir only) found `FileMoto`/`MotoCarac`/`FileLand` **only in `Moto.exe` and its backups** —
  > none of the `.BPT` files contain them in plaintext.

## 5. Hypothesis ranking (updated)

| # | Hypothesis | state |
|---|---|---|
| H1 | The object holding `FileMoto`/`MotoCarac` was populated by a script that **failed to load**, leaving stale/uninitialised buffer contents | **most likely** |
| H2 | `Get()`/`GetString()` reads from the **wrong object or wrong offset** (parser state corruption) | plausible |
| H3 | The value is **encoded somewhere in the write path** at `0x4381F0` / `0x438E7D` | unlikely — `0x414540` is a no-op and `strncpy`/`sprintf` are plain |
| H4 | The `.SPT` scripts themselves are encrypted | **test pending** (see §6) |

## 6. ⏳ DECISIVE TEST — written but NOT yet run

`C:\Games\mr2-tools\findscript.py`

Scans `C:\Games\Moto Racer 2` **and** `D:\` for the literal byte keys
`FileMoto`, `MotoCarac`, `FileLand`, `theme.spt`, `Level.Spt`, and separately dumps
entropy + first 48 bytes of **every** `.SPT` on disk.

```powershell
& C:\Python314\python.exe C:\Games\mr2-tools\findscript.py
```

**How to read the result:**
- Keys found **plaintext** in a `.SPT` → scripts are unencoded → **H4 dead**, chase H1/H2
  (which file *should* hold `FileMoto` vs. which file is actually opened).
- Keys found **nowhere** → scripts **are** encoded → you now have a concrete cipher to
  crack, and "fully decrypt the game" becomes a real, scoped task.
- `.SPT` entropy ≈ 4.0–5.0 → plaintext. Entropy ≈ 7.5–8.0 → encoded/compressed.

*(The first run was interrupted at ~10 min — D:\ is a UDF mount and slow. If it hangs,
drop `"D:\\"` from `ROOTS` and run only the installed copy.)*

## 7. Open side quests

- **`config.bin`**: 40,731 bytes (= 4 + `0x9F17`), entropy 7.996, first dword
  `f6 9c e4 4f` ≠ `0x9F17`. Either whole-file encrypted (no decoder found) or the
  header layout is misread. **Deprioritised — it regenerates on clean exit.**
- **`DirectDraw error 0x88760096`** + `INCORRECT VRAM PARAMETERS!` — not started.
- **2560x1440 high-refresh plan** — not started. See `CLAUDE.md`.
