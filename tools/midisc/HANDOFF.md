# midisc 1.40MIDISC — handoff

**Flash:** `~/Desktop/1.40MIDISC.bin` (`python tools/build_midisc40.py`)  
**Version string:** `1.40MIDISC` (base OS 1.40C)

## Shipped

- Classic MSC sparse `+0x90522` / u16 `MS` / durable pack
- Bank hooks preserve regs (1.40C sample load)
- Solid green lock LEDs
- Scene-lock clamp on **ARP = PAGE_MODE 2** (stock `FUN_40031da4`):
  - MIDI pages: 0=NOTE, 1=LFO, **2=ARP**, 3=CTRL1, 4=CTRL2
  - flats 12–17; enc1 LEG 0–1, enc2 MODE 0–6, enc3 SPD 0–95, enc4 RNGE 0–7

Evidence: `docs/PARAM_PAGES.md` §5b; HW confirmed ARP clamp.

## Reproduce

Own copy of 1.40C only — never commit/share Elektron binaries. Root README.
