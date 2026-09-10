# midisc technical notes (`1.40MIDISC`)

Working facts used by the patch. Base: stock **1.40C** MAIN OS.

## MIDI param pages

UI `PAGE_MODE` at `0x460D1684`. Flat index = `PAGE_MODE * 6 + encoder` (0…5).

MIDI track page map (`FUN_40031da4`, track ≥ 8):

| PAGE_MODE | Page | Flats |
|-----------|------|-------|
| 0 | NOTE | 0–5 |
| 1 | LFO | 6–11 |
| 2 | ARP | 12–17 |
| 3 | CTRL1 | 18–23 |
| 4 | CTRL2 | 24–29 |

ARP knobs: TRAN, LEG, MODE, SPD, RNGE, NLEN.  
Descriptor counts (ARP): LEG=2, MODE=7, SPD=96, RNGE=8 → UI max 1 / 6 / 95 / 7.

Scene-lock clamp (`tools/midisc/hold.py`): if `PAGE_MODE == 2`, encoder =
`flat - 12`; clamp enc 1–4 to those maxes; else 0–127.

## Storage

- Working MSC bank in DRAM cave (`MSC` in `memory_map.py`)
- Persist: sparse pad in part window at bank `+0x90522`, magic u16 `MS` (`0x4D53`)
- Pack/unpack + durable commit on part save (`parts.py`)

## LEDs

Solid green lock LEDs: nop grey-enter / skip paths; track/page addi detour to
stubs that `rts` (see `build.py` + `memory_map.py` LED_* sites).

## Bank hooks

`build_bank_switch` / `build_bank_invalidate` preserve ColdFire regs across the
stock bank write so 1.40C sample load stays correct.

## Key RAM / ROM symbols

Defined in `tools/midisc/memory_map.py` (`PAGE_MODE`, `SCENE_HELD`, `MIDI_FLAG`,
caves, hook sites, sentinels). Addresses are 1.40C-specific.
