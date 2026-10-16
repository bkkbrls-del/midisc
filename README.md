# midisc — `MIDISC2.2`

ColdFire patch that adds **MIDI scene locks** to official Octatrack **OS 1.40C**.

**MIDISC2.2** is the exact **MIDISC4.0** engine (`midisc21` / OKMSMD2.0 line): same MAIN
patch as release21, shipped under the MIDISC2.2 name. There is **no prebuilt
firmware in this repo**. Rebuild from your own 1.40C.

Browser patcher:  
https://bkkbrls-del.github.io/midisc-patcher/

## GNU-as caves for octabam (`gas/`)

`gas/` holds the MIDISC4.0 `midisc21` cave clusters (linked DRAM units + glue).
Stock-site rewrites are in `tools/midisc/hooks21.py`.

To regenerate the `.skip`-gap form from the release JSON (optional):

```bash
OCTABAM=~/octabam PYTHONPATH=tools python3 tools/gas_port21.py
```

That proves each `msc21_{a,b,c}` cluster against the release MAIN image and
exports `engine_follow`, `msc_follow`, `msc_kit_commit` for KITS. The older
`tools/gas_port.py` path still regenerates 8.x encoder caves; it does **not**
match release22.

## Build

```bash
powershell -ExecutionPolicy Bypass -File scripts/fetch-os.ps1   # or scripts/fetch-os.sh
python tools/build_midisc40.py
```

Writes **`MIDISC2.2.bin`** to your Desktop (splash `MIDISC2.2`). Flash from CF root → OS UPGRADE.

The build applies `tools/midisc/release22.json` to hash-checked stock MAIN.

## Safety

Modified OS can brick the unit; not affiliated with Elektron; flash at your own risk.  
**Do not share built `.bin` files** (they contain Elektron’s OS).

*Octatrack* / *Elektron* — trademarks of Elektron Music Machines MAV AB.

## License

MIT for this repo’s code and docs. Not for Elektron firmware.
