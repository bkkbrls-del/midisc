# midisc package

Patch sources for golden **1.40MIDISC5** on OS 1.40C (splash `1.40MDISC5`).

```bash
python tools/build_midisc40.py
```

Needs your own 1.40C. See root README + `docs/TECH.md` + `docs/FLASHING.md`.

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

