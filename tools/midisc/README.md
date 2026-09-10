# midisc package

Patch sources for `1.40MIDISC` on OS 1.40C.

```bash
python tools/build_midisc40.py
```

Needs your own 1.40C. See root README + `docs/TECH.md` + `docs/FLASHING.md`.

| file | role |
|------|------|
| `memory_map.py` | 1.40C addresses / caves / hooks |
| `parts.py` | pack / unpack / save / reload / bank |
| `hold.py` | hold, dial, unlock, ARP clamp |
| `morph.py` | XF mix / morph / plock |
| `scene_ui.py` | clear / copy / paste |
| `emit.py` | shared helpers |
| `build.py` | link, patch sites, repack |
| `HANDOFF.md` | short shipped map |
