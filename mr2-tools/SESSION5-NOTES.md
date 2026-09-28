# SESSION 5 NOTES — 2026-09-27 (MiMo-V2.6-Flash Free, OpenCode)

> **Model:** `mimo-v2.6-flash-free`, provider `opencode`.
> **Handoff target:** Claude, returning ~13:00. **Read `CLAUDE.md` first**, then
> `GRAPHICS-PLAN.md` (this session's deliverable), then `FINDINGS.md` (session 4).

## TL;DR

1. **Session 4's graphics attempt failed because it set `ini D3D=true`.** The proven
   working value is **`D3D=false`**. With `D3D=false` + dgVoodoo DLLs + `VRAM=256`,
   the **very first launch succeeded** and reached the menu.
2. **The deliverable is done:** `C:\Games\GRAPHICS-PLAN.md` — fullscreen 2560×1440
   @ **144 Hz**, measured **144.0 fps**, 7.2 ms latency, no tearing.
3. Display maxes at **144 Hz**, not the ~170 Hz session 4 estimated.
4. `ImageScaleFactor = 3` is a **real, verified improvement** (640×3 = 1920, 480×3 = 1440 —
   an exact integer fit into the pillarbox).
5. **DualSense is still the main untouched item.**
6. **"No sound" bug — found and fixed.** The game's Windows audio session was running
   at **`vol=0%`** while *active* and *unmuted* on the correct device. Root cause:
   **`-NoSound` persists `volume = 0` into `config.bin`**, so every later launch started
   muted **even without the flag** — i.e. the old Rule 2 was the cause of the bug, not
   the cure. Fixed by restoring `mr2-state-backup\config.bin.bak` (`735E…`); a fresh
   launch now reports `vol=100% unmuted`. **New tool: `audiocheck.ps1`.**

## What I ran

| test | result |
|---|---|
| GOG + dgVoodoo + `VRAM=256` + `D3D=false` | ✅ PASS — first working GOG launch |
| Fullscreen A/B: baseline vs `refrate:144` + `EnumerateRefreshRates` | ⚠️ **no difference** — both hold 144 Hz |
| `ImageScaleFactor` 1 vs 3, with a **static-region control** | ✅ **ISF=3 is real** (control 0% diff vs 53.6% diff) |
| PresentMon 2.6.0, 8 s, menu, 1151 frames | ✅ **144.0 fps median**, 6.945 ms, 7.244 ms latency |
| Final validation (config frozen) | ✅ 20/20 samples at 2560×1440 @ 144 Hz, no fatal error |
| Core Audio probe: default endpoint, session state, session volume | ❌→✅ `moto` = `ACTIVE vol=0%` → **`ACTIVE vol=100%`** after `config.bin` restore |
| `config.bin` A/B across 3 saved versions (byte diff, `cfgdiff.py`) | ✅ isolates the mute: `735E…`(original)→100%, `6DAD…`(post-`-NoSound`)→0% |
| `sfx.bkf` inventory (`bkflist.py`) | ⚠️ 140 WAVs present, but **`Speed\Gear2/3/4/6.wav` genuinely absent** (4 gear SFX only) |

## Corrections I made to earlier notes

| claim | source | reality |
|---|---|---|
| *"every GOG launch failed, with AND without dgVoodoo"* | session 4 | session 4 had **`D3D=true`**; `D3D=false` works first try |
| display runs *~170 Hz* | session 4 | **144 Hz max** is what Windows enumerates |
| `refrate:144` + `EnumerateRefreshRates` deliver high refresh | my own first hypothesis | ❌ **A/B says no** — dgVoodoo's D3D11 output is borderless at desktop mode; the panel stays at its desktop refresh either way. **Kept in config for defensiveness only — do not credit them.** |
| `INCORRECT VRAM PARAMETERS!` = a problem to fix | session 3 | it is a **harmless warning**; the working install prints it too. Only *negative* VRAM is fatal |

## Honest open items

1. **Race-load FPS is unmeasured.** The 144 Hz lock is proven on the *menu* only.
   Needs a human at START → LOCAL. Repro: `GRAPHICS-PLAN.md` §8.
2. **`refrate:144` / `EnumerateRefreshRates` are unproven no-ops** in the current
   setup. Re-test only if the display ever drops to 60 Hz.
3. **`ImageScaleFactor=3` with a non-640×480 game resolution is unverified.** ×3 is
   exact only for 640×480; other modes will fall back to a non-integer rescale.
4. **`GRAPHICS-PLAN.md` §6 tuning table is entirely untested** — ScalingMode variants,
   filtering, AA, G-Sync.
5. **DualSense** — untouched.
6. **Reference disc install** `C:\Games\Moto Racer 2\Moto.exe` still carries session 4's
   diagnostic patch (clean: `Moto.exe.pre-callerpatch.bak`).

## Files I added

`GRAPHICS-PLAN.md`, `CLAUDE.md` (rewritten header/status/corrections), and in `mr2-tools\`:
`dispinfo.py`, `refreshpoll.py`, `PresentMon.exe`, `fps-menu.csv`, `fpsreport.py`,
`pngdiff.py`, `cropdiff.py`, `cropzoom.py`, plus screenshots
(`gog-final-fullscreen.png`, `gog-imgscale3.png`, `cmp-ISF1.png`, `cmp-ISF3.png`,
`gog-VALIDATED.png`).

**Late additions (the sound fix):** `audiocheck.ps1` (Core Audio probe — endpoint,
per-process session state/volume, `-SetVol`), `cfgdiff.py` (byte-diffs `config.bin`
versions to isolate a setting change), `bkflist.py` (lists `.BKF` archive contents).

Backups: `mr2-state-backup\gog-original2\` (GOG `motoracer2.ini`, `delphine.err`),
`mr2-state-backup\dgVoodoo.optimized.bak`, and **`config.bin` ×3** —
`config.bin.bak` (`735E…` original, volume normal ✅), `config.bin.version1` (`E28E…`,
session 4), `config.bin.session5-live.bak` (`6DAD…`, the muted one ❌).

Desktop shortcut: **`Moto Racer 2 (1440p 144Hz).lnk`** (`-skipintro -DontLimitFrameRate`).

> **Rule 2 (always launch muted with `-NoSound`) was REVOKED by the user on 2026-09-27.**
> **It was also the direct cause of the "no sound" bug** — `-NoSound` is not side-effect
> free: the game writes its settings back on a clean exit, and repeated `-NoSound` runs
> left `config.bin` holding `volume = 0`, muting every subsequent launch. Restoring
> `mr2-state-backup\config.bin.bak` fixed it. Full write-up: **CLAUDE.md Rule 5**.
> Launch **with sound** by default; if you must use `-NoSound`, restore `config.bin`
> afterwards. (The rule slot is kept so "Rule 4" still points at the xref defect.)

### Diagnosing audio (the method, for next time)

Do **not** guess — the failure was invisible to every file-level check:

- System master volume was fine (**100%**, unmuted), `DirectSound` enumerated both
  devices fine, all music/`sfx.bkf` files were present, and the log showed **no** fatal
  audio error. Every one of those said "should work."
- The only thing that betrayed it was the **OS session level**: the game had a
  `state=1 (ACTIVE)` session at `vol=0%` — rendering audio nobody could hear.
- Tool: `mr2-tools\audiocheck.ps1 -Proc moto` (read) / `-SetVol 100` (one-shot, does
  not persist). It reports the default endpoint per role, and per-process session
  state + volume.
- `SetVol` alone is **not** a fix — a fresh launch reverts to whatever `config.bin`
  holds. Restore `config.bin` for durability.

⚠️ Known-but-minor: the game requests `data\sfx\Speed\Gear2/3/4/6.wav`, which are **not**
in `sfx.bkf` (only `Speed\Gear1` and `Speed\Gear5` exist). 4 missing gear-shift effects —
unrelated to the mute, pre-existing, not worth chasing.

## Method note worth keeping

The menu **animates**, so naive screenshot diffs were misleading (20–53% differences with
no config change at all). The fix was a **control: two screenshots under identical config**
to establish that a given region is static (`cropdiff.py`, logo region → `0.0000%`), then
comparing configs against *that*. **Always run a control before trusting a pixel diff.**
