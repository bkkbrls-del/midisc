# midisc 1.40MIDISCc

**Rebuild:** `$env:PYTHONPATH="tools"; python -m tools.midisc.build`  
**Output:** `~/Desktop/1.40MIDISCc.bin` · splash `1.40MDISCc` (≤10)

MSCN6 morph + CC48/55/56 filter (YES-safe) + Octakit `part_window` seam.

## Fixes vs MIDISCb

- CONTROL YES uses PERSONALIZE `(flag+delta)&1` — no more brick / stuck-off
- Checked (DRAM 0, default) = CC **ON**; unchecked = **OFF**

## Octakit seam (Sam 13 Sep)

| Item | Behaviour |
|------|-----------|
| `part_window` @ `SEAM_CAVE` | IN d3=index → OUT a0=window, d1=stride, d3&=0xFF. Lock store = a0+`SPARSE_OFF`. Override this one routine for kit base. |
| `KITS_GATE` DRAM u8 | 0=stock; nonzero → `bank_switch`/`bank_invalidate` skip part-set coupling |
| `STOCK_APPLY` | still stock (she owns `0x40009094`) |
| Write-into-kit protocol | still last-mile on her side (not a pointer) |

Do not force-push `main`. Do not redistribute built images.
