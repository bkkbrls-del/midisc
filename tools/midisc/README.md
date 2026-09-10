# midisc package

Version `1.40MIDISC` on OS 1.40C.

```bash
python tools/build_midisc40.py
```

→ `~/Desktop/1.40MIDISC.bin`. See root README and `docs/FLASHING.md`.

| file | role |
|------|------|
| `memory_map.py` | addresses, caves, hooks |
| `parts.py` | pack / unpack / save / reload / bank |
| `hold.py` | hold, dial, unlock, ARP clamp |
| `morph.py` | XF mix / morph / plock |
| `scene_ui.py` | clear / copy / paste |
| `emit.py` | shared helpers |
| `build.py` | link + patch + repack |
| `HANDOFF.md` | shipped summary |
