# midisc (`1.40MIDISC`)

OS patch on Elektron Octatrack **1.40C**. MIDI scene locks, XF morph, part persist,
solid lock LEDs, ARP scene-lock clamps.

```bash
python tools/build_midisc40.py
```

Flash: `~/Desktop/1.40MIDISC.bin` → CF root → OS UPGRADE.  
Recovery: stock `OCTATRACK_OS1.40C.syx`.

Do not redistribute built `.bin` / `.syx` (contains Elektron’s OS). See root README.

## Shipped behaviour

See `tools/midisc/HANDOFF.md`.

## Sources

`tools/midisc/` — `memory_map`, `parts`, `hold`, `morph`, `scene_ui`, `build`, `emit`, `util`.
