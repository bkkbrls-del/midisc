# MIDISC2.0 technical notes

Public release of the hardware MIDI-scenes line (internal MIDISC8.20 bytes), rebuilt from stock 1.40C via a sparse MAIN patch.

## Build

`tools/midisc/release20.py` loads `release20.json`, checks stock MAIN SHA256, applies only the listed writes, checks the patched MAIN SHA256, then repacks a card `.bin` (version string `MIDISC2.0`).

DSP payload bytes are untouched. Older `gas/*.s` / Python generators describe earlier implementations; **the JSON manifest is authoritative** for this release.

## Behaviour notes (vs 8.2)

- Pre-trig XF / scene activation uses the published playback path without waiting for a first trig.
- Queued pattern/Part scene publication follows the native first-step boundary; manual Part apply publishes immediately.
- On sequencer ACT bank/pattern commit (`0x400a44f4`), `play_bank` / `play_part` follow that pattern's Part immediately and invalidate the XF context cache. Scene rebuild runs on the next `playback_step` (full register save). The sync cave must **RTS** for the JSR hook — a JMP resume left a dead return on the stack and froze the sequencer.
- `due_unlocked` respects the native active-lock mask so scene refresh does not replace an unscened live lock.
- Native CC loops run before same-track note-ons.
- Recorder / master playback descriptors restored where earlier caves had overwritten them; scene scratch moved off native clipboard addresses.
