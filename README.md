# midisc — `1.40MIDISC`

ColdFire patch that adds **MIDI scene locks** to official Octatrack **OS 1.40C**.

There is **no prebuilt firmware in this repo**. You rebuild from your own 1.40C
(same extract → patch MAIN OS → repack path used by octabam-style tooling).

## Behaviour

- MIDI track scene A/B locks + XF morph between scenes
- Locks survive Part Save → reboot (sparse persist in the part window)
- Bank load keeps machine regs (1.40C sample load stays intact)
- Solid green scene-lock LEDs (no blink path)
- ARP scene-lock values clamped to real knob ranges

Technical map: **`docs/TECH.md`**. Constants: `tools/midisc/memory_map.py`.

## Rebuild from stock 1.40C

Requirements: Python 3. Your own official **1.40C** (never commit/share it).

```bash
# 1) Obtain stock (optional helper)
powershell -ExecutionPolicy Bypass -File scripts/fetch-os.ps1   # or scripts/fetch-os.sh

# 2) Patch MAIN OS + repack flash image
python tools/build_midisc40.py
```

Pipeline inside the build:

1. `ensure_stock()` — use `out/raw/section_3_MAIN_OS.bin` if present, else
   extract from `downloads/extracted/OCTATRACK_OS1.40C.syx`
2. Assemble caves/stubs (`tools/midisc/*.py` + `ot3_asm.py`) and splice hooks
3. `tools/repack_140fx.py` → Desktop **`1.40MIDISC.bin`** (+ syx under `out/`)

Then flash **that build’s** `.bin` (CF root → OS UPGRADE). Details:
`docs/FLASHING.md`.

### Sources

| path | role |
|------|------|
| `tools/midisc/build.py` | place code, patch sites, call repack |
| `tools/midisc/hold.py` | A/B hold store, dial, unlock, ARP clamp |
| `tools/midisc/parts.py` | pack/unpack, save/reload, bank preserve |
| `tools/midisc/morph.py` | XF mix / morph / plock list |
| `tools/midisc/scene_ui.py` | clear / copy / paste |
| `tools/midisc/emit.py` | shared MSC helpers |
| `tools/midisc/memory_map.py` | all 1.40C addresses |
| `tools/ot3_asm.py` | ColdFire assembler |
| `tools/extract_main_os.py` | syx → MAIN OS |
| `tools/repack_140fx.py` | MAIN OS → `.bin` / `.syx` |
| `tools/syx_elektron.py`, `aplib_elektron.py` | ELEK container |

## ⚠️ Safety

Modified OS can brick the unit; not affiliated with Elektron; flash at your
own risk. **Do not share built `.bin` / `.syx`** (they contain Elektron’s OS).
Share this repo; everyone builds from their own 1.40C.

*Octatrack* / *Elektron* — trademarks of Elektron Music Machines MAV AB.

## License

MIT for this repo’s code and docs. Not for Elektron firmware.
