# Flashing a build of `1.40MIDISC8.2`

This project does **not** ship a `.bin`. Build first:

```bash
python tools/build_midisc40.py
```

Output: `~/Desktop/1.40MIDISC8.2.bin` (splash `1.40MDIS82`) and
`out/OCTATRACK_1.40MIDISC8.2.syx` (name may vary by repack helper).

## Install

1. Back up projects.
2. Copy **that build's** `1.40MIDISC8.2.bin` to the CompactFlash **root**.
3. On the unit: **OS UPGRADE** (same as an official update).
4. Confirm version **`1.40MDIS82`**.

## Recovery

Keep stock **1.40C** offline.

- MIDI: official `OCTATRACK_OS1.40C.syx` (FUNC+power -> MIDI OS upgrade), or  
- CF: stock `OCTATRACK_OS1.40C.bin` on the card root -> OS UPGRADE.

## Safety

Modified firmware can leave the unit unusable and puts warranty/support in
question. Not endorsed by Elektron. Flash at your own risk.

*Octatrack* / *Elektron* — trademarks of Elektron Music Machines MAV AB.
