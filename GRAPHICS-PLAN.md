# Moto Racer 2 — 2560×1440 high-refresh graphics plan

> **Status: ✅ DELIVERED and measured.** Fullscreen 2560×1440 @ 144 Hz, game locked at
> **144.0 fps**, 7.2 ms latency, no tearing. Everything below was run and verified on this
> machine — not copied from a guide.
>
> **Author: MiMo-V2.6-Flash Free** (model `mimo-v2.6-flash-free`, provider `opencode`)
> — session 5, 2026-09-27. Handoff to Claude session 5+: see `CLAUDE.md`.

---

## 1. The hardware target (measured, not assumed)

`mr2-tools/dispinfo.py` enumerates via `EnumDisplaySettingsW`:

| | |
|---|---|
| **Native / current** | **2560×1440 @ 144 Hz, 32 bpp** |
| Refresh available **at 1440p** | **60, 120, 144** |
| 4:3 mode at full height | **1920×1440 @ 144** ← exact fit for a 4:3 game |
| Total unique modes | 114 |
| GPU 1 | NVIDIA GeForce RTX 5070 Ti Laptop → 2560×1440 @ 144 |
| GPU 2 | Intel(R) Graphics → 2560×1600 @ 240 (internal panel) |

> ⚠️ **Correction to session-4 notes:** those estimated *~170 Hz* (MSI G274QPF E2's
> panel spec). Windows/driver enumerate **144 Hz max** on this connection. The plan
> targets **144 Hz**. Do not chase 170 — it is not offered.

Because 640×480 × **3** = 1920×1440, the game's native resolution scales into the
pillarbox area by an **exact integer factor**. That single fact drives most of §4.

---

## 2. Measured result (PresentMon 2.6.0)

Capture: `moto.exe`, 8 s, main menu, fullscreen, `mr2-tools/fps-menu.csv` (1151 frames).

| metric | median | p1 | p99 | min | max |
|---|---|---|---|---|---|
| **App present rate** | **144.0 fps** | 136.2 | 152.6 | 131.2 | 163.9 |
| **Displayed to screen** | **144.0 fps** | 142.9 | 145.2 | 141.7 | 145.9 |
| Frame time | **6.945 ms** | — | — | — | — |
| Render→display latency | **7.244 ms** | — | 11.350 | — | — |
| CPU busy | 0.139 ms | — | 0.415 | — | — |
| GPU time | 6.923 ms | — | 11.167 | — | — |

Present details: runtime `DXGI`, `SyncInterval=1`, `AllowsTearing=0`,
`PresentMode = "Composed: Copy with GPU GDI"`.

**Interpretation**

- Displayed rate is pinned at **144.0** (p1 142.9 / p99 145.2) — a **tight, stable lock** to
  the panel. This *is* high-refresh gameplay.
- `SyncInterval=1` + `AllowsTearing=0` ⇒ **vsync-locked, zero tearing.**
- CPU is a non-issue (0.139 ms). GPU time ≈ frame time ⇒ the **display is the limiter**,
  exactly as intended — no headroom is being wasted.
- 7.2 ms render→display is well under one frame (6.9 ms); input response is fine.

### 2b. Race capture — ✅ **144 Hz confirmed under real gameplay** (session 6)

The caveat below used to say race FPS was unmeasured. **It is now measured.**

Capture: `moto.exe`, **15 s**, **during an active race** (road circuit, multiple AI
riders visible — verified by screenshot `mr2-tools/s6-during.png`), `mr2-tools/fps-race.csv`
(**2144 frames, all `moto.exe`**).

| metric | median | p1 | p99 | min | max |
|---|---|---|---|---|---|
| **Displayed to screen** | **144.0 fps** | 129.8 | 145.7 | 71.8 | 166.2 |
| App present rate | 143.7 fps | 79.6 | 738.6 | 71.9 | 1436.4 |
| Frame time | **6.944 ms** | — | — | — | — |
| Render→display latency | **21.043 ms** | — | 27.907 | — | — |
| CPU busy | 0.600 ms | — | 4.251 | — | — |
| GPU time | **6.926 ms** | — | 12.530 | — | — |

Present details: runtime `DXGI`, `SyncInterval=1`, `AllowsTearing=0`,
`PresentMode = **"Hardware Composed: Independent Flip"**`.

**Interpretation**

- ✅ **The headline number: displayed-to-screen median = 144.0 fps in-race.** The lock
  survives the heaviest load the game actually produces. This closes §7 item 2.
- **`p99 = 145.7`** — a race is *tighter* than the menu on the high end, i.e. no runaway.
  The **app present rate** swings wildly (p99 738, max 1436) but that is just the app
  queueing presents faster than the panel; **displayed** is the number that matters.
- **`min = 71.8`** — roughly a single dropped/long frame during a scene load or race
  transition, not sustained. p1 129.8 shows the body of the distribution is fine.
- **GPU time 6.926 ms ≈ frame time 6.944 ms** ⇒ still display-limited with CPU at 0.6 ms.
  The GPU is doing ~exactly one panel-interval of work per frame, so there is real
  headroom in the engine but the pipeline is correctly paced.
- Present mode **upgraded to `Hardware Composed: Independent Flip`** (menu showed
  `Copy with GPU GDI`) — the better, lower-overhead path, which is what you want under load.
- Latency rises from 7.2 ms (menu) to **21.0 ms** in-race. Still ~3 frames at 144 Hz and
  comfortably responsive; noted as the one *measurable* cost of gameplay vs. menu.

> **How to reproduce:** see §8, but **do not use `--process_name` unless elevated** —
> PresentMon needs elevation to filter that way. Without it, capture **everything** and
> filter the CSV on the `Application` column afterwards (that is what produced this
> capture). Also pass **`--stop_existing_session`**, or a stale `PresentMon` ETW session
> will refuse to start.

---

## 3. The stack — why it works

```
moto.exe (1998, DirectDraw + Direct3D, renders 640×480)
   │  DDRAW.dll / D3DImm.dll  ← hooked
   ▼
dgVoodoo2 2.87.5  (DDraw.dll + D3DImm.dll, VRAM=256)
   │  D3D11 swap chain
   ▼
Windows desktop  →  fullscreen 2560×1440 @ 144 Hz
   ▲
   └─ 640×480 image ×3 nearest → 1920×1440, pillarboxed (ScalingMode=stretched_ar)
```

### The load-bearing fact

`[DirectX] VRAM = 256`. Without dgVoodoo the game queries real VRAM, hits a **32-bit
overflow on the RTX 5070 Ti**, and dies:

```
Memory detected : Txt:-14811136 Primary:-1073741824 Total:-65536
(!) INCORRECT VRAM PARAMETERS!
Cannot initialise screen mode          ← FATAL
```

With `VRAM = 256` the same log line reads `Primary:268435456` (positive) and the game runs.

> **`(!) INCORRECT VRAM PARAMETERS!` is a harmless warning, not a failure.** The *working*
> install prints it too. Only **negative** VRAM is fatal. Do not chase this string.

### Session-4 error corrected

Claude (session 4) reported *"every direct launch of GOG `moto.exe` failed … with AND
without dgVoodoo"* and set **`ini D3D = true`**. The proven-working disc install uses
**`D3D = false`**. With `D3D=false` + the dgVoodoo DLLs + `VRAM=256`, the very first launch
succeeded and reached the menu. **`D3D=true` is the likely cause of session 4's failure.**
`D3D=false` is now baked into `motoracer2.ini`.

---

## 4. Final configuration (verified)

### `C:\GOG Games\Moto Racer 2\motoracer2.ini`

```ini
[Settings]
D3D=false
Language=English
ManualSettings=-D3D -KeepAvailableVram800000000
Params=-KeepAvailableVram800000000 -skipintro -DontLimitFrameRate
```

### `C:\GOG Games\Moto Racer 2\dgVoodoo.conf` — only the changed keys

| section | key | value | why |
|---|---|---|---|
| General | `OutputAPI` | `bestavailable` | lets Windows pick the D3D path |
| General | `FullScreenMode` | `true` | fullscreen |
| General | `ScalingMode` | `stretched_ar` | **4:3 pillarbox, no distortion** |
| General | `EnumerateRefreshRates` | `true` | expose refresh rates to the app |
| GeneralExt | `FPSLimit` | **`0`** | uncapped (was `60`) |
| GeneralExt | `ImageScaleFactor` | **`3`** | **pixel-perfect integer upscale** |
| GeneralExt | `DeframerSize` | `1` | thin border when resolution forced |
| DirectX | **`VRAM`** | **`256`** | **CRITICAL — prevents the overflow crash** |
| DirectX | `Resolution` | `unforced, refrate:144` | app picks res; request 144 Hz |
| DirectX | `Filtering` | `appdriven` | let the app decide |
| DirectX | `Antialiasing` | `appdriven` | let the app decide |
| DirectX | `ForceVerticalSync` | `false` | app already presents `SyncInterval=1` |
| DirectX | `Bilinear2DOperations` | `false` | see §5 |
| DirectX | `DisableAltEnterToToggleScreenMode` | `true` | Alt+Enter disabled |

> **Two `Resolution` keys exist.** Line ~157 is `[Glide]` (`unforced` — irrelevant, the game
> does not use Glide); line ~206 is `[DirectX]` — **that is the one that matters.** Editing
> the wrong one silently does nothing.

### Launch

```powershell
$wd = "C:\GOG Games\Moto Racer 2"
Start-Process -FilePath "$wd\moto.exe" `
  -ArgumentList "-skipintro","-DontLimitFrameRate" `
  -WorkingDirectory $wd -PassThru
```

Desktop shortcut created: **`Moto Racer 2 (1440p 144Hz).lnk`** → `moto.exe`,
`-skipintro -DontLimitFrameRate`.

> **Sound: launch with sound.** The old "always `-NoSound`" rule was **revoked by the
> user on 2026-09-27** — they want the GOG soundtrack. `-NoSound` is now just an
> *optional* flag for an unattended test run, never the default.

---

## 5. What was actually tested

### ✅ Test 1 — the fix (GOG would not start at all)

Copied `DDraw.dll`, `D3DImm.dll`, `dgVoodoo.conf` from the proven disc install, set
`FPSLimit 0`, `D3D=false`.

```
process alive after 9s : True
window title          : [Moto Racer 2 - c 1998]
Primary:268435456            ← positive
CfxServer: DirectSound disabled by a command line option  ← -NoSound honored
```
**Result: PASS.** First successful GOG launch.

### ✅ Test 2 — fullscreen + refresh (A/B)

| config | observed display mode |
|---|---|
| A — baseline (`EnumerateRefreshRates=false`, `Resolution=unforced`) | **2560×1440 @ 144 Hz** ×24 samples |
| B — optimized (`=true`, `unforced, refrate:144`) | **2560×1440 @ 144 Hz** ×32 samples |

**Result: no measurable difference.** Both hold 144 Hz — dgVoodoo's D3D11 output runs
borderless at desktop mode, so the panel stays at its desktop refresh either way.

> ⚠️ **Honest finding: `refrate:144` and `EnumerateRefreshRates` are currently *no-ops*.**
> They are kept because they make intent explicit and would matter if the driver's
> "Preferred refresh rate" were ever set to "Application-controlled" (see VOGONS thread
> below). **Do not claim they are what delivers 144 Hz.** What delivers it is dgVoodoo's
> borderless D3D11 output sitting on a 144 Hz desktop.

### ✅ Test 3 — `ImageScaleFactor` 1 vs 3 (with a proper control)

Screenshots alone were inconclusive because the menu animates. Method used:

| region | **control** (same config, 2 shots 1.5 s apart) | **A vs B** (ISF 1 → 3) |
|---|---|---|
| Logo (static) | **0.0000%** — pixel-identical | **53.56%**, max delta 236 |
| Menu text | 3.95% (START pulses) | 27.17% |

The control proves the logo region is static, so the 53.6% is **caused by the setting**.

Zoomed crops (`mr2-tools/cmp-ISF1.png` vs `cmp-ISF3.png`), 2× on the logo:

| | ISF=1 (reference) | **ISF=3 (chosen)** |
|---|---|---|
| Upscaling | filtered / bilinear | **nearest-neighbor** |
| Logo edges | soft, mushy | **crisp, pixel-exact** |
| Fit | scale-to-fit | **exact integer ×3 → 1920×1440** |
| Crop file size | 227 KB | 27 KB (flat blocks = nearest) |

**Result: ISF=3 chosen.** It is a perfect integer scale into the pillarbox and visibly
sharper. `ISF=1` is the fallback if you prefer smooth — one-line change at conf line ~116.

### ✅ Test 4 — oversized cursor (session 6) — root-caused and fixed

The in-game pointer was huge and blocky. **It was never a game or dgVoodoo problem.**

| hypothesis | verdict |
|---|---|
| `CursorScaleFactor` / `SystemHookFlags="cursor"` | ❌ **no-ops** — byte-identical captures at `0` and `1` (config reverted to the validated baseline, MD5 re-verified) |
| game draws its own cursor | ❌ plain framebuffer capture is **empty**; `moto.exe` only imports `LoadCursorA`/`GetCursor`/`SetCursor`/`GetCursorPos` |
| **actual cause** | ✅ **system DPI 144 (Windows scaling 150%) → OS pointer bitmap 48×48** |

Fix: dropped the active display to **100%** (`DisplayConfigSetDeviceInfo` SET_DPI_SCALE
using `path.sourceInfo`). Measured with `measure.py`'s white-pixel bbox:

| | before | after |
|---|---|---|
| effective DPI | 144 | **96** |
| cursor bitmap | 48×48 | **32×32** |
| in-game white bbox | 17×33 / 263 px | **11×22 / 115 px** (≈ the exact 32/48 ratio) |

Full write-up, revert procedure and gotchas: **`CLAUDE.md` → "🖱️ Cursor fix (session 6)"**.
Backup: `mr2-state-backup\scaling-backup.json`.

> **Relevance to this plan:** `CursorScaleFactor` and `SystemHookFlags` are listed here
> only so nobody wastes time on them again — **they do nothing in this game.** The
> validated `dgVoodoo.conf` has `CursorScaleFactor=0` and `SystemHookFlags=` *(empty)*.

### Reference material

- VOGONS — *"Option to select refresh rate without modify resolution"*:
  dgVoodoo author **Dege** confirms the syntax (`unforced, 144`) and that
  **"Enumerate refresh rates" must be enabled**, and that **dgVoodoo defaults to 60 Hz**
  ("the base concept for 60Hz was … the CRT days").
- <https://www.vogons.org/viewtopic.php?t=70235>

---

## 6. Tuning options — NOT yet tested

Safe to try; nothing below has been run.

| option | setting | expected effect |
|---|---|---|
| **Fill vs pillarbox** | `ScalingMode = stretched` | stretches 4:3 → 16:9 (**distorts**; you may prefer it) |
| **CRT look** | `ScalingMode = stretched_ar_crt` | scanline/curved retro presentation |
| **1:1 pixels** | `ScalingMode = centered` | tiny 640×480 image, no scaling |
| **Crisper textures** | `[DirectX] Filtering = pointsampled` | blocky, authentic; vs `bilinear` for smooth |
| **Anti-aliasing** | `[DirectX] Antialiasing = 4x` | smoother geometry edges at 640×480 |
| **Smoother 2D blits** | `Bilinear2DOperations = true` | bilinear scaling of DirectDraw blits |
| **Alt+Enter toggle** | `DisableAltEnterToToggleScreenMode = false` | re-enable Alt+Enter |
| **Extra modes** | `[GeneralExt] ExtraEnumeratedResolutions` | offer extra res to the app |
| **G-Sync** | VSync off + uncapped + NVIDIA G-Sync | removes frame-time judder; **more tearing risk, more setup** |
| **Game flags** | `-TripleBuffer`, `-ZBuffer32`, `-NoFilter`, `-NoDither`, `-NoGouraud` | see `PROGRESS-REPORT.md` §6 for full flag list |

> **Do not force `[DirectX] Resolution` to 2560×1440.** The game renders 640×480;
> forcing a resolution changes what the *game* believes the display is, and session 4
> recorded `max_isf` / `refrate:170` as *"broke it"*. `unforced` + `ImageScaleFactor=3`
> achieves the visual goal without touching the game's own mode selection.

---

## 7. Open items

> 🎯 **USER HANDOFF (2026-09-28):** *"claude still needs to make a 144hz 2560x1440 exe
> with all the fixes and graphics settings and dualsense. and i need to remap some
> buttons but ill do that later."* → the packaging deliverable is item **1**;
> **button remapping is the user's own task, do not do it for them.**

1. **Package the whole stack into one launch target** — everything in §4 already works
   and is measured; this is consolidation + tuning, not new RE. **Clarify first** whether
   the user means a self-contained launcher or an actually-patched `moto.exe`
   (the game *already* runs 144 Hz / 2560×1440 from the existing shortcut). See
   `CLAUDE.md` → **Next steps**.
2. ~~**Race-load FPS not measured**~~ ✅ **CLOSED (session 6) — 144.0 fps displayed
   median in an active race**, 2144 frames, `mr2-tools/fps-race.csv`. Full table +
   interpretation: **§2b**. (Navigation turned out to need no human: the injector just
   had to send real scan codes — see §8.)
3. **`refrate:144` unproven** — A/B showed no difference (Test 2). Re-test only if the
   display ever drops to 60 Hz. **Do not credit them with the 144 Hz result.**
4. **DualSense controls — researched but ⛔ blocked: no gamepad is connected to this
   machine.** Approach and sources are written up in **§10**. Next session should ask the
   user to plug the controller in first.
5. **§6 tuning table is entirely untested** — `ScalingMode` variants, filtering, AA,
   `Bilinear2DOperations`, G-Sync. These belong in the "graphics settings" half of
   item 1; pick and *test* a set rather than shipping it untried.
6. **The reported crash on ENTER — not yet reproduced.** Session 6's first attempt was
   invalid (game minimized → foreground-lock delivered the keys elsewhere). See
   `mr2-tools/SESSION6-NOTES.md`.
7. **`C:\Games\` disc install** — still has Claude's `callerpatch.py` diagnostic patch
   applied to `Moto.exe` (clean copy: `Moto.exe.pre-callerpatch.bak`). Now that GOG is the
   target, that install is reference-only. Consider restoring the clean exe.
8. **`ImageScaleFactor` vs non-integer game resolutions** — if the game ever switches away
   from 640×480 (e.g. 1024×768 via the in-game OPTIONS menu), ×3 will no longer be exact.
   Set `ImageScaleFactor` back to `1` in that case. See §9.
9. **1024×768 native rendering — unproven and not clearly better.** `-Width`/`-Height` are
   ignored (tested negative, §9); it would require in-game OPTIONS navigation. Current
   640×480 ×3 is pixel-perfect, which is likely the better presentation anyway.

**✅ Closed in session 6:** oversized cursor (Test 4), sound confirmed at 100% and durable
(Rule 5), GOG build + full soundtrack verified, safe silent-testing method established
(Rule 7).

---

## 8. Reproducing a measurement

```powershell
$gog = "C:\GOG Games\Moto Racer 2"
$pm  = "C:\Games\mr2-tools\PresentMon.exe"
$csv = "C:\Games\mr2-tools\fps-test.csv"

$p = Start-Process "$gog\moto.exe" -ArgumentList '-skipintro','-DontLimitFrameRate' `
       -WorkingDirectory $gog -PassThru
# optional: add '-NoSound' here for an unattended run. It is NOT a rule any more —
# the user revoked the "always mute" rule on 2026-09-27; launch with sound by default.
Start-Sleep -Seconds 7

# do NOT use -Wait / --terminate_on_proc_exit: PresentMon needs elevation to target by
# process name and will hang otherwise. Start it, sleep, then kill it.
$pmProc = Start-Process $pm -PassThru -NoNewWindow `
            -ArgumentList '--process_name','moto.exe','--output_file',$csv,'--timed','8'
Start-Sleep -Seconds 12
Stop-Process $pmProc.Id -Force -EA SilentlyContinue
Stop-Process $p.Id   -Force -EA SilentlyContinue

& C:\Python314\python.exe C:\Games\mr2-tools\fpsreport.py $csv
```

**Gotchas learned the hard way:**

- PresentMon **requires elevation** to filter by `--process_name`; without it the warning
  appears and `-Wait` hangs past the `--timed` window. Always start it detached + kill.
- ➕ **Without elevation, just drop `--process_name`** and capture everything — then filter
  the CSV on the **`Application`** column (`Import-Csv … | Where Application -eq 'moto.exe'`).
  All 2144 rows of `fps-race.csv` are `moto.exe`, so nothing was lost.
- ➕ **A stale `PresentMon` ETW session blocks the next run**: *"a trace session named
  PresentMon is already running."* Always pass **`--stop_existing_session`**.
- ➕ **Keyboard injection needs real scan codes.** `sendkey.ps1` v1 called
  `keybd_event(vk, scan=0, …)`, and the game (DirectInput) **ignored it** — focus was
  correct, keys "sent", yet the menu never moved. `Tap()` now maps VK→scan via
  `MapVirtualKey` and sets `KEYEVENTF_EXTENDEDKEY` for arrows. **With that fix the game
  navigated fully unattended** — no human needed for START → LOCAL.
- Kill the game **promptly** — it runs fullscreen and takes over the display.
- `Shot` in `helper.ps1` must run `SetProcessDPIAware()` first or captures come back
  1707×960 instead of 2560×1440.
- `-NoSound` is **optional, not a rule** — the "always launch muted" rule was revoked by
  the user on 2026-09-27. Default is **with sound**.
  ⚠️ **It is also not side-effect free:** it persists `volume = 0` into `config.bin`,
  muting every later launch *even without the flag*. This actually broke the user's
  sound. If you use it, restore `mr2-state-backup\config.bin.bak` afterwards.
  **Full write-up: `CLAUDE.md` Rule 5; diagnosis tool `mr2-tools\audiocheck.ps1`.**
  > ➕ **Session 6: to test quietly, do NOT use `-NoSound`.** Mute only the game's own
  > audio session — proven not to reach `config.bin`:
  > `& powershell -File "C:\Games\mr2-tools\volcheck.ps1"` (reads the volume, then mutes
  > in the same call), or `audiocheck.ps1 -Proc moto -SetVol 0`. **`CLAUDE.md` Rule 7.**
- **Never pass `-noprotection`** (Rule 1 — `BLAIREAU !` trap).

### Tooling added this session

| file | purpose |
|---|---|
| `mr2-tools/dispinfo.py` | enumerate all display modes + refresh rates |
| `mr2-tools/refreshpoll.py` | poll the live display mode while the game runs |
| `mr2-tools/PresentMon.exe` | Intel frame-presentation capture (v2.6.0, 980 KB, no install) |
| `mr2-tools/fps-menu.csv` | the 1151-frame capture behind §2 |
| `mr2-tools/fpsreport.py` | FPS / latency statistics from a PresentMon CSV |
| `mr2-tools/pngdiff.py` | whole-image pixel diff |
| `mr2-tools/cropdiff.py` | diff a static crop (isolates animation from real changes) |
| `mr2-tools/cropzoom.py` | crop + nearest-zoom a region for visual comparison |
| `mr2-tools/utf8check.py` | verify UTF-8 integrity of the handoff docs |
| `mr2-tools/gog-final-fullscreen.png` | fullscreen at ISF=1 |
| `mr2-tools/gog-imgscale3.png` | fullscreen at ISF=3 |
| `mr2-tools/cmp-ISF1.png`, `cmp-ISF3.png` | 2× logo crops, the visual A/B |
| `mr2-tools/gog-VALIDATED.png` | final validated state |
| `mr2-tools/gog-1024x768.png` | the `-Width/-Height` test (no-op — see §9) |

---

## 9. External corroboration — PCGamingWiki

<https://www.pcgamingwiki.com/wiki/Moto_Racer_2> independently confirms this plan's core
decisions, and surfaces one **critical** fact:

| PCGamingWiki says | our status |
|---|---|
| *"Game not launching on Windows 10 and newer → **Use dgVoodoo 2**, extract… to `<path-to-game>`"* | ✅ **exactly the fix that worked** (§3) |
| **"Frame rate is capped at 30 FPS by default"** → use `-DontLimitFrameRate` (or append to `Params=`) | ✅ **`-DontLimitFrameRate` is LOAD-BEARING, not optional.** Without it this plan would deliver **30 fps**, not 144. It is in both `Params=` and the shortcut. |
| Widescreen: *"Detects resolutions **up to 1024×768**. Can be forced with dgVoodoo 2."* | ✅ explains why `Resolution = unforced` + dgVoodoo scaling is the right shape |
| Save / settings live in `<path-to-game>\data\config.bin` | ℹ️ "both game progress and in-game settings" — **the resolution setting is likely in there** |
| Windowed: *"Toggle with **Alt+Enter**. Requires 16-bit screen mode."* | ℹ️ explains the `(!) Windowed mode forbiden because desktop n.b.p.p is 32` message |
| API: **Direct3D 3** | ℹ️ hence `D3DImm.dll` — dgVoodoo must hook *both* `DDraw.dll` and `D3DImm.dll` |
| 4-player **local split-screen** supported | 💡 possible future test |

> **Two independent frame-rate limiters exist.** The **game** caps at 30 fps
> (`-DontLimitFrameRate` disables it) and **dgVoodoo** has its own (`FPSLimit`, set to `0`).
> **Both must be off.** This plan sets both.

### ❌ Tested negative — `-Width` / `-Height` are ignored

```
args = -skipintro -DontLimitFrameRate -NoSound -Width1024 -Height768
→ log: Res:640x480    Screen:1228800      (640×480×4 — unchanged)
```
The flags are accepted silently (no error) but **do not change the render resolution**.
To get 1024×768 you must change it **in-game via OPTIONS**, or edit `data\config.bin`
(encrypted — and CLAUDE.md marks that a "side quest, don't sink time here").

**Whether 1024×768 would even be an improvement is unproven.** It is a *taste tradeoff*:

| | 640×480 (**current**) | 1024×768 |
|---|---|---|
| scale into 1920×1440 | **×3 exact integer → pixel-perfect** | ×1.875 non-integer → soft/resampled |
| geometry detail | coarser | finer |
| authenticity | original | higher-fidelity |
| setup cost | none | in-game menu navigation |

**Recommendation: keep 640×480 ×3** unless you specifically want the extra geometry.
Re-test only if someone actually navigates OPTIONS.

---

## 10. Controller / DualSense — research only (no hardware present)

**Status: ⛔ cannot be tested — no gamepad is connected to this machine.**
(`Get-PnpDevice -PresentOnly` returns only laptop internals: touchpad, keyboard, radio.)

What research established for the next pass:

| finding | source |
|---|---|
| **The game HAS controller support** — *"Controller support: ✅"*, *"Full controller support: ✅ (navigating some menus may require mouse/keyboard)"* | PCGamingWiki |
| ⚠️ **"Controller remapping: only recognizes first two axes."** — a real limitation: the game reads **axes 0 and 1 only** (X/Y). | PCGamingWiki |
| **DirectInput is supported** — *"Moto Racer 2 recognizes the Xbox 360 controller as a DirectInput device and runs as it should"* | VOGONS |
| **`AntiMicro` gives analog steering** — *"I use a Logitech F310 gamepad, combined with the program AntiMicro which gives me analog steering in Moto Racer 2"* | Steam Community |
| There is a **"Moto Racer 2 – GOG can't steer [SOLVED]"** thread | Tom's Hardware *(bot-blocked, fetch manually)* |
| Game imports **`DINPUT.dll`** (DirectInput) natively | verified from `moto.exe` imports |
| Vibration: **supported**. Haptics / adaptive triggers / light bar / motion: **not supported** | PCGamingWiki |

### Likely approach for a DualSense

A DualSense enumerates as a **DirectInput** device, so it *should* be picked up natively —
but PS controllers expose odd default axis mappings, and the game only reads **two axes**.

1. **Try native first** — plug in, launch, check OPTIONS → controller. Cheapest test.
2. **If steering/throttle are wrong → `AntiMicro`/`AntiMicroX`**: maps gamepad →
   keyboard/mouse, and per the Steam thread provides **analog** steering.
3. **Or `DS4Windows`** to present the DualSense as an Xbox 360 (DirectInput-recognized)
   controller — matches the VOGONS report.
4. Expect **menus may still need the keyboard** (PCGamingWiki caveat).

**Blocking requirement: the hardware must be plugged in.** Next session should start by
asking the user to connect it.

---
