# midisc package

Patch sources for **MIDISC2.2** on OS 1.40C (splash `MIDISC2.2`).
Exact MIDISC4.0 / midisc21 engine. Desktop: `MIDISC2.2.bin`.

```bash
python tools/build_midisc40.py
# or: $env:PYTHONPATH="tools"; python -m midisc.build
```

Needs your own 1.40C. Browser patcher: https://bkkbrls-del.github.io/midisc-patcher/  
See root README + `HANDOFF.md` + `docs/TECH.md` + `docs/FLASHING.md`.

| file | role |
|------|------|
| `release22.json` / `release22.py` | hash-checked MAIN patch → MIDISC2.2 |
| `release21.json` / `release21.py` | prior MIDISC2.1 release (same MAIN bytes) |
| `hooks21.py` | stock-site Detours/Pokes for octabam |
| `memory_map.py` | 1.40C addresses / caves / hooks |
| `parts.py` | pack / unpack / save / reload / bank / after-project-load |
| `hold.py` | hold, dial, unlock, ARP clamp |
| `morph.py` | XF mix / morph / plock |
| `scene_ui.py` | clear / copy / paste |
| `emit.py` | shared helpers |
| `build.py` | entry → release22 |
| `HANDOFF.md` | short shipped map |
