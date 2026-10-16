# Flashing a build of `MIDISC2.2`

This project does **not** ship a `.bin`. Build first:

```bash
python tools/build_midisc40.py
```

Output: `~/Desktop/MIDISC2.2.bin` (splash `MIDISC2.2`) and
`out/OCTATRACK_MIDISC2.2.syx`.

## Install

1. Back up projects.
2. Copy **that build's** `MIDISC2.2.bin` to the CompactFlash **root**.
3. On the unit: **OS UPGRADE** (same as an official update).
4. Confirm version **`MIDISC2.2`**.

## Recovery

Keep stock **1.40C** offline.

- MIDI: official `OCTATRACK_OS1.40C.syx` (FUNC+power -> MIDI OS upgrade), or  
- CF: stock `OCTATRACK_OS1.40C.bin` on the card root -> OS UPGRADE.

## Safety

Modified firmware can leave the unit unusable and puts warranty/support in
question. Not endorsed by Elektron. Flash at your own risk.

*Octatrack* / *Elektron* — trademarks of Elektron Music Machines MAV AB.
