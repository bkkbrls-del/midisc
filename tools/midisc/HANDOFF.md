# midisc 1.40MIDISC8.2 (safe)

**Flash:** `~/Desktop/1.40MIDISC8.2.bin`  
**Splash:** `MIDISC8.2`  
**Rebuild:** `$env:PYTHONPATH="tools"; python -m tools.midisc.build`

MIDISC8 scenes/Part lifecycle. CC48/55/56 filter **off** (on hold).

**CHAN T1–T8 internal route: DISABLED** (`ENABLE_MIDI_T_ROUTE = False`).
Code remains in `midi_route.py`. First flash bricked on encoder turns / trigs;
NOTE SETUP did not draw T1–T8 correctly; main UI showed `CH:17` for T1.
Do not re-enable until UART/rebuild/inject are fixed and main-UI CHAN format is patched.
