# Clouds-micro on Windows (no WSL)

Everything below runs in **PowerShell** or **cmd** with tools you likely already have.

## Prerequisites

| Tool | Check | Install if missing |
|------|--------|-------------------|
| Python 3.8+ | `python --version` | [python.org](https://www.python.org/downloads/) |
| Git | `git --version` | [git-scm.com](https://git-scm.com/download/win) |
| cmake + g++ | `cmake --version` / `g++ --version` | `winget install BrechtSanders.WinLibs.POSIX.UCRT` |

You do **not** need WSL, Docker, or make.

Optional: **Git Bash** (`C:\Program Files\Git\bin\bash.exe`) if you prefer running the original shell scripts later.

---

## One-time setup

Open PowerShell in the repo folder:

```powershell
cd C:\Users\l\Desktop\octamax\octabam

powershell -ExecutionPolicy Bypass -File scripts\setup-windows.ps1
```

This builds:

- `vendor/elektron-firmware-tool/elektron-firmware-tool.exe` (optional; repack is pure Python)
- `vendor/dsp56300/build/.../dsp_asm.exe` (required to assemble Clouds DSP code)

---

## Download stock OS + extract MAIN OS

```powershell
powershell -ExecutionPolicy Bypass -File scripts\fetch-os.ps1
python tools\extract_main_os.py
```

Creates `out/raw/section_3_MAIN_OS.bin` (1,112,560 bytes).

---

## Build Clouds-micro firmware

```powershell
python tools\build_clouds.py
python tools\repack_clouds.py -V CLOUDS001
```

Outputs:

- `out/mainos_clouds.bin` — patched MAIN OS
- `out/OCTATRACK_CLOUDS.syx` — MIDI recovery / upgrade
- `out/OCTATRACK_CLOUDS.bin` — **CF card flash** (fast path)

---

## Flash on the Octatrack

1. Keep `downloads/extracted/OCTATRACK_OS1.40C.syx` for recovery.
2. Copy `out/OCTATRACK_CLOUDS.bin` to the **root** of the CF card (USB DISK MODE).
3. **PROJECT → OS UPGRADE → YES**
4. On the unit: FX2 → **CLOUDS** (was Spring Reverb).

Recovery: `[FUNC]` + power on → `[TRIG 3]` MIDI UPGRADE → send stock `.syx`.

---

## If `build_clouds.py` fails on dsp_asm

`build_clouds.py` looks for:

```
vendor/dsp56300/build/source/dsp_host/dsp_asm
```

On Windows the binary may be `dsp_asm.exe`. If the script cannot find it, either:

1. Re-run `setup-windows.ps1`, or  
2. Copy/rename:

```powershell
copy vendor\dsp56300\build\source\dsp_host\dsp_asm.exe vendor\dsp56300\build\source\dsp_host\dsp_asm
```

---

## Alternative: Git Bash only for setup

If cmake works in Git Bash but not PowerShell:

```bash
"/c/Program Files/Git/bin/bash.exe" scripts/setup.sh
python tools/extract_main_os.py
python tools/build_clouds.py
python tools/repack_clouds.py
```

---

## What we can do without flashing hardware

| Step | Needs hardware? |
|------|-----------------|
| extract MAIN OS | No |
| assemble `clouds_micro.asm` | No |
| `build_clouds.py` | No |
| `repack_clouds.py` | No |
| Listen to grains | Yes (or wait for M4 + emulator tuning on Windows) |

Milestone 1 only needs a flash to confirm the Spring slot works. After that, DSP edits + rebuild + repack cycle is all on the PC.
