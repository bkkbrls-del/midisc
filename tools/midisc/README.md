# midisc package

Patch sources for **1.40MIDISCN8.1** on OS 1.40C (splash `MIDISCN8.1`).
Desktop: `1.40MIDISCN8.1.bin` (no golden).

MIDISC8 scenes + Part lifecycle. CC48/55/56 CONTROL filter **on hold**.

```bash
python tools/build_midisc40.py
# or: $env:PYTHONPATH="tools"; python -m tools.midisc.build
```

Needs your own 1.40C. Browser patcher: https://bkkbrls-del.github.io/midisc-patcher/  
See root README + `HANDOFF.md` + `docs/TECH.md` + `docs/FLASHING.md`.

| file | role |
|------|------|
| `memory_map.py` | 1.40C addresses / caves / hooks |
| `parts.py` | pack / unpack / save / reload / bank / after-project-load |
| `hold.py` | hold, dial, unlock, ARP clamp |
| `morph.py` | XF mix / morph / plock |
| `scene_ui.py` | clear / copy / paste |
| `emit.py` | shared helpers |
| `build.py` | link, patch sites, repack |
| `HANDOFF.md` | short shipped map |
