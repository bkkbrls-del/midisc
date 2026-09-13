# midisc 1.40MSCN6

**Rebuild:** `python tools/build_midisc40.py` (needs your own 1.40C)  
**Output:** `~/Desktop/1.40MSCN6.bin` · splash `1.40MSCN6` (≤10)  
**Syx:** `out/OCTATRACK_1.40MSCN6.syx`

## Contract

| Topic | Rule |
|-------|------|
| Empty XF side | `TRIG_SNAP` if step locked, else behind (`8f162`) |
| Locked side | MSC scene cell |
| `xf_mix` | writes `MIDI_VOICE`; also `LFO_BASE` for scene-locked flats |
| No scenes | stock plocks only (skip remix) |
| Mid-XF | no LFO row poke every step |
| Full A / full B | scene-locked flats forced onto LFO row (absolute scene) |
| Apply | `STOCK_APPLY` stays stock |
| Banks | Site A pack+publish+unpack; Site B publish+unpack only |
| Boot | xf2 in `SAFE_CAVE`; never body-hook `faf0`/`fbb4`; never `CLEAR_CAVE` |

Octakit compose notes: `docs/TECH.md` → *Compose with Octakit*.

Do not redistribute built images.
