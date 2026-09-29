# Moto Racer 2 on Windows 11 — 1440p widescreen, 144 Hz, DualSense + Xbox

Getting Delphine's **Moto Racer 2** (1998, GOG build) running properly on Windows 11:

- **2560×1440 @ 144 Hz**, true **Hor+ widescreen** (960×540 mode via dgVoodoo `ExtraEnumeratedResolutions`)
- **144.0 fps** measured in races (PresentMon)
- **DualSense and Xbox controllers**, auto-detected per launch — right trigger gas, left trigger brake,
  PlayStation/Xbox-style menus (Options/Menu pauses)
- Sound fixed at 100% (the old `-NoSound` / muted-session bug)

> **No game files are in this repo.** You need your own GOG copy of Moto Racer 2 and
> [dgVoodoo2](http://dege.freeweb.hu/dgVoodoo2/) (2.87.5 used). This repo holds notes, tools and configs only.

## Quick start

1. Install the GOG game to `C:\GOG Games\Moto Racer 2\`, add dgVoodoo's `DDraw.dll` + `D3DImm.dll`.
2. Copy `game-config\dgVoodoo.conf`, `motoracer2.ini`, `launch-mr2.ps1` into the game folder.
3. In game: OPTIONS → DISPLAY → FULL SCREEN = **960×540** → OK (once).
4. Build the launcher once: `mr2-tools\launcher\build.ps1` (uses the C# compiler built into Windows) - it installs
   **`MotoRacer2Launcher.exe`** into the game folder. Point your desktop shortcut at it and double-click to play.
   (`launch-mr2.ps1` still works too.)

## Controls

| Action | Xbox | DualSense |
|---|---|---|
| Steer | Left stick | Left stick |
| Gas / brake | RT / LT | R2 / L2 |
| Turbo / stunts | A | ✕ |
| Gears | RB / LB | R1 / L1 |
| Camera / look back | Y / X | △ / □ |
| Pause | Menu | Options |
| Menus | D-pad, A, B | D-pad, ✕, ○ |

How: `mr2-tools/padprofile.ps1` writes the Player-1 binding table into the running game
(9 × 24-byte records @ `0x6421CB`); `mr2-tools/padhelper.ps1` turns pad presses into keys for
menus, and reads Xbox triggers through **XInput** (DirectInput merges them into one axis).

## Docs

- **`CLAUDE.md`** — full project log / handoff (sessions 1–7, two AI models, corrections log)
- `GRAPHICS-PLAN.md` — the 1440p/144 Hz plan and measurements
- `FINDINGS.md` — `.BPT` encryption + CD-TOC protection (session 4)
- `mr2-tools/` — RE scripts (capstone/pefile), `.BKF` parser, audio/display/input tools
