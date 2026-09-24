# midisc 1.40MIDISC8.2

**Flash:** `~/Desktop/1.40MIDISC8.2.bin`  
**Splash:** `1.40MDIS82`  
**Rebuild:** `$env:PYTHONPATH="tools"; python -m tools.midisc.build`

## vs 1.40MIDISC8.1

1. Track-1 scene locks isolated (`xf_mix` LFO probes use `track*32+param`).
2. Unlocked params send CC again (no `voice_reload` into `d2` on write).

Otherwise same as 8.1: MIDISC8 scenes + Part lifecycle, no CC48/55/56 filter
(`ENABLE_MIDI_CTRL_FILTER = False`). Desktop bin only.
