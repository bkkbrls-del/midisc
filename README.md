# midisc — `1.40MIDISC`

Standalone sources to **reproduce Octatrack MIDI scene locks** on official
**OS 1.40C**. Version stamp: **`1.40MIDISC`**.

This repo is **MIDI scenes only** — not DSP effects, not the full octabam
remixer tree.

## What `1.40MIDISC` holds

- MIDI track **scene A/B locks** + XF morph
- Part save/reload **persist** (classic sparse pad)
- Bank switch/invalidate **register preserve** (1.40C sample load)
- **Solid green** scene-lock LEDs
- **ARP** scene-lock clamps (`PAGE_MODE == 2`, flats 12–17): LEG / MODE / SPD / RNGE

Technical notes: `tools/midisc/HANDOFF.md`, `docs/MIDISC.md`, `docs/MIDI_SCENES.md`,
`docs/PARAM_PAGES.md` (MIDI page map).

## Reproduce (your own 1.40C)

1. Get official **1.40C** (Elektron support). Do **not** commit or share it.
2. Place the extracted stock MAIN OS where the build expects it, **or** put
   `OCTATRACK_OS1.40C.syx` at `downloads/extracted/OCTATRACK_OS1.40C.syx`
   (see `docs/WINDOWS.md` / `scripts/fetch-os.*`).
3. Build:

```bash
python tools/build_midisc40.py
```

4. Flash `~/Desktop/1.40MIDISC.bin` → CF root → **OS UPGRADE**.  
   Recovery: stock `OCTATRACK_OS1.40C.syx`.

### Layout

| path | role |
|------|------|
| `tools/midisc/` | patch sources |
| `tools/build_midisc40.py` | entrypoint |
| `tools/ot3_asm.py` | ColdFire assembler used by the patch |
| `tools/extract_main_os.py` | syx → MAIN OS (if stock not pre-extracted) |
| `tools/repack_140fx.py` | MAIN OS → flashable `.bin` / `.syx` |
| `tools/syx_elektron.py` / `aplib_elektron.py` | Elektron container helpers |
| `docs/*` | MIDI-scenes RE + flash notes only |

## ⚠️ Before you flash anything

Writing a non-official OS to an Octatrack can leave it unusable, and it puts
your warranty in question. Nothing here is endorsed by, supported by, or
affiliated with Elektron. If you flash a modified image you do so entirely at
your own risk. Read `docs/FLASHING.md` before you need recovery.

Back up projects before flashing. MKI and MKII share the same **1.40C** image
(hash-verified); midisc was tested on **MKII**.

**No Elektron binary is redistributed here — and none may be.** A built `.bin`
or `.syx` contains Elektron’s OS — **do not share built images**. Share this
repo; everyone builds their own.

*Octatrack* and *Elektron* are trademarks of Elektron Music Machines MAV AB,
used here only to identify the hardware this project targets.

## License

MIT for this repository’s own code and documentation. It does not extend to
Elektron’s firmware, which is not distributed here.
