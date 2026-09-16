# midisc 1.40MIDISC8.2

**Flash:** `~/Desktop/1.40MIDISC8.2.bin`  
**Splash:** `MIDISC8.2`  
**Rebuild:** `$env:PYTHONPATH="tools"; python -m tools.midisc.build`

MIDISC8 scenes/Part lifecycle. CC48/55/56 filter still **off** (on hold).

**New:** MIDI NOTE SETUP `CHAN` = `T1`–`T8` routes that MIDI track’s note/CC out
**internally** into audio track 1–8 MIDI-in (no DIN/USB). Values `OFF` / `1`–`16`
unchanged. Requires Project **AUDIO NOTE IN** / **AUDIO CC IN** as for external MIDI.
