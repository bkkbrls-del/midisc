# T-route WIP — disabled after HW brick (2026-09-15)

## Symptoms
- Soft-brick / hang on **encoder turns** and **trigs**
- NOTE SETUP: T1–T8 labels not drawn correctly
- Main (non-setup) UI shows **CH:17** for T1 (raw enum), not `T1`

## What shipped then rolled back
`ENABLE_MIDI_T_ROUTE` in `midi_route.py` — set **False**. Cave/hooks not applied.
Desktop/patcher **1.40MIDISC8.2** is N8.1 behavior again (scenes only).

## Likely causes to investigate
1. **`FUN_40010bc8` entry trampoline** — affects all MIDI out; wrong stock replay → hang on any TX (trig/CC)
2. **Rebuild hook `0x40001854`** — runs often; ABI/branch target wrong → route table trash
3. **Inject cave `0x4010C350`** — unproven pad; prefer known CODE islands
4. **Formatter** — only `NOTE_E+0x11a` patched; main CH: display is another path (find `CH:` / channel draw)

## Keep
All of `midi_route.py` logic for next attempt — do not delete.
