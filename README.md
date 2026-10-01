# midisc — `MIDISC2.0`

ColdFire patch that adds **MIDI scene locks** to official Octatrack **OS 1.40C**.

There is **no prebuilt firmware in this repo**. Rebuild from your own 1.40C.

Browser patcher (still 8.2 until updated):  
https://bkkbrls-del.github.io/midisc-patcher/

## Changes from `1.40MIDISC8.2`

1. **No first trig needed** — scenes / XF work before playback starts.
2. **Timing** — scene changes land at the real queued pattern / Part boundary; manual Part confirm is immediate.
3. **Active trig locks hold** — an unscened lock (including ARP OFF?ON) survives scene/XF refresh until the native lock ends.
4. **CC before notes** — native CC values go out before same-track note-ons.
5. **Crash fixes** — FUNC+REC2 and master-track descriptor repairs; scene scratch kept off native clipboards.

Everything else from 8.2 stays (track×32 isolation, unlocked CC path, Part save/reload freeze, etc.).

## Build

```bash
powershell -ExecutionPolicy Bypass -File scripts/fetch-os.ps1   # or scripts/fetch-os.sh
python tools/build_midisc40.py
```

Writes **`MIDISC2.0.bin`** to your Desktop (splash `MIDISC2.0`). Flash from CF root ? OS UPGRADE.

The build applies `tools/midisc/release20.json` to hash-checked stock MAIN. That manifest is the source of truth for this release.

## Safety

Modified OS can brick the unit; not affiliated with Elektron; flash at your own risk.  
**Do not share built `.bin` files** (they contain Elektron’s OS).

*Octatrack* / *Elektron* — trademarks of Elektron Music Machines MAV AB.

## License

MIT for this repo’s code and docs. Not for Elektron firmware.
