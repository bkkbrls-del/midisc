# midisc package

Patch sources for golden **1.40MIDISC8** on OS 1.40C (splash `1.40MDISC8`).
Desktop: `1.40MIDISC8.bin` + `1.40MIDISC68GOLDEN.bin`.

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
