# Moto Racer 2 (Windows 11) - Agent Handoff & Architecture Guide

## 1. Quick Project Status (Session 8 Complete)
* **Goal Achieved:** Native 2560x1440 @ 144 Hz rendering, authentic North American intro video, licensed punk rock soundtrack (*The V-Town Have-Nots: "Unnatural Selection"*), and PS5 DualSense controller support.
* **Working Repository:** `C:\Games` (`sstewart207/moto-racer-2-win11`, branch `main`).
* **Game Installation Directory:** `C:\GOG Games\Moto Racer 2`.
* **User Desktop Shortcut:** `C:\Users\sstew\Desktop\Moto Racer 2 (1440p 144Hz).lnk` -> `C:\GOG Games\Moto Racer 2\MotoRacer2Launcher.exe`.

---

## 2. Core Technical Architecture & Mod Details

### A. Engine Resolution Patch (`moto.exe`)
* **Problem:** `moto.exe` hardcoded a 1024x768 display mode filter in its DirectDraw enumeration callback (`Cdd::enumVideoModes` at VA `0x41A8C5`), preventing modern resolutions from being selected.
* **Solution:** Patched `0x41A912` and `0x41A91F` from `0x400` / `0x300` (1024 / 768) to `0x1000` (4096).
  * Original: `C:\GOG Games\Moto Racer 2\moto.exe.orig` (MD5: `598D3899056340EBCE7EBFC0183F15E0`)
  * Patched: `C:\GOG Games\Moto Racer 2\moto.exe` (MD5: `302EFC8762F80E1CDCD4D1553190159B`)
* **dgVoodoo Configuration:** `C:\GOG Games\Moto Racer 2\dgVoodoo.conf`
  * `[DirectX] ExtraEnumeratedResolutions = 2560x1440, 1920x1080, 1280x720, 960x540, 1024x768`
  * `Resolution = max, refrate:144`
* **In-Game Setting:** OPTIONS -> DISPLAY -> FULL SCREEN -> Cycle to `2560 x 1440` and confirm with OK.

### B. Controller & Launcher (`MotoRacer2Launcher.exe`)
* **Source:** `C:\Games\mr2-tools\launcher\MotoRacer2Launcher.cs`
* **Build Script:** `C:\Games\mr2-tools\launcher\build.ps1`
* **Binary:** `C:\GOG Games\Moto Racer 2\MotoRacer2Launcher.exe`
* **Behavior:**
  * Whitelists both original GOG MD5 (`598D38990563`) and 1440p patched MD5 (`302EFC8762F8`).
  * Auto-detects PS5 DualSense (`0x054C`) or Xbox (`0x045E`).
  * Injects Player 1 memory binding table (`0x6421CB`) at 4s and 8s after launch.
  * DirectInput proxy (`dinput.dll`) maps DualSense buttons to Xbox layout (✕ = button 1 = OK).
  * Helper maps Left Stick (steering), R2 (accelerate), L2 (brake), Cross (turbo). In menus: D-pad = arrows, Cross = OK, Circle/Options = ESC.

### C. Soundtrack & Video Cutscenes (North American NTSC Restoration)
* **Regional Difference:** GOG ships the European PAL version (Christophe Rime jazz/fusion score, 2:30 generic video). The North American release has licensed punk rock by *The V-Town Have-Nots: "Unnatural Selection"* and a 1:07 intro cutscene.
* **Engine Boot Sequence Disassembly (`0x462BF6`):**
  * The engine queues: `data\ea.avi` -> `data\dsi.avi` -> `data\intro.avi`.
  * If `ea.avi` or `dsi.avi` is missing, the MCI player fails immediately and aborts the entire queue.
  * To bypass the 26-second European Delphine Software logo cinematic (`dsi.avi`) and EA logo (`ea.avi`) without breaking the MCI player queue, both were replaced with 0.05-second instant-skip dummy AVIs.
  * Result: The authentic North American intro movie (`intro.avi`) plays immediately upon launch with zero delay.
* **CD Track Configuration (`data\cdtrack.txt`):**
  * `MENU 2` -> Plays `02.wav` (The V-Town Have-Nots: *"Unnatural Selection"*, 3:32 studio master).
  * Race tracks (`GRDPRIX`, `FOREST`, `AMAZSPD`, `AMAZDRT`, `BRITSPD`, `BRITDRT`, `SAHASPD`, `SAHADRT`) mapped to `-1` to silence in-race background music while keeping full 3D motorcycle and environment sound effects.
* **Deployed Files:**
  * `C:\GOG Games\Moto Racer 2\data\ea.avi` (0.05s instant dummy skip).
  * `C:\GOG Games\Moto Racer 2\data\dsi.avi` (0.05s instant dummy skip).
  * `C:\GOG Games\Moto Racer 2\data\intro.avi` (1m 07s retail cutscene with The V-Town Have-Nots: *"Unnatural Selection"*, 44.1 kHz stereo PCM).
  * `C:\GOG Games\Moto Racer 2\data\generic.avi` (Attract mode cutscene).
  * `C:\GOG Games\Moto Racer 2\02.wav` (Full 3:32 studio master of *"Unnatural Selection"* for menu music).
  * Backups: `ea.avi.bak`, `dsi.avi.bak`, `cdtrack.txt.orig`, `generic.avi.gog.bak`, `02.wav.pal.bak`.

---

## 3. Critical Rules & Guardrails For Any Future Agent

> [!CAUTION]
> **1. DO NOT LAUNCH `moto.exe` FROM BACKGROUND DEVELOPER SUBSHELLS!**
> Agent runner subshells run inside an isolated desktop session (`exebox-...`). Launching GUI games from background shells causes the DirectX window to render onto the hidden sandbox desktop, while DirectSound audio plays into the user's headset ("ghost game with no window").
> Always instruct the user to launch the game by double-clicking **`Moto Racer 2 (1440p 144Hz).lnk`** directly on their Windows desktop.

> [!WARNING]
> **2. NEVER PASS `-NoSound` TO `moto.exe`!**
> Passing `-NoSound` writes `volume = 0` into `data\config.bin`, permanently muting the game. If muted, restore volume using `mr2-tools\cfgvol.py` or restore `config.bin`.

> [!IMPORTANT]
> **3. ALWAYS PRESERVE `.orig` AND `.bak` FILES!**
> Do not overwrite original GOG or retail assets without keeping untouched backup files.

> [!NOTE]
> **4. MCI AUDIO FORMAT REQUIREMENT:**
> Windows 11 MCI (`mciSendCommandA`) requires standard **44.1 kHz 16-bit stereo PCM** audio (`pcm_s16le`). Compressed or mono audio formats (e.g. 11kHz 8-bit mono or `adpcm_ms`) cause MCI video playback to terminate silently or crash.
