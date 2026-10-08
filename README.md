# midisc — `MIDISC2.1`

ColdFire patch that adds **MIDI scene locks** to official Octatrack **OS 1.40C**.

There is **no prebuilt firmware in this repo**. Rebuild from your own 1.40C.

Browser patcher:  
https://bkkbrls-del.github.io/midisc-patcher/

## GNU-as caves for octabam (`gas/`)

MIDISC2.1 caves are regenerated from `release21.json` (not the 8.x encoder):

```bash
OCTABAM=~/octabam PYTHONPATH=tools python3 tools/gas_port21.py
```

That proves each `msc21_{a,b,c}` cluster against the release21 MAIN image and
exports `engine_follow`, `msc_follow`, `msc_kit_commit` for KITS. Stock-site
rewrites land in `tools/midisc/hooks21.py`. Gaps release21 does not write are
`.skip` (zeros) so no Elektron stock bytes enter the tree.

The older `tools/gas_port.py` path still regenerates 8.x encoder caves for
historical builds; it does **not** match release21.

## Build

```bash
powershell -ExecutionPolicy Bypass -File scripts/fetch-os.ps1   # or scripts/fetch-os.sh
python tools/build_midisc40.py
```

Writes **`MIDISC2.1.bin`** to your Desktop (splash `MIDISC2.1`). Flash from CF root → OS UPGRADE.

The build applies `tools/midisc/release21.json` to hash-checked stock MAIN.

## Safety

Modified OS can brick the unit; not affiliated with Elektron; flash at your own risk.  
**Do not share built `.bin` files** (they contain Elektron’s OS).

*Octatrack* / *Elektron* — trademarks of Elektron Music Machines MAV AB.

## License

MIT for this repo’s code and docs. Not for Elektron firmware.
