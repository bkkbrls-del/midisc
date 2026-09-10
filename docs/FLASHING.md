# Flashing `1.40MIDISC`

## Flash

1. Copy `1.40MIDISC.bin` to the CompactFlash card root.
2. On the Octatrack: **OS UPGRADE** (same flow as an official OS update).
3. Confirm version string **`1.40MIDISC`**.

Back up projects first.

## Recovery

If the unit will not boot cleanly:

1. Official stock **`OCTATRACK_OS1.40C.syx`** via MIDI sysex upgrade  
   (FUNC+power → MIDI upgrade path on Elektron units), **or**
2. Put stock `OCTATRACK_OS1.40C.bin` on the CF root and run OS UPGRADE again.

Always keep a known-good stock 1.40C image offline. Never rely on a single
modified card image.

## Safety

Modified firmware can leave the unit unusable and puts warranty/support in
question. Not endorsed by Elektron. Flash at your own risk.

Do **not** redistribute built `.bin` / `.syx` files (they contain Elektron’s OS).
