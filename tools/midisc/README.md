# midisc

Version `1.40MIDISC`. Base OS 1.40C.

```bash
python tools/build_midisc40.py
```

Output: `~/Desktop/1.40MIDISC.bin`

Read the root `README.md` before flashing. Do not share built `.bin` / `.syx`.

| file | contents |
|------|----------|
| `memory_map.py` | addresses, caves, hooks, `VER` |
| `parts.py` | pack / unpack / save / reload / clear / bank hooks |
| `hold.py` | scene hold, dial, encoder unlock, **ARP clamp** |
| `morph.py` | XF mix, morph, plock |
| `scene_ui.py` | scene clear / copy / paste |
| `emit.py` | shared MSC/xf helpers |
| `build.py` | link + patch + repack |
| `HANDOFF.md` | what `1.40MIDISC` ships |
