# midisc 1.40MIDISC8 (golden)

**Rebuild:** `$env:PYTHONPATH="tools"; python -m tools.midisc.build`  
**Output:** `~/Desktop/1.40MIDISC8.bin` · golden `~/Desktop/1.40MIDISC68GOLDEN.bin`  
**Splash:** `1.40MDISC8` (≤10)

HW-confirmed: Part Save / Reload / reboot edit persistence, instant part Yes
(MIDI), Part Paste stays on current part.

## Highlights

- **Pack:** working→shadow→PART_PROJECT + PART_SAVED; freeze twin untouched
- **Part Save:** parks FREEZE_SPARSE_OFF; STOCK_SAVE + CKPT/MSC_CKPT
- **Part Reload:** MSC_CKPT → freeze-alt → unpack + pack + xf_mix
- **Part Yes:** apply_bridge syncs PART_DISP + PAT_ACTIVE, unpack + xf_mix now
- **Part Paste:** stock APPLY_WAIT_BNE (no select other parts)
- **CC48/55/56:** MIDI CONTROL ticks (session DRAM; reboot persist TODO)
- STOCK_APPLY head stock; Octakit PART_WINDOW seam; DRAM `0x460C9A00+` (not `0x47fc…`)
