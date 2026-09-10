# midisc — `1.40MIDISC`

Sources to build **MIDI scene locks** on official Octatrack **OS 1.40C**.

## What it does

- MIDI track scene A/B locks + XF morph
- Part save/reload persist
- Bank switch keeps machine regs (sample load stays intact)
- Solid green scene-lock LEDs
- ARP scene-lock value clamps (LEG / MODE / SPD / RNGE)

Details: `docs/TECH.md`. Shipped notes: `tools/midisc/HANDOFF.md`.

## Build

Python 3. Need your own **1.40C** (do not commit or share it).

```bash
# optional helper — downloads official zip into downloads/
powershell -ExecutionPolicy Bypass -File scripts/fetch-os.ps1   # Windows
# sh scripts/fetch-os.sh                                       # Unix

python tools/build_midisc40.py
```

Expects stock syx at `downloads/extracted/OCTATRACK_OS1.40C.syx` (or a prior
extract at `out/raw/section_3_MAIN_OS.bin`). Writes `~/Desktop/1.40MIDISC.bin`.

Flash: CF root → **OS UPGRADE**. Recovery: stock `OCTATRACK_OS1.40C.syx`
(see `docs/FLASHING.md`).

## Layout

| path | role |
|------|------|
| `tools/midisc/` | patch |
| `tools/build_midisc40.py` | entry |
| `tools/ot3_asm.py` | ColdFire asm helper |
| `tools/extract_main_os.py` | syx → MAIN OS |
| `tools/repack_140fx.py` | MAIN OS → `.bin` / `.syx` |
| `tools/syx_elektron.py`, `aplib_elektron.py` | container helpers |

## ⚠️ Before you flash

Non-official OS can brick the unit and voids support/warranty assumptions.
Not affiliated with Elektron. Flash at your own risk.

**Do not share built `.bin` / `.syx`** — they contain Elektron’s OS. Share this
repo; everyone builds from their own 1.40C.

*Octatrack* / *Elektron* are trademarks of Elektron Music Machines MAV AB.

## License

MIT for this repo’s own code and docs. Not for Elektron firmware.
