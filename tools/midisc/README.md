# midisc package

Patch sources for **1.40MIDISC8.2** on OS 1.40C (splash `MIDISC8.2`).
Desktop: `1.40MIDISC8.2.bin` (no golden).

MIDISC8 scenes + Part lifecycle + CHAN T1–T8 internal route. CC filter on hold.

```bash
python tools/build_midisc40.py
# or: $env:PYTHONPATH="tools"; python -m tools.midisc.build
```

| file | role |
|------|------|
| `memory_map.py` | 1.40C addresses / caves / hooks |
| `midi_route.py` | CHAN T1–T8 → audio MIDI-in inject |
| `parts.py` | pack / unpack / save / reload / bank |
| `hold.py` | hold, dial, unlock, ARP clamp |
| `morph.py` | XF mix / morph / plock |
| `scene_ui.py` | clear / copy / paste |
| `build.py` | link, patch sites, repack |
| `HANDOFF.md` | short shipped map |
