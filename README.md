# midisc — `1.40MIDISC8.1`

ColdFire patch that adds **MIDI scene locks** to official Octatrack **OS 1.40C**.

There is **no prebuilt firmware in this repo**. Rebuild from your own 1.40C
(same extract → patch MAIN OS → repack path used by octabam-style tooling),
or use the browser patcher:
**https://bkkbrls-del.github.io/midisc-patcher/**

## Behaviour

- MIDI track scene A/B locks + XF morph between scenes and step plocks
- Empty XF side uses the trig layer when a step is locked, else machine behind
- Full A / full B: scene-locked flats are absolute (step locks not heard on that end)
- Mid-XF: continuous lerp without re-stamping the LFO row every trig (no step jumps)
- Part Save parks a freeze twin; edits survive reboot; Part Reload restores that freeze
- Part Yes applies MIDI scenes immediately (apply bridge + xf_mix)
- Part Paste stays on the current part (stock APPLY_WAIT_BNE)
- Project save/reload keeps locks (all parts); bank load keeps machine regs
- Site B bank publish does **not** pack (avoids durable SAVE mid bank-load)
- `STOCK_APPLY` left stock (compose-friendly with Octakit; avoids project-load hang)
- `part_window` seam for Octakit kit base override; `KITS_GATE` skips bank↔part coupling
- Full scene B: CTRL CC locks stay frozen on dial (CC_TX uses mixed VOICE)
- Solid green scene-lock LEDs (no blink path)
- ARP scene-lock values clamped to real knob ranges
- MIDI CONTROL CC48/55/56 filter menu: **on hold** (not in this build)

Shipped map: **`tools/midisc/HANDOFF.md`**. Technical map: **`docs/TECH.md`**.  
Constants: `tools/midisc/memory_map.py`.

## Rebuild from stock 1.40C

Requirements: Python 3. Your own official **1.40C** (never commit/share it).

```bash
# 1) Obtain stock (optional helper)
powershell -ExecutionPolicy Bypass -File scripts/fetch-os.ps1   # or scripts/fetch-os.sh

# 2) Patch MAIN OS + repack flash image
python tools/build_midisc40.py
# or: $env:PYTHONPATH="tools"; python -m tools.midisc.build
```

Pipeline inside the build:

1. `ensure_stock()` — use `out/raw/section_3_MAIN_OS.bin` if present, else
   extract from `downloads/extracted/OCTATRACK_OS1.40C.syx`
2. Assemble caves/stubs (`tools/midisc/*.py` + `ot3_asm.py`) and splice hooks
3. `tools/repack_140fx.py` → Desktop **`1.40MIDISC8.1.bin`** (splash `1.40MDIS81`, ≤10 chars)
   (+ syx under `out/`; Desktop bin only)

Optional (octabam compose): `python3 tools/gas_port.py` regenerates `gas/*.s` and
proves byte-identity (needs `m68k-elf-binutils`).

Then flash **that build’s** `.bin` (CF root → OS UPGRADE). Details:
`docs/FLASHING.md`.

### Sources

| path | role |
|------|------|
| `tools/midisc/build.py` | place code, patch sites, call repack |
| `tools/midisc/hold.py` | A/B hold store, dial, unlock, ARP clamp |
| `tools/midisc/parts.py` | pack/unpack, save/reload, bank, `part_window` seam |
| `tools/midisc/morph.py` | XF mix / morph / plock / write remix + VOICE→d2 |
| `tools/midisc/midi_filter.py` | MIDI CONTROL CC48/55/56 (disabled / on hold) |
| `tools/midisc/scene_ui.py` | clear / copy / paste |
| `tools/midisc/emit.py` | shared MSC helpers |
| `tools/midisc/memory_map.py` | all 1.40C addresses |
| `tools/gas_port.py` | emit/verify GNU-as caves for relocatable compose |
| `tools/ot3_asm.py` | ColdFire assembler |
| `tools/extract_main_os.py` | syx → MAIN OS |
| `tools/repack_140fx.py` | MAIN OS → `.bin` / `.syx` |
| `tools/syx_elektron.py`, `aplib_elektron.py` | ELEK container |

## ⚠️ Safety

Modified OS can brick the unit; not affiliated with Elektron; flash at your
own risk. **Do not share built `.bin` / `.syx`** (they contain Elektron’s OS).
Share this repo or the patcher page; everyone builds from their own 1.40C.

*Octatrack* / *Elektron* — trademarks of Elektron Music Machines MAV AB.

## License

MIT for this repo’s code and docs. Not for Elektron firmware.
