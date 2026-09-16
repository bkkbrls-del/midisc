# midisc — `1.40MIDISC8.2`

ColdFire patch that adds **MIDI scene locks** to official Octatrack **OS 1.40C**.

There is **no prebuilt firmware in this repo**. Rebuild from your own 1.40C, or use
**https://bkkbrls-del.github.io/midisc-patcher/**

## Behaviour

- MIDI track scene A/B locks + XF morph between scenes and step plocks
- Part Save/Reload/Yes/Paste, project/bank lock retention (MIDISC8 set)
- MIDI NOTE SETUP **CHAN `T1`–`T8`**: notes/CC out → that audio track’s MIDI-in (internal)
- MIDI CONTROL CC48/55/56 filter: **on hold**

Shipped map: `tools/midisc/HANDOFF.md`. Tech: `docs/TECH.md`.

## Rebuild

```bash
python tools/build_midisc40.py
# or: $env:PYTHONPATH="tools"; python -m tools.midisc.build
```

Desktop: **`1.40MIDISC8.2.bin`** (splash `MIDISC8.2`). No golden copy.

## Safety

Modified OS can brick the unit. Do not share built `.bin` / `.syx`. MIT for this
repo’s code/docs only — not Elektron firmware.
